# chat_tutor/chat/views.py
import subprocess
import json
import os
import sys
from pathlib import Path
import time


from chat.apps import MODEL_INSTANCE, VECTOR_STORE
from modules.ai_rag.templates import Template
from modules.ai_rag.model import get_cached_model, get_model
from modules.ai_rag.utils import format_docs
from modules.ai_rag.vector_storage import VectorStorage, get_vector_store
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from chat.models import Conversation, Message


def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat/config.json")
    with open(config_path, "r") as f:
        return json.load(f)


def get_cached_model():
    return MODEL_INSTANCE


def get_cached_vector_store():
    return VECTOR_STORE


def chat_view(request):
    config = load_config()
    disclaimer_text = config.get("disclaimer", "Default disclaimer text.")
    first_message = config.get("first_question", "Hello, I am your AI tutor. How can I help you?")

    # If no active conversation exists, create one with the initial AI message from config.json
    if "conversation_id" not in request.session:
        request.redirect("init_setup")

    conv = get_object_or_404(Conversation, id=request.session["conversation_id"])
    messages = conv.messages.all().order_by("timestamp")
    all_conversations = Conversation.objects.all().order_by("-started_at")

    return render(
        request,
        "chat/chat.html",
        {
            "messages": messages,
            "all_conversations": all_conversations,
            "active_conversation": conv,
            "disclaimer": disclaimer_text,
        },
    )


# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


def send_message(request):
    if request.method == "POST":
        message_text = request.POST.get("message")
        if message_text:
            conv = get_object_or_404(Conversation, id=request.session.get("conversation_id"))

            user_message = Message.objects.create(conversation=conv, sender="user", content=message_text)

            messages = conv.messages.all().order_by("timestamp")
            chat_history = "\n".join(
                [f"{'Student' if msg.sender == 'user' else 'AI Tutor'}: {msg.content}" for msg in messages]
            )

            ai_response, doc_count, query_time = generate_ai_response(message_text, chat_history, request)

            ai_message = Message.objects.create(conversation=conv, sender="ai", content=ai_response)

            return JsonResponse(
                {
                    "user_message": {
                        "sender": user_message.sender,
                        "content": user_message.content,
                    },
                    "ai_message": {
                        "sender": ai_message.sender,
                        "content": ai_message.content,
                    },
                    "doc_count": doc_count,  # Extra info: number of PDFs used
                    "query_time": query_time,
                }
            )
    return JsonResponse({"error": "Invalid request"}, status=400)


def get_local_models():
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        models = result.stdout.strip().splitlines()
        return models
    except Exception as e:
        print("Error retrieving local models:", e)
        return []


def generate_ai_response(question, chat_history, request):
    """Generate an AI response using precomputed resources and return the query time."""
    try:
        model = get_cached_model()

        vector_store = get_cached_vector_store()
        if vector_store:
            retrieved_docs = vector_store.retriever.get_relevant_documents(question)
            doc_count = len(retrieved_docs)
            context = format_docs(retrieved_docs)
        else:
            doc_count = 0
            context = "No course materials available."

        course_name = request.session.get("course_name", "Default Course")
        familiarity = request.session.get("familiarity", "Beginner")
        student_name = request.session.get("student_name", "Student")

        template = Template()

        standalone_question_template = template.standalone_question_template
        standalone_question = model.llm.invoke(
            standalone_question_template.format(chat_history=chat_history, question=question)
        )

        tutor_response_template = template.tutor_response_template
        final_prompt = tutor_response_template.format(
            course_name=course_name,
            familiarity=familiarity,
            student_name=student_name,
            context=context,
            chat_history=chat_history,
            question=standalone_question,
        )

        # Measuring the inference time
        start_query = time.time()
        response = model.llm.invoke(final_prompt)
        query_time = time.time() - start_query
        print(f"Inference took {query_time:.2f} seconds.")

        return response, doc_count, query_time
    except Exception as e:
        return f"I apologize, but I encountered an error while processing your request: {str(e)}", 0, 0


