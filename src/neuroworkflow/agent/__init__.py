"""In-notebook chat agent for NeuroWorkflow (Issue #52).

Usage inside a Jupyter notebook::

    %load_ext neuroworkflow.agent
    %chat how do I build a SONATA network?

or a persistent panel::

    from neuroworkflow.agent import ChatPanel
    ChatPanel(user_token="<your Keycloak token>")   # token enables workflow tools

The agent loop runs in the kernel; the OpenAI key and MCP tools stay on the
backend, reached over HTTP.
"""

from .config import get_config
from .loop import Agent

_agent: Agent | None = None


def get_agent(*, user_token=None, project_id=None) -> Agent:
    """Return the shared agent, creating it on first use.

    Passing ``user_token``/``project_id`` (or changing them) rebuilds the agent.
    """
    global _agent
    needs_new = (
        _agent is None
        or (user_token is not None and _agent._config.user_token != user_token)
        or (project_id is not None and _agent._config.project_id != project_id)
    )
    if needs_new:
        config = get_config(user_token=user_token, project_id=project_id)
        _agent = Agent(config)
    return _agent


def reset_agent():
    """Drop the current agent (clears history and re-reads config on next use)."""
    global _agent
    _agent = None


def chat(message: str):
    """Send one message and stream the reply to stdout."""
    import sys

    def on_text(delta):
        sys.stdout.write(delta)
        sys.stdout.flush()

    get_agent().run(message, on_text=on_text)
    print()


def ChatPanel(**kwargs):
    from .widget import ChatPanel as _ChatPanel

    return _ChatPanel(**kwargs)


def load_ipython_extension(ipython):
    from .magic import register

    register(ipython)
