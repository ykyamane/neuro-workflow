# RIKEN Deployment Overhaul — Implementation Report

**Date:** 2026-01-27
**Branch:** `main` (commit `34c72663`)
**Repository:** https://github.com/oist/neuro-workflow

---

## 1. Overview

This report documents the implementation of the RIKEN deployment overhaul for the NeuroWorkflow application. The work was performed in three phases, following the plan outlined in the plan file. The goal was to transform the application from a local-only development setup into a production-ready system deployable on a RIKEN paired-server architecture (App Server + Compute Server) behind an nginx reverse proxy.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  App Server (public-facing)                                  │
│                                                              │
│  ┌──────────┐    ┌────────────────────────────────────────┐ │
│  │  Nginx   │───>│  Docker Compose                        │ │
│  │ (port 80)│    │  ┌──────────┐  ┌──────────┐           │ │
│  │          │    │  │ Frontend │  │ Backend  │           │ │
│  │  /       │───>│  │ :5173    │  │ :3000    │           │ │
│  │  /api/   │───>│  │          │  │          │──── SSH ──│─│──> Compute Server
│  │  /jupyter│───>│  ├──────────┤  ├──────────┤           │ │
│  │  /mcp/   │───>│  │JupyterHub│  │ Keycloak │           │ │
│  │  /auth/  │───>│  │ :8000    │  │ :8080    │           │ │
│  └──────────┘    │  ├──────────┤  ├──────────┤           │ │
│                  │  │MCP Proxy │  │ Postgres │           │ │
│                  │  │ :8001    │  │ (x2)     │           │ │
│                  │  └──────────┘  └──────────┘           │ │
│                  └────────────────────────────────────────┘ │
│  All Docker ports bind to 127.0.0.1 only                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Compute Server (private)                                    │
│  - Slurm job scheduler                                       │
│  - Python + scientific packages                              │
│  - SSH access from App Server                                │
│  - ~/neuroworkflow-runs/ working directory                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1 — Docker Security + URL Externalization + Nginx

### 2.1 Docker Port Binding (Phase 1A)

**Problem:** All Docker ports were bound to `0.0.0.0`, exposing them publicly. RIKEN security policy prohibits exposing ports other than SSH/HTTP/HTTPS.

**Solution:** All `ports:` entries in `gui/docker-compose.yml` now use `${BIND_HOST:-127.0.0.1}`, defaulting to localhost-only. For local development, set `BIND_HOST=0.0.0.0` in `gui/.env`.

**Files changed:**
- `gui/docker-compose.yml` — 4 port entries updated (backend :3000, JupyterHub :8000, frontend :5173, MCP :8001)

### 2.2 URL Externalization (Phase 1B)

**Problem:** ~30 hardcoded `localhost:PORT` URLs across the frontend and backend, making the app unusable behind a reverse proxy.

**Solution:** Created a centralized URL configuration module and environment-driven settings.

**New file:** `gui/workflow_frontend/src/config/urls.ts`
- Exports `JUPYTER_BASE_URL`, `API_BASE_URL`, `MCP_BASE_URL`
- Reads from `VITE_JUPYTER_BASE_URL`, `VITE_API_BASE_URL`, `VITE_MCP_BASE_URL`
- Falls back to localhost-based detection for local dev compatibility

**Frontend files updated** (10 files):

| File | Change |
|------|--------|
| `homeView.tsx` | Replaced `jupyterBase` IIFE and `localhost:3000/api/box` with config imports |
| `jupyterModal.tsx` | Default prop and dev login URL use `JUPYTER_BASE_URL` |
| `nodeDetailModal.tsx` | `OpenJupyter` uses `JUPYTER_BASE_URL` |
| `calculationNode.tsx` | Removed `jupyterBase` IIFE, uses config import |
| `projectSelector.tsx` | Same pattern |
| `boxView.tsx` | Same pattern |
| `codeEditorModal.tsx` | Default `baseUrl` uses `API_BASE_URL` |
| `useJupyterHub.ts` | Default config uses `JUPYTER_BASE_URL` |
| `workflowRunApi.ts` | `API_PREFIX` uses `API_BASE_URL` |
| `vite.config.ts` | Proxy target from `VITE_PROXY_BACKEND` env var |

**Backend files updated:**
- `config/settings.py` — `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `ALLOWED_HOSTS` now accept additional values via `_EXTRA` env vars (e.g., `CORS_ALLOWED_ORIGINS_EXTRA=https://server.riken.jp`)

### 2.3 Nginx Reference Config (Phase 1C)

**New file:** `gui/nginx/neuro-workflow.conf`

