# Notebook Chat Agent

An AI chat agent that runs **inside a Jupyter notebook** (Issue #52). It helps you
write, run, and debug code and build node-based workflows without leaving the
notebook. It also reads the skills tracked in the repository's `.claude/skills/`
and uses them as guidance (for example, the node-creation skill).

## How it works

```
Jupyter kernel                         Django backend                 OpenAI / MCP
──────────────                         ──────────────                 ────────────
neuroworkflow.agent
  ├─ agent loop      ── POST /api/chat/llm/        ──▶ stream_chat_completion ──▶ OpenAI
  ├─ run_code/…      (runs locally in the kernel)
  └─ workflow tools  ── POST /api/chat/mcp-call/   ──▶ MCPClient ──▶ MCP server ──▶ workflow API
                     ── GET  /api/chat/mcp-tools/
```

- The **agent loop runs in the kernel**, so notebook-native tools (run code, read/write
  files) act directly on your live workspace.
- The **OpenAI key and the MCP workflow tools stay on the backend**; the kernel reaches
  them over HTTP. The kernel cannot reach the MCP server directly (different Docker
  network), so all model and workflow calls are proxied through the backend.
- **LLM calls** authenticate with a shared service token (injected automatically).
  **Workflow tools** require your own Keycloak token so per-user data is scoped correctly.

## Prerequisites

Run the Docker stack as usual:

```bash
cd gui
docker-compose build      # rebuild the nest image (adds httpx + ipywidgets)
docker-compose up
```

The JupyterHub spawner wires everything into each single-user container automatically:

| Variable | Purpose | Default |
| --- | --- | --- |
| `NEUROWORKFLOW_BACKEND_URL` | Backend base URL the kernel calls | `http://backend:3000` |
| `NEUROWORKFLOW_SERVICE_TOKEN` | Shared token for the LLM proxy | (the hub's `JUPYTERHUB_API_TOKEN`) |
| `NEUROWORKFLOW_SKILLS_DIR` | Where `.claude` skills are read from | `/home/jovyan/.claude/skills` |
| `PYTHONPATH` | Makes `import neuroworkflow` resolve | `/home/jovyan/codes` |
| `NEUROWORKFLOW_USER_TOKEN` | Optional Keycloak token for workflow tools | unset |
| `NEUROWORKFLOW_PROJECT_ID` | Optional default workflow id | unset |

The repository's `.claude/` directory is mounted read-only at `/home/jovyan/.claude`,
so the agent reads the git-tracked skills.

> A new single-user container picks up this wiring only when it is **(re)spawned**.
> After changing spawner config, remove the old container (`docker rm -f jupyter-user1`)
> and reopen Jupyter.

## Quick start

### 1. Load the extension

```python
%load_ext neuroworkflow.agent
```

### 2a. Inline chat (magics)

One line:

```python
%chat Create a numpy array of spike times and print the mean inter-spike interval.
```

Multi-line cell:

```python
%%chat
How do I build a SONATA network with the neuroworkflow library?
Show me the minimal code.
```

### 2b. Persistent chat panel (ipywidget)

```python
from neuroworkflow.agent import ChatPanel
ChatPanel()
```

This shows a docked panel with an output area and an input box. Without a token, only
notebook-native tools are available.

## Enabling workflow tools

To let the agent operate on your saved workflow projects (add nodes, read the flow,
generate code, update parameters, …), pass your Keycloak access token:

```python
from neuroworkflow.agent import ChatPanel
ChatPanel(
    user_token="eyJ...",                                  # your Keycloak access token
    project_id="4b5023b0-8f1e-4dfc-87f0-1579c1a9bf00",    # target workflow id
)
```

### Getting your access token

The token is a short-lived JWT (it expires after a few minutes — grab a fresh one when
needed). In the frontend (`http://localhost:5173`), open the browser console while
logged in and run:

```js
window.__NEURO_WORKFLOW_KEYCLOAK__.token
```

Copy the whole `eyJ...` string. (Alternatively, copy the `Authorization: Bearer …` value
from any `/api/...` request in the DevTools Network tab.)

### Getting the workflow id

It is a UUID. Find it in the frontend URL when a project is open, or list projects from
the browser console:

```js
fetch("/api/workflow/", {
  headers: { Authorization: "Bearer " + window.__NEURO_WORKFLOW_KEYCLOAK__.token }
}).then(r => r.json()).then(d => console.table(d.map(p => ({ id: p.id, name: p.name }))));
```

> When the token expires you will get auth errors on workflow tools. Get a new token and
> recreate the panel with `ChatPanel(user_token=…)` — the agent is rebuilt when the token
> changes.

## Tools the agent can use

**Notebook-native (always available, run in your kernel):**

- `run_code` — execute Python in the live kernel (shared namespace); returns stdout/result.
- `read_file` / `write_file` — read and write text files in the workspace
  (under `/home/jovyan/codes`).

**Workflow tools via MCP (require a user token):** `add_node`, `get_flow`, `list_nodes`,
`add_edge`, `update_node_parameter`, `generate_code_batch`, `get_workflow_facts`,
`save_report`, and the rest of the workflow MCP toolset.

## Skills (`.claude/skills`)

On startup the agent loads every `*.md` file in `NEUROWORKFLOW_SKILLS_DIR`
(`/home/jovyan/.claude/skills`) and appends it to the system prompt under
`# Available skills`. The skill content is used as guidance — the agent does not run
Claude's skill machinery, it simply follows the instructions in the markdown.

Currently this is `create-node.md` (the node-creation guide). You can verify it is loaded:

```python
from neuroworkflow.agent import reset_agent, get_agent
reset_agent()
print("Skill: create-node.md" in get_agent().messages[0]["content"])   # -> True
```

To add a skill, commit a new `*.md` under `.claude/skills/`; it is picked up on the next
agent start.

## Python API

```python
from neuroworkflow.agent import chat, get_agent, reset_agent, ChatPanel

chat("explain the BuildSonataNetworkNode ports")   # one-shot, streams to stdout
agent = get_agent(user_token="eyJ...")              # shared singleton (rebuilt if token changes)
reset_agent()                                       # clear history / re-read config
```

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `ModuleNotFoundError: No module named 'neuroworkflow.agent'` | The container mounts the synced copy at `codes/neuroworkflow/`, not `src/`. Make sure `codes/neuroworkflow/agent/` exists (see *Maintenance* below) and the container was respawned. |
| Jupyter shows **500 / "Client secret mismatch"** on spawn | Do **not** set `JUPYTERHUB_API_TOKEN` in the spawner env — it is reserved for the single-user server's own hub OAuth. The agent uses `NEUROWORKFLOW_SERVICE_TOKEN` instead. |
| `ChatPanel()` shows **two panels** | Fixed: the panel is displayed once. If you still see two, restart the kernel so the updated module is reloaded. |
| Workflow tools return auth errors | The Keycloak token expired. Get a fresh one and recreate the panel. |
| Skills don't seem to apply | Check the mount: `import os; os.listdir("/home/jovyan/.claude/skills")` should list `create-node.md`. If empty, respawn the single-user container so the `.claude` volume is mounted. |

## Known limitations

- **Skill path mapping.** Skills authored against repository paths (e.g.
  `src/neuroworkflow/nodes/`, `NODE_CREATION_GUIDE.md`) do not match the container layout,
  where only `/home/jovyan/codes/` is mounted. For node creation, the writable directory is
  `/home/jovyan/codes/nodes/`, and repo-root docs are not present in the kernel. The agent
  still follows the skill's guidance, but file paths from the skill text may need adjusting.
- **Auth scope.** The LLM proxy uses a shared service token (acceptable for a trusted
  lab/hackathon). Per-user identity applies only to the workflow (MCP) tools via your
  Keycloak token.

## Maintenance

The agent package lives in **two places**, matching the existing `core/` and `utils/`
convention:

- `src/neuroworkflow/agent/` — the library source.
- `gui/workflow_backend/django-project/codes/neuroworkflow/agent/` — the synced copy the
  single-user container mounts and imports.

When you edit the agent, update **both** copies (and commit the synced copy too).
