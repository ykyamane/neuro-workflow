# CLAUDE.md

## Project Overview

NeuroWorkflow is a Python library and web application for building and executing neural simulation workflows using a node-based system. Developed by the Neural Computation Unit (Doya Lab) at OIST, supported by Brain/MINDS 2.0.

## Repository Structure

```
neuro-workflow/
├── src/neuroworkflow/       # Core Python library (pip-installable)
│   ├── core/                # Node, Workflow, WorkflowBuilder, Schema, Port
│   ├── nodes/               # Built-in node collection (analysis, io, network, optimization, simulation, stimulus)
│   ├── cli/                 # CLI entry point
│   └── utils/
├── gui/                     # Web application (Docker Compose)
│   ├── workflow_frontend/   # React 19 + TypeScript + Vite
│   ├── workflow_backend/    # Django 5 + DRF + PostgreSQL
│   ├── mcp_server/          # MCP proxy server
│   └── docker-compose.yml
├── examples/                # Python API usage examples
├── notebooks/               # Jupyter notebook tutorials
├── data/                    # Sample data files
├── NODE_SCHEMA.md           # Node definition specification
├── CUSTOM_NODE_TUTORIAL.md  # Custom node creation guide
└── CustomNodeTemplate.py    # Template for new nodes
```

## Tech Stack

### Core Library (`src/neuroworkflow/`)
- Python 3.8+, NumPy
- Key classes: `Node`, `Workflow`, `WorkflowBuilder`, `PortType`, `PortDefinition`, `ParameterDefinition`
- Package config: `pyproject.toml` (setuptools)

### Frontend (`gui/workflow_frontend/`)
- React 19, TypeScript ~5.7, Vite 6
- @xyflow/react (React Flow) for node-based UI
- Chakra UI 2.8 for components
- Supabase for auth
- pnpm for package management
- Dev server: port 5173
- Path alias: `@` → `src/`
- API proxy: `/api` → `http://localhost:3000`

### Backend (`gui/workflow_backend/`)
- Django 5.0, Django REST Framework 3.14
- PostgreSQL 16
- Poetry for dependency management
- Python 3.11.11
- Dev server: port 3000
- JupyterHub for workflow code execution (port 8000)
- MCP server for AI tool integration (port 8001)

## Development Commands

### Web Application (Docker)
```bash
cd gui
docker-compose build
docker-compose up
# Frontend: http://localhost:5173
# Backend API: http://localhost:3000/api
# JupyterHub: http://localhost:8000
```

### Backend (local)
```bash
cd gui/workflow_backend
poetry install
poetry run python django-project/manage.py migrate
poetry run python django-project/manage.py runserver 0.0.0.0:3000
```

### Frontend (local)
```bash
cd gui/workflow_frontend
pnpm install
pnpm run dev          # local development
pnpm run dev:docker   # Docker environment
pnpm run build        # production build
```

### Core Library
```bash
pip install -e ".[dev]"          # editable install with dev tools
pip install -e ".[nest]"         # with NEST simulator support
pip install -e ".[visualization]" # with matplotlib/seaborn
```

### Testing & Linting
```bash
# Backend
cd gui/workflow_backend
poetry run pytest
poetry run black .
poetry run isort .
poetry run flake8

# Core library
pytest
black --line-length 88 src/
isort --profile black src/
```

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/workflow/` | List/create workflow projects |
| GET/PUT/DELETE | `/api/workflow/{id}/` | CRUD on a project |
| GET/PUT | `/api/workflow/{id}/flow/` | Get/save flow data (nodes + edges) |
| GET/POST | `/api/workflow/{id}/nodes/` | List/create nodes |
| GET/POST | `/api/workflow/{id}/edges/` | List/create edges |
| POST | `/api/workflow/{id}/generate-code/` | Generate Python code from workflow |
| POST | `/api/workflow/{id}/run/` | Execute workflow (streaming) |

## Environment Variables

Three `.env` files are needed for the web application:

1. **`gui/.env`** — Docker Compose level (NODES_DIR, OPENAI_API_KEY, JUPYTERHUB_API_TOKEN)
2. **`gui/workflow_backend/.env`** — Django (DB_*, SUPABASE_*, DJANGO_SECRET_KEY, paths)
3. **`gui/workflow_frontend/.env`** — Vite (VITE_API_BASE_URL, VITE_SUPABASE_*)

Template: `gui/workflow_backend/env.template`

## Architecture Notes

- Nodes in `src/neuroworkflow/nodes/` must be synced to `gui/workflow_backend/django-project/codes/nodes/` for the web app. Docker Compose mounts `NODES_DIR` to handle this.
- Core library code in `src/neuroworkflow/core/` is also synced to `gui/workflow_backend/django-project/codes/neuroworkflow/core/`.
- Workflow execution uses JupyterHub's kernel WebSocket API — code is generated from the node graph and sent to a Jupyter kernel for execution.
- Authentication is handled by Supabase (JWT). The backend verifies tokens via `SUPABASE_JWT_SECRET`.
- The chat feature uses OpenAI API with Function Calling and MCP integration.

## Code Style

- Python: black (line-length 88), isort (profile: black)
- TypeScript: ESLint
- Django: flake8
- Commit messages: English, concise description of changes

## GitHub

- Repository: `oist/neuro-workflow`
- Main branch: `main`
- PR workflow: feature branches → PR → merge to main