Provides a complete nginx reverse-proxy configuration with:
- Upstream blocks for all 4 services
- WebSocket support for Vite HMR and Jupyter kernels
- SSE buffering disabled for API streaming and MCP
- Commented-out Keycloak location block (ready for Phase 2)

### 2.4 Production Docker Compose Override (Phase 1D)

**New file:** `gui/docker-compose.prod.yml`

Usage: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

Sets environment variables for behind-nginx operation:
- `VITE_API_BASE_URL=/api`
- `VITE_JUPYTER_BASE_URL=/jupyter`
- `VITE_MCP_BASE_URL=/mcp`

---

## 3. Phase 2 — Keycloak Authentication

### 3.1 Keycloak Docker Services (Phase 2A)

Added to `gui/docker-compose.yml`:
- `keycloak` — Keycloak v26.0 identity server on port 8080
- `keycloak-db` — Dedicated Postgres 16 for Keycloak data
- `keycloak_data` volume for persistence

Configuration uses `KC_HTTP_RELATIVE_PATH=/auth` so Keycloak is served at `/auth/` behind nginx.

### 3.2 Backend Authentication (Phase 2B)

**File:** `gui/workflow_backend/django-project/app/auth/authentication.py`

Completely rewritten to support both providers:

- `KeycloakAuthentication` — Verifies JWTs via RS256 against the Keycloak JWKS endpoint. Gets-or-creates Django users from `sub`, `email`, `given_name`, `family_name` claims.
- `SupabaseAuthentication` — Preserved for backward compatibility. Tries HS256 with JWT secret, falls back to RS256 via JWKS.
- Shared `_BearerAuthentication` base class for token extraction.
- JWKS response caching with automatic refresh on key rotation.

**Other backend changes:**
- `config/config.py` — Added `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID` env vars
- `config/settings.py` — Imports and exposes Keycloak settings alongside Supabase
- `app/chat/views.py` — `_OptionalAuthentication` tries Keycloak first, then Supabase, with silent fallback to anonymous

### 3.3 Frontend Authentication (Phase 2C)

The frontend auth system was rewritten as a **dual-mode facade**: when `VITE_KEYCLOAK_URL` is set, it uses Keycloak; otherwise it falls back to Supabase. This allows gradual migration.

**New file:** `gui/workflow_frontend/src/auth/keycloak.ts`
- Initializes `keycloak-js` adapter from VITE env vars
- Exports `isKeycloakConfigured` flag and `getKeycloak()` singleton

**Rewritten files:**

| File | Change |
|------|--------|
| `authService.ts` | Unified facade: `signIn()`, `signOut()`, `signUp()`, `getAccessToken()`, `getCurrentUser()` all delegate to Keycloak or Supabase based on config |
| `authContext.tsx` | Calls `initKeycloak()` on mount when configured; `onAuthStateChange` wired for both providers |
| `authHeaders.ts` | Gets token via `authService.getAccessToken()` instead of direct Supabase SDK call |
| `apiInterceptors.ts` | Uses `authService.signOut()` on 401 instead of direct Supabase call |

**Dependency:** Added `keycloak-js: ^26.0.0` to `package.json`.

### 3.4 Keycloak Realm Setup (Phase 2D)

**New files:**
- `gui/keycloak/realm-export.json` — Pre-configured realm with:
  - Realm: `neuroworkflow`
  - Client: `neuroworkflow-app` (public, SPA, PKCE-enabled)
  - Roles: `user`, `admin`
  - Redirect URIs for localhost and `*.riken.jp`
- `gui/keycloak/setup.sh` — Automated setup script that waits for Keycloak, obtains an admin token, and imports the realm via the REST API

---

## 4. Phase 3 — Execution Abstraction (SSH + Slurm)

### 4.1 Execution Backend Interface (Phase 3A)

**New directory:** `gui/workflow_backend/django-project/app/workflow/execution/`

| File | Description |
|------|-------------|
| `base.py` | Abstract `ExecutionBackend` with `submit()`, `get_status()`, `get_logs()`, `cancel()`. Defines `ExecutionStatus` enum and `ExecutionResult` dataclass. |
| `local_executor.py` | Runs scripts as subprocesses on the app server. In-memory run tracking with threaded execution. |
| `remote_slurm_executor.py` | SSH + rsync staging, `sbatch` submission, `sacct`/`squeue` polling, remote log retrieval. Configured via `SLURM_HOST`, `SLURM_USER`, `SLURM_SSH_KEY`, etc. |

### 4.2 WorkflowRun Model (Phase 3B)

**File:** `gui/workflow_backend/django-project/app/workflow/models.py`

