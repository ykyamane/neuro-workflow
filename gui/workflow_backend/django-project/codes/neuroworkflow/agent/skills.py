"""Load git-tracked ``.claude`` skills and fold them into the system prompt.

Issue #52 requires the notebook agent to use the skills committed to the repo
(currently ``.claude/skills/create-node.md``). We do not reimplement Claude's
skill machinery — we read the markdown and inject it as guidance, as agreed.
"""

import glob
import logging
import os

logger = logging.getLogger(__name__)

_BASE_PROMPT = (
    "You are NeuroWorkflow Assistant running inside a Jupyter notebook for "
    "neuroscience simulation work. You help the user write, run, and debug "
    "code and build node-based workflows.\n\n"
    "You have notebook-native tools:\n"
    "- run_code: execute Python in the user's live kernel (shared namespace) "
    "and read back stdout/results. Prefer small, verifiable steps.\n"
    "- read_file / write_file: inspect and edit files in the project workspace "
    "(under /home/jovyan/codes).\n"
    "The NeuroWorkflow library is importable as `neuroworkflow` (e.g. "
    "`from neuroworkflow.core.workflow import WorkflowBuilder`); node classes "
    "live under /home/jovyan/codes/nodes.\n\n"
    "Behavior:\n"
    "- Before claiming something works, run it with run_code and check the output.\n"
    "- Keep answers concise. Show the code you run.\n"
    "- Always respond in the same language the user uses.\n"
)

_MCP_PROMPT = (
    "\nYou also have workflow tools (add_node, get_flow, generate_code_batch, "
    "update_node_parameter, etc.) that operate on the user's saved workflow "
    "projects in the web app. When reading parameter values use the "
    "'default_value' field. Ask for confirmation before destructive actions "
    "(deleting nodes/edges).\n"
)


def load_skills(skills_dir: str) -> list[tuple[str, str]]:
    """Return ``(name, markdown)`` for every ``*.md`` skill in ``skills_dir``."""
    if not skills_dir or not os.path.isdir(skills_dir):
        logger.info("Skills directory not found: %s (skipping skills)", skills_dir)
        return []
    skills = []
    for path in sorted(glob.glob(os.path.join(skills_dir, "*.md"))):
        try:
            with open(path, encoding="utf-8") as f:
                skills.append((os.path.basename(path), f.read()))
        except OSError as e:
            logger.warning("Could not read skill %s: %s", path, e)
    return skills


def build_system_prompt(skills_dir: str, *, with_mcp: bool) -> str:
    prompt = _BASE_PROMPT
    if with_mcp:
        prompt += _MCP_PROMPT
    skills = load_skills(skills_dir)
    if skills:
        prompt += "\n# Available skills\n"
        prompt += (
            "The following skills are tracked in this repository. Apply the "
            "relevant one when the user's request matches it.\n"
        )
        for name, text in skills:
            prompt += f"\n## Skill: {name}\n{text}\n"
    return prompt
