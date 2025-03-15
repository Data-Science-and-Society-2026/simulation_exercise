from langchain_community.llms import Ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
import os
import subprocess
import re

# 1. Create the model
llm = Ollama(model="mistral")
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# List of YouTube video URLs
video_urls = [
    "https://www.youtube.com/watch?v=LQQbW3Pve5U",
    "https://www.youtube.com/watch?v=LLl3bQXhhzI",
    "https://www.youtube.com/watch?v=L8jWbCxvrOU",
    "https://www.youtube.com/watch?v=XFoehWRzG-I",
]

# Set paths
pdf_folder = "ai_rag/pdf_folder"
os.makedirs(pdf_folder, exist_ok=True)

# Function to clean video title for filenames
def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_")

# Process each video
for url in video_urls:
    print(f"\n🔹 Processing video: {url}")

    # Get video title
    print("📌 Fetching video title...")
    result = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True)
    video_title = result.stdout.strip()
    clean_title = clean_filename(video_title)

    # Define filenames
    audio_file = f"{clean_title}.mp3"
    transcript_file = os.path.join(pdf_folder, f"{clean_title}.txt")

    if os.path.exists(transcript_file):
        print(f"✅ Transcript already exists: {transcript_file}")
        continue

    # Download audio
    print("⏳ Downloading audio...")
    subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio_file, url], check=True)

    # Transcribe using Whisper
    print("🎙️ Transcribing with Whisper...")
    subprocess.run(["whisper", audio_file, "--model", "small", "--output_format", "txt"], check=True)

    # Save transcript
    whisper_output_file = audio_file.replace(".mp3", ".txt")
    with open(whisper_output_file, "r") as f:
        transcript_text = f.read()

    with open(transcript_file, "w") as f:
        f.write(transcript_text)

    print(f"✅ Transcript saved as: {transcript_file}")

print("\n🎉 All videos processed! Transcripts are now in 'pdf_folder'.")

# 2. Load PDFs
pdf_paths = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith('.pdf')]
all_pages = []

for pdf_path in pdf_paths:
    loader = PyPDFLoader(pdf_path)
    all_pages.extend(loader.load_and_split())

# 3. Load transcripts
transcript_paths = [os.path.join(pdf_folder, file) for file in os.listdir(pdf_folder) if file.endswith('.txt')]

for transcript_path in transcript_paths:
    with open(transcript_path, "r") as f:
        transcript_text = f.read()
    doc = Document(page_content=transcript_text, metadata={"source": transcript_path, "type": "YouTube Transcript"})
    all_pages.append(doc)

print(f"Loaded {len(pdf_paths)} PDFs and {len(transcript_paths)} transcripts.")

# 4. Create vector store
store = DocArrayInMemorySearch.from_documents(all_pages, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 5})

# 5. Create prompt template
template = """
Answer the question based only on the context provided.

Context:
{context}

Question:
{question}
"""

prompt = PromptTemplate.from_template(template)

# 6. Debugging: Print retrieved documents
def format_docs(docs):
    print(f"\nRetrieved {len(docs)} relevant document sections:\n")
    for doc in docs:
        print(f"- {doc.metadata.get('source', 'Unknown Source')}: {doc.page_content[:200]}...\n")
    return "\n\n".join(doc.page_content for doc in docs)

# 7. Build the chain
chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)

# 8. Interactive Q&A
print("\nLoaded documents. You can now ask questions about them.")
while True:
    question = input("\nWhat do you want to learn from the documents?\n")
    print()
    print(chain.invoke({"question": question}))
    print()
