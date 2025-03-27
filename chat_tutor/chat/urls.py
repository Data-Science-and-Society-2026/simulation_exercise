# chat_tutor/chat/urls.py
from django.urls import path


from chat import chat_view, setup_view
from chat import tts_view

urlpatterns = [
    path("", chat_view.chat_view, name="chat"),
    path("file-manager/", chat_view.file_manager, name="file_manager"),
    path("delete-file/<str:filename>/", chat_view.delete_file, name="delete_file"),
    path("delete-link/<int:link_index>/", chat_view.delete_link, name="delete_link"),
    path("conversations/", chat_view.conversation_history, name="conversation_history"),
    path("conversation/<int:conversation_id>/", chat_view.conversation_detail, name="conversation_detail"),
    path("conversation/<int:conversation_id>/export/", chat_view.export_conversation, name="export_conversation"),
    path("new_conversation/", chat_view.new_conversation, name="new_conversation"),
    path("send_message/", chat_view.send_message, name="send_message"),
    path("initial_setup/", setup_view.init_conversation, name="initial_setup"),
    path("model_selection/", setup_view.model_selection, name="model_selection"),
    path("voice_chat/", tts_view.voice_chat, name="voice_chat"),
    path("switch-conversation/<int:conversation_id>/", chat_view.switch_conversation, name="switch_conversation"),
    path("delete-conversation/<int:conversation_id>/", chat_view.delete_conversation, name="delete_conversation"),
]