Added `WorkflowRun` model:
- UUID primary key
- Foreign keys to `FlowProject` and `User`
- `backend` choice field: `local`, `slurm`, `jupyter`
- `status` choice field: `pending`, `running`, `completed`, `failed`, `cancelled`
- Fields: `slurm_job_id`, `exit_code`, `stdout`, `stderr`, `error_message`, `resource_requests` (JSON), `artifacts` (JSON), timestamps

Migration is auto-generated at container startup (`makemigrations` runs in the Docker command).

### 4.3 Async Run API Endpoints (Phase 3C)

**New endpoints in** `gui/workflow_backend/django-project/app/workflow/urls.py`:

| Method | Path | View | Description |
|--------|------|------|-------------|
| POST | `workflow/<id>/runs/submit/` | `WorkflowRunSubmitView` | Submit a run, returns immediately with run_id + status |
| GET | `workflow/<id>/runs/` | `WorkflowRunListView` | List all runs for a workflow (last 50) |
| GET | `workflow/<id>/runs/<run_id>/` | `WorkflowRunDetailView` | Get status, logs, artifacts for a run (polls executor) |
| POST | `workflow/<id>/runs/<run_id>/cancel/` | `WorkflowRunCancelView` | Cancel a pending/running run |

### 4.4 Frontend Run Status Panel (Phase 3D)

**New file:** `gui/workflow_frontend/src/views/home/components/runStatusPanel.tsx`

Floating overlay panel at bottom-right of the workflow canvas that:
- Lists recent runs with status badges
- Polls active runs every 3 seconds
- Displays stdout/stderr in monospace log views
- Provides a cancel button for running jobs
- Collapses/expands to minimize visual clutter

**API functions in** `workflowRunApi.ts`:
- `submitWorkflowRun()`, `getWorkflowRunStatus()`, `listWorkflowRuns()`, `cancelWorkflowRun()`

### 4.5 Slurm Job Wrapper Template (Phase 3E)

**New file:** `gui/workflow_backend/django-project/app/workflow/execution/templates/slurm_wrapper.sh.template`

Template script staged on the compute node alongside the generated Python:
- SBATCH directives (partition, account, resources)
- Conda/venv environment activation
- stdout/stderr capture to log files
- Exit code recording
- `manifest.json` generation with job metadata

---

## 5. Environment Configuration Summary

### 5.1 New Environment Variables

**Backend** (`gui/workflow_backend/.env` / `env.template`):

| Variable | Default | Description |
|----------|---------|-------------|
| `KEYCLOAK_URL` | `http://keycloak:8080/auth` | Keycloak server URL (container-to-container) |
| `KEYCLOAK_REALM` | `neuroworkflow` | Keycloak realm name |
| `KEYCLOAK_CLIENT_ID` | `neuroworkflow-app` | Keycloak client ID |
| `ALLOWED_HOSTS_EXTRA` | _(empty)_ | Additional allowed hosts, comma-separated |
| `ALLOWED_HOSTS_ALL` | _(empty)_ | Set to `true` to allow all hosts |
| `CORS_ALLOWED_ORIGINS_EXTRA` | _(empty)_ | Additional CORS origins |
| `CORS_ALLOW_ALL` | _(empty)_ | Set to `true` to allow all origins |
| `CSRF_TRUSTED_ORIGINS_EXTRA` | _(empty)_ | Additional CSRF trusted origins |
| `SLURM_HOST` | _(empty)_ | Compute server hostname |
| `SLURM_USER` | _(empty)_ | SSH user for compute server |
| `SLURM_SSH_KEY` | _(empty)_ | Path to SSH private key |
| `SLURM_REMOTE_DIR` | `~/neuroworkflow-runs` | Remote working directory |
| `SLURM_PARTITION` | _(empty)_ | Slurm partition |
| `SLURM_ACCOUNT` | _(empty)_ | Slurm account |

**Frontend** (`gui/workflow_frontend/.env` / `env.template`):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `/api` | Browser-facing API URL |
| `VITE_JUPYTER_BASE_URL` | `http://localhost:8000` | Browser-facing JupyterHub URL |
| `VITE_MCP_BASE_URL` | `/mcp` | Browser-facing MCP URL |
| `VITE_KEYCLOAK_URL` | _(empty)_ | Keycloak URL (enables Keycloak auth when set) |
| `VITE_KEYCLOAK_REALM` | `neuroworkflow` | Keycloak realm |
| `VITE_KEYCLOAK_CLIENT_ID` | `neuroworkflow-app` | Keycloak client ID |

