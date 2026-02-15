from django.urls import path
from .views import ConversationListCreateView, ConversationDetailView, ChatStreamView

urlpatterns = [
    path("conversations/", ConversationListCreateView.as_view(), name="chat-conversations"),
    path("conversations/<uuid:conversation_id>/", ConversationDetailView.as_view(), name="chat-conversation-detail"),
    path("stream/", ChatStreamView.as_view(), name="chat-stream"),
]
