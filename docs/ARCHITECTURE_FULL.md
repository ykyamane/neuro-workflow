# NeuroWorkflow — Full-Scale Architecture

This document describes the complete architecture of the NeuroWorkflow system: all components, their responsibilities, interconnections, and data flows. It complements the high-level [ARCHITECTURE.md](ARCHITECTURE.md) with implementation-level detail.

**Visual diagrams:**
- [ARCHITECTURE_DIAGRAM.svg](ARCHITECTURE_DIAGRAM.svg) — full-scale component and connection diagram (open in browser or vector editor).
- [architecture_visualization.html](architecture_visualization.html) — interactive HTML visualization (all components, connections, data flow; click/hover to highlight).

---

## 1. System Overview

NeuroWorkflow is a Python-based framework for building and executing neural simulation workflows. It provides:

- **Node-based workflows**: Computational steps as nodes with typed ports and parameters.
- **Multiple interfaces**: Web UI (React), Python API/CLI, and Jupyter notebooks.
- **Backend services**: Django REST API, JupyterHub for notebooks, MCP server for LLM integration.
- **Core library**: Workflow engine, node system, code/notebook/SnakeMake export, parameter metadata, database adapters.
- **External integrations**: Supabase (auth), PostgreSQL (persistence), optional Local RAG (parameter suggestions), neuroscience DBs (Allen, NeuroMorpho, PubMed, NeuroML-DB, custom).

---

## 2. Top-Level Layout

| Path | Role |
|------|------|
| **`src/`** | Core Python library `neuroworkflow` (nodes, workflow, CLI, metadata, DB adapters). |
| **`gui/`** | Web stack: Django backend, React frontend, MCP server; Docker Compose. |
| **`rag/`** | Optional Local RAG: FastAPI backend (8006), Node frontend (3010) for parameter suggestions. |
| **`brainscaler/`** | Separate product: knowledge graph + conversational AI frontend; can link to workflow UI. |
| **`docs/`** | Architecture and guides. |
| **`logs/`** | Implementation/status notes. |
| **`examples/`** | Example scripts (SONATA, optimization, TVB, etc.). |
| **`notebooks/`** | Jupyter examples and demos. |

---

## 3. Component Descriptions

### 3.1 Core Library — `src/neuroworkflow`

**Role:** Node-based workflow engine, execution, code/notebook/SnakeMake export, parameter metadata service, and database adapters. No Django dependency; used as a library by the backend and by examples/notebooks.

**Tech stack:** Python 3.8+, setuptools. Optional: nest-simulator, matplotlib, pytest, openai.

**Entry points:**

- **CLI:** `neuroworkflow` → `neuroworkflow.cli.commands:main` (e.g. `neuroworkflow run <file.py>`).
- **Library:** Imported by Django for code generation and by examples/notebooks.

**Layout:**

- **`core/`** — `node.py` (base Node), `port.py` (InputPort/OutputPort), `schema.py` (NodeDefinitionSchema, ParameterDefinition, PortDefinition, ResourceRequirements), `workflow.py` (Workflow, WorkflowBuilder, execution order).
- **`nodes/`** — network, simulation, stimulus, analysis, optimization, io.
- **`utils/`** — script_exporter, snakemake_generator, job_managers (e.g. SLURM), parameter_metadata_service, database_adapters, mcp/server.
- **`cli/`** — CLI commands.

**Config:** No app-level config file; relies on environment (e.g. `OPENAI_API_KEY`) and optional config dict for `ParameterMetadataService` and DB adapters.

**Run:** `pip install -e .` then `neuroworkflow run <file.py>` or import in Django/examples.

---

### 3.2 Django Backend — `gui/workflow_backend/`

**Role:** REST API for projects, flow (React Flow JSON), nodes, edges, code generation, workflow run, node upload/sync (box), metadata (parameter suggestions, custom DBs), and auth (Supabase).

**Tech stack:** Django, Django REST Framework, corsheaders, PostgreSQL, python-dotenv.

**Entry:** `gui/workflow_backend/django-project/manage.py` → `config.settings`; runserver on port **3000**.

