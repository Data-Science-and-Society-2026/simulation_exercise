import os
import time
import subprocess
import re
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from difflib import get_close_matches
from typing import List
from collections import defaultdict


# ---- 1. LOAD OLLAMA MODEL & EMBEDDINGS ----
llm = Ollama(model="mistral", temperature=0.3)
embeddings = OllamaEmbeddings(model="nomic-embed-text")


# ---- 2. YOUYUBE VIDEO HANDLING ----
# Optional: Add your YouTube URLs here or leave the list empty
youtube_urls = [
    "https://www.youtube.com/watch?v=LQQbW3Pve5U",
    "https://www.youtube.com/watch?v=LLl3bQXhhzI",
    "https://www.youtube.com/watch?v=L8jWbCxvrOU",
    "https://www.youtube.com/watch?v=XFoehWRzG-I",
]

# Utilities for filenames & citations
def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_") # Cleans up a string so it can safely be used as a filename across different operating systems

def generate_youtube_citation(title, url):
    return f"{title}. (n.d.). Retrieved from {url}" # Generates a basic APA-style citation string for a YouTube video

# Transcribe and process YouTube videos
def process_youtube_videos(urls: List[str], output_dir: str) -> List[Document]:
    video_chunks = []

    for url in urls:
        print(f"\n🎥 Processing video: {url}")
        result = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True)
        video_title = result.stdout.strip()
        safe_title = clean_filename(video_title)

        # Define file paths for audio and transcript
        mp3_file = f"{safe_title}.mp3"
        txt_file = os.path.join(output_dir, f"{safe_title}.txt")

        # If transcript already exists, skip downloading and transcribing
        if os.path.exists(txt_file):
            print(f"Transcript already exists: {txt_file}")
        else:
            print("Downloading audio...")
            subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "--ffmpeg-location", "/opt/homebrew/bin", "-o", mp3_file, url], check=True) # Download audio as mp3 using yt-dlp

            print("Transcribing with Whisper...")
            subprocess.run(["whisper", mp3_file, "--model", "small", "--output_format", "txt"], check=True) # Transcribe audio using Whisper

            whisper_txt = mp3_file.replace(".mp3", ".txt")
            os.rename(whisper_txt, txt_file) # Rename output 
            print(f"Transcript saved to: {txt_file}")

        # Load the transcript text
        with open(txt_file, "r") as f:
            transcript = f.read()

        # Create structured LangChain Document chunks
        citation = generate_youtube_citation(video_title, url)
        chunks = text_splitter.create_documents([transcript])
        for chunk in chunks:
            chunk.page_content = f"=== Start of Video: {video_title} ===\n{chunk.page_content.strip()}\n=== End of Video: {citation} ==="
            chunk.metadata = {
                "source_title": video_title,
                "citation": citation,
                "source_type": "youtube"
            }
            video_chunks.append(chunk)

    return video_chunks


# ---- 3. PDF DOCUMENT HANDLING ----
# Folder where PDFs are stored
pdf_folder = os.getenv("PDF_FOLDER", r"/path/to/pdf/folder") # Change this to the path of the PDF folder
pdf_paths = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith(".pdf")]

# Text splitter for both PDFs and transcripts
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)
enhanced_chunks = []

# Extract title and citation from PDF path
def extract_title_from_path(pdf_path):
    return os.path.splitext(os.path.basename(pdf_path))[0].replace("_", " ")

def generate_simple_citation(title):
    return f"{title}. (n.d.). Retrieved from course materials."

# Load & process PDFs
for pdf_path in pdf_paths:
    loader = PyPDFLoader(pdf_path)
    pages = loader.load_and_split()
    title = extract_title_from_path(pdf_path)
    citation = generate_simple_citation(title)
    split_chunks = text_splitter.split_documents(pages)

    for chunk in split_chunks:
        content = f"=== Start of Article: {title} ===\n{chunk.page_content.strip()}\n=== End of Article: {citation} ==="
        enhanced_chunks.append(Document(
            page_content=content,
            metadata={
                "source_title": title,
                "citation": citation,
                "source_type": "pdf"
            }
        ))

# Combine all sources
video_chunks = process_youtube_videos(youtube_urls, pdf_folder) if youtube_urls else []
all_chunks = enhanced_chunks + video_chunks


# ---- 4. VECTORSTORE HANDLING ----
# Group chunks by their source title
chunks_by_title = defaultdict(list)
for doc in all_chunks:
    title = doc.metadata.get("source_title", "Unknown Title").lower()
    chunks_by_title[title].append(doc)

# Create per-title retrievers
retrievers_by_title = {
    title: DocArrayInMemorySearch.from_documents(docs, embedding=embeddings).as_retriever(search_kwargs={"k": 10})
    for title, docs in chunks_by_title.items()
}

