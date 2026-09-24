# Technical Documentation — AI Production Assistant

> This document is derived directly from the source code in `backend/app/` and
> `compose/docker-compose.yml`. Commands are only included where they correspond to something that actually
> exists in the code. Where the project structure you provided mentions files not present in the reviewed
> archive (`requirements.txt`, root `README.md`, a top-level `frontend/` directory), this is called out
> explicitly rather than assumed — see the notes inline and the summary at the end.

## 1. Project Introduction

The AI Production Assistant is an on-premises Retrieval-Augmented Generation (RAG) system that answers
production-operator questions from indexed technical documentation. A FastAPI backend handles authentication,
retrieval, LLM generation via a local Ollama instance, and persistence to PostgreSQL. See
`docs/SYSTEM_DESIGN.md` for the full architecture.

## 2. Prerequisites

Verified from imports and configuration actually present in the code:

- Python 3 (version not pinned anywhere in the reviewed archive — no `pyproject.toml`, `setup.py`, or
  `runtime.txt` was found).
- Docker + Docker Compose (for PostgreSQL, per `compose/docker-compose.yml`).
- [Ollama](https://ollama.com) installed and runnable locally, with the `phi3:mini` model available
  (hardcoded as `MODEL_NAME` in `app/rag/generator.py`).
- Network/disk access to pre-download the `all-MiniLM-L6-v2` model at least once — the code loads it with
  `local_files_only=True`, meaning it will **fail to start** if the model has never been cached locally on that
  machine.
- A directory for source documents and one for the ChromaDB index (hardcoded as `/srv/ai-data/documents` and
  `/srv/ai-data/chroma` in `app/rag/vector_store.py`).

## 3. Installation

### 3.1 Python Virtual Environment

No environment-creation script was found in the archive. A standard venv works with the project's import
structure (`app.*` imports resolved relative to `backend/`):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 3.2 Dependency Installation

**No `requirements.txt` was found in the reviewed archive**, despite being listed in your stated project
structure. The following packages are inferred directly from the `import`/`from` statements actually present
in the code — install them manually until a real `requirements.txt` is added to the repo:

```bash
pip install fastapi uvicorn pydantic psycopg[binary] bcrypt chromadb sentence-transformers requests pymupdf
```

| Package | Used for | Found in |
|---|---|---|
| `fastapi` | Web framework | `main.py`, endpoint files |
| `uvicorn` | ASGI server | Needed to run `app.main:app` (not imported in code, but required to serve it) |
| `pydantic` | Request/response models | `LoginRequest`, `ChatRequest` |
| `psycopg` | PostgreSQL driver | `db/database.py` |
| `bcrypt` | Password hashing | `services/auth.py` |
| `chromadb` | Vector store | `rag/vector_store.py` |
| `sentence-transformers` | Embedding model | `rag/vector_store.py` |
| `requests` | HTTP calls to Ollama | `rag/generator.py` |
| `pymupdf` (imported as `fitz`) | PDF text extraction | `rag/vector_store.py`, `rag/ingestion.py` |

No version pins could be verified — add them once a real `requirements.txt` exists, ideally generated with
`pip freeze > requirements.txt` from a known-working environment.

### 3.3 Environment Variables / Configuration

The only environment variable actually read by the application code is `DATABASE_URL`
(`app/db/database.py`, via `os.getenv("DATABASE_URL")`). If it is unset, `get_connection()` raises a
`RuntimeError` immediately.

```bash
# .env (example only — never commit real credentials)
DATABASE_URL=postgresql://YOUR_DB_USER:YOUR_DATABASE_PASSWORD@127.0.0.1:5432/YOUR_DB_NAME
```

`compose/docker-compose.yml` separately expects `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` at
compose time (these populate the container; they are not read by the Python application directly):

```bash
# .env used by docker compose
POSTGRES_DB=YOUR_DB_NAME
POSTGRES_USER=YOUR_DB_USER
POSTGRES_PASSWORD=YOUR_DATABASE_PASSWORD
```

Every other configuration value in the codebase (documents directory, ChromaDB path, embedding model name,
Ollama URL, model name, `num_predict`, `temperature`, chunk size/overlap, retrieval `n_results` default) is a
**hardcoded constant** in its respective module — there is no `.env`-driven override for any of them today.

### 3.4 Database Configuration

Schema is created in code, not via a migration tool — `initialize_database()` in `app/db/database.py` runs
`CREATE TABLE IF NOT EXISTS` for `users`, `conversations`, and `messages` (safe to call repeatedly). No
migration framework (Alembic or similar) was found. Call it once, e.g.:

```bash
python -c "from app.db.database import initialize_database; initialize_database()"
```

### 3.5 Ollama / Local LLM Configuration

```bash
# Install Ollama (see https://ollama.com for platform-specific instructions)
ollama pull phi3:mini
ollama list        # confirm phi3:mini is available
```

The application expects Ollama reachable at `http://127.0.0.1:11434` (hardcoded `OLLAMA_URL` in
`rag/generator.py`) — there is no environment override for this URL in the reviewed code.

## 4. Running the Backend

No `Procfile`, `Makefile`, or startup script was found. The application is a standard ASGI app:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Confirm it is running:

```bash
curl http://localhost:8000/health
# {"status": "healthy", "service": "ai-production-assistant"}
```

## 5. Running Supporting Services with Docker Compose

```bash
cd compose
docker compose up -d      # starts PostgreSQL (postgres:17), bound to 127.0.0.1:5432
docker compose ps         # verify the healthcheck passes
docker compose down       # stop it
```

This only starts PostgreSQL. ChromaDB is an embedded library (no service to start), and Ollama must be running
separately (§3.5). The backend itself is **not** part of this Compose file and must be started as in §4.

## 6. Accessing the Frontend

Once the backend is running, open `http://<server-address>:8000/` in a browser. FastAPI serves
`app/static/index.html` directly from the `GET /` route — there is no separate frontend server, build step, or
port. (See the note in §14 about the `frontend/` directory mentioned in your stated project structure but not
found in the reviewed archive.)

## 7. API Documentation

### `GET /health`
No auth. Returns:
```json
{"status": "healthy", "service": "ai-production-assistant"}
```

### `GET /`
No auth. Returns the operator chat UI (`static/index.html`).

### `POST /api/v1/auth/login`
```json
// Request
{"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"}

// 200 response
{"status": "success", "user_id": 1, "username": "YOUR_USERNAME"}

// 401 response
{"detail": "Invalid username or password."}
```

### `POST /api/v1/chat`
```json
// Request
{
  "message": "What should an operator do when there is immediate danger?",
  "n_results": 3,
  "username": "YOUR_USERNAME",
  "password": "YOUR_PASSWORD"
}

// 200 response
{
  "user_id": 1,
  "username": "YOUR_USERNAME",
  "conversation_id": 16,
  "message": "What should an operator do when there is immediate danger?",
  "answer": "...",
  "sources": [
    {"source": "test_sop.txt", "chunk_index": 1, "distance": 0.83}
  ]
}

// 400 — empty message
{"detail": "Message cannot be empty."}

// 401 — bad credentials
{"detail": "Invalid username or password."}

// 500 — any exception during processing
{"detail": "Chat processing failed: <raw exception text>"}
```

`n_results` is optional and defaults to 3. `username`/`password` are **required on every call**, not just once
per session — see §8.

## 8. Authentication Usage

There is currently no session or token to carry between requests. Every `POST /api/v1/chat` call must include
`username` and `password`, and the server re-verifies them against PostgreSQL each time via
`authenticate_user()`. `POST /api/v1/auth/login` exists and works as a standalone credential check, but nothing
in the reviewed frontend code was confirmed to establish a session from it — treat it as an independently
callable endpoint, not as part of a verified login-then-chat flow in the current UI.

There is no signup/registration endpoint. Create a user directly:

```bash
python -c "from app.services.auth import create_user; create_user(username='YOUR_USERNAME', password='YOUR_PASSWORD')"
```

## 9. Chat / Conversation Workflow

Each call to `POST /api/v1/chat` performs, in order: validate message is non-empty → authenticate →
create a **new** conversation row → save the user message → run RAG → save the assistant's answer → return the
response. There is no way to continue an existing conversation across multiple calls in the current
implementation — every question is its own conversation.

## 10. RAG Workflow

1. The question is embedded with `all-MiniLM-L6-v2`.
2. ChromaDB is queried for the top `n_results` most similar chunks (`collection.query`).
3. If no chunks are found, a fixed "could not find relevant information" message is returned and **the LLM is
   never called**.
4. Otherwise, retrieved chunks are formatted into a context block and inserted into a fixed prompt template
   (see `docs/SYSTEM_DESIGN.md` §9.5 for the exact template) that restricts the model to answering only from
   the supplied text.
5. The prompt is sent to Ollama (`phi3:mini`, `num_predict=96`, `temperature=0.1`, `timeout=180`s).
6. The answer and its sources (filename, chunk index, distance) are returned.

## 11. Document Ingestion

Place `.txt` or `.pdf` files directly inside `/srv/ai-data/documents` (non-recursive — subdirectories are not
scanned), then trigger indexing manually:

```bash
python -c "from app.rag.vector_store import index_documents; print(index_documents())"
# {'status': 'success', 'indexed': <n chunks>, 'collection': 'production_documents'}
```

Re-running this is safe — chunks are upserted by a deterministic ID (`<filename>-<chunk_index>`), so existing
entries for a re-indexed file are overwritten rather than duplicated. There is no automatic re-indexing on file
change; this must be re-run manually whenever documents are added or updated.

## 12. Vector Storage

ChromaDB is used as an embedded, persistent store at `/srv/ai-data/chroma`, collection name
`production_documents`. No separate server process is required. To inspect it directly:

```python
import chromadb
client = chromadb.PersistentClient(path="/srv/ai-data/chroma")
col = client.get_or_create_collection("production_documents")
print(col.count())
print(col.get(limit=5))
```

## 13. Troubleshooting

| Symptom | Likely cause | First check |
|---|---|---|
| `/health` unreachable | Backend not running | Confirm `uvicorn` process is up; check the port |
| `RuntimeError: DATABASE_URL environment variable is not set` | `.env` not loaded / not exported | Confirm the variable is set in the shell or process environment before starting `uvicorn` |
| 500 error on `/api/v1/chat` mentioning a connection error | PostgreSQL container not running | `docker compose ps` in `compose/` |
| Model fails to load at startup (`SentenceTransformer`) | `all-MiniLM-L6-v2` not cached locally (`local_files_only=True`) | Pre-download the model once with network access available |
| Chat request hangs then fails after ~180s | Ollama slow to respond (cold start) or `phi3:mini` not pulled | `ollama list`, `ollama ps`; retry once the model is warm |
| "Could not find relevant information" for content you know exists | Document not indexed, or indexed under a different path | Confirm the file is directly inside `/srv/ai-data/documents`; re-run `index_documents()` |
| 401 on every request with credentials you believe are correct | Username mismatch (case-sensitive) or user was never created | Query the `users` table directly; re-run `create_user()` if needed |

## 14. Project Structure

Structure of the **archive actually reviewed** for this documentation:

```
ai-platform/
├── .gitignore
├── backend/
│   └── app/
│       ├── main.py
│       ├── api/v1/endpoints/{auth.py, chat.py}
│       ├── services/{auth.py, conversation.py}
│       ├── db/database.py
│       ├── rag/{ingestion.py, vector_store.py, generator.py}
│       └── static/index.html
└── compose/
    └── docker-compose.yml
```

> **Discrepancy with the structure you provided:** your message described `requirements.txt`, a root
> `README.md`, and a top-level `frontend/index.html`. None of these three were present in the archive used to
> write this documentation. If your current repository has since added them, they were not reviewed here and
> nothing in this document should be assumed to be cross-checked against them — re-run this audit against the
> current repo state if that consistency matters.

## 15. Development Workflow

No CI configuration, linting configuration, or test suite was found in the reviewed archive, so no verified
workflow can be documented here beyond: activate the virtual environment, run the backend locally with
`uvicorn --reload` for iterative development, and manually exercise `/health` and `/api/v1/chat` with `curl` or
the browser UI to validate changes.

## 16. Security Considerations

- All traffic is plain HTTP — no TLS is configured anywhere in the reviewed code or Compose file.
- Credentials are sent in the JSON body of every `/api/v1/chat` call, not just once at login.
- `.env` files (both the backend's and Compose's) must never be committed — `.gitignore` already excludes
  `.env` and `.env.*`, confirmed in the reviewed file.
- Server-side exceptions are currently returned to the client as raw text in the HTTP 500 response body
  (`chat.py`) — avoid relying on this for debugging in a shared/production environment, since it can leak
  internal detail.
- PostgreSQL is bound to `127.0.0.1` only in the provided Compose file — do not change this binding without
  adding equivalent network controls elsewhere.

## 17. Git / GitHub Workflow

The reviewed `.gitignore` excludes `.venv/`, `.env` / `.env.*`, `__pycache__/`, `*.py[cod]`, and `.vscode/`.
No branch strategy, PR template, or CONTRIBUTING file was found in the reviewed archive — none is documented
here, since none could be verified.

## 18. Known Limitations

- No session/JWT authentication — credentials resent and re-verified on every chat request.
- No multi-turn conversation memory.
- Manual, non-recursive document ingestion with no change detection.
- No automated tests.
- No `requirements.txt` in the reviewed archive (dependencies listed in §3.2 are inferred from imports, not
  pinned).
- No HTTPS/TLS.
- Two dead-code paths exist: `rag/ingestion.py`'s `ingest_documents()`, and `db/database.py`'s unused duplicate
  `create_conversation`/`save_message` functions (the ones in `services/conversation.py` are what `chat.py`
  actually calls).
- Raw exception text is returned to API clients on server errors.

## 19. Future Improvements

- Add a real `requirements.txt` (pinned) and a root `README.md` if they don't already exist in the current repo.
- Real session/JWT-based authentication in place of per-request password submission.
- HTTPS/TLS via a reverse proxy.
- Conversation continuation (accept an existing `conversation_id`).
- Automated indexing on document change, and an API-level ingestion trigger instead of a manual Python call.
- Automated test suite, starting with `chunk_text()`, `authenticate_user()`, and the RAG zero-retrieval path.
- Remove the two dead-code paths noted in §18 to avoid confusing future maintainers.

---

## Items Not Verifiable From the Provided Code

For transparency, these are things referenced in your instructions that could **not** be confirmed against the
reviewed archive, and were therefore not documented as fact above:

1. **`requirements.txt`** — not present in the archive; dependency list in §3.2 is inferred from `import`
   statements, not copied from a real file.
2. **Root `README.md`** — not present; this documentation could not be cross-checked for consistency against it
   as requested.
3. **`frontend/index.html`** (top-level) — not present; only `backend/app/static/index.html` exists.
4. **Python version** — no `pyproject.toml`, `setup.py`, `runtime.txt`, or pinned interpreter version found.
5. **Whether `POST /api/v1/auth/login` is actually called by any client code** — the endpoint itself works, but
   no frontend code confirming it's invoked as part of a login flow was found in this archive (a prior
   inspection of `static/index.html` found the opposite — the login form did not call it — but that file's
   current state should be re-checked against your latest repo).
6. **Whether `/docs` and `/openapi.json` are disabled** — not explicitly disabled in the reviewed code, but not
   independently tested against a live server for this document.
7. **Ollama's own bind-address configuration** — assumed localhost-only by convention (default), not verified
   from an Ollama config file, since none was included in the archive.