def new_conversation(request):
    config = load_config()
    first_message = config.get("first_question", "Hello, I am your AI tutor. How can I help you?")

    conv = Conversation.objects.create()
    Message.objects.create(conversation=conv, sender="ai", content=first_message)
    request.session["conversation_id"] = conv.id
    return redirect("chat")


def switch_conversation(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    request.session["conversation_id"] = conv.id
    return redirect("chat")


def conversation_history(request):
    conversations = Conversation.objects.all().order_by("-started_at")
    return render(request, "chat/conversation_history.html", {"conversations": conversations})


def conversation_detail(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    messages = conv.messages.all().order_by("timestamp")
    return render(request, "chat/conversation_detail.html", {"conversation": conv, "messages": messages})


def export_conversation(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    md_text = f"# Conversation from {conv.started_at}\n\n"
    for msg in conv.messages.all().order_by("timestamp"):
        md_text += f"**{msg.sender.capitalize()}**: {msg.content}\n\n"
    response = HttpResponse(md_text, content_type="text/markdown")
    response["Content-Disposition"] = f"attachment; filename=conversation_{conversation_id}.md"
    return response


def delete_conversation(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    conv.delete()
    # If the active conversation was deleted, update the session
    if str(request.session.get("conversation_id")) == str(conversation_id):
        remaining = Conversation.objects.first()
        if remaining:
            request.session["conversation_id"] = remaining.id
        else:
            request.session.pop("conversation_id", None)
    return redirect("chat")


def file_manager(request):
    files_folder = os.path.join(settings.MEDIA_ROOT, "files")
    os.makedirs(files_folder, exist_ok=True)  # Ensure the folder exists

    # Exclude youtube_links.json from the list of files
    all_files = os.listdir(files_folder)
    uploaded_files = [
        f for f in all_files if os.path.isfile(os.path.join(files_folder, f)) and f != "youtube_links.json"
    ]

    # Load the existing YouTube links from the JSON file
    youtube_links = load_youtube_links()

    if request.method == "POST":
        # Check if we're handling a file upload
        if "file" in request.FILES:
            uploaded_file = request.FILES["file"]
            file_path = os.path.join(files_folder, uploaded_file.name)
            with open(file_path, "wb+") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            return redirect("file_manager")

        # Check if we're adding a new YouTube link
        elif "youtube_link" in request.POST:
            new_link = request.POST["youtube_link"].strip()
            if new_link:
                youtube_links.append(new_link)
                save_youtube_links(youtube_links)
            return redirect("file_manager")

    return render(request, "chat/file_manager.html", {"uploaded_files": uploaded_files, "youtube_links": youtube_links})


def delete_file(request, filename):
    files_folder = os.path.join(settings.MEDIA_ROOT, "files")
    file_path = os.path.join(files_folder, filename)

    if os.path.abspath(file_path).startswith(os.path.abspath(files_folder)):
        if os.path.exists(file_path):
            os.remove(file_path)
    return redirect("file_manager")


def delete_link(request, link_index):
    """Delete a link by its index in the youtube_links.json list."""
    youtube_links = load_youtube_links()
    if 0 <= link_index < len(youtube_links):
        youtube_links.pop(link_index)
        save_youtube_links(youtube_links)
    return redirect("file_manager")


def load_youtube_links():
    """Load the list of YouTube links from youtube_links.json if it exists."""
    links_file_path = os.path.join(settings.MEDIA_ROOT, "files", "youtube_links.json")
    if not os.path.exists(links_file_path):
        return []
    with open(links_file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_youtube_links(links):
    """Save the list of YouTube links to youtube_links.json."""
    links_file_path = os.path.join(settings.MEDIA_ROOT, "files", "youtube_links.json")
    with open(links_file_path, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
