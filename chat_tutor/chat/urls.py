# chat_tutor/chat/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('file-manager/', views.file_manager, name='file_manager'),
    path('delete-file/<str:filename>/', views.delete_file, name='delete_file'),
    path('delete-link/<int:link_index>/', views.delete_link, name='delete_link'),
    path('conversations/', views.conversation_history, name='conversation_history'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:conversation_id>/export/', views.export_conversation, name='export_conversation'),
    path('new_conversation/', views.new_conversation, name='new_conversation'),
    path('send_message/', views.send_message, name='send_message'),
    path('switch-conversation/<int:conversation_id>/', views.switch_conversation, name='switch_conversation'),
    path('delete-conversation/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),

]