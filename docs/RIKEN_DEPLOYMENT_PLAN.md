# NeuroWorkflow Deployment Plan: RIKEN App Server + Compute Server

This document captures the agreed architecture and implementation plan for deploying NeuroWorkflow across two RIKEN hosts: a **public app server** (web UI, API, code generation) and a **restricted compute server** (data, Slurm, execution, authoritative PostgreSQL).

---

## 1. Architecture Summary

| Layer | App server (public IP) | Compute server (restricted) |
|--------|--------------------------|-----------------------------|
| **Runs** | Reverse proxy, frontend, Django backend, job poller, SSH client | Slurm, execution runtime, datasets, results, logs, **PostgreSQL** |
| **Does not run** | Computation, DB storage | Public web, user-facing API |
| **Connection** | SSH to compute (staging + sbatch); DB client to compute PostgreSQL (private network or SSH tunnel) | Accepts SSH from app only; PostgreSQL private |

**Data rule:** All DB metadata (users, workflows, requests, jobs, history) and all large outputs live on the compute server. The app server only holds transient code staging and returns status/small artifacts to the frontend.

---

## 2. Execution Flow

1. User creates/edits workflow in the web UI (app server).
2. Django generates Python code and manifest (app server).
3. App server stages the project bundle to compute over **SSH** (`rsync` / `scp`).
4. App server submits job on compute with **`sbatch`** (via SSH).
5. Slurm runs the job on compute (wrapper runs generated Python, writes stdout/stderr and manifest).
6. App server **polls** job state (`squeue` / `sacct` via SSH, or DB table updated by compute-side wrapper).
7. Results and logs stay on compute storage.
8. App server reads job metadata from compute PostgreSQL and exposes status/results to the frontend.
9. User can **explicitly download** selected result files (app pulls via SSH/SCP and streams to browser).

---

## 3. Database and Configuration

- **Single authoritative DB:** PostgreSQL on the compute server.
- **App server:** Connects to that DB over private network or SSH tunnel (no second DB).
- **Use DB for:** users, workflows, workflow versions, execution requests, Slurm job IDs, status history, result metadata, file paths/manifests.
- **Use filesystem on compute for:** generated Python, notebooks, stdout/stderr logs, images, model outputs, archives.

