import os
from langchain_community.vectorstores import DocArrayInMemorySearch

from chat_tutor import settings

VECTOR_STORE = None


class VectorStorage:
    def __init__(self, pages, embeddings) -> None:
        self.store = DocArrayInMemorySearch.from_documents(pages, embeddings)
        self.retriever = self.store.as_retriever()


def get_vector_store(model):
    global VECTOR_STORE
    if VECTOR_STORE is None:
        print("Processing PDFs and creating vector store...")
        files_folder = os.path.join(settings.MEDIA_ROOT, "files")
        pdf_paths = [os.path.join(files_folder, file) for file in os.listdir(files_folder) if file.endswith(".pdf")]
        if pdf_paths:
            from langchain.document_loaders import PyPDFLoader

            all_pages = []
            for pdf_path in pdf_paths:
                loader = PyPDFLoader(pdf_path)
                all_pages.extend(loader.load_and_split())
            VECTOR_STORE = VectorStorage(all_pages, model.embeddings)
        else:
            VECTOR_STORE = None
    else:
        print("Using cached vector store.")
    return VECTOR_STORE
