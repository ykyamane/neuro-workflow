"""Tests for the notebook chat agent backend proxies (Issue #52).

Covered:
- ServiceTokenAuthentication accepts the shared JupyterHub token and nothing else.
- The LLM proxy streams OpenAI chunks as SSE and requires auth.
- The MCP proxies require a real (Keycloak) user and forward to MCPClient.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def service_token(monkeypatch):
    token = "test-service-token"
    monkeypatch.setenv("JUPYTERHUB_API_TOKEN", token)
    return token


def _read_stream(resp) -> str:
    return b"".join(resp.streaming_content).decode()


# --------------------------------------------------------------------------
# Service-token auth + LLM proxy
# --------------------------------------------------------------------------

def test_llm_proxy_rejects_anonymous():
    client = APIClient()
    resp = client.post(reverse("chat-notebook-llm"), {"messages": [{"role": "user", "content": "hi"}]}, format="json")
    assert resp.status_code == 401


def test_llm_proxy_rejects_wrong_service_token(service_token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer not-the-token")
    resp = client.post(reverse("chat-notebook-llm"), {"messages": [{"role": "user", "content": "hi"}]}, format="json")
    assert resp.status_code == 401


def test_llm_proxy_streams_with_service_token(service_token, monkeypatch):
    async def fake_stream(messages, tools=None):
        assert messages[0]["content"] == "hi"
        yield {"type": "content_delta", "content": "Hello"}
        yield {"type": "content_delta", "content": " world"}
        yield {"type": "done"}

    monkeypatch.setattr("app.chat.views.stream_chat_completion", fake_stream)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {service_token}")
    resp = client.post(
        reverse("chat-notebook-llm"),
        {"messages": [{"role": "user", "content": "hi"}]},
        format="json",
    )
    assert resp.status_code == 200
    body = _read_stream(resp)
    assert "event: content_delta" in body
    assert "Hello" in body and "world" in body
    assert "event: done" in body


def test_llm_proxy_rejects_empty_messages(service_token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {service_token}")
    resp = client.post(reverse("chat-notebook-llm"), {"messages": []}, format="json")
    assert resp.status_code == 400


# --------------------------------------------------------------------------
# MCP proxies (require a real user, forward to MCPClient)
# --------------------------------------------------------------------------

class _FakeMCP:
    def __init__(self, auth_token=None):
        self.auth_token = auth_token

    async def initialize(self):
        return {}

    async def list_tools(self):
        return [
            {
                "name": "add_node",
                "description": "Add a node",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def call_tool(self, name, arguments):
        return f"called {name} with {arguments}"


def test_mcp_tools_rejects_anonymous():
    client = APIClient()
    assert client.get(reverse("chat-notebook-mcp-tools")).status_code == 401


def test_mcp_tools_returns_openai_functions(auth_client, user_alice, monkeypatch):
    monkeypatch.setattr("app.chat.views.MCPClient", _FakeMCP)
    client = auth_client(user_alice)
    resp = client.get(reverse("chat-notebook-mcp-tools"))
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "add_node"


def test_mcp_call_executes_tool(auth_client, user_alice, monkeypatch):
    monkeypatch.setattr("app.chat.views.MCPClient", _FakeMCP)
    client = auth_client(user_alice)
    resp = client.post(
        reverse("chat-notebook-mcp-call"),
        {"tool_name": "add_node", "arguments": {"x": 1}},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "called add_node with {'x': 1}"


def test_mcp_call_requires_tool_name(auth_client, user_alice):
    client = auth_client(user_alice)
    resp = client.post(reverse("chat-notebook-mcp-call"), {}, format="json")
    assert resp.status_code == 400
