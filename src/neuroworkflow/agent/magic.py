"""``%chat`` / ``%%chat`` magics for talking to the agent inline."""

from __future__ import annotations

import sys


def _stream_text(delta: str):
    sys.stdout.write(delta)
    sys.stdout.flush()


def _announce_tool(name: str, args: dict):
    preview = ", ".join(f"{k}={v!r}"[:60] for k, v in args.items())
    print(f"\n\033[2m[tool] {name}({preview})\033[0m")


def chat_magic(line: str, cell: str | None = None):
    """Send a message to the notebook agent.

    Line form:  ``%chat how do I build a SONATA network?``
    Cell form:  ``%%chat`` followed by a multi-line prompt.
    """
    from . import get_agent

    message = (cell if cell is not None else line).strip()
    if not message:
        print("Usage: %chat <message>  or  %%chat (cell)")
        return
    agent = get_agent()
    agent.run(message, on_text=_stream_text, on_tool=_announce_tool)
    print()


def register(ipython):
    ipython.register_magic_function(chat_magic, magic_kind="line_cell", magic_name="chat")
