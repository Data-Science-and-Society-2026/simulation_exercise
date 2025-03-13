from ollama import chat
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
import os
import time

# ---- 1. Load Ollama Model & Embeddings ----
llm = Ollama(model="mistral")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# ---- 2. Load Multiple PDFs & Process Them ----
pdf_folder = os.getenv('PDF_FOLDER', r"/Users/macbook/Desktop/BCs Data Science and Society/Term 4a/Simulation Exercise/simulation_exercise-1/ai_rag/pdf_folder")
pdf_paths = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith('.pdf')]

all_pages = []
for pdf_path in pdf_paths:
    loader = PyPDFLoader(pdf_path)
    all_pages.extend(loader.load_and_split())  # Append pages to one list

# ---- 3. Create a Vector Store for Document Retrieval ----
store = DocArrayInMemorySearch.from_documents(all_pages, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 3})  # Retrieve top 3 relevant chunks

# ---- 4. Get Student's Information ----
# ---- 4. Get Student's Information ----
# --- Define Prompts ---
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

# --- Create Processing Chains ---
extract_name_chain = name_prompt | llm | StrOutputParser()
extract_course_chain = course_prompt | llm | StrOutputParser()
extract_level_chain = level_prompt | llm | StrOutputParser()

# --- Define Functions ---
def get_student_name(user_input):
    return extract_name_chain.invoke({"text": user_input}).strip()

def get_course_name(user_input):
    return extract_course_chain.invoke({"text": user_input}).strip()

def get_familiarity_level(user_input):
    return extract_level_chain.invoke({"text": user_input}).strip()

# --- User Input & AI Extraction ---
user_response = input("Hello, How can I call you? ")
student_name = get_student_name(user_response)

course_input = input(f"Nice to meet you, {student_name}! What course would you like me to teach? ")
course_name = get_course_name(course_input)

level_input = input(f"How familiar are you with {course_name}? (Beginner, Intermediate, Advanced): ")
familiarity = get_familiarity_level(level_input)

print(f"Great! I will be your tutor for {course_name} at the {familiarity} level. Let's begin!\n")

# ---- 5. Define Prompt Templates ----
# Template for standalone question generation
standalone_question_template = """
Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question.

Conversation History:
{chat_history}

Follow-up Question:
{question}

Standalone Question:
"""

standalone_question_prompt = PromptTemplate.from_template(standalone_question_template)

# Template for the AI tutor's response
tutor_response_template = """
### AI Role
You are an autonomous AI educator specializing in the course: {course_name}, capable of independently guiding students through structured lessons, answering questions, and dynamically adapting to their learning needs without requiring constant human intervention.
Use the uploaded course materials to provide these structured lessons along with real-world examples. If no materials are available, inform the user and provide general guidance while ensuring responses remain aligned with educational frameworks. If a user asks something outside the course scope, politely guide them back to relevant topics. 

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
When applicable use {student_name} to personalize responses.
Offer tailored suggestions that acknowledge progress and guide further learning. For example:
"Great job applying this concept! To further develop your understanding, consider exploring [related topics]."
“Your analysis is excellent! If you'd like a different perspective, try explaining this concept using an analogy or real-world example — can make complex ideas more relatable.”

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

# ---- 6. Function to Format Retrieved Docs ----
def format_docs(docs):
    return "\n\n".join([f"Document Excerpt:\n{doc.page_content.strip()}" for doc in docs])

# ---- 7. Initialize Chat History ----
chat_history = []

# ---- 8. Function to Generate Standalone Question ----
def generate_standalone_question(question, chat_history):
    # Format the chat history
    formatted_history = "\n".join([f"Student: {msg['content']}" if msg['role'] == 'user' else f"AI Tutor: {msg['content']}" for msg in chat_history])
    # Create the prompt
    prompt = standalone_question_prompt.format(chat_history=formatted_history, question=question)
    # Generate the standalone question
    response = llm(prompt)
    return response.strip()

# ---- 9. Interactive Q&A Loop ----
while True:
    user_input = input("Ask your AI tutor a question (or type 'exit' to quit): ")
    
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Goodbye! 👋")
        break

    # Start timing
    start_time = time.time()

    # Generate a standalone question based on the chat history
    standalone_question = generate_standalone_question(user_input, chat_history)
    
    # Retrieve context documents
    retrieved_docs = retriever.get_relevant_documents(standalone_question)
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

    # Calculate and display elapsed time
    elapsed_time = time.time() - start_time
    print(f"\n\n(Response generated in {elapsed_time:.2f} seconds)")
    print("\n" + "-" * 60)  # Divider for readability