**Config:** `gui/workflow_backend/.env` (from `env.template`): `DB_*`, `SUPABASE_*`, `DJANGO_SECRET_KEY`, `HOST_PROJECT_PATH`, `PROJECTS_BASE_PATH`, `UPLOAD_NODES_PATH`, `NEURO_PATH`, optional `LOCAL_RAG_*`, `OPENAI_API_KEY`.

**Apps:**

- **`app.workflow`** — FlowProject, FlowNode, FlowEdge; CRUD, flow get/put, generate-code, run.
- **`app.box`** — PythonFile (node definitions); upload, list, sync, categories, parameters update.
- **`app.metadata`** — ParameterMetadataService integration; parameter suggest, species-specific, custom-databases CRUD and test.
- **`app.auth`** — Supabase-based auth; health, protected, profile.

**Database:** PostgreSQL (host `db` in Docker; env `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`).

**Run (local):** `python django-project/manage.py runserver 0.0.0.0:3000`. In Docker: see Section 6.

---

### 3.3 React Frontend — `gui/workflow_frontend/`

**Role:** Workflow editor (React Flow), project list, node detail/parameters, parameter suggestions UI, custom DBs management, code generation trigger, workflow run.

**Tech stack:** React 19, TypeScript, Vite, Chakra UI, React Flow (@xyflow/react), Aspida (API client), Supabase client.

**Entry:** `npm run dev` / `pnpm dev` (Vite), or `dev:docker` for Docker; dev server port **5173**.

**Config:** `gui/workflow_frontend/.env`: `VITE_API_BASE_URL` (e.g. `http://localhost:3000/api`), `VITE_SUPABASE_*`, optional `VITE_DEBUG_API`, `VITE_INTERNAL_SECRET`.

**Run:** From `gui/workflow_frontend`: `pnpm install && pnpm dev`. In Docker: `npm run dev:docker`.

---

### 3.4 MCP Server — `gui/mcp_server/`

**Role:** Model Context Protocol proxy for LLM tools; exposes workflow tools (list projects, get flow, etc.) by calling the Django backend.

**Tech stack:** FastMCP, HTTP transport.

**Entry:** `proxy.py` loads `mcp_config.json` and runs FastMCP proxy; `workflow_mcp.py` is the workflow tool server (invoked by config).

**Config:** `mcp_config.json`: workflow server command `python3 ./workflow_mcp.py`, env `DJANGO_API_URL=http://backend:3000/api/workflow`. Env: `MCP_PROXY_PORT=8001`.

**Run:** `python3 proxy.py`; in Docker, port **8001**. Cursor/LLM connects to MCP.

---

### 3.5 JupyterHub — `gui/workflow_backend/django-project/neuroworkflow/`

**Role:** Spawns NEST/JupyterLab containers for running generated code/notebooks in isolated environments.

**Tech stack:** JupyterHub 4, DockerSpawner, DummyAuthenticator.

**Entry:** `jupyterhub -f jupyterhub_config.py`; hub on port **8000**.

**Config:** `jupyterhub_config.py` (network, spawner, auth); Dockerfile for single-user image (NEST, TVB).

**Run:** Via Docker Compose in `gui/` (service `jupyterhub`). Frontend may link to hub at `localhost:8000`.

---

### 3.6 Local RAG — `rag/`

**Role:** Optional semantic search over papers/chunks for parameter suggestions; used by the backend metadata service via the Local RAG adapter.

**Tech stack:** FastAPI backend (port **8006**), Node frontend (default **3010** in this repo to avoid conflict with backend 3000).

**Entry:** `rag/setup_and_run.py` or manual start of backend and frontend.

**Config:** Backend URL for neuro-workflow is `LOCAL_RAG_BASE_URL` in backend `.env` (e.g. `http://localhost:8006` or `http://host.docker.internal:8006`).

**Run:** `python setup_and_run.py` from `rag/` (backend 8006, frontend 3010). See `logs/RUNNING_NEURO_WORKFLOW_AND_RAG.md` for port and Docker coexistence.

---

### 3.7 BrainScaler — `brainscaler/`

