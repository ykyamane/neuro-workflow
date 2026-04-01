# Local RAG Adapter – Implementation and Architecture Report

This document describes the **Local RAG adapter**: a database adapter that connects the neuro-workflow parameter suggestions system to a local RAG (Retrieval-Augmented Generation) or semantic-search backend. It allows the UI to show parameter values and citations derived from your own indexed documents (e.g. papers, NeuroMorpho.Org PDFs) alongside suggestions from Allen Brain Atlas, NeuroMorpho, PubMed, and NeuroML-DB.

---

## 1. Overview

### 1.1 Purpose

- **Input**: Parameter name, description, species, and optional context (e.g. brain region, cell type) when a user requests AI suggestions for a node parameter in the workflow UI.
- **Output**: A list of `ParameterSuggestion` objects (value, source=`local_rag`, confidence, description, citation) that are merged with suggestions from other adapters and shown in the UI.

### 1.2 Design principles

- **Adapter pattern**: Same interface as other DB adapters (`query_parameter()`, `get_source_name()`, `is_available()`).
- **RAG-agnostic**: Prefers POST `/global_query` (in-repo RAG / HyperRag-style) but can fall back to POST/GET `/query` with common payload shapes.
- **Response normalization**: Handles multiple response shapes (e.g. `final_answer` / `synthesis`, `relevant_docs`, `supporting_data`, `all_document_data`).
- **LLM + fallbacks**: Uses OpenAI to turn RAG text into structured suggestions; if that returns nothing, tries a single-value LLM extraction, then regex-based number extraction so that narrative synthesis text still yields at least one suggestion when possible.

---

## 2. Architecture

### 2.1 Component diagram (text)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Neuro-Workflow UI (parameter field → “Get suggestions”)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Django: GET /api/metadata/parameters/suggest/?parameter_name=...        │
│  (app/metadata/views.py)                                                 │
│  → get_metadata_service_instance() → ParameterMetadataService            │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ParameterMetadataService (parameter_metadata_service.py)                │
│  – Runs all adapters in parallel threads                                 │
│  – Waits up to database_query_timeout_sec (10s default; 120s+ if RAG)    │
│  – Merges results, then optional AI validation/enhancement               │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐
│ AllenBrain      │  │ NeuroMorpho     │  │ LocalRAGAdapter                  │
│ PubMed          │  │ NeuroML-DB      │  │ (database_adapters/local_rag.py) │
│ Custom DBs      │  │                 │  │                                 │
└─────────────────┘  └─────────────────┘  └─────────────────────────────────┘
                                                      │
                                                      ▼
                                         ┌─────────────────────────┐
                                         │ Local RAG backend        │
                                         │ (e.g. in-repo RAG :8006) │
                                         │ POST /global_query       │
                                         └─────────────────────────┘
```

### 2.2 Data flow (Local RAG only)

1. **Build query**  
   `_build_query(parameter_name, parameter_description, species, context)` produces a natural-language string, e.g.:  
   `"What is the typical or reported value for the parameter: dendrite_diameter? Context: Mean diameter of dendrites (μm). Species: mouse. Return short excerpts that state a specific numerical value and its source (paper or reference)."`

2. **Call RAG**  
   `_query_rag(query_text)` tries in order:
   - **POST /global_query** with `{ "query": query_text, "top_k": min(max_chunks, 20), "session_uuids": [], "comprehensive": false }`.
   - If that fails or returns no chunks: POST `/query` with `{"query": ...}`, `{"question": ...}`, `{"q": ...}`.
   - If still no chunks: GET `/query?query=...&q=...`.

3. **Normalize response**  
   Response is turned into a list of chunks `{ "text", "source", "score" }`:
   - **Global-query path**: `_normalize_global_query_response()` (see §3.3).
   - **Query fallback**: `_normalize_rag_response()` (generic keys: `results`, `chunks`, `documents`, `data`, `items`, and common item shapes).

4. **Curate to suggestions**  
   - If OpenAI client is available: `_curate_with_llm()` → optional fallback single-value LLM → optional `_extract_numbers_regex()`.
   - If not: `_extract_simple()` (regex only, no LLM).

5. **Return**  
   List of `ParameterSuggestion` with `source=local_rag`, merged by the service with other adapters’ results.

---

## 3. Implementation details

### 3.1 Class and base

- **File**: `src/neuroworkflow/utils/database_adapters/local_rag.py`
- **Class**: `LocalRAGAdapter(DatabaseAdapter)`
- **Base**: `DatabaseAdapter` in `database_adapters/base.py` defines `query_parameter()`, `get_source_name()`, and takes `config` and optional `openai_client`.

**Constructor config (typical keys):**

| Key | Purpose |
|-----|--------|
| `base_url` | RAG API root (e.g. `http://host.docker.internal:8006`) |
| `query_endpoint` | Fallback path, e.g. `/query` |
| `timeout` | HTTP timeout in seconds (e.g. 90 for /global_query) |
| `max_chunks` | Max chunks to use from response (e.g. 10) |
| `source_name` | Display label, e.g. `"Local RAG"` |
| `username` / `password` | Optional auth |
| `login_endpoint` | Optional token endpoint; if empty, username-as-Bearer is used |
| `use_username_as_bearer` | If true and username set, send `Authorization: Bearer <username>` |
| `enabled` | If false, `is_available()` is false |
| `openai_client` | Used for LLM curation and fallback extraction |

