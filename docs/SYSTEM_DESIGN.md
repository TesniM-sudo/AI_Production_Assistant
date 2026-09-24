# System Design — AI Production Assistant (Enterprise On-Premises AI Chatbot)

> This document describes the system's architecture by combining two sources: the project's diagram set
> (referenced, not recreated, below) and direct inspection of the source code in `backend/app/` and
> `compose/docker-compose.yml`. **Where the two agree, the diagrams are cited as the visual reference. Where a
> diagram depicts something not yet in the code, this document says so explicitly**, using the same
> `«IMPLEMENTED»` / `«TARGET»` / `«PLANNED»` / `«FUTURE»` vocabulary the diagrams themselves use, so terminology
> stays consistent across the diagram set, the code, and this document.

## 0. Diagram Set and Status Legend

The following diagrams exist for this project and are referenced throughout this document by name. Place the
corresponding image files under `docs/diagrams/` (adjust filenames/paths below to match your repository):

| # | Diagram | Its own stated status |
|---|---|---|
| 1 | System Context Diagram | Existing context + target behavior |
| 2 | Infrastructure Architecture | Host/VM/OS/runtime layers «IMPLEMENTED»; application services «TARGET/PLANNED» |
| 3 | Docker Deployment Architecture — Target State | «TARGET» — explicitly not to be documented as running until verified |
| 4 | Application Component Architecture — Target State | «TARGET» — "does not mean every service has already been deployed" |
| 5 | Network & Security Architecture | Mixed: UFW/OpenSSH «IMPLEMENTED»; Nginx/TLS/Docker internal network «TARGET» |
| 6 | Use Case Diagram | «TARGET» application behavior — "does not imply every use case is already implemented" |
| 7 | Class Diagram — Target Application Design | Explicitly "Target logical software model" |
| 8 | Activity Diagram — RAG Data Flow (ingestion + query) | Target flow, admin-upload half in particular |
| 9 | Sequence Diagram — Chat / Document Ingestion | Explicitly "Target sequence... not current deployment status" |
| 10 | Future Agentic RAG Architecture | Explicitly «FUTURE» — "NOT part of the currently implemented architecture" |

This document uses the same four status tags consistently:

- **`«IMPLEMENTED»`** — verified directly in `backend/app/` or `compose/docker-compose.yml`.
- **`«TARGET»`** — depicted in a diagram as the intended near-term architecture, not yet in the code.
- **`«PLANNED»`** — depicted as intended but with no committed timeline, per the diagrams' own labeling.
- **`«FUTURE»`** — depicted only in the Future Agentic RAG Architecture diagram; explicitly out of current scope.

## 1. System Overview

The AI Production Assistant is an on-premises Retrieval-Augmented Generation (RAG) system. See the **System
Context Diagram** for the actor/system boundary view: an Authorized User and an Administrator reach the
platform through a web browser over the internal company network. The diagram itself notes that internal
implementation details (PostgreSQL, ChromaDB, Ollama, Docker) are intentionally omitted at that level — this
document is where those details are filled in, against the actual code.

**`«IMPLEMENTED»`**: a production operator submits a question through a browser; the backend retrieves relevant
document chunks from a vector store and generates an answer using a locally hosted LLM, then persists the
exchange. **`«TARGET»`** (System Context Diagram, Network & Security Architecture): HTTPS as the transport, and
an Administrator role distinct from a regular user — neither exists in the code today (see §7, §14).

## 2. System Objectives

Verified as implemented: answer operator questions grounded in indexed documentation; run entirely on-premises
(no external LLM API); persist question/answer exchanges. The **Use Case Diagram** additionally depicts document
management, user/role management, chat-history retrieval, and logout as target use cases — none of these are
implemented (§13).

## 3. High-Level Architecture

The **Application Component Architecture — Target State** diagram shows the intended layering: Presentation
Layer (Frontend, Administration Interface) → Nginx Reverse Proxy → API Layer → {Chat Service, Document Service,
Authentication & Authorization} → {RAG Orchestrator → Embedding/LLM/Retrieval Service} → Data Layer
(PostgreSQL, ChromaDB, Document Storage) and Local AI Runtime (Ollama → Local LLM, Local Embedding Model).

**What actually exists**, mapped onto that same diagram's boxes:

| Diagram box | Actual implementation | Status |
|---|---|---|
| Frontend | `app/static/index.html`, served by FastAPI's `GET /` | `«IMPLEMENTED»` (simpler than diagrammed — no separate Frontend container) |
| Administration Interface | Nothing — no admin UI or admin-only route exists | `«TARGET»`, not implemented |
| Nginx Reverse Proxy | Not present anywhere in the code or Compose file | `«TARGET»` |
| API Layer | `app/main.py` + two `APIRouter`s (`auth`, `chat`) | `«IMPLEMENTED»`, but as two flat routers, not a distinct "API Layer" module |
| Chat Service | `app/api/v1/endpoints/chat.py` (the route function itself does the orchestration) | `«IMPLEMENTED»`, merged into the endpoint rather than a separate service class |
| Authentication & Authorization | `app/services/auth.py` — authentication only; no authorization/role logic | `«IMPLEMENTED»` (auth half only) |
| Document Service | No upload/update/delete endpoint or module exists | `«TARGET»`, not implemented |
| RAG Orchestrator | `app/rag/generator.py::generate_rag_answer()` | `«IMPLEMENTED»`, as a single function rather than a distinct orchestrator class |
| Embedding Service | Inline in `app/rag/vector_store.py` (module-level `SentenceTransformer` instance) | `«IMPLEMENTED»`, not a separate service |
| Retrieval Service | `app/rag/vector_store.py::search_documents()` | `«IMPLEMENTED»`, not a separate service |
| LLM Service | Inline `requests.post()` call in `generator.py` | `«IMPLEMENTED»`, not a separate service |
| PostgreSQL | `compose/docker-compose.yml`, 3 tables | `«IMPLEMENTED»` |
| ChromaDB | Embedded persistent client, `/srv/ai-data/chroma` | `«IMPLEMENTED»` |
| Document Storage | `/srv/ai-data/documents`, read directly from disk | `«IMPLEMENTED»` (as a plain directory, not a managed storage service) |
| Ollama / Local LLM | `127.0.0.1:11434`, `phi3:mini` | `«IMPLEMENTED»` |

In short: the *logic* in the target component diagram largely exists, but consolidated into far fewer modules
than the diagram depicts, and with the entire Administration/Document Service/Nginx layer absent.

## 4. Main Components and Responsibilities

| Component | File | Status |
|---|---|---|
| Application entry point | `app/main.py` | `«IMPLEMENTED»` |
| Auth endpoint | `app/api/v1/endpoints/auth.py` | `«IMPLEMENTED»` |
| Chat endpoint | `app/api/v1/endpoints/chat.py` | `«IMPLEMENTED»` |
| Auth service | `app/services/auth.py` | `«IMPLEMENTED»` (hashing/verification only, no authorization/roles) |
| Conversation service | `app/services/conversation.py` | `«IMPLEMENTED»` — this is the version `chat.py` actually calls |
| Database module | `app/db/database.py` | `«IMPLEMENTED»`; also contains unused duplicate `create_conversation`/`save_message` (dead code) |
| Ingestion helper | `app/rag/ingestion.py` | Present but **unused** — not called by the active indexing path |
| Vector store | `app/rag/vector_store.py` | `«IMPLEMENTED»` |
| Generator | `app/rag/generator.py` | `«IMPLEMENTED»` |
| Frontend | `app/static/index.html` | `«IMPLEMENTED»` |
| Nginx | — | `«TARGET»` (Docker Deployment Architecture, Network & Security Architecture) |
| Administration Interface / Document Service / User management | — | `«TARGET»` (Application Component Architecture, Use Case Diagram, Class Diagram) |
| Agentic layer (LangGraph, MCP, planning/verification agents, RAG evaluation, observability) | — | `«FUTURE»` (Future Agentic RAG Architecture diagram, explicitly marked "NOT part of the currently implemented architecture") |

## 5. Frontend Architecture

**`«IMPLEMENTED»`**: a single static HTML file (`app/static/index.html`) with inline CSS and vanilla JavaScript,
served directly by `GET /`. No framework, no build step, no separate Frontend process.

**`«TARGET»`** (Application Component Architecture, Docker Deployment Architecture): a distinct `frontend`
container behind Nginx, plus a separate Administration Interface for the Administrator actor. Neither exists —
today's single HTML file serves the one implemented use case (asking a question), with no admin-facing screens.

## 6. FastAPI Backend Architecture

`app/main.py` is minimal: creates the FastAPI app (`title="AI Production Assistant"`, `version="0.1.0"`),
defines `/health` and `/` inline, and mounts the `auth` and `chat` routers under `/api/v1`. This corresponds to
the "API Layer" box in the Application Component Architecture diagram, but as two flat routers rather than a
distinct layer with sub-modules. There is no middleware, no reverse proxy in front of it (§14), and no separate
configuration module.

## 7. Authentication Architecture