**Role:** Separate product: knowledge graph (brainscaler) + conversational AI frontend (brainscaler_frontend). Can link to neuro-workflow UI (e.g. `http://localhost:5173`).

**Tech stack:** Python (FastHTML, Neo4j, etc.), Supabase; frontend on **5001**.

**Run:** See `brainscaler/README.md` (Docker or conda). Not part of the main neuro-workflow Docker stack.

---

### 3.8 Database Adapters (Core Library)

**Location:** `src/neuroworkflow/utils/database_adapters/`.

**Role:** Query external neuroscience databases and Local RAG; return structured parameter suggestions to `ParameterMetadataService`.

**Adapters:**

- **AllenBrainAdapter** — Allen Brain Atlas.
- **NeuroMorphoAdapter** — NeuroMorpho.org.
- **PubMedAdapter** — PubMed/NCBI.
- **NeuroMLDBAdapter** — NeuroML-DB.
- **GenericDatabaseAdapter** — User-defined HTTP/API custom DBs (configured via Django metadata app).
- **LocalRAGAdapter** — Local RAG backend (HTTP to `LOCAL_RAG_BASE_URL`).

**Usage:** Backend builds `ParameterMetadataService` with config (OpenAI, custom DBs, Local RAG); metadata views call the service, which uses these adapters.

---

### 3.9 Simulation Backends

**Role:** Execution backends used by workflow nodes (e.g. simulation nodes). Loaded as Python modules; not tightly coupled.

**Examples:** NEST Simulator, TVB (The Virtual Brain), SONATA. Custom backends can be added.

---

## 4. Interconnections

### 4.1 Frontend ↔ Backend

- **Direction:** Frontend → Backend.
- **Protocol:** HTTP/REST.
- **Base URL:** Same origin `/api` or `VITE_API_BASE_URL` (e.g. `http://localhost:3000/api`).
- **Routes:**  
  - `api/auth/` — health, protected, profile.  
  - `api/box/` — upload, files, uploaded-nodes, sync, copy, parameters/update, categories.  
  - `api/workflow/` — projects CRUD, flow, nodes, edges, instance_name, parameters, generate-code, run, sample-flow.  
  - `api/metadata/` — parameters/suggest, parameters/species-specific, custom-databases (list, detail, test-connection).

### 4.2 Backend ↔ PostgreSQL

- **Direction:** Backend → DB.
- **Config:** Django `DATABASES.default`; host `db` (Docker), env `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`.

### 4.3 Backend ↔ Core Library

- **Direction:** Backend → Core library.
- **Mechanism:** Python import; in Docker, `../src` is mounted at `/django-app/src`.
- **Use cases:** Code generation (WorkflowBuilder + node classes), workflow run (RunWorkflowService runs generated `.py` in subprocess).

### 4.4 Backend ↔ Parameter Metadata

- **Direction:** Backend (app.metadata) → ParameterMetadataService (core library).
- **Mechanism:** Lazy import of `ParameterMetadataService`; config from env (OpenAI, custom DBs, Local RAG).
- **Flow:** Metadata views call the service; service uses database adapters (Allen, NeuroMorpho, PubMed, NeuroML-DB, Generic, LocalRAG).

### 4.5 Backend ↔ Local RAG

- **Direction:** Backend (via LocalRAGAdapter) → Local RAG backend.
- **Protocol:** HTTP to `LOCAL_RAG_BASE_URL` (e.g. `http://localhost:8006` or `http://host.docker.internal:8006`), optional Bearer/login.

### 4.6 Backend ↔ Supabase

- **Direction:** Backend → Supabase (auth).
- **Config:** `SUPABASE_URL`, `SUPABASE_ANON_KEY` in Django config.

### 4.7 Frontend ↔ Supabase

- **Direction:** Frontend → Supabase (login/session).
- **Config:** `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`; `createAuthHeaders()` for API calls.

### 4.8 MCP ↔ Backend

- **Direction:** MCP workflow tools → Backend.
- **Protocol:** HTTP to `DJANGO_API_URL` (e.g. `http://backend:3000/api/workflow`).
- **Port:** MCP proxy **8001**; Cursor/LLM connects to MCP.

