# Local RAG Adapter for Parameter Suggestions

## Overview

The **Local RAG adapter** integrates a local RAG-based semantic search system (e.g. HyperRag) into the NeuroWorkflow parameter suggestion pipeline. It behaves like the PubMed adapter: it queries a knowledge base of papers for parameter-related snippets, then uses an LLM to turn those snippets into structured **ParameterSuggestion** results (value, source, confidence, description, citation) so they appear alongside suggestions from Allen Brain Atlas, NeuroMorpho, PubMed, and NeuroML-DB.

## How It Works

1. **Query formulation**  
   For each parameter request, the adapter builds a short natural-language query (parameter name, description, species, context) asking for typical/reported values and references.

2. **RAG API call**  
   It calls your local RAG API (e.g. `POST /query` or `/search`) with that text. The adapter supports common request shapes: `{"query": "..."}`, `{"question": "..."}`, or `{"q": "..."}`.

3. **Response normalization**  
   Responses are normalized from typical RAG shapes: `results`, `chunks`, `documents`, `data`, or `items`. Each item is expected to have `text` (or `content`/`body`/`abstract`) and optionally `metadata` (e.g. `source`, `citation`, `title`).

4. **LLM curation**  
   The combined excerpts are sent to the same LLM used elsewhere (e.g. gpt-4o-mini). The model extracts numerical values, units, and references and returns JSON in the same schema as the other adapters. Results are converted to **ParameterSuggestion** (value, source=`local_rag`, confidence, description, citation, metadata).

5. **Fallback without LLM**  
   If OpenAI is not configured, a simple regex-based numeric extraction is used and confidence is set to 0.5.

## Configuration

The adapter is configured via the **ParameterMetadataService** and (in the Django backend) via **environment variables**.

### Environment variables (backend `.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCAL_RAG_BASE_URL` | Base URL of your RAG API (e.g. `http://localhost:5000`) | (empty – adapter disabled if not set) |
| `LOCAL_RAG_QUERY_ENDPOINT` | Path for the query endpoint | `/query` |
| `LOCAL_RAG_ENABLED` | Set to `true` to enable when `LOCAL_RAG_BASE_URL` is set | `true` |
| `LOCAL_RAG_TIMEOUT` | Request timeout in seconds | `15` |
| `LOCAL_RAG_MAX_CHUNKS` | Max number of chunks to send to the LLM | `10` |
| `LOCAL_RAG_SOURCE_NAME` | Label used in descriptions (e.g. "Local RAG") | `Local RAG` |
| `LOCAL_RAG_USERNAME` | Username for RAG API login | (empty) |
| `LOCAL_RAG_PASSWORD` | Password for RAG API login | (empty) |
| `LOCAL_RAG_LOGIN_ENDPOINT` | Path for login (only if your RAG has a token API) | (empty) |
| `LOCAL_RAG_USE_USERNAME_AS_BEARER` | Use username as Bearer token (no login call); set to `true` for the in-repo RAG | `true` |

**In-repo RAG (e.g. `rag/` in this repo):** The backend (port 8006) has **no** `/login` endpoint. It expects **`Authorization: Bearer <username>`** and looks up the user in `users.json`. So you only set `LOCAL_RAG_USERNAME` (and optionally `LOCAL_RAG_PASSWORD` for your own reference); leave `LOCAL_RAG_LOGIN_ENDPOINT` unset or empty. The adapter sends Bearer username by default (`LOCAL_RAG_USE_USERNAME_AS_BEARER=true`). For other RAGs that return a token from a login endpoint, set `LOCAL_RAG_LOGIN_ENDPOINT` and the adapter will POST to get a token.

Example (add to `gui/workflow_backend/.env` when your RAG is running; typical RAG backend port is **8006**, frontend 3000):