Refer to the **Sequence Diagram**'s `alt [Authentication successful] / [Authentication failed]` branch for the
intended shape — this part matches the code closely:

- Passwords are hashed with bcrypt (`bcrypt.gensalt()` + `bcrypt.hashpw()`).
- `authenticate_user()` looks up the user by username and verifies with `bcrypt.checkpw()`.
- `POST /api/v1/chat` returns HTTP 401 on failure, matching the diagram's "HTTP 401 → Authentication error"
  branch.

**Where the diagrams go beyond the code** (Class Diagram's `AuthenticationService.authorize()`/`.logout()`,
Use Case Diagram's `Manage Users/Authorization`, `Logout`, and the `Role` entity):

- There is **no authorization/role layer** — no `Role` concept, no admin-vs-operator distinction enforced
  anywhere in the backend.
- There is **no session and no logout** — `create_session_token()` exists in `services/auth.py` but is never
  called. Every `/api/v1/chat` call re-submits and re-verifies `username`/`password`.
- The Sequence Diagram routes the request through Nginx first (`Target: HTTPS`) — not present in the code;
  all traffic is direct, unencrypted HTTP to Uvicorn.

## 8. Conversation Management

`chat.py` calls, in order: `create_conversation()` → `save_message(role="user")` → RAG →
`save_message(role="assistant")`. **A new conversation is created on every call** — there is no
`getConversationHistory()` equivalent (shown in the Class Diagram's `ChatService`) and no `View Chat History`
use case (Use Case Diagram) implemented anywhere in the code.

## 9. RAG Architecture

### 9.1 Document Ingestion Pipeline

The top half of the **Activity Diagram** ("RAG Data Flow") depicts an administrator-driven, authorized upload
flow with document status tracking (`UPLOADED → PROCESSING → READY/FAILED`, matching the Class Diagram's
`DocumentStatus` enum). **None of this exists in the code.** The actual, `«IMPLEMENTED»` path is:

- `index_documents()` in `vector_store.py` is a plain function with no caller, no authorization check, and no
  status tracking — it must be invoked manually (e.g. from a Python shell).
- It reads every `.txt`/`.pdf` file directly inside `/srv/ai-data/documents` (non-recursive).
- There is no `Document`, `DocumentMetadata`, or `DocumentStatus` table/entity in PostgreSQL — only chunk-level
  metadata (`source`, `chunk_index`) stored as ChromaDB metadata, not in a relational table.

### 9.2 Text Extraction and Chunking

`chunk_text(text, chunk_size=500, overlap=50)` — a fixed-size, character-based sliding window (not
token/sentence-aware), matching the "Split text into chunks" step of the Activity Diagram, though without the
preceding "Normalize extracted text" step shown there — no text normalization step exists in the code beyond
`.strip()`.

### 9.3 Embedding Generation

`all-MiniLM-L6-v2`, loaded once via `sentence-transformers` with `local_files_only=True`. Matches the Activity
Diagram's "Generate embeddings using local embedding model" step and the Class/Component diagrams' "Local
Embedding Model" box — implemented inline in `vector_store.py`, not as a separate `EmbeddingService` class.

### 9.4 Vector Database / Retrieval Layer

ChromaDB, embedded persistent client at `/srv/ai-data/chroma`, collection `production_documents`. Matches the
"Search ChromaDB for similar chunks" step of the Activity Diagram and the `VectorRepository` interface shape in
the Class Diagram (`store`, `similaritySearch`), though implemented as direct function calls
(`collection.upsert`, `collection.query`) rather than behind a repository interface.

### 9.5 LLM Generation Layer

`generate_rag_answer()` matches the Activity Diagram's "Relevant context found?" branch closely:

- **If chunks are found:** builds a grounded prompt and calls Ollama (`phi3:mini`, `num_predict=96`,
  `temperature=0.1`, `timeout=180`s) — matching "Construct grounded prompt" → "Send prompt to local LLM through
  Ollama" → "Generate grounded answer" → "Attach document references".
- **If no chunks are found:** the diagram shows "Return controlled response" → "Direct user to responsible
  person/process if required". **The actual code only does the first half** — it returns a fixed string,
  `"I could not find relevant information in the available documents."`, with no escalation or routing logic.

## 10. PostgreSQL / Database Role

**`«IMPLEMENTED»`**: exactly three tables — `users`, `conversations`, `messages` — created via
`CREATE TABLE IF NOT EXISTS` in `initialize_database()`. Raw SQL via `psycopg`, no ORM.

**`«TARGET»`** (Class Diagram — Domain Entities): `Document`, `DocumentMetadata`, `DocumentChunk`,
`DocumentStatus`, and `Role` entities, plus a `UserRepository`/`DocumentRepository`/`ConversationRepository`
abstraction layer. None of these exist — the current schema is exactly the three tables above, nothing more.

## 11. Docker / Compose Role

**`«IMPLEMENTED»`**: `compose/docker-compose.yml` defines exactly **one** service — PostgreSQL 17
(`ai-postgres`), with a healthcheck, a bind-mounted volume at `/srv/ai-data/postgres`, and port binding
`127.0.0.1:5432:5432` (localhost-only).

**`«TARGET»`** (Docker Deployment Architecture diagram, explicitly self-labeled and carrying the note *"These
application containers/services must not be documented as running until their deployment has been verified"*):
a full multi-container Compose project — `nginx`, `frontend`, `backend` (FastAPI), `ollama`, and `chromadb`
containers, all on a Docker internal network, with `/srv/ai-data` subdirectories (`models/`, `postgres/`,
`vectors/`, `documents/`, `backups/`) as shared persistent storage.

This is the clearest and most important gap between the diagrams and the code: **only PostgreSQL is
containerized today.** The backend runs natively (via a virtual environment and, per prior deployment context,
a `systemd` unit — not Docker), and ChromaDB and Ollama both run as native local processes, not containers. The
diagram is internally consistent about this being a target, not a claim of current state — this document
preserves that distinction.

## 12. Data Flow

### 12.1 User Query Flow

See the **Sequence Diagram** for the full visual flow. It matches the code with three exceptions, all `«TARGET»`
elements not yet implemented:

1. The diagram routes through **Nginx** first — the actual client connects directly to Uvicorn over plain HTTP.
2. The diagram shows distinct **Chat Service / RAG Service / Embedding Service / LLM Service** components — the
   actual code merges these into `chat.py`, `generator.py`, and `vector_store.py`.
3. The diagram's zero-context branch implies a controlled hand-off ("direct user to responsible person") — the
   actual code returns a single fixed string with no further routing (§9.5).

Everything else — validate → authenticate → create conversation → save user message → embed → retrieve →
generate → save assistant message → respond — matches the diagram and the code exactly, including step 4's
`Store user message` occurring **before** retrieval/generation, and step 19's `Store assistant response`
occurring **after**.

### 12.2 Document Ingestion Flow

See the top half of the **Activity Diagram**. As detailed in §9.1, the diagrammed flow (administrator
authorization check → validation → storage → metadata save → extraction → status tracking → "READY") is
`«TARGET»`. The actual, `«IMPLEMENTED»` flow is a single manual function call
(`index_documents()`) with none of the surrounding authorization, validation, or status-tracking steps.

## 13. API Architecture

| Method & Path | Status | Diagram reference |
|---|---|---|
| `GET /health` | `«IMPLEMENTED»` | — |
| `GET /` | `«IMPLEMENTED»` | — |
| `POST /api/v1/auth/login` | `«IMPLEMENTED»` | Sequence Diagram, Authentication branch |
| `POST /api/v1/chat` | `«IMPLEMENTED»` | Sequence Diagram, Use Case Diagram (`Ask Question`) |
| Document upload / update / delete | Not implemented | Use Case Diagram (`Manage Documents`), Class Diagram (`DocumentService`) — `«TARGET»` |
| User / role management | Not implemented | Use Case Diagram (`Manage Users/Authorization`) — `«TARGET»` |
| Conversation history retrieval | Not implemented | Class Diagram (`ChatService.getConversationHistory`) — `«TARGET»` |
| Logout | Not implemented | Use Case Diagram (`Logout`) — `«TARGET»`, no session exists to log out of |

## 14. Security Considerations

| Area | Status | Diagram reference |
|---|---|---|
| Password hashing (bcrypt) | `«IMPLEMENTED»` | — |
| HTTPS/TLS | `«TARGET»` — not implemented | System Context Diagram, Network & Security Architecture (Nginx marked as the intended TLS termination point) |
| Session/token auth | `«TARGET»` — not implemented (dead code only) | Class Diagram |
| Role-based access control | `«TARGET»` — not implemented | Class Diagram (`Role`), Use Case Diagram |
| PostgreSQL network exposure | `«IMPLEMENTED»` mitigation — bound to `127.0.0.1` only | Network & Security Architecture ("Do not expose PostgreSQL directly to client machines" — already true) |
| Ollama network exposure | `«IMPLEMENTED»` mitigation (by address, `127.0.0.1:11434`) | Network & Security Architecture ("Ollama should not be directly reachable by end users" — already true by current call pattern) |
| Docker internal network isolation | `«TARGET»` — only one container exists today, so there is no multi-container network to isolate yet | Network & Security Architecture |
| UFW firewall, OpenSSH | Diagram marks `«IMPLEMENTED»` at OS level | Network & Security Architecture — outside this codebase, not independently verified from source in this document |
| Raw exception text returned on HTTP 500 | `«IMPLEMENTED»` (as a gap) — `chat.py`'s error handler leaks internal exception text | — |
| Prompt-injection surface via indexed documents | Structural, unmitigated | — |

## 15. Deployment Architecture

Per the **Infrastructure Architecture** diagram: a physical host runs VMware Workstation Pro, hosting an
"AI Server VM" on Ubuntu Server (version and Python version as stated in that diagram — not independently
re-verified against a live shell in this document). OS-level services (systemd, UFW, OpenSSH, Chrony/NTP) and
the development runtime (Git, Python, venv) are marked `«IMPLEMENTED»` in that diagram. The **Application
Services** layer (Nginx, Frontend, Ollama, ChromaDB, PostgreSQL, FastAPI) is marked `«TARGET/PLANNED»` in the
same diagram — consistent with §11's finding that only PostgreSQL is actually containerized, while the backend,
ChromaDB, and Ollama run as native processes today (per prior deployment context: the backend via a virtual
environment and a `systemd` unit, not Docker).

## 16. Technology Choices and Their Roles

| Technology | Role | Status |
|---|---|---|
| FastAPI + Uvicorn | HTTP API framework | `«IMPLEMENTED»` |
| PostgreSQL 17 (Docker) | Relational persistence | `«IMPLEMENTED»` |
| ChromaDB | Vector store | `«IMPLEMENTED»` (native process, not containerized) |
| sentence-transformers / all-MiniLM-L6-v2 | Embeddings | `«IMPLEMENTED»` (native, not containerized) |
| Ollama + phi3:mini | Local LLM generation | `«IMPLEMENTED»` (native, not containerized) |
| PyMuPDF (`fitz`) | PDF text extraction | `«IMPLEMENTED»` |
| bcrypt | Password hashing | `«IMPLEMENTED»` |
| psycopg | PostgreSQL driver | `«IMPLEMENTED»` |
| Docker Compose | PostgreSQL packaging today; full-stack packaging intended | `«IMPLEMENTED»` (Postgres only) / `«TARGET»` (rest) |
| Nginx | Reverse proxy, intended TLS termination | `«TARGET»` |
| LangGraph / MCP / planning & verification agents | Agentic orchestration layer | `«FUTURE»` — see Future Agentic RAG Architecture diagram |

## 17. System Limitations

- No session/JWT authentication, no logout, no authorization/role layer.
- No multi-turn conversation memory or conversation-history retrieval.
- Document ingestion is a manual, unguarded, non-recursive function call with no status tracking.
- No document management, no user management — both `«TARGET»` per the Use Case and Class diagrams.
- Only PostgreSQL is containerized; the target multi-container Compose stack (Nginx, frontend, backend, Ollama,
  ChromaDB) does not exist yet.
- No HTTPS/TLS anywhere in the request path.
- No reranking or retrieval-quality evaluation.
- Two dead-code paths: `rag/ingestion.py`'s unused `ingest_documents()`, and `db/database.py`'s unused duplicate
  `create_conversation`/`save_message`.
- Raw exception text returned to API clients on server errors.
- No automated tests.

## 18. Possible Future Architectural Improvements

Near-term (`«TARGET»`, already diagrammed):

- Containerize the backend, ChromaDB, and Ollama alongside PostgreSQL, per the Docker Deployment Architecture
  diagram.
- Add Nginx as a reverse proxy and TLS termination point, per the Network & Security Architecture diagram.
- Implement real session/JWT authentication and a role/authorization layer, per the Class and Use Case diagrams.
- Implement document management (upload/update/delete) and conversation-history retrieval endpoints.
- Add the `Document`/`DocumentMetadata`/`DocumentStatus` schema and a proper repository layer, per the Class
  Diagram.

Longer-term (`«FUTURE»`, per the Future Agentic RAG Architecture diagram — explicitly not part of the current
or near-term plan):

- An agentic RAG layer (query planning, a verification agent that validates responses against retrieved
  context and can trigger a retry, a state/workflow manager, potentially built on LangGraph).
- An MCP layer for controlled access to approved internal tools.
- RAG evaluation and observability tooling.

This document deliberately keeps this tier separate from the `«TARGET»` items above, matching the diagram's own
explicit note that it is "NOT part of the currently implemented architecture."
