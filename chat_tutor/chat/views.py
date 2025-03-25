# chat_tutor/chat/views.py
import json
import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Conversation, Message


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def chat_view(request):
    config = load_config()
    disclaimer_text = config.get('disclaimer', "Default disclaimer text.")
    first_message = config.get('first_question', "Hello, I am your AI tutor. How can I help you?")
    
    # If no active conversation exists, create one with the initial AI message from config.json
    if 'conversation_id' not in request.session:
        conv = Conversation.objects.create()
        Message.objects.create(
            conversation=conv,
            sender='ai',
            content=first_message
        )
        request.session['conversation_id'] = conv.id
    else:
        conv = get_object_or_404(Conversation, id=request.session['conversation_id'])
    
    messages = conv.messages.all().order_by('timestamp')
    all_conversations = Conversation.objects.all().order_by('-started_at')
    
    return render(request, 'chat/chat.html', {
        'messages': messages,
        'all_conversations': all_conversations,
        'active_conversation': conv,
        'disclaimer': disclaimer_text,
    })

# Add these imports at the top of your file
import sys
from pathlib import Path

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import components from your ai_rag package
from ai_rag.model import get_model
from ai_rag.utils import format_docs
from ai_rag.vector_storage import VectorStorage


def send_message(request):
    if request.method == "POST":
        message_text = request.POST.get("message")
        if message_text:
            conv = get_object_or_404(Conversation, id=request.session.get('conversation_id'))
            
            # Save user's message
            user_message = Message.objects.create(conversation=conv, sender="user", content=message_text)
            
            # Get conversation history
            messages = conv.messages.all().order_by('timestamp')
            chat_history = "\n".join([
                f"{'Student' if msg.sender == 'user' else 'AI Tutor'}: {msg.content}" 
                for msg in messages
            ])
            
            # Generate AI response using the existing ai_rag modules
            ai_response = generate_ai_response(message_text, chat_history)
            
            # Save AI response
            ai_message = Message.objects.create(conversation=conv, sender="ai", content=ai_response)
            
            return JsonResponse({
                'user_message': {
                    'sender': user_message.sender,
                    'content': user_message.content,
                },
                'ai_message': {
                    'sender': ai_message.sender,
                    'content': ai_message.content,
                }
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

def generate_ai_response(question, chat_history):
    """Generate an AI response using RAG with the given question and chat history."""
    try:
        # Initialize the AI model using your existing module
        model = get_model("mistral")
        
        # Get PDF files from media folder
        files_folder = os.path.join(settings.MEDIA_ROOT, 'files')
        pdf_paths = [
            os.path.join(files_folder, file) 
            for file in os.listdir(files_folder) 
            if file.endswith('.pdf')
        ]
        
        # Load PDFs if we have any
        if pdf_paths:
            from langchain.document_loaders import PyPDFLoader
            all_pages = []
            for pdf_path in pdf_paths:
                loader = PyPDFLoader(pdf_path)
                all_pages.extend(loader.load_and_split())
            
            # Create vector store with the documents
            vector_storage = VectorStorage(all_pages, model.embeddings)
            
            # Retrieve relevant documents
            retrieved_docs = vector_storage.retriever.get_relevant_documents(question)
            context = format_docs(retrieved_docs)
        else:
            context = "No course materials available."
        
        # Using the standalone question template logic from ai_rag
        standalone_question_template = """
        Given the following conversation history and a follow-up question, rephrase the follow-up question to be a standalone question.
        
        Conversation History:
        {chat_history}
        
        Follow-up Question:
        {question}
        
        Standalone Question:
        """
        
        standalone_question_prompt = PromptTemplate.from_template(standalone_question_template)
        standalone_question = model.llm(standalone_question_prompt.format(
            chat_history=chat_history,
            question=question
        ))
        
        # Using the tutor response template from ai_rag
        tutor_response_template = """
        ### AI Role
        You are an autonomous AI educator capable of independently guiding students through structured lessons, answering questions, and dynamically adapting to their learning needs without requiring constant human intervention.
        
        ### Response Formatting
        Adapt your response format based on the question and content:
        Always include:
        - Contextual introduction
        - Concept explanation with examples
        - End with a relevant engaging question
        
        Use the provided context and conversation history to answer the student's question.
        
        Course Materials Context:
        {context}
        
        Conversation History:
        {chat_history}
        
        Student's Question:
        {question}
        
        AI Tutor's Response:
        """
        
        tutor_response_prompt = PromptTemplate.from_template(tutor_response_template)
        
        # Prepare the final prompt
        final_prompt = tutor_response_prompt.format(
            context=context,
            chat_history=chat_history,
            question=standalone_question
        )
        
        # Get response from the model
        response = model.llm(final_prompt)
        return response
    except Exception as e:
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"

def new_conversation(request):
    config = load_config()
    first_message = config.get('first_question', "Hello, I am your AI tutor. How can I help you?")
    
    conv = Conversation.objects.create()
    Message.objects.create(
        conversation=conv,
        sender='ai',
        content=first_message
    )
    request.session['conversation_id'] = conv.id
    return redirect('chat')

def switch_conversation(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    request.session['conversation_id'] = conv.id
    return redirect('chat')

def conversation_history(request):
    conversations = Conversation.objects.all().order_by('-started_at')
    return render(request, 'chat/conversation_history.html', {'conversations': conversations})

def conversation_detail(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    messages = conv.messages.all().order_by('timestamp')
    return render(request, 'chat/conversation_detail.html', {'conversation': conv, 'messages': messages})

def export_conversation(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    md_text = f"# Conversation from {conv.started_at}\n\n"
    for msg in conv.messages.all().order_by('timestamp'):
        md_text += f"**{msg.sender.capitalize()}**: {msg.content}\n\n"
    response = HttpResponse(md_text, content_type='text/markdown')
    response['Content-Disposition'] = f'attachment; filename=conversation_{conversation_id}.md'
    return response

def delete_conversation(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)
    conv.delete()
    # If the active conversation was deleted, update the session
    if str(request.session.get('conversation_id')) == str(conversation_id):
        remaining = Conversation.objects.first()
        if remaining:
            request.session['conversation_id'] = remaining.id
        else:
            request.session.pop('conversation_id', None)
    return redirect("chat")

def file_manager(request):
    files_folder = os.path.join(settings.MEDIA_ROOT, 'files')
    os.makedirs(files_folder, exist_ok=True)  # Ensure the folder exists

    # Exclude youtube_links.json from the list of files
    all_files = os.listdir(files_folder)
    uploaded_files = [
        f for f in all_files
        if os.path.isfile(os.path.join(files_folder, f)) and f != 'youtube_links.json'
    ]

    # Load the existing YouTube links from the JSON file
    youtube_links = load_youtube_links()

    if request.method == 'POST':
        # Check if we're handling a file upload
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            file_path = os.path.join(files_folder, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            return redirect('file_manager')
        
        # Check if we're adding a new YouTube link
        elif 'youtube_link' in request.POST:
            new_link = request.POST['youtube_link'].strip()
            if new_link:
                youtube_links.append(new_link)
                save_youtube_links(youtube_links)
            return redirect('file_manager')

    return render(request, 'chat/file_manager.html', {
        'uploaded_files': uploaded_files,
        'youtube_links': youtube_links
    })

def delete_file(request, filename):
    files_folder = os.path.join(settings.MEDIA_ROOT, 'files')
    file_path = os.path.join(files_folder, filename)
    
    if os.path.abspath(file_path).startswith(os.path.abspath(files_folder)):
        if os.path.exists(file_path):
            os.remove(file_path)
    return redirect('file_manager')

def delete_link(request, link_index):
    """Delete a link by its index in the youtube_links.json list."""
    youtube_links = load_youtube_links()
    if 0 <= link_index < len(youtube_links):
        youtube_links.pop(link_index)
        save_youtube_links(youtube_links)
    return redirect('file_manager')


def load_youtube_links():
    """Load the list of YouTube links from youtube_links.json if it exists."""
    links_file_path = os.path.join(settings.MEDIA_ROOT, 'files', 'youtube_links.json')
    if not os.path.exists(links_file_path):
        return []
    with open(links_file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_youtube_links(links):
    """Save the list of YouTube links to youtube_links.json."""
    links_file_path = os.path.join(settings.MEDIA_ROOT, 'files', 'youtube_links.json')
    with open(links_file_path, 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
