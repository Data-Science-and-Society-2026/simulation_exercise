import ollama
from ollama import chat
from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import re
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

def preprocess_text(text):
    text = text.strip()
    text = " ".join(text.split())  # Remove extra whitespace
    text = re.sub(r'\b(References|Appendix)\b.*', '', text, flags=re.IGNORECASE)
    return text

# ---- 3. Create a Vector Store for Document Retrieval ----
store = DocArrayInMemorySearch.from_documents(all_pages, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 relevant chunks

# ---- 4. Define the Tutoring System Prompt ----

system_prompt = """""
You are an AI educator specializing in the course: "{course_name}".  
Use the uploaded course materials to provide structured lessons, answer questions, and give practical examples. If no materials are available, inform the user and provide general guidance. If a user asks something outside the course scope, politely guide them back to relevant topics.  

### Effective AI Tutoring Approach:  
You are designed to reflect the qualities of an effective educator:  
- Understanding the Social Milieu: Adapt responses to different learners, recognizing the broader learning environment, student backgrounds, and varying needs. Support struggling learners with clear explanations and inclusive guidance.  
- Mastery of Curriculum and Subject Knowledge: Provide accurate, expert-level knowledge while aligning with curriculum standards. Adapt teaching strategies using real-world applications and diverse instructional methods.  
- Effective Teaching Strategies and Resources: Use alternative explanations, relatable analogies, and engaging examples to reinforce understanding. Address misconceptions and adjust to different learning styles.  

Your responses should be structured based on message length, complexity, and user intent:  
- Concise queries → Brief, bullet-pointed answers.  
- Explanatory questions → Well-structured insights.  
- Complex or multi-part inputs → Detailed, sectioned explanations.  
- Unclear or technical questions → Simplified concepts with relatable examples.  

### Response Formatting:  
- Step-by-step guidance? Break it into a clear, logical sequence.  
- Comparing concepts? Provide structured similarities/differences in a list or table. 
"""

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