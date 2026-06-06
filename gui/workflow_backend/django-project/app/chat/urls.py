from django.urls import path, re_path
from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    ChatStreamView,
    NotebookLLMView,
    NotebookMCPToolsView,
    NotebookMCPCallView,
    AnthropicProxyView,
)

urlpatterns = [
    path("conversations/", ConversationListCreateView.as_view(), name="chat-conversations"),
    path("conversations/<uuid:conversation_id>/", ConversationDetailView.as_view(), name="chat-conversation-detail"),
    path("stream/", ChatStreamView.as_view(), name="chat-stream"),
    path("llm/", NotebookLLMView.as_view(), name="chat-notebook-llm"),
    path("mcp-tools/", NotebookMCPToolsView.as_view(), name="chat-notebook-mcp-tools"),
    path("mcp-call/", NotebookMCPCallView.as_view(), name="chat-notebook-mcp-call"),
    # Anthropic API passthrough for the in-kernel Claude agent (key stays here).
    re_path(r"^anthropic/(?P<subpath>.*)$", AnthropicProxyView.as_view(), name="chat-anthropic-proxy"),
]
