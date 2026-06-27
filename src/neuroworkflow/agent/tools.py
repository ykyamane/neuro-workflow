"""Live-kernel Python execution for the Claude agent's ``run_code`` tool.

``run_code`` executes against the notebook's live namespace dict so variables
persist across calls. It runs inside the agent's worker thread (the Claude Agent
SDK runs there, isolated from the kernel's own event loop), so we ``exec`` the
code rather than calling ``ipython.run_cell`` — run_cell would clash with the
worker thread's running event loop. Captured stdout/stderr is echoed back to the
notebook cell *and* returned to the model.
"""

import ast
import contextlib
import io
import sys

_MAX_RESULT_CHARS = 8000


def _truncate(text: str) -> str:
    if len(text) > _MAX_RESULT_CHARS:
        return text[:_MAX_RESULT_CHARS] + "\n...[truncated]"
    return text


def run_code(code: str, namespace: dict) -> str:
    """Execute ``code`` against ``namespace``; return captured output/result."""
    out, err = io.StringIO(), io.StringIO()
    result_repr = None
    error_text = None
    try:
        parsed = ast.parse(code)
        last_expr = None
        if parsed.body and isinstance(parsed.body[-1], ast.Expr):
            last_expr = parsed.body.pop()
        module = ast.Module(body=parsed.body, type_ignores=[])
        ast.fix_missing_locations(module)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exec(compile(module, "<chat>", "exec"), namespace)
            if last_expr is not None:
                expr = ast.Expression(last_expr.value)
                ast.fix_missing_locations(expr)
                value = eval(compile(expr, "<chat>", "eval"), namespace)
                if value is not None:
                    result_repr = repr(value)
    except Exception as e:  # surface execution errors back to the model
        error_text = f"{type(e).__name__}: {e}"

    stdout_text = out.getvalue()
    stderr_text = err.getvalue()
    # Echo to the user's cell as well (the model gets the text in the return).
    if stdout_text:
        sys.stdout.write(stdout_text)
    if stderr_text:
        sys.stdout.write(stderr_text)

    parts = []
    if stdout_text:
        parts.append(stdout_text.rstrip())
    if stderr_text:
        parts.append("[stderr]\n" + stderr_text.rstrip())
    if error_text:
        parts.append("[error] " + error_text)
    elif result_repr is not None:
        parts.append("[result] " + result_repr)
    return _truncate("\n".join(parts)) if parts else "(no output)"