# Create global retriever
global_retriever = DocArrayInMemorySearch.from_documents(all_chunks, embedding=embeddings).as_retriever(search_kwargs={"k": 10})

# For fuzzy matching titles
known_titles = list(set(doc.metadata["source_title"] for doc in all_chunks))


# ---- 5. STUDENT INFORMATION EXTRACTION ----
# Prompts to extract name, course, and level
name_prompt = PromptTemplate.from_template(
    "Extract the first name from this text: {text}. Only return the name, nothing else."
)
course_prompt = PromptTemplate.from_template(
    "Extract the course name from this text: {text}. Only return the course name, nothing else."
)
level_prompt = PromptTemplate.from_template(
    "Extract the familiarity level (Beginner, Intermediate, or Advanced) from this text: {text}. "
    "Only return one of these three words, nothing else."
)

# Prompt chains
extract_name_chain = name_prompt | llm | StrOutputParser()
extract_course_chain = course_prompt | llm | StrOutputParser()
extract_level_chain = level_prompt | llm | StrOutputParser()

# Helper functions
def get_student_name(user_input):
    return extract_name_chain.invoke({"text": user_input}).strip()

def get_course_name(user_input):
    return extract_course_chain.invoke({"text": user_input}).strip()

def get_familiarity_level(user_input):
    return extract_level_chain.invoke({"text": user_input}).strip()

# Capture student info
user_response = input("Hello, How can I call you? ")
student_name = get_student_name(user_response)

course_input = input(f"Nice to meet you, {student_name}! What course would you like me to teach? ")
course_name = get_course_name(course_input)

level_input = input(f"How familiar are you with {course_name}? (Beginner, Intermediate, Advanced): ")
familiarity = get_familiarity_level(level_input)

print(f"Great! I will be your tutor for {course_name} at the {familiarity} level. Let's begin!\n")


# ---- 6. AI TUTOR PROMPT SETUP ----
# Template for standalone question rephrasing
standalone_question_template = """
Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question.

Conversation History:
{chat_history}

Follow-up Question:
{question}

Standalone Question:
"""
standalone_question_prompt = PromptTemplate.from_template(standalone_question_template)

# Main tutor response prompt template
tutor_response_template = """
### AI Role
Hey there! You’re an expert tutor who’s great at making learning fun and engaging, especially for the course: {course_name}. You explain things in a clear, friendly way and love using real-world examples. Keep things conversational and approachable!
Your goal is to guide students through structured lessons, answer their questions, and adapt to their learning needs—just like a great teacher would. If course materials are available, use them to provide solid explanations with practical examples. If not, no worries! Just offer general guidance while keeping things relevant and easy to follow.
If a student asks something outside the course, gently steer them back on track while keeping the conversation positive and engaging. Let’s make learning an enjoyable experience!”

### Conversational Continuity & Memory
Treat the entire interaction with the student as a continuous conversation. Keep track of the key points and questions raised during the session, and use them to inform future responses. This will help maintain coherence and ensure responses are relevant to the student's ongoing learning process. Adapt your explanations and teaching style based on the flow of the conversation and the student's evolving needs. Ensure that each response builds upon previous exchanges to keep the conversation dynamic and engaging.

### Effective AI Tutoring Approach
You are designed to reflect the qualities of an effective educator:
Begin by assessing the student's background knowledge based on {familiarity} and tailor your responses accordingly.
Provide accurate, expert-level knowledge while aligning with curriculum standards. Adapt teaching strategies using real-world applications and diverse instructional methods. 

Structure your responses based on the complexity and intent of the user’s input:
For short questions, provide brief, bullet-pointed answers.
For explanatory questions, provide well-structured, in-depth insights.
For complex or multi-part questions (e.g., a given code and error), provide detailed, sectioned explanations.
For unclear or highly technical questions, simplify the concepts and provide relatable examples.
Regardless, remember to maintain a positive and encouraging tone throughout the interaction, to motivate the student.

### Response Formatting
Adapt your response format based on the question and content:
Always include:
Contextual introduction  - start with a brief introduction about the topic at hand 
Concept explanation - provide structured answers using analogies and examples as needed.
Engagement - end with a relevant catchy question encouraging active learning.

When explaining processes or instructions:
Provide clear, step-by-step guidance
When comparing concepts:
Use structured comparisons (e.g., lists, tables, or prose explanations highlighting key differences and similarities)

### Linguistics and Formatting Guidelines
Avoid using explicit speech references, such as "point number one" or "firstly," to ensure the response is visually functional and does not require verbalization when converted to speech.

### Engagement
Encourage active learning by ending explanations with relevant, thought-provoking questions when appropriate. For example: ‘How do you think this concept applies to [real-world example]?’ Exceptions: If the user asks for a simple definition, quick fact, or straightforward procedural step, do not include a follow-up question unless clarification is likely needed.

### Personalized Feedback
Use {student_name}’s name whenever possible to make learning feel more personal and engaging. Celebrate their progress and offer helpful suggestions to keep them moving forward.
Try responses like:
💡 “Nice work, {student_name}! You’ve got the hang of this. If you want to take it a step further, try exploring [related topics]—it connects really well with what you just learned!”
🌟 “Great thinking! If you want a fresh perspective, how about explaining this concept using a real-world example? It’s a great way to make tricky ideas click!”
Keep the encouragement natural, and adjust your feedback based on how {student_name} is engaging with the topic. If they seem confident, challenge them with deeper questions. If they’re struggling, break things down step by step. The goal is to make learning feel exciting, achievable, and interactive!

### Referencing
- Strictly rely on the given course materials (no assumptions, no outside knowledge).
- Clearly reference the arguments made by different authors when applicable.
- Use APA 7 citation style for direct quotations and paraphrased ideas by including author(s) last name, year of publication, and page number (if applicable) - e.g., (Smith, 2022, p. 45).
- If multiple authors discuss a similar topic, compare and contrast their perspectives.

Use the provided context and conversation history to answer the student's question.

Course Materials Context:
{context}

Conversation History:
{chat_history}

Student's Question:
{question}

AI Tutor's Response:
"""
tutor_response_prompt = PromptTemplate.from_template(tutor_response_template)

