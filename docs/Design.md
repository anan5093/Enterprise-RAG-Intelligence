# Design Document
**Project:** Enterprise RAG Intelligence
**Version:** 1.0.0
**Status:** Draft — For Engineering Review
**Last Updated:** 2026
**Maintainer:** Anand Raj (@anan5093)

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Backend Design](#2-backend-design)
3. [Frontend Design](#3-frontend-design)
4. [Retrieval Architecture](#4-retrieval-architecture)
5. [Security Architecture](#5-security-architecture)
6. [Explainability Design](#6-explainability-design)
7. [Ingestion Pipeline Design](#7-ingestion-pipeline-design)
8. [Observability Design](#8-observability-design)
9. [Deployment Design](#9-deployment-design)
10. [API Design](#10-api-design)
11. [Data Flow](#11-data-flow)
12. [Scalability Considerations](#12-scalability-considerations)
13. [Failure Handling](#13-failure-handling)
14. [Future Enhancements](#14-future-enhancements)

---

## 1. System Architecture

### 1.1 High-Level Architecture

Enterprise RAG Intelligence is a layered, security-first platform. The architectural decision to enforce RBAC **before** prompt construction is the central design constraint that shapes every layer below it.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL CLIENTS                             │
│   Browser (Next.js Frontend)  │  API Clients (curl, SDK)             │
└────────────────────┬─────────────────────────────────────────────────┘
                     │ HTTPS (TLS termination at ingress/proxy)
┌────────────────────▼─────────────────────────────────────────────────┐
│                        API GATEWAY LAYER                             │
│            FastAPI  ·  Rate Limiting  ·  Input Validation            │
└──────┬─────────────────────┬──────────────────────┬──────────────────┘
       │                     │                      │
┌──────▼──────┐   ┌──────────▼──────────┐  ┌───────▼────────┐
│  AUTH &     │   │   QUERY PIPELINE    │  │  INGESTION     │
│  SECURITY   │   │                     │  │  PIPELINE      │
│  LAYER      │   │  Router             │  │                │
│             │   │  ↓                  │  │  Loader        │
│  JWT        │   │  Hybrid Retrieval   │  │  ↓ Parser      │
│  RBAC       │   │  ↓                  │  │  ↓ Chunker     │
│  Audit      │   │  RBAC Filter ←──────│  │  ↓ Embedder    │
│             │   │  ↓                  │  │  ↓ Indexer     │
└─────────────┘   │  Reranker           │  └───────┬────────┘
                  │  ↓                  │          │
                  │  Prompt Builder     │  ┌───────▼────────────┐
                  │  ↓                  │  │   STORAGE LAYER    │
                  │  Guard + Generator  │  │                    │
                  │  ↓                  │  │  FAISS Index       │
                  │  Explainability     │  │  BM25 Index        │
                  └────────┬────────────┘  │  Audit Log Store   │
                           │               └────────────────────┘
┌──────────────────────────▼─────────────────────────────────────────┐
│                      OBSERVABILITY LAYER                           │
│        Prometheus /metrics  ·  Structured Logs  ·  Grafana         │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 Layered Architecture

| Layer | Responsibility | Modules |
|---|---|---|
| API Gateway | Request routing, auth middleware, rate limiting, input validation | `api`, `core` |
| Security | JWT validation, RBAC policy, audit logging | `security` |
| Query Pipeline | Routing, retrieval, filtering, generation | `retrieval`, `generation`, `explainability` |
| Ingestion Pipeline | Loading, parsing, chunking, embedding, indexing | `ingestion` |
| Storage | FAISS vector index, BM25 index, audit store | `runtime/faiss_index/` |
| Observability | Metrics, logging, health | `observability` |

### 1.3 Component Responsibilities

| Component | Module | Responsibility |
|---|---|---|
| FastAPI App | `api` | Define routes, inject dependencies, handle serialization |
| Config & Logging | `core` | Centralized app config, structured logging, rate limiting |
| Auth Middleware | `security/auth.py` | Validate JWT, extract user identity and role |
| RBAC Policy | `security` | Enforce chunk-level access control, record denials |
| Audit Logger | `security` | Append-only structured audit event emission |
| Source Loaders | `ingestion` | Format-specific document loading |
| Chunker | `ingestion` | Split documents into retrieval-sized units |
| Metadata Extractor | `ingestion` | Attach lineage and RBAC tags to chunks |
| Vector Store | `retrieval` | FAISS index read/write operations |
| Hybrid Search | `retrieval` | Parallel FAISS + BM25 execution and score fusion |
| Reranker | `retrieval` | Second-pass relevance ordering |
| Source Router | `retrieval` | Query classification and routing |
| Prompt Builder | `generation` | Assemble grounded prompt from authorized chunks |
| Guardrail | `generation` | Detect and suppress unsupported claims |
| Generator | `generation` | LLM API call and response extraction |
| Provenance Tracker | `explainability` | Build citation and trace objects |
| Confidence Scorer | `explainability` | Compute response confidence |
| Metrics Collector | `observability` | Prometheus counter/histogram instrumentation |

---

## 2. Backend Design

### 2.1 FastAPI Architecture

The backend is a single FastAPI application (`backend/app/main.py`) organized into the module hierarchy described above. FastAPI's dependency injection system is used throughout to compose security checks, database connections (if any), and service dependencies.

```
backend/app/
├── main.py               # FastAPI app instantiation, middleware registration, router inclusion
├── api/                  # Route definitions and FastAPI dependencies
│   ├── routes/
│   │   ├── auth.py       # POST /login
│   │   ├── query.py      # POST /query
│   │   ├── ingest.py     # POST /ingest
│   │   └── audit.py      # GET /audit-logs
│   └── deps.py           # get_current_user, require_role, etc.
├── core/
│   ├── config.py         # Settings (env vars, Pydantic BaseSettings)
│   ├── logging.py        # Structured JSON logger
│   └── rate_limit.py     # Rate limiting middleware/decorator
├── ingestion/            # Pipeline stages (see §7)
├── retrieval/            # Retrieval stages (see §4)
├── security/             # Auth, RBAC, audit (see §5)
├── generation/           # Prompt, guard, generator (see §2.4)
├── explainability/       # Citations, trace, confidence (see §6)
└── observability/        # Prometheus instrumentation (see §8)
```

### 2.2 API Layer

Routes are thin. They:
1. Accept and validate input via Pydantic request models.
2. Invoke FastAPI dependencies for auth and role checks.
3. Delegate to service/pipeline functions.
4. Serialize and return response models.

Route handlers must not contain business logic. Business logic lives in service modules.

### 2.3 Service Layer

Each major capability is encapsulated in a service class or function set:

- `QueryService`: orchestrates the full query pipeline (routing → retrieval → RBAC filter → reranking → generation → explainability).
- `IngestionService`: orchestrates the ingestion pipeline (load → parse → chunk → embed → index).
- `AuditService`: writes structured audit events.
- `AuthService`: validates credentials and issues JWTs.

### 2.4 Request Lifecycle — Query

```
POST /query
  │
  ├─ [1] Input validation (Pydantic)
  ├─ [2] JWT validation (FastAPI dependency → security/auth.py)
  ├─ [3] Rate limit check (core/rate_limit.py)
  ├─ [4] Route query (retrieval/routing.py)
  ├─ [5] Hybrid retrieval: FAISS + BM25 in parallel
  ├─ [6] Score fusion → candidate list
  ├─ [7] RBAC filter (security/rbac.py) ← SECURITY BOUNDARY
  ├─ [8] Reranking (retrieval/reranker.py)
  ├─ [9] Prompt construction (generation/prompt.py)
  │       └─ if authorized chunks = 0 → return "Insufficient authorized data available."
  ├─ [10] Hallucination guard (generation/guardrails.py)
  ├─ [11] LLM generation (generation/generator.py)
  ├─ [12] Explainability assembly (explainability/)
  │        ├─ citations
  │        ├─ confidence score
  │        └─ trace metadata
  ├─ [13] Audit log write (security/audit.py) — non-blocking
  ├─ [14] Metrics increment (observability/)
  └─ [15] Return QueryResponse
```

### 2.5 Security Layer (Module: `security`)

- `auth.py`: Credential validation, JWT issuance (`python-jose` or equivalent — implementation detail not fully defined in repository), `DEMO_USERS` store.
- `rbac.py`: Chunk-level access control. Compares `chunk.metadata.allowed_roles` against `current_user.role`.
- `policy.py`: Higher-level policy checks (e.g., endpoint-level role requirements).
- `audit.py`: Structured event emission.

### 2.6 Explainability Layer (Module: `explainability`)

Assembles the `citations`, `confidence`, and `trace` fields from pipeline execution context. See §6.

### 2.7 Observability Layer (Module: `observability`)

Exposes Prometheus counters and histograms. See §8.

---

## 3. Frontend Design

### 3.1 Next.js Architecture

The frontend uses Next.js with the **App Router** (`app/` directory). All pages are React Server Components or Client Components as appropriate.

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with session provider
│   ├── page.tsx            # Root redirect (to /login or /chat)
│   ├── login/
│   │   └── page.tsx        # Login page
│   ├── chat/
│   │   └── page.tsx        # Chat interface (protected)
│   ├── upload/
│   │   └── page.tsx        # Document upload (admin only)
│   └── admin/
│       └── page.tsx        # Admin audit dashboard (admin/compliance only)
├── components/
│   ├── shell/              # Layout shell, navigation
│   ├── cards/              # Reusable card components
│   ├── trace/              # Trace visualization component
│   └── dashboard/          # Audit log table, metrics link
├── lib/
│   ├── api.ts              # Typed API client functions
│   └── session.ts          # Session/token management utilities
└── next.config.js          # Next.js config (API base URL, etc.)
```

### 3.2 App Router Structure

- Route protection is enforced via middleware or layout-level session checks.
- `NEXT_PUBLIC_API_BASE_URL` environment variable controls the backend API base URL.
- Server-side rendering is used where appropriate for initial data fetches.

### 3.3 Authentication Flow

```
User visits /chat
  │
  ├─ Session check (lib/session.ts)
  │   ├─ No valid token → redirect to /login
  │   └─ Valid token → render /chat
  │
User submits login form (/login)
  │
  ├─ POST /login (lib/api.ts → backend /login)
  ├─ Success: store access_token (session state)
  ├─ Redirect to /chat
  └─ Failure: display error message
```

**Token storage mechanism** is an implementation detail not fully defined in the repository. Common patterns: in-memory state (most secure, lost on page refresh) or httpOnly cookie (requires cookie-based session endpoint on backend). Engineers must define this before production deployment.

### 3.4 Chat Flow

```
User types query → Submit button
  │
  ├─ POST /query with Authorization: Bearer <token>
  ├─ Display loading indicator
  ├─ On success:
  │   ├─ Render answer text
  │   ├─ Render citations list
  │   ├─ Render confidence badge
  │   └─ Render collapsible trace panel (CHAT-002)
  └─ On error:
      ├─ "Insufficient authorized data available." → styled notice
      └─ API error → user-friendly error message
```

### 3.5 Upload Flow

```
Admin visits /upload
  │
  ├─ Role check: non-admin → redirect or disable form
  │
Admin fills form:
  ├─ path, source_type, department, owner, confidentiality
  ├─ allowed_roles (multi-select), rbac_tags
  │
Submit → POST /ingest with admin JWT
  ├─ Success → confirmation with chunk count
  └─ Error → display error detail
```

### 3.6 Admin Monitoring UI

```
Admin/Compliance visits /admin
  │
  ├─ Role check enforced
  ├─ GET /audit-logs → render paginated audit log table
  │   Columns: timestamp, user, role, query, denied_count, confidence, outcome
  └─ Link to Grafana dashboard
```

---

## 4. Retrieval Architecture

### 4.1 Why Hybrid Retrieval

Pure dense vector search (FAISS) excels at semantic similarity but can miss documents that match on exact keyword terms — especially for technical identifiers, proper nouns, product names, and alert codes common in enterprise datasets. Pure BM25 keyword search handles exact matches well but fails on paraphrase and semantic variations.

Hybrid retrieval combines both: **dense search covers semantic intent; sparse BM25 search covers lexical precision.** Score fusion then selects the best candidates from both perspectives, producing a more robust candidate set than either method alone.

### 4.2 FAISS Vector Search

```
Query Text
  │
  ├─ Embedding model (same model used at ingestion time)
  ├─ Query vector: float32[D]
  └─ FAISS.search(query_vector, top_k)
      └─ Returns: [(chunk_id, score), ...] sorted by cosine/L2 similarity
```

- Index type: Implementation detail not yet defined in repository (assumed `IndexFlatL2` or `IndexIVFFlat`).
- Index files: `runtime/faiss_index/`
- Embedding model: Implementation detail not yet defined in repository.

### 4.3 BM25 Retrieval

```
Query Text
  │
  ├─ Tokenize query
  └─ BM25.get_scores(tokenized_query)
      └─ Returns: [(chunk_id, bm25_score), ...] sorted by score
```

- BM25 library: Implementation detail not yet defined in repository (commonly `rank_bm25` in Python).
- BM25 corpus is built from chunk text at ingestion time.

### 4.4 Hybrid Score Fusion

**Assumption**: Reciprocal Rank Fusion (RRF) or weighted linear interpolation. Not specified in repository.

```
FAISS candidates: [(id_A, score_F_A), (id_B, score_F_B), ...]
BM25 candidates:  [(id_B, score_B_B), (id_C, score_B_C), ...]
  │
  ├─ Normalize scores within each list to [0, 1]
  ├─ Combine: fused_score(chunk) = α * norm_faiss_score + (1-α) * norm_bm25_score
  │             (or RRF: 1/(k + rank_faiss) + 1/(k + rank_bm25))
  ├─ Deduplicate by chunk_id
  └─ Sort by fused_score → unified candidate list
```

### 4.5 Reranking

The reranker applies a second relevance pass over the fused candidates using the original query text. This corrects ordering errors from score fusion and produces the final chunk set presented to the RBAC filter.

```
Fused candidate list + original query
  │
  └─ Reranker.rerank(query, candidates, top_n)
      └─ Returns: reordered list, top_n chunks
```

- Reranking model: Implementation detail not yet defined in repository. Likely a cross-encoder or lightweight scoring function.
- Reranking executes on the pre-RBAC candidate set. **RBAC filtering must execute on the reranked output, not before, to avoid reranker bias from denied chunk presence leaking into scores.**

### 4.6 Source Routing

The router classifies the query (e.g., by department keyword, query type, or explicit routing metadata) and selects the appropriate retrieval source(s). Routing decisions are recorded in the trace.

```
Query text
  │
  └─ Router.classify(query) → route_decision
      ├─ default: hybrid (FAISS + BM25)
      └─ specialized: route to department-specific sub-index (future)
```

### 4.7 Retrieval Pipeline Summary

```
Query
  │
  [1] Route classification
  [2] Dense search (FAISS) ─────────────┐
  [3] Sparse search (BM25) ─────────────┤
  [4] Score fusion ←────────────────────┘
  [5] Reranking
  [6] RBAC filter  ← SECURITY BOUNDARY
  [7] → Authorized chunks to Prompt Builder
```

---

## 5. Security Architecture

### 5.1 JWT Validation

```
Incoming Request
  │
  ├─ Extract Authorization header
  ├─ Decode JWT header → identify algorithm
  ├─ Verify signature using JWT_SECRET
  ├─ Check exp claim (expiry)
  ├─ Extract sub (user identity) and role claim
  └─ Inject CurrentUser into FastAPI dependency graph
```

JWT validation is implemented as a FastAPI dependency (`deps.py: get_current_user`) applied to all protected routes.

### 5.2 RBAC Filtering (Pre-Generation)

```
candidate_chunks: List[Chunk]
current_user.role: str
  │
  for chunk in candidate_chunks:
    if current_user.role in chunk.metadata.allowed_roles:
      authorized.append(chunk)
    else:
      denied_count += 1
  │
  if len(authorized) == 0:
    return "Insufficient authorized data available."
  │
  trace.denied_count = denied_count
  return authorized
```

This logic executes in `security/rbac.py` and is invoked by `QueryService` between the reranking step and prompt construction.

### 5.3 Pre-Generation Authorization Enforcement

The RBAC filter is architecturally enforced as step [6] in the retrieval pipeline. The prompt builder receives only the authorized chunk list; it has no access to the pre-filter candidate list. This design prevents accidental leakage through prompt construction logic bugs.

### 5.4 Audit Logging Pipeline

```
Pipeline event occurs (login, query, ingest, access denial)
  │
  AuditService.log(event_type, user, metadata)
    │
    ├─ Construct structured event dict:
    │   { timestamp, event_type, user_id, role, action_detail, outcome }
    ├─ Serialize to JSON
    └─ Write to audit store (append-only)
         └─ Mechanism: implementation detail not fully defined in repository
              (file-based, database, or log aggregation pipeline)
```

Audit writes are non-blocking (async or fire-and-forget) to avoid impacting query latency. Write failures are captured at ERROR level in application logs.

### 5.5 Security Boundaries and Trust Zones

```
┌─────────────────────────────────────────────────────┐
│  EXTERNAL TRUST ZONE (untrusted)                    │
│  - Browser clients                                  │
│  - API clients                                      │
└──────────────────────┬──────────────────────────────┘
                       │ TLS
┌──────────────────────▼──────────────────────────────┐
│  API TRUST ZONE (partially trusted after JWT)       │
│  - FastAPI API layer                                │
│  - JWT validated here                               │
│  - Rate limiting enforced here                      │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  SERVICE TRUST ZONE (trusted internal)              │
│  - Query pipeline                                   │
│  - Ingestion pipeline                               │
│  - RBAC filter ← enforcement point                  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  STORAGE TRUST ZONE (trusted internal)              │
│  - FAISS index (filesystem)                         │
│  - Audit log store                                  │
└─────────────────────────────────────────────────────┘
```

### 5.6 Threat Model

| Threat | Attack Vector | Control |
|---|---|---|
| Unauthorized data access | Valid JWT, wrong role | Pre-generation RBAC filter (SEC-004) |
| Token forgery | Crafted JWT | Signature verification with JWT_SECRET |
| Credential stuffing | Brute-force `/login` | Rate limiting (SEC-006) |
| Prompt injection | Malicious content in user query | Static prompt templates + guardrail |
| Prompt injection via document | Malicious content injected at ingestion | Input sanitization at ingestion; chunk isolation in prompt |
| Path traversal via ingestion | Malicious `path` field | Allowlist directory validation (SEC-013) |
| Secrets exposure | Hardcoded secrets in code | Environment variable injection; `DEMO_USERS` replacement requirement |
| Metrics/docs exposure | Public `/metrics` or `/docs` | Network restriction in production (SEC-017, SEC-018) |

### 5.7 Prompt Injection Considerations

Prompt injection is mitigated at two levels:

1. **Structural**: Prompt templates are static parameterized structures. User query text is injected into a clearly delimited `[USER QUERY]` section. Document chunks are injected into a `[EVIDENCE]` section with explicit boundaries. The LLM is instructed to answer only from the evidence section.
2. **Detection**: The hallucination guard post-processes generated responses to verify claims are grounded in the provided evidence. Claims not attributable to evidence chunks are suppressed.

---

## 6. Explainability Design

### 6.1 Citation Generation

For every query that produces a non-empty response, citations are constructed from the authorized chunks used in the prompt:

```python
citations = [
    {
        "chunk_id": chunk.id,
        "source_path": chunk.metadata.source_path,
        "department": chunk.metadata.department,
        "owner": chunk.metadata.owner,
        "confidentiality": chunk.metadata.confidentiality,
        "relevance_score": chunk.rerank_score,
        "text_excerpt": chunk.text[:200]   # Configurable excerpt length
    }
    for chunk in authorized_prompt_chunks
]
```

Citations expose only metadata the requesting user is authorized to see (RBAC was applied before this step).

### 6.2 Trace Metadata

The trace object captures the full pipeline execution record:

```python
trace = {
    "route": route_decision,            # e.g., "hybrid", "bm25_only"
    "authorized_chunk_ids": [...],       # IDs of chunks passed to prompt
    "denied_count": int,                 # Count of RBAC-denied chunks
    "filters_applied": {
        "user_role": current_user.role,
        "rbac_tags_matched": [...]
    },
    "retrieval_timings_ms": {
        "dense_search": float,
        "sparse_search": float,
        "fusion": float,
        "reranking": float,
        "rbac_filter": float
    }
}
```

### 6.3 Confidence Scoring

Confidence is a scalar [0.0, 1.0] computed from:

- Average rerank score of prompt chunks (proxy for retrieval quality).
- Number of authorized chunks relative to retrieved candidate count.
- Guardrail pass/fail signals.

**Exact scoring formula is an implementation detail not yet defined in the repository.** The design principle is: low evidence quality or high denial rate should produce low confidence.

### 6.4 Provenance Tracking

Each chunk carries full lineage metadata from ingestion: `source_path`, `department`, `owner`, `confidentiality`, `ingestion_timestamp`. This enables post-hoc tracing of any citation back to its source document and ingestion event.

---

## 7. Ingestion Pipeline Design

### 7.1 Source Loaders

Each `source_type` has a dedicated loader in `ingestion/`:

| Source Type | Loader Responsibility |
|---|---|
| `csv` | Parse rows into text records |
| `json` | Parse JSON objects/arrays into text representations |
| `pdf` | Extract text from PDF pages (library: implementation detail not defined in repository) |
| `docx` | Extract text from Word documents (library: implementation detail not defined in repository) |
| `sql` | Query a SQL source and extract row data (connection string: implementation detail not defined in repository) |
| `markdown` / `text` | Read plain text or Markdown files |

### 7.2 Parsing and Chunking

After loading, raw text passes through the chunking stage:

```
Raw document text
  │
  ├─ [1] Clean: remove encoding artifacts, normalize whitespace
  ├─ [2] Split: divide into chunks by size/overlap parameters
  │         (chunk size and overlap: implementation detail not defined in repository)
  ├─ [3] Each chunk assigned: chunk_id (UUID), position index, parent document ID
  └─ [4] Chunk list → metadata extraction
```

### 7.3 Metadata Extraction

RBAC and lineage metadata is attached to each chunk from the ingestion request:

```python
chunk.metadata = {
    "chunk_id": uuid4(),
    "source_path": request.path,
    "source_type": request.source_type,
    "department": request.department,
    "owner": request.owner,
    "confidentiality": request.confidentiality,
    "allowed_roles": request.allowed_roles,
    "rbac_tags": request.rbac_tags,
    "ingestion_timestamp": utcnow(),
    "position_index": int
}
```

### 7.4 Embedding and Index Creation

```
Chunk text
  │
  ├─ Embedding model → float32 vector
  ├─ FAISS index: add vector with chunk_id
  ├─ BM25 corpus: append tokenized chunk text
  └─ Metadata store: persist chunk metadata keyed by chunk_id
```

Both FAISS and BM25 indexes are updated atomically per ingestion batch. Concurrent write safety is an implementation detail not yet defined in the repository.

### 7.5 Validation

Ingestion requests are validated at the API layer before pipeline execution:

- `source_type` must be in the allowed set.
- `path` must resolve within allowed directories.
- `allowed_roles` values must belong to the defined role set.
- Required metadata fields (`department`, `owner`, `confidentiality`) must be non-empty.

### 7.6 Async Execution

Per the architecture diagram, ingestion is async. The API acknowledges the request immediately. The pipeline runs in the background. Failures are captured in the audit log.

---

## 8. Observability Design

### 8.1 Prometheus Metrics

The `observability` module instruments the following metric types (specific metric names are implementation details; below is the design intent):

| Metric Name (intent) | Type | Labels | Description |
|---|---|---|---|
| `rag_query_total` | Counter | `role`, `outcome` | Total query requests by role and outcome |
| `rag_query_duration_seconds` | Histogram | `stage` | Query pipeline stage latency |
| `rag_denied_chunks_total` | Counter | `role` | Cumulative count of RBAC-denied chunks |
| `rag_confidence_score` | Histogram | — | Distribution of confidence scores |
| `rag_ingestion_total` | Counter | `source_type`, `outcome` | Ingestion requests by source type |
| `rag_auth_failures_total` | Counter | — | Authentication failure count |

All metrics are exposed at `GET /metrics` in Prometheus text exposition format.

### 8.2 Structured Logging

Application logs are emitted in JSON format with the following fields:

```json
{
  "timestamp": "ISO8601",
  "level": "INFO|WARNING|ERROR",
  "module": "string",
  "event": "string",
  "user_id": "string|null",
  "request_id": "uuid|null",
  "detail": {}
}
```

Structured JSON logs are compatible with log aggregation pipelines (e.g., ELK, Loki).

### 8.3 Health Checks

`GET /health` performs the following checks:

| Check | Healthy Condition |
|---|---|
| Application process | Process is running |
| FAISS index | Index file readable |
| (LLM connectivity) | Implementation detail not defined in repository |

Returns HTTP 200 with `{"status": "ok"}` if all checks pass. Returns HTTP 503 with component status if any check fails.

### 8.4 Grafana Integration

In Docker Compose, a Grafana service is configured with:
- Data source: Prometheus at `http://prometheus:9090`
- Dashboard: Optional pre-built dashboard for RAG metrics (implementation detail not defined in repository as specific dashboard JSON).
- Credentials: `admin`/`admin` (must be rotated before shared use).

### 8.5 Monitoring Recommendations

The following Prometheus alerting rules are recommended (not defined in repository, stated as design guidance):

| Alert | Condition |
|---|---|
| High denial rate | `rag_denied_chunks_total` rate > threshold → possible misconfigured RBAC |
| Low confidence | `rag_confidence_score` histogram p50 < 0.4 → retrieval quality degradation |
| Auth failure spike | `rag_auth_failures_total` rate > threshold → potential credential stuffing |
| Ingestion failure | `rag_ingestion_total{outcome="error"}` rate > 0 → pipeline issue |

---

## 9. Deployment Design

### 9.1 Local Development Architecture

```
Terminal 1: uvicorn app.main:app --reload (port 8000)
Terminal 2: npm run dev (port 3000)

FAISS index: runtime/faiss_index/ (local filesystem)
Config: environment variables set in shell
```

No containerization. Developer runs each service directly. Suitable for backend and frontend development in isolation.

### 9.2 Docker Compose Architecture

```
┌─────────────────────────────────────────────────────┐
│  docker-compose.yml                                 │
│                                                     │
│  ┌──────────────┐    ┌──────────────┐               │
│  │   backend    │    │   frontend   │               │
│  │  FastAPI     │    │  Next.js     │               │
│  │  port 8000   │    │  port 3000   │               │
│  └──────┬───────┘    └──────────────┘               │
│         │ health check dependency                   │
│  ┌──────▼───────┐    ┌──────────────┐               │
│  │  prometheus  │    │   grafana    │               │
│  │  port 9090   │    │  port 3001   │               │
│  └──────────────┘    └──────────────┘               │
│                                                     │
│  Volumes:                                           │
│    runtime/faiss_index/ → backend volume            │
│    prometheus.yml       → prometheus config         │
└─────────────────────────────────────────────────────┘
```

Frontend depends on backend health check passing before starting. Prometheus scrapes backend `/metrics` per `deploy/prometheus.yml`. Grafana reads from Prometheus.

### 9.3 Kubernetes Deployment Model

```
deploy/k8s/
├── secrets.example.yaml    # Secret template (must be replaced)
├── backend.yaml            # Backend Deployment + Service
└── frontend.yaml           # Frontend Deployment + Service
```

**Backend Deployment:**
- Image: built from `backend/Dockerfile` (assumed; Dockerfile presence not confirmed in README).
- Replicas: ≥ 2 for HA (recommendation).
- FAISS index: must be mounted from a `PersistentVolumeClaim` shared across replicas (see §12).
- Liveness probe: `GET /health`
- Readiness probe: `GET /health`
- Environment variables: injected from Kubernetes `Secret` objects.

**Frontend Deployment:**
- Image: built from `frontend/Dockerfile` (assumed).
- `NEXT_PUBLIC_API_BASE_URL`: set to internal Kubernetes service name or ingress URL.

**Secrets Management:**
- `deploy/k8s/secrets.example.yaml` provides the secret schema.
- Operators must populate `JWT_SECRET`, LLM API key, and any other credentials.
- Recommended: use a secrets management tool (e.g., Vault, Sealed Secrets) rather than plaintext Kubernetes secrets in repositories.

### 9.4 Statelessness

The FastAPI backend is designed to be stateless:
- No in-process session state.
- JWT tokens carry all identity information.
- FAISS index is persisted to the filesystem (external volume), not in memory per process.

### 9.5 Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `JWT_SECRET` | JWT signing secret | Yes |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend → backend base URL | Yes (frontend) |
| LLM API key | LLM provider credentials | Yes (name: implementation detail) |
| Rate limit configuration | Rate limit thresholds | Implementation detail |

---

## 10. API Design

### 10.1 Endpoint Table

| Endpoint | Method | Auth | Role | Request Body | Response |
|---|---|---|---|---|---|
| `/login` | POST | No | — | `LoginRequest` | `TokenResponse` |
| `/query` | POST | JWT | Any | `QueryRequest` | `QueryResponse` |
| `/ingest` | POST | JWT | Admin | `IngestRequest` | `IngestResponse` |
| `/audit-logs` | GET | JWT | Admin, Compliance | — (query params) | `AuditLogListResponse` |
| `/health` | GET | No | — | — | `HealthResponse` |
| `/metrics` | GET | No | — | — | Prometheus text |

### 10.2 Request/Response Examples

#### POST /login

Request:
```json
{
  "username": "admin",
  "password": "admin-change-me"
}
```

Response (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /query

Request:
```json
{
  "query": "Show critical security alerts from last month"
}
```

Response (200):
```json
{
  "answer": "The following critical security alerts were identified: ...",
  "citations": [
    {
      "chunk_id": "a1b2c3d4-...",
      "source_path": "examples/data/security_alerts.json",
      "department": "compliance",
      "owner": "compliance",
      "confidentiality": "confidential",
      "relevance_score": 0.91,
      "text_excerpt": "Critical alert: Unauthorized access attempt detected..."
    }
  ],
  "confidence": 0.87,
  "trace": {
    "route": "hybrid",
    "authorized_chunk_ids": ["a1b2c3d4-...", "b2c3d4e5-..."],
    "denied_count": 3,
    "filters_applied": {
      "user_role": "Admin",
      "rbac_tags_matched": ["compliance", "alerts"]
    },
    "retrieval_timings_ms": {
      "dense_search": 45.2,
      "sparse_search": 12.1,
      "fusion": 3.4,
      "reranking": 22.7,
      "rbac_filter": 1.1
    }
  }
}
```

Insufficient evidence response (200 with specific message):
```json
{
  "answer": "Insufficient authorized data available.",
  "citations": [],
  "confidence": 0.0,
  "trace": {
    "route": "hybrid",
    "authorized_chunk_ids": [],
    "denied_count": 8,
    "filters_applied": { "user_role": "Guest" }
  }
}
```

#### POST /ingest

Request:
```json
{
  "path": "examples/data/security_alerts.json",
  "source_type": "json",
  "department": "compliance",
  "owner": "compliance",
  "confidentiality": "confidential",
  "allowed_roles": ["Admin", "Compliance"],
  "rbac_tags": ["compliance", "alerts"]
}
```

Response (200):
```json
{
  "status": "accepted",
  "chunks_indexed": 24,
  "source_path": "examples/data/security_alerts.json"
}
```

### 10.3 Auth Flow

```
Client → POST /login → { access_token }
Client → stores token
Client → all subsequent requests: Authorization: Bearer {access_token}
Backend → validate on every protected request
```

### 10.4 Error Handling Standards

| HTTP Status | Condition |
|---|---|
| 200 | Success (including "Insufficient authorized data available." response) |
| 400 | Invalid request parameters (unsupported `source_type`, etc.) |
| 401 | Missing, expired, or invalid JWT |
| 403 | Valid JWT but insufficient role |
| 404 | Resource not found (e.g., file path in ingest) |
| 422 | Pydantic validation failure |
| 503 | LLM provider unavailable or downstream failure |

All error responses follow the FastAPI default error structure:
```json
{
  "detail": "Human-readable error message"
}
```

---

## 11. Data Flow

### 11.1 Query Execution Flow

```
Client
  │ POST /query { query: "..." }
  │
  ▼
FastAPI Route (api/routes/query.py)
  │ Pydantic validation
  │ get_current_user(token) dependency
  ▼
QueryService.execute(query, current_user)
  │
  ├─ Router.classify(query) → route_decision
  │
  ├─ Parallel:
  │   ├─ FAISS.search(embed(query), top_k) → dense_candidates
  │   └─ BM25.search(tokenize(query), top_k) → sparse_candidates
  │
  ├─ fuse(dense_candidates, sparse_candidates) → fused_candidates
  │
  ├─ Reranker.rerank(query, fused_candidates) → reranked_candidates
  │
  ├─ RBAC.filter(reranked_candidates, current_user.role) → authorized_chunks
  │                                                          denied_count
  │
  ├─ if len(authorized_chunks) == 0:
  │     return InsufficientDataResponse
  │
  ├─ PromptBuilder.build(query, authorized_chunks) → prompt
  │
  ├─ Guard.check(prompt) → validated_prompt
  │
  ├─ Generator.generate(validated_prompt) → raw_answer
  │
  ├─ ExplainabilityBuilder.build(
  │     authorized_chunks, raw_answer, denied_count, route_decision
  │   ) → citations, confidence, trace
  │
  ├─ AuditService.log(query_event) [non-blocking]
  │
  └─ return QueryResponse { answer, citations, confidence, trace }
```

### 11.2 Ingestion Flow

```
Client (Admin)
  │ POST /ingest { path, source_type, metadata... }
  │
  ▼
FastAPI Route (api/routes/ingest.py)
  │ Pydantic validation
  │ get_current_user + require_role("Admin")
  ▼
IngestionService.ingest_async(request, requesting_user)
  │ → acknowledge response immediately
  │
  ▼ [Background]
  ├─ validate_path(request.path)
  ├─ Loader[source_type].load(request.path) → raw_text
  ├─ Chunker.chunk(raw_text) → chunk_list
  ├─ for chunk in chunk_list:
  │     chunk.metadata = build_metadata(request)
  │     vector = EmbeddingModel.encode(chunk.text)
  │     FAISS.add(vector, chunk.id)
  │     BM25.add(chunk.text)
  │     MetadataStore.save(chunk)
  └─ AuditService.log(ingest_event)
```

### 11.3 Authorization Flow

```
Request with JWT
  │
  ├─ Decode JWT → { user_id, role, exp }
  ├─ Check exp → expired? → 401
  ├─ Check signature → invalid? → 401
  ├─ Inject CurrentUser(user_id, role) into request context
  │
  ├─ Route-level role check (deps.py: require_role(allowed_roles)):
  │     current_user.role in allowed_roles? → proceed
  │     else → 403
  │
  └─ Chunk-level RBAC filter (security/rbac.py):
        for each candidate chunk:
          current_user.role in chunk.allowed_roles? → authorized
          else → denied, increment denied_count
```

---

## 12. Scalability Considerations

### 12.1 Horizontal API Scaling

The FastAPI backend is stateless by design. Multiple replicas can be deployed behind a load balancer. Session state is carried in JWTs; no sticky sessions are required.

In Kubernetes: increase `backend.yaml` replica count. Requires a shared PVC for the FAISS index.

### 12.2 FAISS Index Scaling

FAISS operates on a single-process in-memory index backed by on-disk persistence. Scaling considerations:

| Scenario | Approach |
|---|---|
| Single-node | Local filesystem, no change |
| Multi-replica (Kubernetes) | Shared PVC (ReadWriteMany); ingestion writes must be serialized via locking or leader election |
| Very large index (> millions of chunks) | Consider migrating to a managed vector database (see §14) |

### 12.3 Retrieval Scaling

BM25 and FAISS retrieval are CPU-bound. Scaling options:

- Horizontal API replicas each hold their own in-memory index loaded from shared storage.
- Retrieval operations are read-only and parallelizable.

### 12.4 Ingestion Scaling

Ingestion is write-heavy. Concurrent ingestion from multiple replicas risks index corruption without write locking. In v1.0.0, ingestion is assumed to be a low-frequency administrative operation. High-throughput ingestion requires a dedicated ingestion worker with exclusive index write access.

---

## 13. Failure Handling

### 13.1 Degraded Retrieval

| Failure | Behavior |
|---|---|
| FAISS index empty or unavailable | Fall back to BM25-only retrieval; log warning; note in trace |
| BM25 index empty or unavailable | Fall back to FAISS-only retrieval; log warning; note in trace |
| Both indexes empty | Return `"Insufficient authorized data available."` |
| Reranker unavailable | Fall back to fused score ordering; log warning |

### 13.2 Missing Documents

If `POST /ingest` references a non-existent file path: return HTTP 404 immediately, no background pipeline started, audit log entry written.

### 13.3 Unauthorized Access

- Invalid/expired JWT → HTTP 401, audit log entry written.
- Valid JWT, insufficient role → HTTP 403, audit log entry written.
- RBAC filter removes all chunks → return `"Insufficient authorized data available."` with `denied_count` in trace.

### 13.4 Ingestion Failures

Failures during background ingestion (parse errors, embedding errors, index write errors):
- Error captured in audit log with stack trace summary.
- Application log entry at ERROR level.
- No automatic retry in v1.0.0.

### 13.5 Monitoring Failures

Prometheus or Grafana unavailability:
- Has no effect on backend API operation.
- Application logs continue to function.
- Alert: monitoring gap creates operational blindness; operators should alert on scrape failures.

### 13.6 LLM Provider Failure

- LLM API call failure → HTTP 503 returned to client.
- Retrieval trace is still populated (retrieval succeeded).
- Audit log entry records LLM failure.
- No cached response mechanism in v1.0.0.

---

## 14. Future Enhancements

These enhancements are consistent with the current architecture and technology choices. They do not introduce speculative or unrelated capabilities.

| Enhancement | Rationale | Alignment |
|---|---|---|
| JWT token refresh endpoint | Improves UX; eliminates forced re-login on expiry | Extends existing JWT auth |
| Identity provider (IdP) / SSO integration | Replaces `DEMO_USERS` with enterprise-grade identity management | Extends `security/auth.py` |
| Managed vector database (e.g., Weaviate, Qdrant) | Enables multi-replica index access without shared-volume complexity | Replaces FAISS; retrieval module is designed for extensibility |
| Department-specific sub-indexes | Allows more precise source routing by department | Extends source router and FAISS indexer |
| Token-level streaming responses | Improves perceived latency for long answers | Extends `generation` module with streaming yield |
| Document deletion and index rebuild | Enables full data lifecycle management | Extends ingestion pipeline |
| Ingestion retry queue | Improves reliability of background ingestion pipeline | Extends async ingestion worker |
| Configurable chunking parameters via API | Allows per-source-type tuning without code change | Extends ingestion request schema |
| Grafana dashboard JSON provisioning | Pre-built dashboards auto-loaded on Docker Compose startup | Extends `deploy/prometheus.yml` configuration |
| Prompt template versioning | Enables controlled rollout of prompt strategy changes | Extends `examples/prompts/` structure |
