"""Notebook-native tools the agent can call inside the live kernel.

These must run in the kernel (not the backend) so they share the user's
namespace and filesystem. MCP workflow tools are handled separately via the
backend proxy.
"""

import os

_MAX_RESULT_CHARS = 8000

# read_file/write_file are LLM-driven, so confine them to the workspace to
# avoid accidentally exposing or clobbering files outside it. (run_code can
# still reach anything the kernel can — this guard is for the file tools.)
_WORKSPACE_ROOT = os.path.realpath(
    os.environ.get("NEUROWORKFLOW_WORKSPACE_ROOT", "/home/jovyan/codes")
)


def _resolve_in_workspace(path: str) -> str:
    """Resolve ``path`` to an absolute path, rejecting anything outside the root."""
    resolved = os.path.realpath(path)
    if resolved != _WORKSPACE_ROOT and not resolved.startswith(_WORKSPACE_ROOT + os.sep):
        raise ValueError(f"path is outside the workspace ({_WORKSPACE_ROOT}): {path}")
    return resolved

NOTEBOOK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_code",
            "description": (
                "Execute Python code in the user's live Jupyter kernel. The code "
                "shares the notebook's namespace, so variables persist across "
                "calls. Returns captured stdout/stderr and the last expression "
                "result. Output is also shown to the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to run."}
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file from the workspace and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write (overwrite) a UTF-8 text file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path."},
                    "content": {"type": "string", "description": "Full file contents to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
]

NOTEBOOK_TOOL_NAMES = {t["function"]["name"] for t in NOTEBOOK_TOOLS}


def _truncate(text: str) -> str:
    if len(text) > _MAX_RESULT_CHARS:
        return text[:_MAX_RESULT_CHARS] + "\n...[truncated]"
    return text


def _run_code(code: str, ipython) -> str:
    from IPython.utils.capture import capture_output

    with capture_output(display=True) as cap:
        result = ipython.run_cell(code)
    cap.show()  # surface the output to the user as well

    parts = []
    if cap.stdout:
        parts.append(cap.stdout.rstrip())
    if cap.stderr:
        parts.append("[stderr]\n" + cap.stderr.rstrip())
    if result.error_in_exec is not None:
        parts.append(f"[error] {type(result.error_in_exec).__name__}: {result.error_in_exec}")
    elif result.result is not None:
        parts.append("[result] " + repr(result.result))
    return _truncate("\n".join(parts)) if parts else "(no output)"


def _read_file(path: str) -> str:
    resolved = _resolve_in_workspace(path)
    with open(resolved, encoding="utf-8") as f:
        return _truncate(f.read())


def _write_file(path: str, content: str) -> str:
    resolved = _resolve_in_workspace(path)
    directory = os.path.dirname(resolved)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(resolved, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} chars to {resolved}"


def dispatch(name: str, args: dict, ipython) -> str:
    """Run a notebook-native tool and return a text result for the model."""
    try:
        if name == "run_code":
            return _run_code(args["code"], ipython)
        if name == "read_file":
            return _read_file(args["path"])
        if name == "write_file":
            return _write_file(args["path"], args["content"])
        return f"[error] unknown notebook tool: {name}"
    except Exception as e:  # surface tool failures back to the model
        return f"[error] {type(e).__name__}: {e}"
