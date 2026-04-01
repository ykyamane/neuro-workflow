# Running Neuro-Workflow (Docker) and RAG Together

## Why Docker quits when you start RAG

1. **Port conflict**: RAG’s startup script used to kill whatever was on ports **3000** and **8006**. Neuro-workflow’s backend runs in Docker on **host port 3000**. Killing the process on 3000 can make Docker disconnect and show “EOF”.
2. **If you run RAG from another copy** (e.g. `HyperRag/int`), that copy may still use port 3000 and kill it. You must either change that copy or start RAG with a different port and avoid killing 3000.

## Fix in this repo (`neuro-workflow/rag/`)

- RAG’s default frontend port is **3010** (not 3000).
- The script **never kills processes on port 3000** (reserved for neuro-workflow). If something is on 3000, it skips cleanup and tells you to use another RAG port.

## If you run RAG from somewhere else (e.g. HyperRag/int)

Do one of the following.

### Option A: Use port 3010 and avoid killing 3000

1. **Start neuro-workflow first** (Docker).
2. **Start RAG** (setup script uses frontend 3010 by default in this repo):
   ```bash
   cd /path/to/rag   # or HyperRag/int
   python3 setup_and_run.py
   ```
   When asked to start the backend, say yes. In the **other terminal** for the frontend:
   ```bash
   cd frontend
   npm start
   ```
   In **neuro-workflow/rag**, the frontend default is **3010**, so `npm start` listens on 3010. If you use another RAG copy (e.g. HyperRag), run `PORT=3010 npm start` there, or change that copy’s `frontend/server.js` to use `process.env.PORT || 3010`.
3. Open RAG at **http://localhost:3010**. Backend stays **http://localhost:8006**.

### Option B: Disable port cleanup in your RAG copy

In your RAG folder (e.g. HyperRag/int), in `setup_and_run.py`, find the call to `cleanup_existing_processes(...)` and comment it out or guard it so it does not run when neuro-workflow might be using 3000. Then start backend and frontend manually:

```bash
# Terminal 1 – backend
python3 start_server.py --port 8006

# Terminal 2 – frontend (use 3010 so it doesn’t conflict with neuro-workflow on 3000)
cd frontend && PORT=3010 npm start
```

### Option C: Add the “don’t kill 3000” safeguard in your RAG copy

In `setup_and_run.py` (or equivalent) in your RAG project, in the function that kills processes on a port (e.g. `kill_processes_on_port`), add at the top:

```python
# Never kill port 3000 (neuro-workflow / Docker)
if port == 3000:
    print("⚠️ Skipping cleanup for port 3000 (reserved for neuro-workflow)")
    return True
```

Then use **3010** for the RAG frontend (e.g. `FRONTEND_PORT=3010` or change the default to 3010) so the script only cleans 3010 and 8006.

## If the problem persists (Docker still quits)

- **Memory**: Docker + RAG can use a lot of RAM. In Docker Desktop → Settings → Resources, increase **Memory** (e.g. 6–8 GB). Close other heavy apps when running both.
- **Order**: Start **neuro-workflow (Docker) first**, then start RAG with **FRONTEND_PORT=3010** so nothing tries to free or use port 3000.
- **Confirm which RAG you run**: If it’s not `neuro-workflow/rag/`, apply the same port (3010) and “don’t kill 3000” logic in that copy.

## Parameter suggestions from RAG (Local RAG in neuro-workflow UI)

When the neuro-workflow **backend runs in Docker**, it cannot use `http://localhost:8006` to reach the RAG backend on your machine: inside the container, `localhost` is the container itself.

1. In **neuro-workflow** backend env (e.g. `gui/workflow_backend/.env`), set:
   - `LOCAL_RAG_BASE_URL=http://host.docker.internal:8006`  
     (use `localhost` only if the backend runs **outside** Docker on the same host as RAG.)  
     On **Linux** Docker, add `extra_hosts: ["host.docker.internal:host-gateway"]` to the backend service in docker-compose so `host.docker.internal` resolves.
   - `LOCAL_RAG_USERNAME=<your_rag_username>` (e.g. from RAG’s `users.json`).
   - Optional: `LOCAL_RAG_TIMEOUT=90` (default). RAG’s `/global_query` can take 30–90+ seconds; if you see "Read timed out", increase this (e.g. `120`).
2. Restart the neuro-workflow backend (e.g. restart Docker Compose) so it picks up the new env.
3. After restart, backend logs should show either **"Local RAG configured: base_url=..."** or **"Local RAG adapter initialized"**. If you see **"Local RAG not configured"**, `LOCAL_RAG_BASE_URL` is missing or empty. If RAG calls fail, you’ll see a warning like **"Local RAG /global_query failed: ..."** (check that RAG is running and reachable).

## Summary

| App              | Backend port | Frontend port |
|------------------|-------------|---------------|
| Neuro-workflow   | 3000        | 5173          |
| RAG (use this)   | 8006        | **3010**      |

Use RAG frontend on **3010** and never kill or use **3000** when neuro-workflow is running.