### 4.9 Frontend ↔ JupyterHub

- **Direction:** Frontend → JupyterHub (notebook links / launch).
- **Base:** Typically `http://localhost:8000` for hub.

### 4.10 Core Library ↔ Simulation Backends

- **Direction:** Nodes (core/nodes) → Simulation backends (NEST, TVB, SONATA).
- **Mechanism:** Python modules; no tight coupling.

---

## 5. Data Flows

### 5.1 Workflow Definition and Persistence

1. User creates/edits workflow in React Flow.
2. Frontend sends flow as JSON via `PUT /api/workflow/<id>/flow/`.
3. Backend stores in Django DB (FlowProject, FlowNode, FlowEdge).

### 5.2 Code Generation

1. Frontend POSTs nodes/edges to `POST /api/workflow/<id>/generate-code/`.
2. Backend `CodeGenerationService` uses React Flow JSON + node definitions.
3. Code generation uses core `WorkflowBuilder` and node classes.
4. Output: Python script (and optionally .ipynb) under `codes/projects/<ProjectName>/`.

### 5.3 Workflow Run

1. Frontend POSTs to `POST /api/workflow/<id>/run/`.
2. Backend `RunWorkflowService` runs `python <generated_script>` in subprocess.
3. Stdout/stderr returned to frontend (no JupyterHub in this path).

### 5.4 Parameter Suggestions

1. User opens suggestion UI in frontend.
2. Frontend GET `/api/metadata/parameters/suggest/?...`.
3. Backend `ParameterSuggestionView` → `ParameterMetadataService`.
4. Service uses OpenAI (if configured) and database adapters (Allen, NeuroMorpho, PubMed, NeuroML-DB, custom DBs, Local RAG).
5. Aggregated suggestions returned to frontend. Custom DBs: CRUD and test via `api/metadata/custom-databases/`.

### 5.5 Node Definitions

- Stored in DB and on disk (`codes/nodes/`).
- Sync: `api/box/sync/`; upload: `api/box/upload/`.
- Backend reads from `UPLOAD_NODES_PATH` and `NEURO_PATH`.

### 5.6 RAG Flow (Parameter Suggestions)

1. User triggers suggestion → backend metadata service.
2. Local RAG adapter sends HTTP request to RAG backend (e.g. `/query`).
3. RAG returns chunks; adapter (and optionally OpenAI) normalizes to `ParameterSuggestion` format.

---

## 6. Docker Topology (`gui/docker-compose.yml`)

- **db** — Postgres 16; network `workflow`.
- **backend** — Build `workflow_backend`; migrations + runserver 3000; depends on `db`; networks `workflow`, `jupyterhub-network`; volumes: backend code, nodes dir, `../src` (read-only).
- **frontend** — Build `workflow_frontend`; `npm run dev:docker`; port 5173; depends on `backend`; network `workflow`.
- **mcp** — Build `mcp_server`; `python3 proxy.py`; port 8001; depends on `backend`; network `workflow`.
- **jupyterhub** — Build `neuroworkflow` (JupyterHub); port 8000; network `jupyterhub-network`; volumes for config and data.

**Networks:** `workflow` (db, backend, frontend, mcp), `jupyterhub-network` (backend, jupyterhub).

---

## 7. Port Summary

| Service | Port | Notes |
|--------|------|--------|
| Django backend | 3000 | REST API |
| React frontend | 5173 | Vite dev |
| MCP proxy | 8001 | LLM tools |
| JupyterHub | 8000 | Notebooks |
| Local RAG backend | 8006 | Optional |
| Local RAG frontend | 3010 | Optional (this repo default) |
| BrainScaler frontend | 5001 | Separate product |
| PostgreSQL | 5432 | Internal in Docker (optional host expose) |

---

*This document and the accompanying `ARCHITECTURE_DIAGRAM.svg` provide a full-scale reference for the NeuroWorkflow architecture. For high-level vision and extension points, see [ARCHITECTURE.md](ARCHITECTURE.md).*
