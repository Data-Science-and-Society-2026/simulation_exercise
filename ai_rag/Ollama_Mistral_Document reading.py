from ollama import chat
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
import os
import time
from functools import lru_cache

from ai_rag.prompt import ai_prompt

# ---- 1. Load Ollama Model & Embeddings ----
llm = Ollama(model="mistral")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# ---- 2. Load Multiple PDFs & Process Them ----
pdf_folder = os.getenv(
    "PDF_FOLDER",
    r"/Users/macbook/Desktop/BCs Data Science and Society/Term 4a/Simulation Exercise/simulation_exercise-1/ai_rag/pdf_folder",
)
pdf_paths = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith(".pdf")]

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

system_prompt = ai_prompt(course_name, familiarity, student_name)

print(f"Great! I will be your tutor for {course_name}. Let's begin!\n")


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

    if user_input.lower() in ["exit", "quit", "bye"]:
        print("Goodbye! 👋")
        break

    # Start timing
    start_time = time.time()

    # Get context from retriever (with caching for repeat questions)
    context = get_cached_response(user_input)

    # **NEW**: Format conversation history (last 5 exchanges for memory)
    formatted_history = "\n".join(
        [
            f"{'AI TUTOR' if msg['role'] == 'assistant' else 'STUDENT'}: {msg['content']}"
            for msg in conversation_history[-5:]  # Keep only the last 5 messages
        ]
    )

    # Create final prompt with context and system instructions
    final_prompt = system_prompt.format(context=context, question=user_input, history=formatted_history)

    # Single LLM call with streaming
    print("\n💡 AI Tutor's Response:\n")
    stream = chat(
        model="mistral",
        messages=[{"role": "system", "content": final_prompt}, {"role": "user", "content": user_input}],
        stream=True,
        options={"temperature": 0.7, "top_p": 0.9, "presence_penalty": 1.0, "frequency_penalty": 1.2, "seed": 42},
    )

    # **NEW**: Store user input in conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Display streaming response and store AI's reply
    full_response = ""
    for chunk in stream:
        content = chunk["message"]["content"]
        full_response += content
        print(content, end="", flush=True)

    # **NEW**: Store AI's response in conversation history
    conversation_history.append({"role": "assistant", "content": full_response})

    # Calculate and display elapsed time
    elapsed_time = time.time() - start_time
    print(f"\n\n(Response generated in {elapsed_time:.2f} seconds)")

    print("\n" + "-" * 60)  # Divider for readability
