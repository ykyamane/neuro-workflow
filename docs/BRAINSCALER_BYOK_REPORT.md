# BrainScaler: BYOK (Bring Your Own Key) — implementation report

## Purpose

Allow each logged-in user to store **their own** OpenAI and/or Anthropic API keys for chat and RAG. Keys are **encrypted at rest** in the app database; plaintext is not stored. The UI does not echo saved keys back.

## Scope (what is covered)

| Stored credential | Used for |
|-------------------|----------|
| OpenAI key (BYOK) | OpenAI chat (`ChatOpenAI`), neo4j_graphrag `OpenAILLM`, and `OpenAIEmbeddings` in RAG retrieval when that path runs with user key wiring. |
| Anthropic key (BYOK) | Anthropic chat (`ChatAnthropic`), neo4j_graphrag `AnthropicLLM` for RAG where applicable. |

If only one provider’s key is stored, the other may still fall back to **server environment** variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) where the code still expects them (e.g. embeddings if no OpenAI BYOK).

## Encryption

- **Algorithm:** Fernet (symmetric encryption via `cryptography`).
- **Master secret:** `BYOK_ENCRYPTION_KEY` — a single Fernet key in the **server** environment (not per user).
- **Storage:** Ciphertext in Postgres/SQLite table `user_byok_credentials` (`openai_key_enc`, `anthropic_key_enc`, `updated_at`), keyed by `user_id`.

Anyone with **database access** sees only ciphertext. Decryption requires `BYOK_ENCRYPTION_KEY`. If that master key leaks **and** the DB is exposed, stored user keys can be decrypted — treat `BYOK_ENCRYPTION_KEY` like a root secret (secret manager, no Git commits).

## Configuration

1. Generate a Fernet key (one-time per deployment, keep stable across restarts unless rotating with a migration plan):

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. Set in `brainscaler/brainscaler_frontend/.env` (or container env):

   ```env
   BYOK_ENCRYPTION_KEY=<paste_generated_key>
   ```

3. Rebuild/restart the frontend container so the variable is loaded.

`docker-compose.yml` passes `BYOK_ENCRYPTION_KEY` from the host `.env` into the `frontend` service.

## UI and routes

- **Navigation:** Settings → **API keys (BYOK)** (`/settings/api_keys`).
- **Behavior:** Password fields for OpenAI / Anthropic; optional **Remove saved … key** checkboxes; blank submit keeps existing value for that field.
- If `BYOK_ENCRYPTION_KEY` is unset, the page explains that BYOK is disabled until an admin configures it.

## Code layout (reference)

| Area | Role |
|------|------|
| `shared/components/byok_crypto.py` | Encrypt/decrypt with `BYOK_ENCRYPTION_KEY`. |
| `shared/components/byok_store.py` | Table ensure, save, load decrypted keys for LLM use. |
| `features/settings/page/byok_settings.py` | Settings page and POST handler. |
| `aifront.py` | Routes for `/settings/api_keys`; chat `start_chat` loads per-user keys and passes them into `LLMManager`. |
| `shared/components/llm.py` | `LLMManager(..., openai_api_key=..., anthropic_api_key=...)` for chat + RAG; embeddings use user OpenAI key when set. |

## Dependencies

- `cryptography` is listed in `pyproject.toml`; **`uv.lock` must be updated** after dependency changes (`uv lock`) so Docker `uv sync --locked` succeeds.

## Embedding / index consistency (operational note)

RAG retrieval assumes **the same embedding model and dimensions** as used when the knowledge graph / vector index was built. BYOK does not change that contract: swapping embedding models still requires **re-embedding / rebuilding** indexes to stay consistent.

## Related SQL

- Optional manual DDL: `brainscaler/brainscaler_frontend/sql/brainscaler_byok.sql` (table also created on first use when BYOK is enabled).

---

*Document status: short technical report for operators and future contributors.*