**Source identifier**: `get_source_name()` returns `"local_rag"` (constant `LOCAL_RAG_SOURCE`). This is the value used in `ParameterSuggestion.source` and in logging (“Got N suggestions from local_rag”).

### 3.2 RAG API contract

**Primary: POST /global_query**

- **Request**: `{ "query": "<natural language>", "top_k": N, "session_uuids": [], "comprehensive": false }`
- **Response**: JSON with at least one of:
  - **Main answer**: `final_answer`, `finalAnswer`, `synthesis`, or `answer` (string).
  - **Relevant docs**: `relevant_docs` or `relevantDocs` (list of strings or objects with `text`).
  - **Supporting data**: `supporting_data` or `supportingData` (object or list). If object, it may contain:
    - `references`, `chunks` (list of strings or `{ text, source?, score? }`);
    - `all_document_data`: list of `{ doc_name, supporting_data: { child_chunks, parent_chunks } }`; chunks can be string or `{ text, content, body }`.

The adapter accepts responses wrapped under a top-level `data` key if the main keys are not at the root.

**Fallback: POST /query or GET /query**

- POST body: `{"query": "..."}`, `{"question": "..."}`, or `{"q": "..."}`.
- Response: any structure that `_normalize_rag_response()` can interpret (e.g. `results`, `chunks`, `documents`, `data`, `items`, or array root; items with `text`, `content`, `body`, `abstract`, or nested `metadata.text`).

### 3.3 Response normalization (`_normalize_global_query_response`)

- **Main text**: First non-empty of `final_answer`, `finalAnswer`, `synthesis`, `answer`; added as one chunk with `source: "synthesis"`.
- **Relevant docs**: Each string or `{ text }` from `relevant_docs` / `relevantDocs` added as a chunk.
- **Supporting data** (dict):
  - `references` or `chunks`: each string or `{ text, source, score }` added.
  - `all_document_data`: for each entry, `supporting_data.child_chunks` and `parent_chunks` are scanned; each item’s `text`, `content`, or `body` is added with `source: doc_name`.
- **Supporting data** (list): first `max_chunks` items, string or `{ text, source }`.
- Result is trimmed to `max_chunks` chunks.

This design matches the in-repo RAG `GlobalQueryResponse` and the handler’s `supporting_data.all_document_data` structure.

### 3.4 Curation pipeline (chunks → ParameterSuggestion)

1. **Main LLM curation** (`_curate_with_llm`)
   - Builds a single string from all chunks (with “[Excerpt N] (Source: …)” headers).
   - Sends to OpenAI (e.g. `gpt-4o-mini`) with a structured prompt: extract every numerical value that clearly refers to the parameter; include units, citation, confidence; return JSON `{ "values": [ { "value", "units", "citation", "confidence", "context" } ] }`.
   - Parses JSON and builds `ParameterSuggestion` list; logs “Local RAG: LLM curation returned N suggestions”.

