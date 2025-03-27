from django.apps import AppConfig
import os
from django.conf import settings
from modules.ai_rag.model import get_model
from modules.ai_rag.vector_storage import VectorStorage
from modules.ai_rag.utils import format_docs  # if needed

MODEL_INSTANCE = None
VECTOR_STORE = None


class ChatConfig(AppConfig):
    name = "chat"

    def ready(self):
        global MODEL_INSTANCE, VECTOR_STORE  # loading model
        MODEL_INSTANCE = get_model("mistral")
        print("Preloaded model instance.")

        # Precompute the vector store from PDFs if available
        files_folder = os.path.join(settings.MEDIA_ROOT, "files")
        pdf_paths = [os.path.join(files_folder, file) for file in os.listdir(files_folder) if file.endswith(".pdf")]
        if pdf_paths:
            print("Processing PDFs for vector store...")
            from langchain_community.document_loaders import PyPDFLoader  # Use updated import if available

            all_pages = []
            for pdf_path in pdf_paths:
                loader = PyPDFLoader(pdf_path)
                all_pages.extend(loader.load_and_split())
            VECTOR_STORE = VectorStorage(all_pages, MODEL_INSTANCE.embeddings)
            print("Vector store created with", len(pdf_paths), "PDF(s).")
        else:
            VECTOR_STORE = None
            print("No PDFs found; vector store not created.")
