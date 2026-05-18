# Task Breakdown
**Project:** Enterprise RAG Intelligence
**Version:** 1.0.0
**Status:** Draft — For Engineering Review
**Last Updated:** 2026
**Maintainer:** Anand Raj (@anan5093)

---

## Table of Contents

1. [Task Overview](#1-task-overview)
2. [Authentication Module Tasks](#2-authentication-module-tasks)
3. [Authorization & RBAC Module Tasks](#3-authorization--rbac-module-tasks)
4. [Document Ingestion Module Tasks](#4-document-ingestion-module-tasks)
5. [Hybrid Retrieval Module Tasks](#5-hybrid-retrieval-module-tasks)
6. [LLM Generation Module Tasks](#6-llm-generation-module-tasks)
7. [Explainability Module Tasks](#7-explainability-module-tasks)
8. [Audit Logging Module Tasks](#8-audit-logging-module-tasks)
9. [Observability Module Tasks](#9-observability-module-tasks)
10. [Frontend — Chat Module Tasks](#10-frontend--chat-module-tasks)
11. [Frontend — Upload Module Tasks](#11-frontend--upload-module-tasks)
12. [Frontend — Admin Dashboard Tasks](#12-frontend--admin-dashboard-tasks)
13. [Deployment & Infrastructure Tasks](#13-deployment--infrastructure-tasks)
14. [Testing & QA Tasks](#14-testing--qa-tasks)
15. [Security Hardening Tasks](#15-security-hardening-tasks)
16. [Task Dependency Map](#16-task-dependency-map)
17. [Milestone Summary](#17-milestone-summary)

---

## 1. Task Overview

### Priority Legend

| Symbol | Priority | Meaning |
|---|---|---|
| 🔴 | P1 | Must Have — blocking for any release |
| 🟡 | P2 | Should Have — required for production quality |
| 🟢 | P3 | Nice to Have — post-MVP improvement |

### Status Legend

| Status | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Complete |

### Module Ownership

| Module | Owner Role |
|---|---|
| Backend API, Security, Generation, Retrieval | Backend Engineer |
| Ingestion Pipeline | Backend Engineer |
| Frontend (Chat, Upload, Admin) | Frontend Engineer |
| Docker Compose, Kubernetes | DevOps / Platform Engineer |
| Security review, threat model validation | Security Engineer |
| Test coverage | QA Engineer |

---

## 2. Authentication Module Tasks

> **Corresponding Requirements:** AUTH-001, AUTH-002, AUTH-003
> **Corresponding Design:** §2.5, §3.3, §5.1, §10.2, §11.3

---

### TASK-AUTH-001 — Implement POST /login endpoint 🔴

**File:** `backend/app/api/routes/auth.py`

- [ ] Define `LoginRequest` Pydantic model (`username: str`, `password: str`)
- [ ] Define `TokenResponse` Pydantic model (`access_token: str`, `token_type: str`)
- [ ] Implement route handler: validate credentials against `DEMO_USERS` store in `security/auth.py`
- [ ] On success: issue signed JWT via `AuthService`
- [ ] On failure: return HTTP 401 with `{ "detail": "Invalid credentials" }`
- [ ] On missing fields: Pydantic returns HTTP 422 automatically — verify this behavior in tests
- [ ] Ensure passwords are never written to application logs

**Acceptance:** `POST /login` with valid credentials returns a bearer token. Invalid credentials return 401. Missing fields return 422.

---

### TASK-AUTH-002 — Implement JWT issuance in AuthService 🔴

**File:** `backend/app/security/auth.py`

- [ ] Implement `AuthService.create_access_token(user_id, role)` using `python-jose` (or equivalent)
- [ ] Sign token with `JWT_SECRET` (read from environment, never hardcoded)
- [ ] Embed claims: `sub` (user identity), `role`, `exp` (expiry, e.g. 1 hour)
- [ ] Signing algorithm: `HS256` minimum
- [ ] Return signed JWT string

**Acceptance:** Issued JWT decodes correctly with the correct `sub`, `role`, and `exp` claims.

---

### TASK-AUTH-003 — Implement JWT validation FastAPI dependency 🔴

**File:** `backend/app/api/deps.py`

- [ ] Implement `get_current_user(token: str = Depends(oauth2_scheme))` dependency
- [ ] Decode and validate JWT signature against `JWT_SECRET`
- [ ] Validate `exp` claim; return HTTP 401 with `"Token expired"` on expiry
- [ ] Return `CurrentUser(user_id, role)` dataclass/model for injection into route handlers
- [ ] Return HTTP 401 for malformed or tampered tokens

**Acceptance:** Protected routes reject expired, tampered, and missing tokens with HTTP 401.

---

### TASK-AUTH-004 — Externalize JWT secret and configure DEMO_USERS 🔴

**File:** `backend/app/core/config.py`, `backend/app/security/auth.py`

- [ ] Add `JWT_SECRET` to `Settings` (Pydantic `BaseSettings`), sourced from environment variable
- [ ] Add startup assertion: raise if `JWT_SECRET` is unset or below 32-character minimum
- [ ] Ensure `DEMO_USERS` store is clearly flagged with `# REPLACE BEFORE PRODUCTION` comments
- [ ] Document replacement procedure in `README.md` or a dedicated `SECURITY.md`

**Acceptance:** Application fails to start if `JWT_SECRET` is unset. No secrets appear in source code.

---

### TASK-AUTH-005 — Audit logging for authentication events 🔴

**File:** `backend/app/api/routes/auth.py`, `backend/app/security/audit.py`

- [ ] On successful login: emit audit event `{ event_type: "login_success", user_id, timestamp }`
- [ ] On failed login: emit audit event `{ event_type: "login_failure", username, timestamp, source_ip (if available) }`
- [ ] Audit write is non-blocking (fire-and-forget / async)

**Acceptance:** Both login success and failure produce audit log entries. See TASK-AUDIT-003.

---

## 3. Authorization & RBAC Module Tasks

> **Corresponding Requirements:** RBAC-001 through RBAC-004, SEC-004, SEC-005, SEC-009, SEC-010
> **Corresponding Design:** §2.5, §5.2, §5.3, §11.3

---

### TASK-RBAC-001 — Define role enumeration 🔴

**File:** `backend/app/security/rbac.py` (or `core/config.py`)

- [ ] Define `Role` enum: `Admin`, `Finance`, `Engineering`, `Compliance`, `Guest`
- [ ] Export role set for use in RBAC filter, ingestion validation, and policy checks
- [ ] Ensure role enum is referenced consistently across all modules (no magic strings)

**Acceptance:** All role references throughout the codebase use the central `Role` enum.

---

### TASK-RBAC-002 — Implement chunk-level RBAC filter 🔴

**File:** `backend/app/security/rbac.py`

- [ ] Implement `RBACFilter.filter(chunks: List[Chunk], user_role: str) -> (authorized: List[Chunk], denied_count: int)`
- [ ] For each chunk: check `user_role in chunk.metadata.allowed_roles`; if not, increment `denied_count`
- [ ] Return tuple of authorized chunks and denied count
- [ ] If `len(authorized) == 0`: calling code (QueryService) returns `"Insufficient authorized data available."` — do not raise exception in the filter itself
- [ ] Log denied access at DEBUG level (without logging chunk content)
- [ ] Unit test with adversarial role combinations (e.g., `Guest` user against `Finance`-only chunks)

**Acceptance:** No chunk with a restricted `allowed_roles` list appears in the authorized output when the user's role is absent from that list. `denied_count` is always accurate.

---

### TASK-RBAC-003 — Enforce RBAC filter as step [6] in QueryService 🔴

**File:** `backend/app/retrieval/` (query pipeline orchestration)

- [ ] Confirm filter is called after reranking (step [5]) and before prompt construction (step [9])
- [ ] Confirm `PromptBuilder` only receives the authorized chunk list — never the pre-filter candidates
- [ ] Add inline comment at the call site marking the security boundary: `# SECURITY BOUNDARY — RBAC filter`

**Acceptance:** Code review confirms RBAC filter placement; no code path allows pre-filter chunks to reach `PromptBuilder`.

---

### TASK-RBAC-004 — Implement endpoint-level role checks via FastAPI dependency 🔴

**File:** `backend/app/api/deps.py`, `backend/app/security/policy.py`

- [ ] Implement `require_role(allowed_roles: List[str])` dependency factory
- [ ] Apply to `/ingest`: require `Admin`
- [ ] Apply to `/audit-logs`: require `Admin` or `Compliance`
- [ ] Return HTTP 403 with `{ "detail": "Insufficient role" }` for unauthorized roles
- [ ] Role check must occur in the dependency, not in route handler body

**Acceptance:** `POST /ingest` with non-Admin JWT returns 403. `GET /audit-logs` with non-Admin/Compliance JWT returns 403.

---

### TASK-RBAC-005 — Validate allowed_roles values at ingestion time 🔴

**File:** `backend/app/ingestion/` (metadata extraction stage), `backend/app/api/routes/ingest.py`

- [ ] On `POST /ingest`: validate each value in `allowed_roles` against the `Role` enum
- [ ] Unknown/invalid roles → return HTTP 422 with descriptive error
- [ ] Valid but empty `allowed_roles` → log warning; treat as deny-all (no users can access these chunks)

**Acceptance:** Ingestion request with `allowed_roles: ["Unicorn"]` returns HTTP 422.

---

## 4. Document Ingestion Module Tasks

> **Corresponding Requirements:** INGEST-001 through INGEST-005, RBAC-004, SEC-013, SEC-014
> **Corresponding Design:** §7, §11.2

---

### TASK-INGEST-001 — Implement POST /ingest route and IngestRequest model 🔴

**File:** `backend/app/api/routes/ingest.py`

- [ ] Define `IngestRequest` Pydantic model: `path`, `source_type`, `department`, `owner`, `confidentiality`, `allowed_roles`, `rbac_tags`
- [ ] Define `IngestResponse` Pydantic model: `status`, `chunks_indexed`, `source_path`
- [ ] Apply `require_role("Admin")` dependency
- [ ] Validate `source_type` against allowed set: `csv`, `json`, `pdf`, `docx`, `sql`, `markdown`, `text`
- [ ] Validate `path` against allowlist directory (SEC-013) — reject with HTTP 400 on traversal attempt
- [ ] Delegate to `IngestionService.ingest_async()` and return immediate acknowledgment

**Acceptance:** Valid admin request returns `{ "status": "accepted", "chunks_indexed": N, "source_path": "..." }`. Non-admin returns 403. Invalid `source_type` returns 400. Path traversal attempt returns 400.

---

### TASK-INGEST-002 — Implement path traversal allowlist validation 🔴

**File:** `backend/app/ingestion/` or `backend/app/security/`

- [ ] Define allowlisted base directories (e.g., `examples/data/`, configurable via environment)
- [ ] Resolve and canonicalize the provided `path` using `pathlib.Path.resolve()`
- [ ] Reject if resolved path is not under an allowlisted directory
- [ ] Return HTTP 400 with `"Path not permitted"` detail

**Acceptance:** `path: "../../etc/passwd"` is rejected. `path: "examples/data/file.json"` is accepted.

---

### TASK-INGEST-003 — Implement source loaders for all 6 format types 🔴

**Files:** `backend/app/ingestion/loaders/`

For each format, implement a dedicated loader class with a `.load(path) -> str` interface:

- [ ] `CSVLoader`: parse rows into text records
- [ ] `JSONLoader`: parse JSON objects/arrays into text representations
- [ ] `PDFLoader`: extract text from PDF pages (select and document library)
- [ ] `DOCXLoader`: extract text from Word documents (select and document library)
- [ ] `SQLLoader`: query SQL source and extract row data (document connection string convention)
- [ ] `MarkdownLoader` / `TextLoader`: read plain text or Markdown files
- [ ] Factory function: `get_loader(source_type) -> BaseLoader`
- [ ] Each loader raises a descriptive exception on parse failure

**Acceptance:** Each loader returns non-empty text for valid test files in each format.

---

### TASK-INGEST-004 — Implement chunker 🔴

**File:** `backend/app/ingestion/chunker.py`

- [ ] Implement `Chunker.chunk(text: str) -> List[ChunkText]`
- [ ] Define chunk size and overlap parameters (make configurable via `Settings`)
- [ ] Assign each chunk: UUID `chunk_id`, `position_index`, `parent_document_id`
- [ ] Handle edge cases: empty text (log warning, return empty list), text shorter than chunk size (return as single chunk)
- [ ] Document chosen chunking strategy (fixed-size, sentence-based, etc.)

**Acceptance:** Chunker correctly splits a 10,000-character document into expected chunks with correct overlap and position metadata.

---

### TASK-INGEST-005 — Implement metadata extraction and attachment 🔴

**File:** `backend/app/ingestion/metadata.py`

- [ ] Implement `MetadataExtractor.build(request: IngestRequest, chunk_id, position_index) -> ChunkMetadata`
- [ ] Attach: `chunk_id`, `source_path`, `source_type`, `department`, `owner`, `confidentiality`, `allowed_roles`, `rbac_tags`, `ingestion_timestamp` (UTC), `position_index`
- [ ] Validate all required fields are non-empty — reject at ingestion request validation stage if missing

**Acceptance:** Every chunk produced from an ingestion request carries the full metadata dict.

---

### TASK-INGEST-006 — Implement embedding and FAISS index update 🔴

**File:** `backend/app/ingestion/indexer.py`, `backend/app/retrieval/vector_store.py`

- [ ] Select and document embedding model (must match the model used at query time)
- [ ] Implement `EmbeddingModel.encode(text: str) -> np.ndarray`
- [ ] Implement `FAISSStore.add(vector, chunk_id)` and `FAISSStore.save(path)`
- [ ] Implement `BM25Store.add(tokenized_text, chunk_id)` and persistence mechanism
- [ ] Implement `MetadataStore.save(chunk)` (persist chunk metadata keyed by `chunk_id`)
- [ ] Ensure FAISS and BM25 indexes are updated atomically per ingestion batch
- [ ] Document write-locking limitation (concurrent ingestion safety not fully defined in v1.0.0)

**Acceptance:** After ingestion, FAISS search returns the ingested chunk as a candidate for relevant queries.

---

### TASK-INGEST-007 — Implement async ingestion pipeline 🟡

**File:** `backend/app/ingestion/service.py`

- [ ] Implement `IngestionService.ingest_async(request, requesting_user)` using FastAPI `BackgroundTasks` or `asyncio`
- [ ] API response returns immediately with `status: "accepted"`
- [ ] Background task captures failures (parse errors, embedding errors, index write errors) in audit log and application log at ERROR level
- [ ] Preserve requesting user identity in async context for audit logging

**Acceptance:** `POST /ingest` returns within 500ms regardless of document size. Background pipeline completes without blocking.

---

### TASK-INGEST-008 — Implement example data preload script 🟡

**File:** `backend/app/scripts/ingest_examples.py`

- [ ] Script loads all files from `examples/data/` using `IngestionService`
- [ ] Applies appropriate metadata (department, owner, allowed_roles) per example dataset
- [ ] Populates FAISS and BM25 indexes in `runtime/faiss_index/`
- [ ] Exits with error if `examples/data/` directory is missing
- [ ] Document in `README.md` with the exact command to run

**Acceptance:** Running the script populates the index; subsequent queries return results from example data.

---

## 5. Hybrid Retrieval Module Tasks

> **Corresponding Requirements:** RETR-001 through RETR-005
> **Corresponding Design:** §4

---

### TASK-RETR-001 — Implement FAISS vector store read operations 🔴

**File:** `backend/app/retrieval/vector_store.py`

- [ ] Implement `FAISSStore.load(path)` — load index from `runtime/faiss_index/`
- [ ] Implement `FAISSStore.search(query_vector: np.ndarray, top_k: int) -> List[(chunk_id, score)]`
- [ ] Handle empty index gracefully: return empty list, do not raise
- [ ] Document index type decision (`IndexFlatL2` vs `IndexIVFFlat`) with rationale

**Acceptance:** FAISS search on a populated index returns `top_k` candidates with scores. Empty index returns empty list.

---

### TASK-RETR-002 — Implement BM25 retrieval 🔴

**File:** `backend/app/retrieval/bm25_store.py`

- [ ] Select and document BM25 library (e.g., `rank_bm25`)
- [ ] Implement `BM25Store.search(query_tokens: List[str], top_k: int) -> List[(chunk_id, score)]`
- [ ] Load BM25 corpus from persisted state at startup
- [ ] Handle empty corpus gracefully: return empty list

**Acceptance:** BM25 search returns relevant chunks for keyword-matching queries.

---

### TASK-RETR-003 — Implement hybrid score fusion 🔴

**File:** `backend/app/retrieval/fusion.py`

- [ ] Select and document fusion strategy (RRF or weighted linear interpolation); document `α` parameter if linear
- [ ] Implement `fuse(dense_candidates, sparse_candidates) -> List[(chunk_id, fused_score)]`
- [ ] Normalize scores within each candidate list to [0, 1] before combining
- [ ] Deduplicate by `chunk_id` (a chunk appearing in both lists gets combined score)
- [ ] Sort output by descending `fused_score`
- [ ] Graceful degradation: one empty input → return the other list unchanged

**Acceptance:** Fusion output is deduplicated and correctly sorted. Queries with empty FAISS or BM25 results return valid fused output from the non-empty source.

---

### TASK-RETR-004 — Implement reranker 🔴

**File:** `backend/app/retrieval/reranker.py`

- [ ] Select and document reranking model or algorithm (cross-encoder or lightweight scoring)
- [ ] Implement `Reranker.rerank(query: str, candidates: List[Chunk], top_n: int) -> List[Chunk]`
- [ ] Apply reranking on the pre-RBAC candidate set (post-fusion)
- [ ] Fallback: if reranker unavailable, return fused list in original score order; log warning
- [ ] Record reranking latency in trace metadata (`retrieval_timings_ms.reranking`)

**Acceptance:** Reranked output is a reordered subset of the fused candidates, top_n in length.

---

### TASK-RETR-005 — Implement query source router 🟡

**File:** `backend/app/retrieval/routing.py`

- [ ] Implement `Router.classify(query: str) -> route_decision`
- [ ] Default route: `"hybrid"` (FAISS + BM25)
- [ ] Document extension point for department-specific sub-indexes (future; see §14)
- [ ] Record `route_decision` in trace metadata (`trace.route`)

**Acceptance:** All queries receive a `route_decision` value. Default is `"hybrid"`.

---

### TASK-RETR-006 — Implement parallel FAISS + BM25 execution 🔴

**File:** `backend/app/retrieval/` (QueryService or retrieval orchestrator)

- [ ] Execute FAISS search and BM25 search concurrently (via `asyncio.gather` or `ThreadPoolExecutor`)
- [ ] Record individual timings for each in trace: `dense_search`, `sparse_search`

**Acceptance:** Both search operations run concurrently; trace timings reflect parallel execution.

---

## 6. LLM Generation Module Tasks

> **Corresponding Requirements:** GEN-001 through GEN-004
> **Corresponding Design:** §2.4, §2.6, §5.7

---

### TASK-GEN-001 — Implement PromptBuilder 🔴

**File:** `backend/app/generation/prompt.py`

- [ ] Load prompt template from `examples/prompts/` (static parameterized template)
- [ ] Implement `PromptBuilder.build(query: str, authorized_chunks: List[Chunk]) -> str`
- [ ] Insert user query into a clearly delimited `[USER QUERY]` section
- [ ] Insert chunk content into a clearly delimited `[EVIDENCE]` section with explicit boundaries per chunk
- [ ] If `authorized_chunks` is empty: raise `InsufficientEvidenceError` (QueryService returns fallback response, LLM is never called)
- [ ] Do not interpolate user input into instruction sections of the prompt (SEC-007)

**Acceptance:** Prompt structure matches the template; user input is bounded by delimiters. Empty chunk list does not call the LLM.

---

### TASK-GEN-002 — Implement LLM generator 🔴

**File:** `backend/app/generation/generator.py`

- [ ] Integrate with the chosen LLM provider API (document provider and library in code comments)
- [ ] Read LLM API key from environment variable (`Settings`)
- [ ] Implement `Generator.generate(prompt: str) -> str`
- [ ] On LLM API failure: raise `LLMUnavailableError` → caller returns HTTP 503
- [ ] Extract text from LLM response content blocks (handle potential multi-block responses)

**Acceptance:** Generator returns answer text for a valid prompt. API failure propagates as HTTP 503.

---

### TASK-GEN-003 — Implement hallucination guard 🔴

**File:** `backend/app/generation/guardrails.py`

- [ ] Implement `Guard.check(answer: str, source_chunks: List[Chunk]) -> str`
- [ ] Detect claims in the answer that are not grounded in any source chunk text
- [ ] Suppress or flag ungrounded claims (document chosen strategy: redaction vs. warning)
- [ ] Guard bypass must be logged at WARNING level; ungrounded answer must not be silently returned
- [ ] Guard executes before the response leaves the generation module

**Acceptance:** A response containing a factual claim absent from all source chunks is flagged or modified by the guard.

---

### TASK-GEN-004 — Implement insufficient evidence fallback 🔴

**File:** `backend/app/retrieval/` (QueryService orchestration)

- [ ] When `authorized_chunks` is empty after RBAC filter: return `QueryResponse` with `answer: "Insufficient authorized data available."`, `citations: []`, `confidence: 0.0`
- [ ] Do not call `PromptBuilder` or `Generator` in this path
- [ ] Populate `trace` with `authorized_chunk_ids: []`, `denied_count: N`
- [ ] `denied_count` is the only indication of denied activity; chunk IDs and content must not appear

**Acceptance:** Query by `Guest` user against `Finance`-only index returns the exact fallback string with empty citations and zero confidence.

---

## 7. Explainability Module Tasks

> **Corresponding Requirements:** EXPL-001 through EXPL-003
> **Corresponding Design:** §6

---

### TASK-EXPL-001 — Implement citation builder 🔴

**File:** `backend/app/explainability/citations.py`

- [ ] Implement `CitationBuilder.build(authorized_chunks: List[Chunk]) -> List[Citation]`
- [ ] Each `Citation` includes: `chunk_id`, `source_path`, `department`, `owner`, `confidentiality`, `relevance_score`, `text_excerpt` (first 200 chars, configurable)
- [ ] Only include metadata the requesting user is authorized to see (RBAC was applied before this step)
- [ ] Return empty list if no authorized chunks

**Acceptance:** Each citation in the response maps 1:1 to a chunk in `authorized_chunks`. No denied chunk metadata appears.

---

### TASK-EXPL-002 — Implement confidence scorer 🔴

**File:** `backend/app/explainability/confidence.py`

- [ ] Implement `ConfidenceScorer.score(authorized_chunks, reranked_candidates, guard_signals) -> float`
- [ ] Inputs: average rerank score, ratio of authorized to total retrieved chunks, guardrail pass/fail
- [ ] Output: scalar `[0.0, 1.0]`
- [ ] Low evidence quality or high denial rate → lower confidence
- [ ] Document exact formula as code comment
- [ ] Return `0.0` for the insufficient-evidence path

**Acceptance:** Confidence is bounded `[0.0, 1.0]`. A query where all but 1 chunk was denied produces a noticeably lower confidence than a query where all chunks were authorized.

---

### TASK-EXPL-003 — Implement trace builder 🔴

**File:** `backend/app/explainability/trace.py`

- [ ] Implement `TraceBuilder.build(...)` consuming pipeline execution context
- [ ] Output fields: `route`, `authorized_chunk_ids`, `denied_count`, `filters_applied` (`user_role`, `rbac_tags_matched`), `retrieval_timings_ms` (`dense_search`, `sparse_search`, `fusion`, `reranking`, `rbac_filter`)
- [ ] If a stage was skipped (e.g., reranker fallback): set corresponding timing field to `null`
- [ ] `denied_count` is exposed; denied chunk IDs and content must never appear in the trace

**Acceptance:** Trace object in the API response contains all specified fields. Timings reflect actual stage durations.

---

## 8. Audit Logging Module Tasks

> **Corresponding Requirements:** AUDIT-001 through AUDIT-004, SEC-011, SEC-012
> **Corresponding Design:** §5.4

---

### TASK-AUDIT-001 — Implement AuditService core 🔴

**File:** `backend/app/security/audit.py`

- [ ] Implement `AuditService.log(event_type, user_id, role, detail: dict)`
- [ ] Construct structured event dict: `{ timestamp (ISO8601), event_type, user_id, role, action_detail, outcome }`
- [ ] Serialize to JSON and append to the audit store (define storage mechanism: file-based append or database insert)
- [ ] Audit write is non-blocking (async or fire-and-forget)
- [ ] On write failure: log at ERROR level in application logs; do not raise exception to caller

**Acceptance:** AuditService.log() writes a valid JSON entry to the audit store. Write failure does not propagate to API response.

---

### TASK-AUDIT-002 — Emit query audit events 🔴

**File:** `backend/app/api/routes/query.py` or `QueryService`

- [ ] After query pipeline completes: call `AuditService.log("query", user_id, role, { query_text, denied_count, confidence, outcome })`
- [ ] Non-blocking: does not add to query response latency

**Acceptance:** Every `POST /query` produces an audit log entry with correct fields.

---

### TASK-AUDIT-003 — Emit authentication audit events 🔴

**File:** `backend/app/api/routes/auth.py`

- [ ] On login success: `AuditService.log("login_success", username, role, { source_ip })`
- [ ] On login failure: `AuditService.log("login_failure", username, null, { source_ip })`

**Acceptance:** Both success and failure login events appear in the audit log.

---

### TASK-AUDIT-004 — Emit ingestion audit events 🔴

**File:** `backend/app/ingestion/service.py`

- [ ] On ingestion completion: `AuditService.log("ingest_success", admin_user_id, "Admin", { source_path, source_type, chunks_indexed })`
- [ ] On ingestion failure: `AuditService.log("ingest_failure", admin_user_id, "Admin", { source_path, error_summary })`

**Acceptance:** All ingestion events (success and failure) produce audit entries.

---

### TASK-AUDIT-005 — Implement GET /audit-logs endpoint 🔴

**File:** `backend/app/api/routes/audit.py`

- [ ] Apply `require_role(["Admin", "Compliance"])` dependency
- [ ] Support pagination via query parameters (`page`, `page_size`)
- [ ] Return `AuditLogListResponse` with array of audit records
- [ ] Ensure audit store is read-only from this endpoint (no delete or modify operations)

**Acceptance:** Admin and Compliance roles receive paginated logs. Other roles receive HTTP 403.

---

## 9. Observability Module Tasks

> **Corresponding Requirements:** OBS-001 through OBS-003, NFR-OBS-001 through NFR-OBS-003
> **Corresponding Design:** §8

---

### TASK-OBS-001 — Implement Prometheus metrics instrumentation 🔴

**File:** `backend/app/observability/metrics.py`

- [ ] Implement the following metrics using `prometheus_client`:
  - `rag_query_total` (Counter, labels: `role`, `outcome`)
  - `rag_query_duration_seconds` (Histogram, labels: `stage`)
  - `rag_denied_chunks_total` (Counter, labels: `role`)
  - `rag_confidence_score` (Histogram)
  - `rag_ingestion_total` (Counter, labels: `source_type`, `outcome`)
  - `rag_auth_failures_total` (Counter)
- [ ] Increment each metric at the appropriate pipeline stage
- [ ] Instrument retrieval stage timings using the Histogram

**Acceptance:** After running queries and ingestions, `/metrics` shows non-zero values for all implemented metrics.

---

### TASK-OBS-002 — Expose GET /metrics endpoint 🔴

**File:** `backend/app/main.py` or `backend/app/api/routes/`

- [ ] Mount Prometheus metrics endpoint at `GET /metrics`
- [ ] Endpoint must be unauthenticated in development
- [ ] Add comment: must be network-restricted in production (SEC-018)
- [ ] Metrics collection failure must not affect API availability

**Acceptance:** `GET /metrics` returns HTTP 200 with valid Prometheus text exposition format.

---

### TASK-OBS-003 — Implement structured JSON application logging 🔴

**File:** `backend/app/core/logging.py`

- [ ] Configure Python logger to emit JSON format with fields: `timestamp`, `level`, `module`, `event`, `user_id`, `request_id`, `detail`
- [ ] Apply to all modules via a shared logger factory
- [ ] Ensure passwords and JWT secrets are never logged

**Acceptance:** Application logs are valid JSON. No secrets appear in log output.

---

### TASK-OBS-004 — Implement GET /health endpoint 🔴

**File:** `backend/app/api/routes/` or `backend/app/main.py`

- [ ] Implement health check: verify FAISS index file is readable
- [ ] Return `{ "status": "ok" }` with HTTP 200 if all checks pass
- [ ] Return HTTP 503 with component detail if any check fails
- [ ] Response time must be < 2 seconds (NFR-AVAIL-001)
- [ ] Health endpoint must not expose internal config or secrets

**Acceptance:** `/health` returns 200 with populated index. Returns 503 with missing index file.

---

### TASK-OBS-005 — Configure Prometheus and Grafana in Docker Compose 🟡

**Files:** `deploy/prometheus.yml`, `docker-compose.yml`

- [ ] Configure Prometheus scrape job targeting `backend:8000/metrics`
- [ ] Configure Grafana data source pointing to Prometheus at `http://prometheus:9090`
- [ ] Set Grafana default credentials (document rotation requirement in `README.md`)
- [ ] Grafana accessible at `http://localhost:3001`
- [ ] Grafana and Prometheus failure must not affect API or frontend

**Acceptance:** Docker Compose up → Grafana at port 3001 shows Prometheus data.

---

## 10. Frontend — Chat Module Tasks

> **Corresponding Requirements:** CHAT-001, CHAT-002, AUTH-001 (frontend), RBAC-002 (frontend display)
> **Corresponding Design:** §3.4

---

### TASK-CHAT-001 — Implement login page and session management 🔴

**Files:** `frontend/app/login/page.tsx`, `frontend/lib/session.ts`, `frontend/lib/api.ts`

- [ ] Render login form: username and password fields, submit button
- [ ] On submit: `POST /login` via `api.ts`; store `access_token` in session state
- [ ] On success: redirect to `/chat`
- [ ] On failure: display user-friendly error message (not raw API error)
- [ ] Define and document token storage mechanism: in-memory state (recommended) or httpOnly cookie
- [ ] Session check on `/chat` load: no valid token → redirect to `/login`
- [ ] JWT must be sent in `Authorization: Bearer` header; never in URL parameters

**Acceptance:** Valid credentials redirect to chat. Invalid credentials show error. Direct access to `/chat` without login redirects to `/login`.

---

### TASK-CHAT-002 — Implement chat query submission and response rendering 🔴

**Files:** `frontend/app/chat/page.tsx`, `frontend/components/cards/`

- [ ] Render query input field and submit button
- [ ] On submit: `POST /query` with `Authorization: Bearer <token>`; display loading indicator during request
- [ ] On success: render `answer` text, `citations` list (source, department, relevance score, excerpt), `confidence` badge
- [ ] On `"Insufficient authorized data available."` response: render styled notice (not a generic error)
- [ ] On API error: display user-friendly error message

**Acceptance:** Query response renders all three components — answer, citations, confidence. Insufficient evidence response is visually distinct.

---

### TASK-CHAT-003 — Implement trace visualization panel 🟡

**Files:** `frontend/app/chat/page.tsx`, `frontend/components/trace/`

- [ ] Render collapsible trace panel below each response
- [ ] Display: routing decision, authorized chunk count, denied count, retrieval timings
- [ ] If `trace` field is missing or null: hide panel entirely
- [ ] Denied chunk content must never appear in the trace panel (data is already sanitized at API layer, confirm at frontend)

**Acceptance:** Trace panel is collapsible. Missing trace data hides the panel. All specified trace fields are displayed when present.

---

## 11. Frontend — Upload Module Tasks

> **Corresponding Requirements:** UPLOAD-001, RBAC-004, INGEST-001
> **Corresponding Design:** §3.5

---

### TASK-UPLOAD-001 — Implement document upload page 🔴

**Files:** `frontend/app/upload/page.tsx`

- [ ] Role gate: non-Admin users → redirect or disable form with clear message
- [ ] Render form fields: `path`, `source_type` (dropdown of allowed types), `department`, `owner`, `confidentiality`, `allowed_roles` (multi-select), `rbac_tags`
- [ ] On submit: `POST /ingest` with admin JWT
- [ ] On success: display confirmation with `chunks_indexed` count
- [ ] On API error: display error detail from response

**Acceptance:** Admin user can successfully submit a valid ingestion request and see chunk count confirmation. Non-Admin sees redirect or disabled state.

---

## 12. Frontend — Admin Dashboard Tasks

> **Corresponding Requirements:** ADMIN-001, ADMIN-002, AUDIT-004
> **Corresponding Design:** §3.6

---

### TASK-ADMIN-001 — Implement admin audit log viewer 🔴

**Files:** `frontend/app/admin/page.tsx`, `frontend/components/dashboard/`

- [ ] Role gate: non-Admin/Compliance → redirect or access denied message
- [ ] Fetch `GET /audit-logs` with pagination on page load and on page change
- [ ] Render paginated table: columns — `timestamp`, `user`, `role`, `query`, `denied_count`, `confidence`, `outcome`
- [ ] On API unavailable: show error state; do not show stale data silently

**Acceptance:** Admin and Compliance users see the audit log table. Pagination controls work. API error shows error state.

---

### TASK-ADMIN-002 — Add Grafana link to admin dashboard 🟢

**Files:** `frontend/app/admin/page.tsx`, `frontend/components/dashboard/`

- [ ] Add navigation link to Grafana dashboard URL (configurable via environment variable)
- [ ] If Grafana URL is unconfigured: hide link gracefully

**Acceptance:** Admin page shows Grafana link when URL is configured.

---

## 13. Deployment & Infrastructure Tasks

> **Corresponding Requirements:** Deployment design §9, Kubernetes §9.3, Scalability §12
> **Corresponding Design:** §9

---

### TASK-DEPLOY-001 — Configure Docker Compose full-stack deployment 🔴

**File:** `docker-compose.yml`

- [ ] Define `backend` service: FastAPI, port 8000, health check on `/health`
- [ ] Define `frontend` service: Next.js, port 3000, depends on backend health check
- [ ] Define `prometheus` service: port 9090, config from `deploy/prometheus.yml`
- [ ] Define `grafana` service: port 3001, data source pre-configured to Prometheus
- [ ] Mount `runtime/faiss_index/` as a volume into the backend service
- [ ] Inject all environment variables from a `.env` file (document required variables)
- [ ] Add `.env.example` with all required keys and placeholder values

**Acceptance:** `docker compose up` starts all four services. Frontend successfully queries backend. Grafana is reachable at port 3001.

---

### TASK-DEPLOY-002 — Write backend and frontend Dockerfiles 🔴

**Files:** `backend/Dockerfile`, `frontend/Dockerfile`

- [ ] Backend: Python 3.12 base, install `requirements.txt`, expose port 8000, run `uvicorn app.main:app`
- [ ] Frontend: Node.js 22 base, install deps, build Next.js, expose port 3000
- [ ] Both: no secrets baked into images; all config via environment variables

**Acceptance:** Both images build successfully. Backend image runs health check cleanly.

---

### TASK-DEPLOY-003 — Write Kubernetes deployment manifests 🟡

**Files:** `deploy/k8s/backend.yaml`, `deploy/k8s/frontend.yaml`, `deploy/k8s/secrets.example.yaml`

- [ ] Backend `Deployment`: replicas ≥ 2, liveness probe `/health`, readiness probe `/health`, env from `Secret`
- [ ] Backend `Service`: ClusterIP or LoadBalancer as appropriate
- [ ] Frontend `Deployment`: `NEXT_PUBLIC_API_BASE_URL` set to internal backend service name
- [ ] `secrets.example.yaml`: document all required secret keys (`JWT_SECRET`, LLM API key, etc.)
- [ ] PVC for FAISS index: `ReadWriteMany` access mode; mount into backend pods
- [ ] Document: concurrent ingestion write-lock limitation; recommend single-ingestion-at-a-time in multi-replica setup

**Acceptance:** `kubectl apply` on all manifests succeeds against a test cluster. Backend pods pass readiness probes.

---

### TASK-DEPLOY-004 — Configure rate limiting middleware 🔴

**File:** `backend/app/core/rate_limit.py`

- [ ] Implement or configure rate limiting for `POST /login` and `POST /query`
- [ ] Rate limit thresholds configurable via environment variables
- [ ] Exceeding limit: return HTTP 429 with `Retry-After` header
- [ ] Document thresholds in `.env.example`

**Acceptance:** Exceeding the login rate limit returns HTTP 429. Normal usage is not affected.

---

### TASK-DEPLOY-005 — Disable /docs and restrict /metrics in production 🔴

**File:** `backend/app/main.py`, Kubernetes network policy or ingress

- [ ] Add `DISABLE_DOCS` environment variable; if set, disable FastAPI Swagger UI (`/docs`, `/redoc`)
- [ ] Document the network restriction requirement for `/metrics` in the deployment guide
- [ ] Add network policy example to `deploy/k8s/` restricting `/metrics` to Prometheus namespace

**Acceptance:** `/docs` returns 404 when `DISABLE_DOCS=true`. `/metrics` is blocked by network policy outside the Prometheus pod.

---

## 14. Testing & QA Tasks

> **Corresponding Requirements:** All acceptance criteria in §8; NFR-MAINT-003
> **Corresponding Design:** All modules

---

### TASK-TEST-001 — Unit tests: RBAC filter 🔴

**File:** `backend/tests/security/test_rbac.py`

- [ ] Test: `Admin` user accesses `Finance`-only chunk → authorized
- [ ] Test: `Guest` user accesses `Finance`-only chunk → denied, `denied_count == 1`
- [ ] Test: all chunks denied → `authorized == []`
- [ ] Test: chunk with empty `allowed_roles` → denied for all users
- [ ] Test: chunk with all roles → authorized for all users

---

### TASK-TEST-002 — Unit tests: JWT validation 🔴

**File:** `backend/tests/security/test_auth.py`

- [ ] Test: valid JWT → `CurrentUser` returned with correct claims
- [ ] Test: expired JWT → HTTP 401
- [ ] Test: tampered signature → HTTP 401
- [ ] Test: missing `Authorization` header → HTTP 401

---

### TASK-TEST-003 — Unit tests: ingestion pipeline 🔴

**File:** `backend/tests/ingestion/`

- [ ] Test each loader with a valid fixture file in its format
- [ ] Test chunker with short, long, and empty inputs
- [ ] Test metadata extractor populates all required fields
- [ ] Test path traversal rejection (`../../etc/passwd` returns HTTP 400)
- [ ] Test invalid `source_type` returns HTTP 400

---

### TASK-TEST-004 — Unit tests: retrieval pipeline 🔴

**File:** `backend/tests/retrieval/`

- [ ] Test FAISS search returns expected candidates from a seeded index
- [ ] Test BM25 search returns keyword-matched candidates
- [ ] Test score fusion deduplicates and sorts correctly
- [ ] Test fusion with one empty input degrades gracefully
- [ ] Test reranker fallback on unavailability

---

### TASK-TEST-005 — Unit tests: generation module 🔴

**File:** `backend/tests/generation/`

- [ ] Test `PromptBuilder.build()` with authorized chunks produces correctly structured prompt
- [ ] Test `PromptBuilder.build()` with empty chunks raises `InsufficientEvidenceError`
- [ ] Test hallucination guard flags an ungrounded claim
- [ ] Test `Generator.generate()` handles LLM API failure as HTTP 503

---

### TASK-TEST-006 — Integration tests: query pipeline end-to-end 🔴

**File:** `backend/tests/integration/test_query.py`

- [ ] Test: authenticated user → receives answer with citations and trace
- [ ] Test: `Guest` user + Finance-only index → `"Insufficient authorized data available."`, `denied_count > 0`
- [ ] Test: unauthenticated request → HTTP 401
- [ ] Test: expired token → HTTP 401
- [ ] Test: non-Admin `POST /ingest` → HTTP 403
- [ ] Test: non-Admin/Compliance `GET /audit-logs` → HTTP 403

---

### TASK-TEST-007 — Integration tests: ingestion end-to-end 🟡

**File:** `backend/tests/integration/test_ingest.py`

- [ ] Test: Admin ingests a valid JSON file → `chunks_indexed > 0`
- [ ] Test: Admin ingests a non-existent file path → HTTP 404
- [ ] Test: Admin ingests with unknown `source_type` → HTTP 400
- [ ] Test: After ingestion, query returns content from the ingested document

---

### TASK-TEST-008 — Unit tests: explainability module 🔴

**File:** `backend/tests/explainability/`

- [ ] Test: confidence score is within `[0.0, 1.0]`
- [ ] Test: citation list maps 1:1 to authorized chunks
- [ ] Test: trace includes all required fields
- [ ] Test: denied chunk IDs do not appear in trace output

---

### TASK-TEST-009 — Frontend: route protection tests 🟡

- [ ] Test: unauthenticated user accessing `/chat` is redirected to `/login`
- [ ] Test: non-Admin accessing `/upload` sees redirect or disabled form
- [ ] Test: non-Admin/Compliance accessing `/admin` sees access denied

---

## 15. Security Hardening Tasks

> **Corresponding Requirements:** SEC-001 through SEC-020, NFR-SEC-001 through NFR-SEC-004
> **Corresponding Design:** §5.6, §5.7

---

### TASK-SEC-001 — Pre-deployment security checklist 🔴

Create `SECURITY.md` or section in `README.md` covering:

- [ ] Replace `DEMO_USERS` in `security/auth.py` before any shared deployment
- [ ] Set `JWT_SECRET` to a random 256-bit string via environment variable
- [ ] Rotate Grafana credentials from `admin`/`admin`
- [ ] Set `DISABLE_DOCS=true` in production
- [ ] Restrict `/metrics` to internal Prometheus network
- [ ] Review and populate `deploy/k8s/secrets.example.yaml` with real secrets via a secrets manager
- [ ] Enforce TLS at the ingress layer for all production traffic

---

### TASK-SEC-002 — Prompt injection hardening 🔴

**Files:** `backend/app/generation/prompt.py`, `examples/prompts/`

- [ ] Audit prompt template to ensure user query text is placed inside a clearly bounded `[USER QUERY]` section
- [ ] Ensure no user input is interpolated into the LLM instruction section
- [ ] Document prompt template versioning approach (see §14 future enhancements)
- [ ] Verify guardrail stage catches injection-induced hallucinations in test scenarios

---

### TASK-SEC-003 — Input length bounding 🔴

**File:** `backend/app/api/routes/query.py`, `backend/app/api/routes/ingest.py`

- [ ] Add maximum length validator to `QueryRequest.query` field (SEC-020)
- [ ] Document the bound (e.g., 4,000 characters) in API docs and `.env.example`
- [ ] Return HTTP 422 with descriptive message for overlength queries

---

### TASK-SEC-004 — CI check for production safety issues 🟡

**File:** `.github/workflows/ci.yml`

- [ ] Add linting step: scan `security/auth.py` for presence of `DEMO_USERS` with a hardcoded password pattern — fail CI if found in production branch
- [ ] Add check: `JWT_SECRET` not present as a hardcoded string anywhere in codebase
- [ ] Document CI checks in `README.md`

---

## 16. Task Dependency Map

The following dependency chains must be respected during sprint planning. A task cannot begin until all its upstream tasks are complete.

```
Core Infrastructure (all others depend on these)
  TASK-AUTH-004 (config & secrets)
  TASK-OBS-003 (structured logging)
  TASK-RBAC-001 (role enumeration)

Authentication (must precede all protected endpoints)
  TASK-AUTH-002 → TASK-AUTH-003 → TASK-AUTH-001

Ingestion Pipeline
  TASK-INGEST-002 (path validation)
  → TASK-INGEST-001 (POST /ingest route)
  → TASK-INGEST-003 (loaders)
  → TASK-INGEST-004 (chunker)
  → TASK-INGEST-005 (metadata)
  → TASK-INGEST-006 (embedding + indexing)
  → TASK-INGEST-007 (async pipeline)
  → TASK-INGEST-008 (example data script)

Query Pipeline
  TASK-RETR-001 + TASK-RETR-002 (FAISS + BM25)
  → TASK-RETR-003 (score fusion)
  → TASK-RETR-004 (reranker)
  → TASK-RBAC-002 (RBAC filter) ← SECURITY BOUNDARY
  → TASK-GEN-001 (prompt builder)
  → TASK-GEN-002 (generator)
  → TASK-GEN-003 (guardrail)
  → TASK-EXPL-001 + TASK-EXPL-002 + TASK-EXPL-003 (explainability)
  → TASK-AUDIT-002 (query audit event)

Frontend
  TASK-AUTH-001 (login endpoint) → TASK-CHAT-001 (login page)
  → TASK-CHAT-002 (chat UI)
  → TASK-CHAT-003 (trace panel)

  TASK-INGEST-001 → TASK-UPLOAD-001 (upload UI)

  TASK-AUDIT-005 → TASK-ADMIN-001 (audit log viewer)

Deployment
  TASK-DEPLOY-002 (Dockerfiles)
  → TASK-DEPLOY-001 (Docker Compose)
  → TASK-DEPLOY-003 (Kubernetes)

Security Hardening (runs in parallel; must complete before release)
  TASK-SEC-001, TASK-SEC-002, TASK-SEC-003
```

---

## 17. Milestone Summary

### Milestone 1 — Core Backend (Blocking Foundation)

Must complete before any other work can be tested end-to-end.

| Task ID | Description | Priority |
|---|---|---|
| TASK-AUTH-004 | Externalize secrets, configure DEMO_USERS | 🔴 |
| TASK-OBS-003 | Structured JSON logging | 🔴 |
| TASK-RBAC-001 | Role enumeration | 🔴 |
| TASK-AUTH-002 | JWT issuance | 🔴 |
| TASK-AUTH-003 | JWT validation dependency | 🔴 |
| TASK-AUTH-001 | POST /login endpoint | 🔴 |
| TASK-RBAC-004 | Endpoint-level role checks | 🔴 |
| TASK-OBS-004 | GET /health endpoint | 🔴 |

---

### Milestone 2 — Ingestion Pipeline

| Task ID | Description | Priority |
|---|---|---|
| TASK-INGEST-002 | Path traversal validation | 🔴 |
| TASK-INGEST-001 | POST /ingest route | 🔴 |
| TASK-INGEST-003 | All 6 source loaders | 🔴 |
| TASK-INGEST-004 | Chunker | 🔴 |
| TASK-INGEST-005 | Metadata extraction | 🔴 |
| TASK-INGEST-006 | Embedding + FAISS/BM25 indexing | 🔴 |
| TASK-RBAC-005 | Validate allowed_roles at ingestion | 🔴 |
| TASK-INGEST-007 | Async ingestion pipeline | 🟡 |
| TASK-INGEST-008 | Example data preload script | 🟡 |

---

### Milestone 3 — Query Pipeline

| Task ID | Description | Priority |
|---|---|---|
| TASK-RETR-001 | FAISS vector search | 🔴 |
| TASK-RETR-002 | BM25 keyword search | 🔴 |
| TASK-RETR-006 | Parallel retrieval execution | 🔴 |
| TASK-RETR-003 | Hybrid score fusion | 🔴 |
| TASK-RETR-004 | Reranker | 🔴 |
| TASK-RBAC-002 | Chunk-level RBAC filter | 🔴 |
| TASK-RBAC-003 | RBAC as pipeline step [6] | 🔴 |
| TASK-GEN-004 | Insufficient evidence fallback | 🔴 |
| TASK-GEN-001 | PromptBuilder | 🔴 |
| TASK-GEN-002 | LLM generator | 🔴 |
| TASK-GEN-003 | Hallucination guard | 🔴 |
| TASK-EXPL-001 | Citation builder | 🔴 |
| TASK-EXPL-002 | Confidence scorer | 🔴 |
| TASK-EXPL-003 | Trace builder | 🔴 |
| TASK-RETR-005 | Query source router | 🟡 |

---

### Milestone 4 — Audit Logging & Observability

| Task ID | Description | Priority |
|---|---|---|
| TASK-AUDIT-001 | AuditService core | 🔴 |
| TASK-AUDIT-002 | Query audit events | 🔴 |
| TASK-AUDIT-003 | Auth audit events | 🔴 |
| TASK-AUDIT-004 | Ingestion audit events | 🔴 |
| TASK-AUDIT-005 | GET /audit-logs endpoint | 🔴 |
| TASK-OBS-001 | Prometheus metrics | 🔴 |
| TASK-OBS-002 | GET /metrics endpoint | 🔴 |

---

### Milestone 5 — Frontend

| Task ID | Description | Priority |
|---|---|---|
| TASK-CHAT-001 | Login page and session management | 🔴 |
| TASK-CHAT-002 | Chat query UI | 🔴 |
| TASK-UPLOAD-001 | Document upload page | 🔴 |
| TASK-ADMIN-001 | Audit log viewer | 🔴 |
| TASK-CHAT-003 | Trace visualization panel | 🟡 |
| TASK-ADMIN-002 | Grafana link in admin | 🟢 |

---

### Milestone 6 — Deployment & Hardening

| Task ID | Description | Priority |
|---|---|---|
| TASK-DEPLOY-002 | Dockerfiles | 🔴 |
| TASK-DEPLOY-001 | Docker Compose | 🔴 |
| TASK-DEPLOY-004 | Rate limiting | 🔴 |
| TASK-DEPLOY-005 | Disable /docs, restrict /metrics | 🔴 |
| TASK-SEC-001 | Pre-deployment security checklist | 🔴 |
| TASK-SEC-002 | Prompt injection hardening | 🔴 |
| TASK-SEC-003 | Input length bounding | 🔴 |
| TASK-DEPLOY-003 | Kubernetes manifests | 🟡 |
| TASK-OBS-005 | Prometheus + Grafana Docker Compose config | 🟡 |
| TASK-SEC-004 | CI production safety checks | 🟡 |

---

### Milestone 7 — Testing & QA

| Task ID | Description | Priority |
|---|---|---|
| TASK-TEST-001 | Unit tests: RBAC filter | 🔴 |
| TASK-TEST-002 | Unit tests: JWT validation | 🔴 |
| TASK-TEST-003 | Unit tests: ingestion pipeline | 🔴 |
| TASK-TEST-004 | Unit tests: retrieval pipeline | 🔴 |
| TASK-TEST-005 | Unit tests: generation module | 🔴 |
| TASK-TEST-006 | Integration tests: query pipeline | 🔴 |
| TASK-TEST-008 | Unit tests: explainability module | 🔴 |
| TASK-TEST-007 | Integration tests: ingestion | 🟡 |
| TASK-TEST-009 | Frontend route protection tests | 🟡 |

---

*End of TASK.md*
