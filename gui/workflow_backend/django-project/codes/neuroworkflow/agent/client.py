"""HTTP client from the kernel to the Django backend (workflow MCP tools).

The kernel cannot reach the MCP server directly (different Docker network), so
workflow tool calls are proxied through the backend, forwarding the user's own
Keycloak JWT for per-user data access. (LLM calls no longer go through here: the
Claude Agent SDK reaches Anthropic via the backend's ``/api/chat/anthropic``
proxy, configured through ``ANTHROPIC_BASE_URL``.)
"""

from __future__ import annotations

from .config import AgentConfig


class BackendError(RuntimeError):
    pass


class BackendClient:
    def __init__(self, config: AgentConfig):
        self._config = config

    def _httpx(self):
        import httpx

        return httpx

    def list_mcp_tools(self) -> list[dict]:
        """Return MCP tools in OpenAI function format (empty if no user token)."""
        if not self._config.has_mcp:
            return []
        httpx = self._httpx()
        url = f"{self._config.backend_url}/api/chat/mcp-tools/"
        headers = {"Authorization": f"Bearer {self._config.user_token}"}
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                raise BackendError(f"mcp-tools {resp.status_code}: {resp.text}")
            return resp.json().get("tools", [])

    def call_mcp_tool(self, name: str, arguments: dict) -> str:
        httpx = self._httpx()
        url = f"{self._config.backend_url}/api/chat/mcp-call/"
        headers = {"Authorization": f"Bearer {self._config.user_token}"}
        payload = {"tool_name": name, "arguments": arguments}
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                return f"[error] mcp-call {resp.status_code}: {resp.text}"
            return resp.json().get("result", "")
