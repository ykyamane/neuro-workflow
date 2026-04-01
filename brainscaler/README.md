# BrainScaler (OIST) – inside neuro-workflow

This folder contains two cloned OIST repositories. They are **independent** of the main neuro-workflow codebase but live here for convenience.

| Directory | Repo | Role |
|-----------|------|------|
| **brainscaler/** | [oist/brainscaler](https://github.com/oist/brainscaler) | Backend: knowledge graph, ontologies, graph building, RAG pipeline |
| **brainscaler_frontend/** | [oist/brainscaler_frontend](https://github.com/oist/brainscaler_frontend) | Frontend: “Conversational AI” web app (Supabase, Neo4j, LLM chat) |

**Relationship:** They **complement each other** – frontend is the UI that talks to Neo4j (and other services); the backend repo has the tools to build and populate the graph/ontology data.

---

## Two ways to run BrainScaler (port 5001)

**Important:** The Docker stack in **`gui/`** is for **neuro-workflow** (Workflow UI at 5173) only. It does **not** run BrainScaler. BrainScaler has its **own** run options below.

### Option A: Full BrainScaler with Docker (intended by OIST)

Runs the frontend plus Postgres, Neo4j, and MCP in one stack. Use this when you want the full setup.

```bash
cd brainscaler/brainscaler_frontend   # must run from here so ../../env_at_workflow_backend is found
cp .env.example .env   # edit .env: API keys, Neo4j password
docker compose build
docker compose up
```

Supabase credentials are loaded from the repo root file **`env_at_workflow_backend`** (mounted as `.env.backend` in the container). Ensure that file has `SUPABASE_URL` and `SUPABASE_KEY` (same value as `SUPABASE_ANON_KEY` there). Then open **http://localhost:5001**. See `brainscaler_frontend/README.md` for details.

**Sign-up but no activation email?** Supabase requires email confirmation; the message often doesn’t arrive. To log in anyway, confirm your user once with the script in **`gui/SUPABASE_LOGIN_AFTER_SIGNUP.md`** (Option B): you need the project’s **service_role** key from Supabase Dashboard → Project Settings → API, then run `gui/scripts/confirm_supabase_user_by_email.py` with your email.

### Option B: Run with conda locally (admin without activation)

Runs only the frontend on your machine. You can log in as admin with **any email/password** and no Supabase activation if you set one variable. Docker and full Supabase flow are unchanged.

1. **One-time setup** in `brainscaler_frontend/.env`:
   - Copy **SUPABASE_URL** and **SUPABASE_KEY** from the repo root file **`env_at_workflow_backend`** (so the app starts; the key is the same as `SUPABASE_ANON_KEY` there).
   - Add **`BRAINSCALER_DEV_LOCAL_AUTH=1`** so login/sign-up bypass Supabase and accept any credentials with admin role.

2. **Run:**
   ```bash
   conda activate neuro
   cd brainscaler/brainscaler_frontend
   python aifront.py
   ```

3. Open **http://localhost:5001**. Sign up or log in with **any email and password**; you’re in as admin, no activation email.

**Note:** This only affects your local run. Docker does not set `BRAINSCALER_DEV_LOCAL_AUTH`, so the Docker setup still uses full Supabase and email confirmation. If Postgres/Neo4j aren’t running locally, the app will use SQLite for local data when `BRAINSCALER_DEV_LOCAL_AUTH=1`.

---

## Already done

- Both repos are cloned (shallow, `--depth 1`).
- Frontend Python deps are installed in the `neuro` env (`requirements.txt` + langchain, neo4j, python-fasthtml).

---

## Workflow and Dashboard links (optional)

**Are these intended to work?** Yes. BrainScaler’s menu is designed to link to the neuro-workflow app (Workflow) and a separate Dashboard. In this repo, “Workflow” is the neuro-workflow React GUI; the backend is the Django API in `gui/workflow_backend`. The project’s main docs describe a Docker-based run; running everything locally with conda is valid but you must install the backend’s Python deps (e.g. Django) yourself—they are not part of the BrainScaler frontend env.

The BrainScaler nav bar has **Workflow** and **Dashboard** links. They point to:

- **Workflow** → `http://localhost:5173` (neuro-workflow React GUI)
- **Dashboard** → `http://localhost:15173` (separate dashboard app, if you run it)

If you open those links and see a blank or “not loaded” page, that app is not running (for Workflow: run `cd gui && docker compose up`). To use **Workflow**:

1. Install the workflow backend dependencies (once), then start the backend and frontend:
   ```bash
   # Install backend deps into neuro env (Django, DRF, etc.)
   conda activate neuro
   pip install -r gui/workflow_backend/requirements.txt

   # Terminal 1 – backend (manage.py is inside django-project)
   cd gui/workflow_backend/django-project
   python manage.py runserver

   # Terminal 2 – frontend (Vite on port 5173)
   cd gui/workflow_frontend
   pnpm install   # once
   pnpm dev
   ```
2. Open **http://localhost:5173** in the browser; the Workflow link in BrainScaler will then load the same app (it opens in a new tab).

The **Dashboard** link points to port 15173 by default; if you don’t run a dashboard service there, that link will stay empty until you start one or change `DASHBOARD_URL` in `brainscaler_frontend/.env`.

---

## Backend (brainscaler)

The main **brainscaler** repo has no single “app” to run; it contains notebooks, ontology files, and subprojects (e.g. `graph_with_ontology/build_graph/`). Use its README and notebooks as needed. Subprojects have their own `pyproject.toml` (e.g. build_graph requires Python ≥3.14) and can be installed separately if you use them.

---

## Updating the clones

```bash
cd brainscaler/brainscaler && git pull
cd ../brainscaler_frontend && git pull
```

If you originally used a shallow clone and want full history later: `git fetch --unshallow`.
