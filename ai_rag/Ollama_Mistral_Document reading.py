from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os

# 1. Create the model
llm = Ollama(model="mistral")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 2. Load multiple PDFs into a single list
pdf_folder = r".\pdf_folder"
pdf_paths = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith('.pdf')]

all_pages = []

for pdf_path in pdf_paths:
    loader = PyPDFLoader(pdf_path)
    all_pages.extend(loader.load_and_split())  # Append pages to one list

# 3. Create a single vector store with all documents
store = DocArrayInMemorySearch.from_documents(all_pages, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 most relevant documents

# 4. Create the prompt template
template = """
Answer the question based only on the context provided.

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
