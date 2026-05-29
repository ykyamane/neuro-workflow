"""HTTP client from the kernel to the Django backend.

The kernel cannot reach the MCP server directly (different Docker network) and
must not hold the OpenAI key, so both LLM streaming and MCP tool calls are
proxied through the backend. LLM calls authenticate with the shared service
token; MCP calls forward the user's own Keycloak JWT for per-user data access.
"""

import json

from .config import AgentConfig


class BackendError(RuntimeError):
    pass


class BackendClient:
    def __init__(self, config: AgentConfig):
        self._config = config

    def _httpx(self):
        import httpx

        return httpx

    def stream_llm(self, messages: list[dict], tools: list[dict] | None):
        """Yield ``(event_type, data)`` SSE chunks from the LLM proxy."""
        httpx = self._httpx()
        url = f"{self._config.backend_url}/api/chat/llm/"
        headers = {"Authorization": f"Bearer {self._config.service_token}"}
        payload = {"messages": messages}
        if tools:
            payload["tools"] = tools

        with httpx.Client(timeout=None) as client:
            with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = resp.read().decode(errors="replace")
                    raise BackendError(f"LLM proxy {resp.status_code}: {body}")
                event_type = None
                for line in resp.iter_lines():
                    if not line:
                        event_type = None
                        continue
                    if line.startswith("event: "):
                        event_type = line[7:]
                    elif line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue
                        yield event_type, data

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