# ---- 6. UTILITY FUNCTIONS ----
# Format retrieved documents for display
def format_docs(docs):
    formatted = []
    for doc in docs:
        title = doc.metadata.get("source_title", "Unknown Title")
        citation = doc.metadata.get("citation", "No citation available")
        excerpt = doc.page_content.strip()
        formatted.append(f"Title: {title}\n{excerpt}\n(Source: {citation})")
    return "\n\n".join(formatted)

# Generate a standalone question based on the chat history
def generate_standalone_question(question, chat_history):
    # Format the chat history
    formatted_history = "\n".join([f"Student: {msg['content']}" if msg['role'] == 'user' else f"AI Tutor: {msg['content']}" for msg in chat_history])
    # Create the prompt
    prompt = standalone_question_prompt.format(chat_history=formatted_history, question=question)
    # Generate the standalone question
    response = llm.invoke(prompt)
    return response.strip()
    
# Extract the title of a document from a question
def extract_title_from_question(question, known_titles):
    matches = get_close_matches(question.lower(), [t.lower() for t in known_titles], n=1, cutoff=0.6)
    if matches:
        for title in known_titles:
            if title.lower() == matches[0]:
                return title
    return None


# ---- 7. INTERACTIVE Q&A LOOP ----
chat_history = []

while True:
    user_input = input("Ask your AI tutor a question (or type 'exit' to quit): ")
    
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Goodbye! 👋")
        break

    # Start timing - for performance monitoring
    #start_time = time.time()

    # Generate a standalone question based on the chat history
    standalone_question = generate_standalone_question(user_input, chat_history)
    
    # Retrieve context documents
    # Check if question refers to a specific article
    mentioned_title = extract_title_from_question(standalone_question, known_titles)

    if mentioned_title and mentioned_title in retrievers_by_title:
        retriever = retrievers_by_title[mentioned_title]
    else:
        retriever = global_retriever

    retrieved_docs = retriever.invoke(standalone_question)
    
    context = format_docs(retrieved_docs)

    # Format the chat history for the tutor's response
    formatted_history = "\n".join([f"Student: {msg['content']}" if msg['role'] == 'user' else f"AI Tutor: {msg['content']}" for msg in chat_history])

    # Create the final prompt for the AI tutor's response
    final_prompt = tutor_response_prompt.format(
        course_name=course_name,
        student_name=student_name,
        familiarity=familiarity,
        context=context,
        chat_history=formatted_history,
        question=standalone_question
    )

    # Generate the AI tutor's response with streaming
    # Initialize an empty variable to store the full response
    full_response = ""

    # Streaming response from the Ollama model
    for chunk in llm.stream(final_prompt):
        content = chunk  # Ollama returns text chunks directly
        full_response += content
        print(content, end='', flush=True)  # Print in real-time

    # Add AI response to chat history
    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": full_response})

    # Calculate and display elapsed time - for performance monitoring
    #elapsed_time = time.time() - start_time
    #print(f"\n\n(Response generated in {elapsed_time:.2f} seconds)")
    
    print("\n" + "-" * 60)  # Divider for readability
