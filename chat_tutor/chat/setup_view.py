from django.shortcuts import render, redirect
from django.conf import settings
import os
from chat.chat_view import get_local_models
from modules.ai_rag.model import get_model
from modules.ai_rag.vector_storage import VectorStorage
import os
import time
from chat.forms import SetupForm
from chat.models import Conversation, Message


def init_conversation(request):
    if "selected_model" not in request.session:
        return redirect("model_selection")

    if request.method == "POST":
        course_name = request.POST.get("course_name")
        student_name = request.POST.get("student_name")
        familiarity = request.POST.get("familiarity")

        request.session["course_name"] = course_name
        request.session["student_name"] = student_name
        request.session["familiarity"] = familiarity

        from chat.models import Conversation, Message

        conv = Conversation.objects.create()
        initial_message = "Hello, I am your AI tutor. How can I help you?"
        Message.objects.create(conversation=conv, sender="ai", content=initial_message)
        request.session["conversation_id"] = conv.id

        return redirect("chat")
    return render(request, "chat/initial_setup.html")


# Global caches (optional)
MODEL_INSTANCE = None
VECTOR_STORE = None


def model_selection(request):
    global MODEL_INSTANCE, VECTOR_STORE
    local_models = get_local_models()  # your helper function to list local models

    if request.method == "POST":
        selected_model = request.POST.get("model")
        if not selected_model:
            return render(
                request, "chat/model_selection.html", {"error": "Please select a model.", "models": local_models}
            )

        # Save the selected model in session
        request.session["selected_model"] = selected_model

        # Measure model load time
        start_time = time.time()
        MODEL_INSTANCE = get_model(selected_model)
        load_time = time.time() - start_time
        print(f"Loaded model '{selected_model}' in {load_time:.2f} seconds.")
        request.session["model_load_time"] = load_time  # optionally store this in the session

        # Preload vector store if PDFs exist
        files_folder = os.path.join(settings.MEDIA_ROOT, "files")
        pdf_paths = [os.path.join(files_folder, file) for file in os.listdir(files_folder) if file.endswith(".pdf")]
        if pdf_paths:
            from langchain_community.document_loaders import PyPDFLoader  # adjust as needed

            all_pages = []
            for pdf_path in pdf_paths:
                loader = PyPDFLoader(pdf_path)
                all_pages.extend(loader.load_and_split())
            VECTOR_STORE = VectorStorage(all_pages, MODEL_INSTANCE.embeddings)
            print("Vector store preloaded with", len(pdf_paths), "PDF(s).")
        else:
            VECTOR_STORE = None

        request.session["cached_model"] = selected_model
        return redirect("initial_setup")

    return render(request, "chat/model_selection.html", {"models": local_models})