**Config externalization:** All of the following should be environment-driven (no hardcoding):

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (compute DB; today `DB_HOST` is hardcoded as `"db"` in settings).
- `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, CORS/CSRF origins.
- Execution mode: `EXECUTION_BACKEND` = `local` | `ssh_slurm`.
- SSH: `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_KEY_PATH`, `REMOTE_PROJECT_ROOT`, `REMOTE_RESULTS_ROOT`.
- Slurm defaults: partition, account, time, memory, CPU (for generated job scripts).

---

## 4. Orchestration: Phase 1 vs Phase 2

- **Phase 1 (recommended):** Direct **Slurm** submission only. One generated Python script → one Slurm job. Lower cost, easier to debug on a restricted cluster.
- **Phase 2 (optional):** Add **Snakemake** only if you need multi-stage pipelines, file-based dependencies, resumable runs, or fan-out/fan-in.

---

## 5. Repository Changes (Implementation Checklist)

### A. Execution abstraction

**Current state:** `RunWorkflowService` in `gui/workflow_backend/django-project/app/workflow/run_workflow_service.py` runs `subprocess.run(["python", script_path])` locally. There is no remote path.

**Target:**

- Introduce an **executor interface** (e.g. `ExecutionBackend`) with:
  - `submit(workflow_id, project_name, script_path, resources, ...) -> job_id`
  - `get_status(job_id) -> status`
  - `get_logs(job_id) -> {stdout, stderr}` (and optional artifact manifest)
  - `cancel(job_id)` (optional)
- Implementations:
  - **Local:** current behaviour (subprocess), for dev/local.
  - **SSH+Slurm:** stage project dir to compute via SSH (rsync/scp), generate Slurm script (reuse or adapt `src/neuroworkflow/utils/job_managers/slurm.py`), run `sbatch` over SSH, poll via `squeue`/`sacct` over SSH.

**Note:** Existing `src/neuroworkflow/utils/job_managers/` has `JobManager` and `SLURMJobManager` that assume Slurm is **local**. For RIKEN you need a **remote** path: either a new `RemoteSlurmJobManager` that runs all commands (sbatch, squeue, sacct) via SSH, or a thin SSH helper that forwards to the existing `SLURMJobManager` on the compute host (e.g. via a small agent on compute). The cleanest is: app server uses SSH to (1) rsync project, (2) run `sbatch <script>` and capture job id, (3) run `squeue`/`sacct` for status; Slurm script on compute runs the generated Python and writes logs/manifest.

**Files to add/change:**

- `app/workflow/execution/` (or under `app/workflow/`): define `ExecutionBackend` and `LocalExecutor`, `RemoteSlurmExecutor`.
- `run_workflow_service.py`: use backend from settings/env (`EXECUTION_BACKEND`), call `submit()` and return `job_id`; no longer block until completion.
- New API: `GET /api/workflow/<workflow_id>/runs/<run_id>/` (or `/jobs/<job_id>/`) returning status, logs, artifact manifest; optional `GET .../runs/<run_id>/download/<path>` for selected files.

### B. Job / Run model

**Current state:** No persistent job/run table. Run is synchronous and stateless.

**Target:** Add a **Job** (or **WorkflowRun**) model, e.g. in `app/workflow/models.py`, with at least:

- `workflow` (FK to FlowProject)
- `request_id` / `run_id` (UUID)
- `slurm_job_id` (nullable, for Slurm mode)
- `status` (pending, running, completed, failed, cancelled)
- `submitted_at`, `started_at`, `ended_at`
- `requested_cpus`, `requested_memory_mb`
- `remote_workdir`, `stdout_path`, `stderr_path`, `artifact_manifest_path`
- `exit_code` (nullable)

**Files to change:**

- `app/workflow/models.py`: add `WorkflowRun` (or `Job`) and run migrations.
- `app/workflow/views.py`: run endpoint creates a run record and calls executor.submit(); new status/logs endpoints read from run record and optionally from executor.
- Optional: background **poller** that periodically updates run status from Slurm (or from compute-side DB updates) and writes back to the same table.

### C. Compute-side job wrapper

**Current state:** Slurm job script in `src/neuroworkflow/utils/job_managers/slurm.py` embeds Python inline. For RIKEN, the script will run on compute where the staged project already exists.

**Target:** A small **wrapper script** (or generator) that:

- Sets up the runtime (env, modules, or container).
- Executes the generated Python script (path passed as argument or fixed layout).
- Writes stdout/stderr to known paths.
- Writes a **machine-readable manifest** (e.g. JSON: list of output files, exit code, timestamps).
- Optionally updates a DB row (e.g. status, end time) if app server uses DB for polling.

**Location:** Can live under `gui/workflow_backend/` or `src/neuroworkflow/utils/` as a template (e.g. `run_neuro_job.sh.in`) or be generated per run. The app server stages this script together with the project when using RemoteSlurmExecutor.

### D. Database host and env

**Current state:** `config/settings.py` uses `"HOST": "db"` for PostgreSQL. `config/config.py` and `env.template` do not define `DB_HOST`.

**Target:**

- Add `DB_HOST = os.getenv("DB_HOST", "db")` in `config/config.py`.
- Use `DB_HOST` in `settings.py` for `DATABASES["default"]["HOST"]`.
- In `env.template`, add `DB_HOST=db` and a comment that for RIKEN this should be the compute server host (or tunnel endpoint).

### E. Frontend: async run and status

**Current state:** Frontend likely POSTs to run and waits for a single response.

**Target:**

- Run returns immediately with `job_id` / `run_id` and initial status (e.g. pending).
- Frontend polls `GET /api/workflow/<id>/runs/<run_id>/` (or jobs endpoint) for status and logs.
- UI shows progress (pending → running → completed/failed) and allows opening logs and downloading selected outputs.

---

## 6. Runtime on Compute

- Use a **versioned execution environment** (Python + NEST/TVB/etc.) on the compute server.
- If Docker is allowed on compute: use the existing NEST/TVB image path documented in the repo.
- If Docker is not allowed: build an **Apptainer/Singularity** image from the same stack and run Slurm jobs with that image.

---

## 7. Security

- App server is the only public entry point.
- Compute server accepts SSH only from the app server (key-based, no password).
- PostgreSQL on compute listens only on private interface (or localhost + SSH tunnel).
- No public Jupyter; no Docker socket on the public path.
- SSH keys and DB credentials in env/secrets, not in the repository.

---

## 8. Minimal Deployment Sequence

| Phase | Actions |
|-------|--------|
| **0** | Run repo locally; confirm workflow create, code generation, and one successful local run. |
| **1** | Deploy frontend + Django on app server; deploy PostgreSQL + storage + Slurm runtime on compute; point Django `DB_*` to compute (private or tunnel). |
| **2** | Implement remote staging (SSH rsync/scp), `sbatch` over SSH, polling (`squeue`/`sacct`), and job/run model; expose status (and optionally logs) in API and UI. |
| **3** | Store logs and artifact manifests on compute; add download endpoint for selected outputs; retention/cleanup rules. |
| **4** | Runtime isolation (containers/Apptainer), notebook/result preview, Snakemake only if needed. |

---

## 9. Summary

The plan is **consistent with the codebase** and with the whiteboard: one public app server, one private compute server, SSH for staging and Slurm, one PostgreSQL on compute, and all heavy data and execution on compute. The main code work is: (1) execution abstraction (local vs SSH+Slurm), (2) job/run model and API, (3) compute-side wrapper and staging, (4) DB host in config, (5) frontend async run and status. Phase 1 uses direct Slurm only; Snakemake can be added later if the workload requires it.