**Docker Compose** (`gui/.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `BIND_HOST` | `127.0.0.1` | Port binding host (`0.0.0.0` for local dev) |
| `KEYCLOAK_DB_PASSWORD` | `keycloak` | Keycloak database password |
| `KEYCLOAK_ADMIN` | `admin` | Keycloak admin username |
| `KEYCLOAK_ADMIN_PASSWORD` | `admin` | Keycloak admin password |

---

## 6. Files Created and Modified

### New Files (12)

| File | Purpose |
|------|---------|
| `gui/.env.example` | Environment template for Docker Compose |
| `gui/docker-compose.prod.yml` | Production override for behind-nginx deployment |
| `gui/nginx/neuro-workflow.conf` | Reference nginx reverse-proxy configuration |
| `gui/keycloak/realm-export.json` | Keycloak realm definition |
| `gui/keycloak/setup.sh` | Automated realm import script |
| `gui/workflow_frontend/src/config/urls.ts` | Centralized URL configuration |
| `gui/workflow_frontend/src/auth/keycloak.ts` | Keycloak JS adapter |
| `gui/workflow_frontend/src/views/home/components/runStatusPanel.tsx` | Run status overlay component |
| `gui/workflow_backend/.../execution/__init__.py` | Execution package init |
| `gui/workflow_backend/.../execution/base.py` | Abstract execution backend |
| `gui/workflow_backend/.../execution/local_executor.py` | Local subprocess executor |
| `gui/workflow_backend/.../execution/remote_slurm_executor.py` | SSH + Slurm executor |
| `gui/workflow_backend/.../execution/templates/slurm_wrapper.sh.template` | Slurm job template |

### Modified Files (27)

| File | Change Summary |
|------|----------------|
| `gui/docker-compose.yml` | Port binding + Keycloak services |
| `gui/workflow_backend/env.template` | New env vars (Keycloak, CORS, deployment) |
| `gui/workflow_backend/.../config/config.py` | Keycloak env vars |
| `gui/workflow_backend/.../config/settings.py` | Keycloak settings, env-driven CORS/CSRF/HOSTS |
| `gui/workflow_backend/.../app/auth/authentication.py` | Dual Keycloak + Supabase auth |
| `gui/workflow_backend/.../app/chat/views.py` | Dual-mode optional auth |
| `gui/workflow_backend/.../app/workflow/models.py` | WorkflowRun model |
| `gui/workflow_backend/.../app/workflow/serializers.py` | WorkflowRun serializers |
| `gui/workflow_backend/.../app/workflow/urls.py` | Async run endpoints |
| `gui/workflow_backend/.../app/workflow/views.py` | Run submit/status/cancel views |
| `gui/workflow_frontend/env.template` | New VITE env vars |
| `gui/workflow_frontend/package.json` | Added keycloak-js |
| `gui/workflow_frontend/src/auth/authService.ts` | Dual-mode auth facade |
| `gui/workflow_frontend/src/auth/authContext.tsx` | Keycloak init support |
| `gui/workflow_frontend/src/api/authHeaders.ts` | Unified token retrieval |
| `gui/workflow_frontend/src/api/apiInterceptors.ts` | Provider-agnostic 401 handling |
| `gui/workflow_frontend/src/api/workflowRunApi.ts` | Async run API functions |
| `gui/workflow_frontend/src/views/home/homeView.tsx` | RunStatusPanel integration + URL config |
| `gui/workflow_frontend/src/views/home/components/jupyterModal.tsx` | URL config |
| `gui/workflow_frontend/src/views/home/components/nodeDetailModal.tsx` | URL config |
| `gui/workflow_frontend/src/views/home/components/calculationNode.tsx` | URL config |
| `gui/workflow_frontend/src/views/home/components/projectSelector.tsx` | URL config |
| `gui/workflow_frontend/src/views/home/components/codeEditorModal.tsx` | URL config |
| `gui/workflow_frontend/src/views/box/boxView.tsx` | URL config |
| `gui/workflow_frontend/src/hooks/useJupyterHub.ts` | URL config |
| `gui/workflow_frontend/vite.config.ts` | Env-driven proxy target |

---

## 7. Deployment Checklist

### App Server

- [ ] Clone the repo: `git clone https://github.com/oist/neuro-workflow.git /data/neuro-workflow`
- [ ] Create `gui/.env` from `gui/.env.example` with:
  - `NODES_DIR` and `HOST_PROJECT_PATH` pointing to the actual paths
  - `KEYCLOAK_ADMIN_PASSWORD` — a strong password
  - `KEYCLOAK_DB_PASSWORD` — a strong password
  - Do NOT set `BIND_HOST` (defaults to `127.0.0.1`)
- [ ] Create `gui/workflow_backend/.env` from `gui/workflow_backend/env.template` with:
  - `DB_PASSWORD` — a strong database password
  - `DJANGO_SECRET_KEY` — a new random secret key
  - `KEYCLOAK_URL=http://keycloak:8080/auth`
  - `KEYCLOAK_REALM=neuroworkflow`
  - `KEYCLOAK_CLIENT_ID=neuroworkflow-app`
  - `ALLOWED_HOSTS_EXTRA=your-server.riken.jp`
  - `CORS_ALLOWED_ORIGINS_EXTRA=https://your-server.riken.jp`
  - `CSRF_TRUSTED_ORIGINS_EXTRA=https://your-server.riken.jp`
  - Supabase variables can be left blank to disable Supabase auth
- [ ] Create `gui/workflow_frontend/.env` from `gui/workflow_frontend/env.template` with:
  - `VITE_API_BASE_URL=/api`
  - `VITE_JUPYTER_BASE_URL=/jupyter`
  - `VITE_MCP_BASE_URL=/mcp`
  - `VITE_KEYCLOAK_URL=/auth`
  - `VITE_KEYCLOAK_REALM=neuroworkflow`
  - `VITE_KEYCLOAK_CLIENT_ID=neuroworkflow-app`
- [ ] Install nginx config:
  ```
  sudo cp gui/nginx/neuro-workflow.conf /etc/nginx/sites-available/neuro-workflow
  sudo ln -sf /etc/nginx/sites-available/neuro-workflow /etc/nginx/sites-enabled/
  sudo nginx -t && sudo systemctl reload nginx
  ```
- [ ] Uncomment the `/auth/` location block in the nginx config for Keycloak
- [ ] Start the application:
  ```
  cd /data/neuro-workflow/gui
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  ```
- [ ] Import the Keycloak realm (one-time):
  ```
  ./keycloak/setup.sh
  ```
- [ ] Create initial users via the Keycloak admin console at `https://your-server.riken.jp/auth/admin/`

### Compute Server

- [ ] Create a dedicated user (e.g., `neuroworkflow`) for SSH access
- [ ] Set up key-based SSH authentication from the App Server
- [ ] Install Python with the required scientific packages (NEST, etc.)
- [ ] Ensure Slurm is configured and the user can submit jobs
- [ ] Create the working directory: `mkdir -p ~/neuroworkflow-runs`
- [ ] Add Slurm env vars to the App Server's `gui/workflow_backend/.env`:
  ```
  SLURM_HOST=compute-server-ip-or-hostname
  SLURM_USER=neuroworkflow
  SLURM_SSH_KEY=/path/to/private/key
  SLURM_REMOTE_DIR=~/neuroworkflow-runs
  SLURM_PARTITION=default
  ```

---

## 8. Backward Compatibility

The implementation preserves full backward compatibility with the existing setup:

- **Authentication:** Supabase still works when `VITE_KEYCLOAK_URL` is not set. The backend tries Keycloak first, then falls back to Supabase.
- **Local development:** Setting `BIND_HOST=0.0.0.0` in `gui/.env` restores the old behavior of publicly-bound ports. The `VITE_JUPYTER_BASE_URL` config falls back to the same window-location-based detection that was previously hardcoded.
- **Execution:** The existing SSE-streaming execution via JupyterHub (`POST /api/workflow/<id>/run/`) is unchanged. The new async API (`/runs/submit/`, etc.) is additive.

---

## 9. Known Limitations and Future Work

1. **Keycloak `start-dev` mode:** The current Docker config uses `start-dev` for Keycloak, which is not optimized for production. For a production deployment, switch to `start` with proper HTTPS configuration.

2. **Frontend production build:** The frontend currently runs via Vite dev server even in "production." For true production, build the frontend (`npm run build`) and serve the static files via nginx directly, bypassing the Vite container.

3. **Slurm executor state persistence:** The `LocalExecutor` stores run state in memory (lost on restart). For production use, run state should be read from the `WorkflowRun` database model, which persists across restarts.

4. **Slurm executor metadata:** The `RemoteSlurmExecutor._read_remote_meta()` method reads from a local staging directory that doesn't yet store the `job_id` after submission. This needs a write step after successful `sbatch`.

5. **RunStatusPanel UX:** The panel currently shows for all projects regardless of whether async runs exist. It could be hidden when there are no runs, or integrated more tightly with the existing SSE-based execution flow.

6. **SSL/TLS:** The nginx config listens on port 80. For production, add an HTTPS server block with certificates (e.g., Let's Encrypt via certbot).

7. **Keycloak production realm setup:** The redirect URIs in `realm-export.json` include wildcard `*.riken.jp`. For production, restrict these to the exact server domain.
