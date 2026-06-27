"""Tests for the notebook chat agent backend proxies (Issue #52).

Covered:
- The MCP proxies require a real (Keycloak) user and forward to MCPClient.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


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