```bash
LOCAL_RAG_BASE_URL=http://localhost:8006
LOCAL_RAG_USERNAME=john_doe
LOCAL_RAG_PASSWORD=john123
# No LOGIN_ENDPOINT: this RAG uses Bearer <username> (see users.json)
# LOCAL_RAG_USE_USERNAME_AS_BEARER=true
```

If your RAG runs on another host/port, set `LOCAL_RAG_BASE_URL` accordingly. From Docker, use a hostname the backend container can reach (e.g. `http://host.docker.internal:8006` on Mac/Windows if the RAG runs on the host).

### Programmatic config

When creating **ParameterMetadataService** with a config dict, you can pass:

```python
config = {
    "local_rag": {
        "base_url": "http://localhost:8006",
        "query_endpoint": "/query",
        "enabled": True,
        "timeout": 15,
        "max_chunks": 10,
        "source_name": "Local RAG",
        "username": "john_doe",   # optional, for login
        "password": "john123",   # optional
        "login_endpoint": "/login",  # optional
        "api_key": "",           # optional (alternative to username/password)
        "api_key_header": "X-API-Key",  # optional
    }
}
```

## RAG API expectations

**In-repo RAG (this repo’s `rag/`):**
- **Auth**: `Authorization: Bearer <username>`. No login endpoint on the backend; user list in `rag/users.json`.
- **Query**: Adapter calls **POST /global_query** with `{"query": "...", "top_k": N, "session_uuids": [], "comprehensive": false}`. Response: `final_answer`, `relevant_docs`, `supporting_data` — normalized into chunks for LLM curation.
- **Port**: Backend **8006**, frontend 3000.

**Generic RAG (other backends):**
- **Method**: POST to `/query` or `/global_query`; GET with `query`/`q` as fallback.
- **Body**: JSON with `query` (and for /global_query: `top_k`, `session_uuids`, `comprehensive`), or `question`/`q`.
- **Response**: Either `final_answer` + `relevant_docs` (see `_normalize_global_query_response`) or a list under `results`/`chunks`/`documents`/`data`/`items` with `text` or `content`, optional `metadata`/`source`, `score`.

## Running your RAG (e.g. HyperRag)

You run the RAG separately, for example:

- Backend: `cd /path/to/HyperRag/int && ./start_local.sh` (or `python start_server.py --port 8006`)
- Frontend (if needed): `cd /path/to/HyperRag/int/frontend && PORT=3000 npm start`

Typical ports: **Backend API 8006**, Frontend **3010** (default). RAG’s default frontend port is 3010 so that its startup “port cleanup” does not kill neuro-workflow’s backend on port 3000 when both run (e.g. neuro-workflow in Docker on 3000). Set `LOCAL_RAG_BASE_URL=http://localhost:8006` to the **backend API** base URL. If the RAG uses authentication, set `LOCAL_RAG_USERNAME` (and optionally `LOCAL_RAG_PASSWORD`).

## Files

- **Adapter**: `src/neuroworkflow/utils/database_adapters/local_rag.py`
- **Registration**: `src/neuroworkflow/utils/parameter_metadata_service.py` (MetadataSource.LOCAL_RAG, LocalRAGAdapter in `_initialize_database_adapters`)
- **Backend config**: `gui/workflow_backend/django-project/app/metadata/views.py` (builds `config['local_rag']` from env)
- **Env template**: `gui/workflow_backend/env.template` (optional LOCAL_RAG_* variables)

## Coherence with existing system

- Uses the same **ParameterSuggestion** dataclass and **DatabaseAdapter** interface as Allen, NeuroMorpho, PubMed, NeuroML-DB.
- Participates in the same parallel query execution and timeout as other adapters.
- Source name is `local_rag` (MetadataSource.LOCAL_RAG); suggestions are merged and returned with the rest in the existing suggest API.
- No UI changes: the Settings → Custom Databases flow is for **user-defined** REST sources; Local RAG is a **built-in** adapter configured by env (or service config), similar to PubMed.
