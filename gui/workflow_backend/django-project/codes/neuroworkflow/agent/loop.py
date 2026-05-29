"""The in-kernel agent loop.

Mirrors the backend ``orchestrate_chat`` structure (stream a completion, run any
tool calls, repeat) but runs synchronously in the kernel so notebook-native
tools execute against the live namespace. LLM streaming and MCP tools go
through the backend via ``BackendClient``.
"""

import json

from . import tools as nb_tools
from .client import BackendClient
from .config import AgentConfig
from .skills import build_system_prompt

MAX_LOOPS = 10


class Agent:
    def __init__(self, config: AgentConfig, ipython=None):
        self._config = config
        self._client = BackendClient(config)
        self._ipython = ipython
        self._mcp_tools = self._client.list_mcp_tools()
        self._mcp_names = {
            t.get("function", {}).get("name") for t in self._mcp_tools
        }
        system_prompt = build_system_prompt(
            config.skills_dir, with_mcp=bool(self._mcp_tools)
        )
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]

    @property
    def _tools(self) -> list[dict]:
        return nb_tools.NOTEBOOK_TOOLS + self._mcp_tools

    def _get_ipython(self):
        if self._ipython is not None:
            return self._ipython
        from IPython import get_ipython

        return get_ipython()

    def run(self, user_message: str, on_text=None, on_tool=None) -> str:
        """Run one user turn to completion; return the final assistant text.

        ``on_text(delta)`` is called for streamed text; ``on_tool(name, args)``
        before each tool runs.
        """
        self.messages.append({"role": "user", "content": user_message})
        final_text = ""

        for _ in range(MAX_LOOPS):
            text, tool_calls = self._stream_turn(on_text)

            assistant_msg: dict = {"role": "assistant", "content": text or None}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["args"]},
                    }
                    for tc in tool_calls
                ]
            self.messages.append(assistant_msg)

            if not tool_calls:
                final_text = text
                break

            for tc in tool_calls:
                result = self._run_tool(tc, on_tool)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tc["name"],
                        "content": result,
                    }
                )

        return final_text

    def _stream_turn(self, on_text):
        """Consume one streamed completion; return (text, [tool_call,...])."""
        text = ""
        tool_calls: dict[int, dict] = {}
        for event_type, data in self._client.stream_llm(self.messages, self._tools):
            if event_type == "content_delta":
                delta = data.get("content", "")
                text += delta
                if on_text and delta:
                    on_text(delta)
            elif event_type == "tool_call_delta":
                idx = data.get("index", 0)
                tc = tool_calls.setdefault(idx, {"id": None, "name": "", "args": ""})
                if data.get("id"):
                    tc["id"] = data["id"]
                if data.get("function_name"):
                    tc["name"] = data["function_name"]
                tc["args"] += data.get("arguments_delta", "")
            elif event_type == "error":
                raise RuntimeError(data.get("message", "LLM error"))
            elif event_type in ("done", "tool_calls_complete"):
                break
        ordered = [tool_calls[i] for i in sorted(tool_calls) if tool_calls[i]["id"]]
        return text, ordered

    def _run_tool(self, tc: dict, on_tool) -> str:
        name = tc["name"]
        try:
            args = json.loads(tc["args"]) if tc["args"] else {}
        except json.JSONDecodeError:
            return f"[error] invalid JSON arguments for {name}: {tc['args']!r}"
        if on_tool:
            on_tool(name, args)
        if name in nb_tools.NOTEBOOK_TOOL_NAMES:
            return nb_tools.dispatch(name, args, self._get_ipython())
        if name in self._mcp_names:
            return self._client.call_mcp_tool(name, args)
        return f"[error] unknown tool: {name}"