2. **Fallback single-value LLM** (if main returns 0 and there is a long synthesis chunk)
   - Takes the synthesis chunk (or first chunk), up to 4000 characters.
   - Asks the model for one number matching the parameter plus units and citation; JSON `{ "value", "units", "citation" }` or `{ "value": null }`.
   - Logs “Local RAG: trying fallback single-value LLM extraction” and on success “Local RAG: fallback single-value extraction added 1 suggestion”.

3. **Regex extraction** (if still 0 suggestions)
   - `_extract_numbers_regex(parameter_name, text, source_label)` runs on the same synthesis text.
   - Patterns: e.g. `(\d+\.?\d*)\s*(?:μm|µm|um|micrometer...)`, parameter/diameter/dendrite within ~60 chars of a number, and generic `X.XX μm`.
   - Values in plausible range (e.g. 0.001–1000), deduplicated; up to 3 suggestions added with confidence 0.55 and citation “Local RAG synthesis”.
   - Logs “Local RAG: regex extraction added N suggestion(s)”.

If no OpenAI client is available, only `_extract_simple()` is used (parameter-name + number regex on chunks).

### 3.5 Authentication

- **Username-as-Bearer (default for in-repo RAG)**  
  If `use_username_as_bearer` is true and `username` is set, no login call is made; every request is sent with `Authorization: Bearer <username>`. The RAG backend is expected to treat the Bearer token as the username.

- **Login endpoint**  
  If `login_endpoint` is set, the adapter can POST credentials (e.g. `username`/`password`) and use the returned `access_token` or `token` for `Authorization: Bearer <token>`.

- **API key**  
  If `api_key` is set and no Bearer token is used, the key can be sent in a header (e.g. `X-API-Key`).

---

## 4. Integration

### 4.1 ParameterMetadataService

- **File**: `src/neuroworkflow/utils/parameter_metadata_service.py`
- **Enum**: `MetadataSource.LOCAL_RAG = "local_rag"`
- **Initialization**: In `_initialize_database_adapters()`, if `config["local_rag"]` exists, a `LocalRAGAdapter` is constructed with the keys listed in §3.1 (including `openai_client`). It is appended to `self.database_adapters` only if `local_rag_adapter.is_available()` is true; then “Local RAG adapter initialized” is logged.

**Overall timeout**: When Local RAG is configured, the view sets `config['database_query_timeout_sec']` to `max(rag_timeout + 30, 120)` so the service waits long enough (e.g. 120 s) for /global_query to complete. Otherwise the default is 10 s.

### 4.2 Metadata view (config builder)

- **File**: `gui/workflow_backend/django-project/app/metadata/views.py`
- **Function**: `get_metadata_service_instance()` builds `config` from the environment and passes it to `get_metadata_service(config=config)`.

**When Local RAG is enabled:**

- `LOCAL_RAG_BASE_URL` must be non-empty (e.g. `http://host.docker.internal:8006`).
- Then `config['local_rag']` is populated from:
  - `LOCAL_RAG_BASE_URL`, `LOCAL_RAG_ENABLED`, `LOCAL_RAG_QUERY_ENDPOINT`, `LOCAL_RAG_TIMEOUT`, `LOCAL_RAG_MAX_CHUNKS`, `LOCAL_RAG_SOURCE_NAME`
  - `LOCAL_RAG_USERNAME`, `LOCAL_RAG_PASSWORD`, `LOCAL_RAG_LOGIN_ENDPOINT`, `LOCAL_RAG_USE_USERNAME_AS_BEARER`
- And `config['database_query_timeout_sec']` is set as above.
- Log: “Local RAG configured: base_url=...”

**When `LOCAL_RAG_BASE_URL` is missing:**

- No `config['local_rag']`, so no Local RAG adapter is created.
- Log: “Local RAG not configured (...)”.

### 4.3 Suggest endpoint

