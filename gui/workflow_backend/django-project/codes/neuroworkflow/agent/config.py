"""Runtime configuration for the in-notebook chat agent.

Values come from the environment that the JupyterHub spawner injects into the
single-user container. ``user_token`` is the only one a user typically sets by
hand: it is their Keycloak access token, required for per-user MCP workflow
tools (the kernel has no browser session to obtain it automatically).
"""

import os
from dataclasses import dataclass


@dataclass
class AgentConfig:
    backend_url: str
    service_token: str
    user_token: str | None
    skills_dir: str
    project_id: str | None

    @property
    def has_mcp(self) -> bool:
        return bool(self.user_token)


def get_config(
    *,
    user_token: str | None = None,
    project_id: str | None = None,
) -> AgentConfig:
    return AgentConfig(
        backend_url=os.environ.get(
            "NEUROWORKFLOW_BACKEND_URL", "http://backend:3000"
        ).rstrip("/"),
        # The shared backend service token, injected by the spawner under a
        # non-reserved name (JUPYTERHUB_API_TOKEN in the kernel is the
        # per-server hub token, a different value).
        service_token=os.environ.get("NEUROWORKFLOW_SERVICE_TOKEN", ""),
        user_token=user_token or os.environ.get("NEUROWORKFLOW_USER_TOKEN") or None,
        skills_dir=os.environ.get(
            "NEUROWORKFLOW_SKILLS_DIR", "/home/jovyan/.claude/skills"
        ),
        project_id=project_id or os.environ.get("NEUROWORKFLOW_PROJECT_ID") or None,
    )
