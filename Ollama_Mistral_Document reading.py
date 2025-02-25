from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import os

# 1. Create the model
llm = Ollama(model="mistral")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 2. Load multiple PDFs into a single list
pdf_folder = r"C:\Users\douaa\OneDrive\Desktop\DSS Program\simulation_exercise\pdf_folder"
pdf_paths = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith('.pdf')]

all_pages = []

for pdf_path in pdf_paths:
    loader = PyPDFLoader(pdf_path)
    all_pages.extend(loader.load_and_split())  # Append pages to one list

# 2.1 Document pre-processing
def preprocess_text(text):
    text = text.strip()
    text = " ".join(text.split())  # Remove extra whitespace
    text = re.sub(r'\b(References|Appendix)\b.*', '', text, flags=re.IGNORECASE)
    return text

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
all_pages = text_splitter.split_documents(all_pages)

# 3. Create a single vector store with all documents
store = DocArrayInMemorySearch.from_documents(all_pages, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 most relevant documents

# 4. Create the prompt template
template = """
You are an AI educator specializing in the course: "{course_name}". 
Use the uploaded course materials to provide structured lessons, answer questions, and give practical examples. 
If no materials are available, inform the user and provide general guidance. 
If a user asks something outside the course scope, politely guide them back to relevant topics.

Adapt your response based on message length, structure, and complexity:
- If the question is short and straightforward, provide a concise answer using bullet points or a brief summary.
- If the question is clear but requires explanation, give a structured response with key insights.
- If the input is long or includes multiple thoughts, offer a detailed response with sectioned explanations and examples.
- If the question is difficult to read or highly technical, simplify key concepts, define important terms, and include relatable examples.

Adjust formatting based on question type:
- When the user requests step-by-step instructions, break down the answer into a logical sequence.
- When comparing two or more concepts, present key similarities and differences in a clear structure, such as a list or a table.

Ensure all responses remain clear, relevant, and aligned with course materials rather than adding unnecessary detail.

Context:
{context}

Question:
{question}
"""

prompt = PromptTemplate.from_template(template)

# Debugging: Print retrieved documents
def format_docs(docs):
    print(f"\nRetrieved {len(docs)} relevant document sections:\n")
    for doc in docs:
        print(f"- {doc.metadata.get('source', 'Unknown Source')}: {doc.page_content[:200]}...\n")
    return "\n\n".join(doc.page_content for doc in docs)

# 5. Build the chain of operations
chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)

# 6. Print loaded documents
print("\nImported documents:")
for pdf_path in pdf_paths:
    print(f"- {os.path.basename(pdf_path)}")

print(f"\nLoaded {len(pdf_paths)} documents. You can now ask questions about them.")

# 7. Interactive Q&A
while True:
    question = input("\nWhat do you want to learn from the documents?\n")
    print()
    print(chain.invoke({"question": question}))
    print()
