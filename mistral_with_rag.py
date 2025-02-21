import ollama
from ollama import chat
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os

# ---- 1. Load Ollama Model & Embeddings ----
llm = Ollama(model="mistral")
embeddings = OllamaEmbeddings(model="nomic-embed-text")  # Ensure a valid embedding model

# ---- 2. Load Multiple PDFs & Process Them ----
pdf_paths = [
    r"/Users/macbook/Desktop/BCs Data Science and Society/Term 4a/Simulation Exercise/information-14-00152.pdf",
    r"/Users/macbook/Desktop/BCs Data Science and Society/Term 4a/Simulation Exercise/The_Manifesto_Corpus_A_new_resource_for_research_o.pdf"
]

all_pages = []
for pdf_path in pdf_paths:
    loader = PyPDFLoader(pdf_path)
    all_pages.extend(loader.load_and_split())  # Append pages to one list

# ---- 3. Create a Vector Store for Document Retrieval ----
store = DocArrayInMemorySearch.from_documents(all_pages, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 relevant chunks

# ---- 4. Define the Tutoring System Prompt ----
system_prompt = """You are an AI tutor. Use the provided course materials to give structured responses, explain concepts clearly, and answer questions concisely.

- If the question is short, answer briefly.
- If it needs explanation, give structured insights.
- If complex, break it down into sections.
- If unclear, define terms and simplify.

Adjust formatting based on question type:
- When the user requests step-by-step instructions, break down the answer into a logical sequence.
- When comparing two or more concepts, present key similarities and differences in a clear structure, such as a list or a table.

Ensure all responses remain clear, relevant, and aligned with course_materials rather than adding unnecessary detail."""

# ---- 5. Define the RAG Prompt Template ----
template = """
Use only the context from the retrieved documents to answer the question. Do NOT use external knowledge.

Context:
{context}

Question:
{question}

Provide a clear, structured, and educational response.
"""

prompt = PromptTemplate.from_template(template)

# ---- 6. Function to Format Retrieved Docs ----
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# ---- 7. Define RAG Chain (Retrieval + Generation) ----
chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)

# ---- 8. Start Interactive Q&A ----
print("\n📚 AI Tutor is Ready! You can ask questions about the uploaded PDFs.\n")

while True:
    user_input = input("Ask your AI tutor a question (or type 'exit' to quit): ") # this is for a typed question, this part should be altered to take the verbal user input
    
    if user_input.lower() == 'exit':
        print("Goodbye! 👋")
        break

    # Generate response from RAG pipeline
    response = chain.invoke({"question": user_input})

    # Use streaming chat from Ollama to refine response
    stream = chat(
        model="mistral",
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': response}
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

    print("\n💡 AI Tutor's Response:\n")
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)

    print("\n" + "-" * 60)  # Divider for better readability