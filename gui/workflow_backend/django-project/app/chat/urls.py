from django.urls import path
from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    ChatStreamView,
    NotebookLLMView,
    NotebookMCPToolsView,
    NotebookMCPCallView,
)

urlpatterns = [
    path("conversations/", ConversationListCreateView.as_view(), name="chat-conversations"),
    path("conversations/<uuid:conversation_id>/", ConversationDetailView.as_view(), name="chat-conversation-detail"),
    path("stream/", ChatStreamView.as_view(), name="chat-stream"),
    path("llm/", NotebookLLMView.as_view(), name="chat-notebook-llm"),
    path("mcp-tools/", NotebookMCPToolsView.as_view(), name="chat-notebook-mcp-tools"),
    path("mcp-call/", NotebookMCPCallView.as_view(), name="chat-notebook-mcp-call"),
]
