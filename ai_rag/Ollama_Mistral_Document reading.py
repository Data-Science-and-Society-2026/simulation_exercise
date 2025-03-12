from ollama import chat
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
import os
import time
from functools import lru_cache

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
student_name = input("Hello! What is your name? ")
course_name = input(f"Nice to meet you, {student_name}! What course would you like me to teach? ")
familiarity = input(f"How familiar are you with {course_name}? (Beginner, Intermediate, Advanced): ")

print(f"Great! I will be your tutor for {course_name}. Let's begin!\n")

# ---- 5. The Tutoring System Prompt ----
system_prompt = f""" 
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

The following information was retrieved from course materials based on the student's question:
{{context}}

Conversation History: {{history}}

Student question: {{question}}

"""

# ---- 6. Function to Format Retrieved Docs ----
def format_docs(docs):
    return " ".join([doc.page_content.strip() for doc in docs])  # Strip whitespace, single space between pages

# ---- 7. Start Interactive Q&A ----
# Simple cache for frequent queries
@lru_cache(maxsize=32)
def get_cached_response(question):
    # Retrieve context documents
    retrieved_docs = retriever.invoke(question)
    formatted_context = format_docs(retrieved_docs)
    return formatted_context

# **NEW**: Store conversation history
conversation_history = []

while True:
    user_input = input("Ask your AI tutor a question (or type 'exit' to quit): ")
    
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("Goodbye! 👋")
        break
    
    # Start timing
    start_time = time.time()
        
    # Get context from retriever (with caching for repeat questions)
    context = get_cached_response(user_input)


    # **NEW**: Format conversation history (last 5 exchanges for memory)
    formatted_history = "\n".join([
        f"{'AI TUTOR' if msg['role'] == 'assistant' else 'STUDENT'}: {msg['content']}" 
        for msg in conversation_history[-5:]  # Keep only the last 5 messages
    ])

    # Create final prompt with context and system instructions
    final_prompt = system_prompt.format(
        context=context,
        question=user_input,
        history=formatted_history
    )
    
    # Single LLM call with streaming
    print("\n💡 AI Tutor's Response:\n")
    stream = chat(
        model="mistral",
        messages=[
            {'role': 'system', 'content': final_prompt},
            {'role': 'user', 'content': user_input}
        ],
        stream=True,
        options={
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 1.0,
            "frequency_penalty": 1.2,
            "seed": 42
        }
    )
    
   # **NEW**: Store user input in conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Display streaming response and store AI's reply
    full_response = ""
    for chunk in stream:
        content = chunk['message']['content']
        full_response += content
        print(content, end='', flush=True)

    # **NEW**: Store AI's response in conversation history
    conversation_history.append({"role": "assistant", "content": full_response})

    # Calculate and display elapsed time
    elapsed_time = time.time() - start_time
    print(f"\n\n(Response generated in {elapsed_time:.2f} seconds)")
        
    print("\n" + "-" * 60)  # Divider for readability