- The same view serves **GET /api/metadata/parameters/suggest/** with query params such as `parameter_name`, `parameter_description`, `node_type`, `species`.
- It calls `get_metadata_service_instance()` and then the service’s method that runs all adapters (including Local RAG) in parallel, merges results, and optionally runs AI validation/enhancement before returning JSON to the frontend.

---

## 5. Configuration reference

All of these are optional except `LOCAL_RAG_BASE_URL` (required to enable the adapter).

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_RAG_BASE_URL` | (none) | RAG API base URL. Use `http://host.docker.internal:8006` when the backend runs in Docker and RAG runs on the host. |
| `LOCAL_RAG_ENABLED` | `true` | Set to `false` to disable the adapter even when base URL is set. |
| `LOCAL_RAG_USERNAME` | (none) | Username for auth; with `USE_USERNAME_AS_BEARER=true` sent as Bearer token. |
| `LOCAL_RAG_PASSWORD` | (none) | Used only if `LOCAL_RAG_LOGIN_ENDPOINT` is set. |
| `LOCAL_RAG_LOGIN_ENDPOINT` | (none) | If empty, Bearer &lt;username&gt; is used (no login call). |
| `LOCAL_RAG_USE_USERNAME_AS_BEARER` | `true` | Send `Authorization: Bearer <username>` when no login endpoint. |
| `LOCAL_RAG_QUERY_ENDPOINT` | `/query` | Fallback path when /global_query is not used. |
| `LOCAL_RAG_TIMEOUT` | `90` | HTTP timeout in seconds for RAG calls; /global_query often needs 30–90+ s. |
| `LOCAL_RAG_MAX_CHUNKS` | `10` | Max chunks taken from the RAG response. |
| `LOCAL_RAG_SOURCE_NAME` | `Local RAG` | Display name for this source. |

Defined in `gui/workflow_backend/env.template` and loaded from `gui/workflow_backend/.env` (or equivalent) by the Django app.

---

## 6. Docker and timeouts

- **Backend in Docker, RAG on host**: Set `LOCAL_RAG_BASE_URL=http://host.docker.internal:8006` so the container can reach the host. On Linux, add `extra_hosts: ["host.docker.internal:host-gateway"]` for the backend service if needed.
- **RAG latency**: /global_query can take 30–90+ seconds. Default `LOCAL_RAG_TIMEOUT=90` and `database_query_timeout_sec` (120 when RAG is configured) allow the request to complete and the result to be collected with other adapters.
- **Runbook**: See `logs/RUNNING_NEURO_WORKFLOW_AND_RAG.md` for ports (RAG backend 8006, frontend 3010) and for not killing port 3000 (neuro-workflow backend).

---

## 7. File and symbol reference

| Item | Location |
|------|----------|
| Local RAG adapter implementation | `src/neuroworkflow/utils/database_adapters/local_rag.py` |
| Base adapter | `src/neuroworkflow/utils/database_adapters/base.py` |
| Adapter registration and timeout | `src/neuroworkflow/utils/parameter_metadata_service.py` |
| Config from env and suggest endpoint | `gui/workflow_backend/django-project/app/metadata/views.py` |
| Env template | `gui/workflow_backend/env.template` |
| Runbook (ports, Docker, RAG) | `logs/RUNNING_NEURO_WORKFLOW_AND_RAG.md` |
| Source identifier | `LOCAL_RAG_SOURCE = "local_rag"`; `MetadataSource.LOCAL_RAG` |

---

## 8. Log messages (diagnostics)

- “Local RAG configured: base_url=...” / “Local RAG not configured (...)”  
  Config build in the metadata view.
- “Local RAG adapter initialized”  
  Adapter added to the service.
- “Local RAG: got N chunks from /global_query (first chunk len=X)”  
  Successful /global_query and normalization.
- “Local RAG /global_query failed: ...”  
  HTTP or connection error calling /global_query.
- “Local RAG: LLM curation returned N suggestions”  
  Main LLM extraction result.
- “Local RAG: trying fallback single-value LLM extraction”  
  Fallback LLM attempted.
- “Local RAG: fallback single-value extraction added 1 suggestion”  
  Fallback LLM succeeded.
- “Local RAG: regex extraction added N suggestion(s)”  
  Regex extraction used.
- “Got 0 suggestions from local_rag” / “Collected N suggestions from local_rag”  
  Per-request result in the metadata service.

This report reflects the implementation as of the Local RAG adapter integration and the fixes for timeouts, response normalization, and fallback extraction (LLM + regex).
