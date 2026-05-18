# Requirements Document
**Project:** Enterprise RAG Intelligence
**Version:** 1.0.0
**Status:** Draft — For Engineering Review
**Last Updated:** 2026
**Maintainer:** Anand Raj (@anan5093)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Product Overview](#2-product-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Security Requirements](#5-security-requirements)
6. [System Constraints](#6-system-constraints)
7. [External Interfaces](#7-external-interfaces)
8. [Acceptance Criteria](#8-acceptance-criteria)
9. [Risks and Assumptions](#9-risks-and-assumptions)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) documents the complete functional and non-functional requirements for the **Enterprise RAG Intelligence** platform. It serves as the authoritative reference for engineering, product, security, and operations teams throughout the development and maintenance lifecycle.

### 1.2 Scope

Enterprise RAG Intelligence is a full-stack Retrieval-Augmented Generation (RAG) platform designed for organizations that require controlled, auditable, and explainable AI-driven access to internal knowledge bases. The system encompasses:

- A Python/FastAPI backend exposing a REST API for authentication, document ingestion, hybrid retrieval, and grounded generation.
- A Next.js frontend providing chat, upload, and admin monitoring interfaces.
- A security layer enforcing RBAC-first filtering prior to LLM prompt construction.
- An observability stack using Prometheus metrics with optional Grafana dashboards.
- Deployment targets: local development, Docker Compose, and Kubernetes.

Out of scope for v1.0.0: real-time streaming responses, federated identity provider (IdP) integration, multi-tenancy at the database level, and fine-tuning of foundation models.

### 1.3 Intended Audience

| Audience | Usage |
|---|---|
| Backend Engineers | Implement API, retrieval, and security layers |
| Frontend Engineers | Implement chat, upload, and admin UIs |
| DevOps / Platform Engineers | Implement containerization and Kubernetes deployment |
| Security Engineers | Review and validate RBAC, audit, and threat model |
| QA Engineers | Derive test cases from functional requirements |
| Technical Product Managers | Prioritize and track implementation progress |
| Enterprise Architects | Evaluate integration with existing infrastructure |

### 1.4 Definitions and Acronyms

| Term | Definition |
|---|---|
| RAG | Retrieval-Augmented Generation — an AI architecture that grounds LLM outputs in retrieved document chunks |
| RBAC | Role-Based Access Control — permission model restricting resource access by user role |
| JWT | JSON Web Token — a signed, self-contained token used for stateless authentication |
| FAISS | Facebook AI Similarity Search — a library for efficient dense vector similarity search |
| BM25 | Best Match 25 — a probabilistic keyword-based ranking algorithm |
| Hybrid Retrieval | Combination of dense vector search and BM25 sparse search |
| Reranking | A second-stage relevance pass that reorders retrieved chunks by query relevance |
| Chunk | A discrete unit of document content produced by the ingestion pipeline's chunking stage |
| Trace | Structured metadata attached to a query response describing routing, RBAC decisions, and retrieval details |
| Confidence Score | A normalized scalar (0–1) indicating the system's estimated reliability of a generated answer |
| Ingestion | The pipeline that loads, parses, chunks, embeds, and indexes source documents |
| Guardrails | Mechanisms that detect and suppress hallucinated or unsupported claims |
| Audit Log | An immutable, timestamped record of security-relevant events |
| Prometheus | An open-source metrics collection and alerting system |
| Grafana | An open-source metrics visualization dashboard |

---

## 2. Product Overview

### 2.1 System Goals

1. Provide enterprise users with an AI assistant that answers questions exclusively from authorized, organization-owned documents.
2. Enforce access control at the retrieval layer so that the LLM never receives evidence the requesting user is not authorized to see.
3. Produce fully grounded, cited responses with explicit confidence scores and retrieval traces to support auditability and user trust.
4. Enable administrators to ingest documents from multiple common enterprise formats (CSV, JSON, PDF, DOCX, SQL, Markdown/text) with lineage metadata.
5. Deliver operational visibility through structured logs, Prometheus metrics, and an admin monitoring dashboard.
6. Support deployment in local, containerized, and Kubernetes environments without code changes.

### 2.2 Key Business Value

- **Risk reduction**: Pre-generation RBAC filtering eliminates the risk of the LLM inadvertently summarizing restricted content in mixed-user deployments.
- **Trust and compliance**: Every answer is traceable to specific source chunks; the system refuses to answer when authorized evidence is insufficient.
- **Operational efficiency**: Multi-format ingestion and self-service upload reduce the overhead of maintaining a curated knowledge base.
- **Auditability**: Structured audit logs and trace metadata satisfy internal and regulatory audit requirements.

### 2.3 Enterprise AI Use Cases

- Internal helpdesk over HR, policy, and compliance documents.
- Engineering knowledge base search over internal wikis and documentation.
- Compliance query interface for regulatory and audit documents.
- Security operations assistant over alert and incident data.
- Finance analytics Q&A over internal financial datasets.

### 2.4 Problems Solved

| Problem | Solution |
|---|---|
| LLM leaks restricted data in shared deployments | RBAC filtering applied before prompt construction |
| Hallucinated answers with no source traceability | Extractive, citation-backed generation with guardrails |
| Difficulty ingesting diverse enterprise document formats | Unified ingestion pipeline supporting 6 source types |
| No visibility into AI system behavior | Prometheus metrics, structured audit logs, trace metadata |
| Complex enterprise deployment | Docker Compose and Kubernetes manifests included |

---

## 3. Functional Requirements

Requirements are grouped by module. Each requirement uses the following notation:

- **ID**: `<MODULE>-<NNN>`
- **Priority**: P1 (Must Have) · P2 (Should Have) · P3 (Nice to Have)

---

### 3.1 Authentication Module

#### AUTH-001 — User Login

| Field | Detail |
|---|---|
| **Description** | The system shall authenticate users by validating a username/password credential pair and issuing a signed JWT access token on success. |
| **Priority** | P1 |
| **Inputs** | `POST /login` body: `{ "username": string, "password": string }` |
| **Outputs** | `{ "access_token": string, "token_type": "bearer" }` |
| **Failure Conditions** | Invalid credentials → HTTP 401. Missing fields → HTTP 422. |
| **Security Considerations** | Passwords must not be logged. Tokens must be short-lived. Demo credentials (`DEMO_USERS` in `auth.py`) must be replaced before production deployment. |

#### AUTH-002 — JWT Token Validation

| Field | Detail |
|---|---|
| **Description** | Every protected endpoint shall validate the `Authorization: Bearer <token>` header before processing. Expired, malformed, or tampered tokens must be rejected. |
| **Priority** | P1 |
| **Inputs** | HTTP `Authorization` header on every protected request |
| **Outputs** | Decoded user identity and role claims if valid; HTTP 401 if invalid |
| **Failure Conditions** | Missing header → HTTP 401. Expired token → HTTP 401. Signature mismatch → HTTP 401. |
| **Security Considerations** | JWT secret must be externalized via environment variable, never hardcoded. Token expiry must be enforced server-side. |

#### AUTH-003 — Token Expiry Enforcement

| Field | Detail |
|---|---|
| **Description** | The system shall enforce JWT expiry (`exp` claim). Expired tokens must not grant access to any endpoint. |
| **Priority** | P1 |
| **Inputs** | JWT `exp` claim |
| **Outputs** | HTTP 401 with message `"Token expired"` |
| **Failure Conditions** | Clock skew may cause edge-case rejections. |
| **Security Considerations** | Server clock must be synchronized via NTP. Token refresh mechanism is not defined in v1.0.0 (see Assumptions). |

---

### 3.2 Authorization and RBAC Module

#### RBAC-001 — Role Assignment

| Field | Detail |
|---|---|
| **Description** | Each user account shall be assigned exactly one role from the defined role set: `Admin`, `Finance`, `Engineering`, `Compliance`, `Guest`. |
| **Priority** | P1 |
| **Inputs** | User record in the identity store |
| **Outputs** | Role claim embedded in the JWT payload |
| **Failure Conditions** | User with no role assigned → deny all access. |
| **Security Considerations** | Role assignment is controlled exclusively by Admin users. |

#### RBAC-002 — Pre-Generation RBAC Filtering

| Field | Detail |
|---|---|
| **Description** | After retrieval, the system shall filter the candidate chunk set by comparing chunk `allowed_roles` metadata against the requesting user's role. Chunks the user is not authorized to see must be removed before the prompt is constructed. |
| **Priority** | P1 |
| **Inputs** | Retrieved chunk list with metadata; authenticated user role |
| **Outputs** | Filtered chunk list; `denied_count` field in trace |
| **Failure Conditions** | If all chunks are denied → response must be `"Insufficient authorized data available."` |
| **Security Considerations** | This is the primary security control. It must execute synchronously before any prompt builder code runs. Filtering logic must be unit-tested with adversarial role combinations. |

#### RBAC-003 — Admin-Only Endpoints

| Field | Detail |
|---|---|
| **Description** | The `/audit-logs` endpoint and admin dashboard data endpoints shall require the `Admin` or `Compliance` role. |
| **Priority** | P1 |
| **Inputs** | Authenticated JWT with role claim |
| **Outputs** | Authorized response or HTTP 403 |
| **Failure Conditions** | Non-admin role → HTTP 403. |
| **Security Considerations** | Role check must occur in FastAPI dependency, not in route handler logic. |

#### RBAC-004 — Ingestion Authorization

| Field | Detail |
|---|---|
| **Description** | The `/ingest` endpoint shall require the `Admin` role. Non-admin users must receive HTTP 403. |
| **Priority** | P1 |
| **Inputs** | Authenticated JWT with role claim |
| **Outputs** | Ingestion accepted or HTTP 403 |
| **Failure Conditions** | Non-admin attempts ingestion → HTTP 403, audit log entry created. |
| **Security Considerations** | Ingestion can modify the index; it is a privileged operation. |

---

### 3.3 Document Ingestion Module

#### INGEST-001 — Multi-Format Source Loading

| Field | Detail |
|---|---|
| **Description** | The ingestion pipeline shall load documents from the following source types: `csv`, `json`, `pdf`, `docx`, `sql`, `markdown`/`text`. |
| **Priority** | P1 |
| **Inputs** | `POST /ingest` body: `{ "path": string, "source_type": string, "department": string, "owner": string, "confidentiality": string, "allowed_roles": [string], "rbac_tags": [string] }` |
| **Outputs** | Ingestion confirmation with chunk count; chunks indexed in FAISS and BM25 store |
| **Failure Conditions** | Unsupported `source_type` → HTTP 400. File not found at `path` → HTTP 404. Parse error → HTTP 422 with error detail. |
| **Security Considerations** | The `path` parameter must be validated against an allowlist of directories to prevent path traversal. |

#### INGEST-002 — Chunking

| Field | Detail |
|---|---|
| **Description** | The ingestion pipeline shall split loaded document content into discrete chunks suitable for retrieval. Chunk size and overlap strategy are implementation details not yet fully defined in the repository. |
| **Priority** | P1 |
| **Inputs** | Parsed document text |
| **Outputs** | List of text chunks with position metadata |
| **Failure Conditions** | Empty document → warning logged, no chunks indexed. |
| **Security Considerations** | Chunk boundaries must not split RBAC metadata from content. |

#### INGEST-003 — Metadata Extraction and Lineage

| Field | Detail |
|---|---|
| **Description** | Each chunk shall be tagged with metadata derived from the ingestion request: `department`, `owner`, `confidentiality`, `allowed_roles`, `rbac_tags`, source file path, and ingestion timestamp. |
| **Priority** | P1 |
| **Inputs** | Ingestion request metadata fields |
| **Outputs** | Chunk metadata dict stored alongside chunk embedding |
| **Failure Conditions** | Missing required metadata fields → reject ingestion with HTTP 422. |
| **Security Considerations** | `allowed_roles` must be validated against the known role set. Unknown roles in `allowed_roles` must be rejected or flagged. |

#### INGEST-004 — Async Ingestion Pipeline

| Field | Detail |
|---|---|
| **Description** | The ingestion pipeline (loading, chunking, embedding, indexing) shall execute asynchronously per the architecture diagram. The API response shall not block on full pipeline completion. |
| **Priority** | P2 |
| **Inputs** | Validated ingestion request |
| **Outputs** | Immediate acknowledgment response; background pipeline completes asynchronously |
| **Failure Conditions** | Background failure → error captured in audit log. No retry mechanism defined in v1.0.0. |
| **Security Considerations** | Asynchronous context must preserve the requesting user's identity for audit logging. |

#### INGEST-005 — Example Data Preload

| Field | Detail |
|---|---|
| **Description** | The system shall provide a script (`app.scripts.ingest_examples`) that preloads bundled example datasets from `examples/data/` into the FAISS index. |
| **Priority** | P2 |
| **Inputs** | Example dataset files in `examples/data/` |
| **Outputs** | Populated FAISS index in `runtime/faiss_index/` |
| **Failure Conditions** | Missing example data directory → script exits with error. |
| **Security Considerations** | Example data must not contain real PII or sensitive enterprise data. |

---

### 3.4 Hybrid Retrieval Module

#### RETR-001 — Dense Vector Search (FAISS)

| Field | Detail |
|---|---|
| **Description** | The retrieval layer shall perform approximate nearest-neighbor vector search using FAISS over embedded document chunks. |
| **Priority** | P1 |
| **Inputs** | Query embedding vector; top-K parameter |
| **Outputs** | Ranked list of candidate chunks with similarity scores |
| **Failure Conditions** | Empty FAISS index → return empty candidate list; do not throw. |
| **Security Considerations** | FAISS index files in `runtime/faiss_index/` must be protected from unauthorized filesystem access. |

#### RETR-002 — Sparse BM25 Keyword Search

| Field | Detail |
|---|---|
| **Description** | The retrieval layer shall perform BM25 keyword retrieval over indexed document chunks in parallel with dense vector search. |
| **Priority** | P1 |
| **Inputs** | Tokenized query string; top-K parameter |
| **Outputs** | Ranked list of candidate chunks with BM25 scores |
| **Failure Conditions** | Empty BM25 index → return empty candidate list. |
| **Security Considerations** | BM25 index must contain only metadata required for scoring; full chunk content exposure is controlled by retrieval layer. |

#### RETR-003 — Hybrid Score Fusion

| Field | Detail |
|---|---|
| **Description** | The retrieval layer shall combine FAISS and BM25 candidate lists using a score fusion strategy (implementation detail not yet fully defined in repository — assumed to be weighted reciprocal rank fusion or linear interpolation). |
| **Priority** | P1 |
| **Inputs** | FAISS candidate list; BM25 candidate list |
| **Outputs** | Unified, deduplicated, score-ordered candidate list |
| **Failure Conditions** | One retrieval source returns empty → graceful degradation using the other source. |
| **Security Considerations** | Score fusion must not reintroduce denied chunks. |

#### RETR-004 — Reranking

| Field | Detail |
|---|---|
| **Description** | The retrieval pipeline shall apply a reranking stage to reorder the fused candidate list by relevance to the original query. Reranking model or algorithm is an implementation detail not yet fully defined in the repository. |
| **Priority** | P1 |
| **Inputs** | Fused candidate list; original query string |
| **Outputs** | Reordered candidate list |
| **Failure Conditions** | Reranker unavailable → fall back to fused score ordering without reranking; log warning. |
| **Security Considerations** | Reranking must execute on the post-RBAC-filtered chunk set to avoid leaking relevance signals from denied chunks. |

#### RETR-005 — Query Source Routing

| Field | Detail |
|---|---|
| **Description** | The query router shall classify the incoming query and route it to the appropriate retrieval source(s) or pipeline variant. Routing logic is an implementation detail not yet fully defined in the repository. |
| **Priority** | P2 |
| **Inputs** | Query string; available source metadata |
| **Outputs** | Routing decision recorded in trace metadata |
| **Failure Conditions** | Unrecognized query type → route to default hybrid pipeline. |
| **Security Considerations** | Routing decisions must be recorded in trace for auditability. |

---

### 3.5 LLM Generation Module

#### GEN-001 — Prompt Construction

| Field | Detail |
|---|---|
| **Description** | The prompt builder shall assemble a structured prompt from the user's query and the RBAC-filtered, reranked chunk set. |
| **Priority** | P1 |
| **Inputs** | Query string; authorized chunk list with text and metadata |
| **Outputs** | Constructed prompt string passed to the generator |
| **Failure Conditions** | Empty authorized chunk set → do not call LLM; return insufficient data message. |
| **Security Considerations** | Prompt templates must be defined in `examples/prompts/` and not constructed from raw user input to mitigate prompt injection. |

#### GEN-002 — Grounded Response Generation

| Field | Detail |
|---|---|
| **Description** | The generator shall produce an answer grounded exclusively in the provided authorized chunks. The LLM integration target is an implementation detail not yet fully defined in the repository. |
| **Priority** | P1 |
| **Inputs** | Constructed prompt |
| **Outputs** | Generated answer text |
| **Failure Conditions** | LLM call failure → HTTP 503 with retry guidance. |
| **Security Considerations** | LLM API credentials must be externalized via environment variables. |

#### GEN-003 — Hallucination Guard

| Field | Detail |
|---|---|
| **Description** | The generation pipeline shall include a guardrail stage that detects and suppresses claims not grounded in the retrieved chunks. |
| **Priority** | P1 |
| **Inputs** | Generated answer; source chunk list |
| **Outputs** | Validated answer or modified answer with unsupported claims removed/flagged |
| **Failure Conditions** | Guard bypass → log warning; do not surface ungrounded answer silently. |
| **Security Considerations** | Guard must execute before the response is returned to the caller. |

#### GEN-004 — Insufficient Evidence Response

| Field | Detail |
|---|---|
| **Description** | When no authorized chunks survive RBAC filtering, or when the evidence set is below the minimum confidence threshold, the system must return the literal string `"Insufficient authorized data available."` rather than hallucinating a response. |
| **Priority** | P1 |
| **Inputs** | Post-filter chunk count; confidence score |
| **Outputs** | Standardized refusal string |
| **Failure Conditions** | None — this is the explicit fallback. |
| **Security Considerations** | This response must not leak information about the existence or count of denied chunks beyond `denied_count` in the trace. |

---

### 3.6 Explainability Module

#### EXPL-001 — Citation Generation

| Field | Detail |
|---|---|
| **Description** | Every successful query response shall include a `citations` array listing the source chunks used to construct the answer, including chunk ID, source path, and relevant metadata. |
| **Priority** | P1 |
| **Inputs** | Authorized, reranked chunks used in prompt |
| **Outputs** | `citations` array in API response |
| **Failure Conditions** | No citations if no chunks were used. |
| **Security Considerations** | Citations must not expose metadata from denied chunks. |

#### EXPL-002 — Confidence Scoring

| Field | Detail |
|---|---|
| **Description** | The system shall compute and return a `confidence` score (0.0–1.0) for each query response. Scoring methodology is an implementation detail not yet fully defined in the repository. |
| **Priority** | P1 |
| **Inputs** | Reranked chunk relevance scores; chunk count; generation quality signals |
| **Outputs** | `confidence` float in API response |
| **Failure Conditions** | Unable to compute → return `null` with warning in trace. |
| **Security Considerations** | Confidence must not reflect quality signals derived from denied chunks. |

#### EXPL-003 — Retrieval Trace Metadata

| Field | Detail |
|---|---|
| **Description** | The system shall include a `trace` object in every query response containing: routing decision, authorized chunk IDs, `denied_count`, filters applied, and retrieval stage timings. |
| **Priority** | P1 |
| **Inputs** | All pipeline stage decisions and outputs |
| **Outputs** | `trace` object in API response |
| **Failure Conditions** | Partial trace (e.g., reranker failed) → include available trace fields; mark missing fields as `null`. |
| **Security Considerations** | `denied_count` is permitted; denied chunk IDs or content must never appear in the trace. |

---

### 3.7 Audit Logging Module

#### AUDIT-001 — Query Audit Events

| Field | Detail |
|---|---|
| **Description** | The system shall write a structured audit log entry for every query request containing: timestamp, user identity, role, query text, `denied_count`, confidence, and response outcome. |
| **Priority** | P1 |
| **Inputs** | Query request context; pipeline execution results |
| **Outputs** | Audit log entry persisted to audit store |
| **Failure Conditions** | Audit write failure must not fail the query response (non-blocking). Failure must be captured in application log at ERROR level. |
| **Security Considerations** | Audit logs must be append-only. Users must not be able to modify or delete their own audit records. |

#### AUDIT-002 — Ingestion Audit Events

| Field | Detail |
|---|---|
| **Description** | The system shall write an audit log entry for every ingestion request containing: timestamp, admin user identity, source path, source type, metadata applied, and outcome. |
| **Priority** | P1 |
| **Inputs** | Ingestion request context; pipeline outcome |
| **Outputs** | Audit log entry |
| **Failure Conditions** | Same as AUDIT-001. |
| **Security Considerations** | Ingestion audit records are critical for lineage tracing. |

#### AUDIT-003 — Authentication Audit Events

| Field | Detail |
|---|---|
| **Description** | The system shall write an audit log entry for every login attempt (success and failure), capturing: timestamp, username, outcome, and source IP (if available). |
| **Priority** | P1 |
| **Inputs** | Login request context |
| **Outputs** | Audit log entry |
| **Failure Conditions** | Same as AUDIT-001. |
| **Security Considerations** | Failed login accumulation can indicate brute-force; rate limiting (SEC-006) complements this. |

#### AUDIT-004 — Audit Log Retrieval Endpoint

| Field | Detail |
|---|---|
| **Description** | `GET /audit-logs` shall return paginated audit log entries. Access restricted to `Admin` and `Compliance` roles. |
| **Priority** | P1 |
| **Inputs** | Authenticated request with optional pagination parameters |
| **Outputs** | Array of audit log records |
| **Failure Conditions** | Non-authorized role → HTTP 403. |
| **Security Considerations** | Audit log contents may include sensitive query text; endpoint must enforce TLS in production. |

---

### 3.8 Observability Module

#### OBS-001 — Prometheus Metrics Endpoint

| Field | Detail |
|---|---|
| **Description** | The FastAPI backend shall expose a `/metrics` endpoint in Prometheus exposition format. |
| **Priority** | P1 |
| **Inputs** | HTTP `GET /metrics` (unauthenticated in development; should be network-restricted in production) |
| **Outputs** | Prometheus-format text response |
| **Failure Conditions** | Metrics collection failure must not affect API availability. |
| **Security Considerations** | In production, `/metrics` must be restricted to the Prometheus scrape network via network policy or reverse proxy rules. |

#### OBS-002 — Health Check Endpoint

| Field | Detail |
|---|---|
| **Description** | The backend shall expose a `/health` endpoint returning service health status. Used by Docker Compose health check and Kubernetes liveness/readiness probes. |
| **Priority** | P1 |
| **Inputs** | HTTP `GET /health` |
| **Outputs** | `{ "status": "ok" }` or degraded status with component details |
| **Failure Conditions** | Critical dependency failure → return non-200 status to trigger orchestrator restart. |
| **Security Considerations** | Health endpoint must not expose internal configuration or secrets. |

#### OBS-003 — Grafana Dashboard Integration

| Field | Detail |
|---|---|
| **Description** | Docker Compose stack shall include a Grafana service pre-configured to scrape the Prometheus instance. |
| **Priority** | P2 |
| **Inputs** | `prometheus.yml` scrape config; Grafana data source config |
| **Outputs** | Accessible Grafana UI at `http://localhost:3001` |
| **Failure Conditions** | Grafana unavailability must not affect backend or frontend operation. |
| **Security Considerations** | Default Grafana credentials (`admin`/`admin`) must be changed before any non-local deployment. |

---

### 3.9 Admin Dashboard Module

#### ADMIN-001 — Audit Log Viewer

| Field | Detail |
|---|---|
| **Description** | The frontend admin dashboard shall render paginated audit log entries fetched from `GET /audit-logs`. |
| **Priority** | P1 |
| **Inputs** | Authenticated admin/compliance session; API audit log response |
| **Outputs** | Rendered audit log table in frontend |
| **Failure Conditions** | API unavailable → display error state; do not silently show stale data. |
| **Security Considerations** | Admin dashboard routes must validate session role on the frontend and re-validate at the API level. |

#### ADMIN-002 — Metrics Visibility

| Field | Detail |
|---|---|
| **Description** | The admin dashboard shall provide a link or embedded view to the Grafana monitoring dashboard. |
| **Priority** | P3 |
| **Inputs** | Grafana URL configuration |
| **Outputs** | Navigation link in admin UI |
| **Failure Conditions** | Grafana unavailable → display informational message. |
| **Security Considerations** | Grafana access must be independently authenticated. |

---

### 3.10 Frontend Chat Module

#### CHAT-001 — Query Submission

| Field | Detail |
|---|---|
| **Description** | The chat UI shall allow authenticated users to submit natural-language queries and display the response including `answer`, `citations`, and `confidence`. |
| **Priority** | P1 |
| **Inputs** | User query text; session JWT |
| **Outputs** | Rendered answer with citations and confidence indicator |
| **Failure Conditions** | API error → display user-friendly error message. Insufficient data response → display accordingly. |
| **Security Considerations** | JWT must be sent in the `Authorization` header, not as a URL parameter or cookie without Secure/HttpOnly flags. |

#### CHAT-002 — Trace Visualization

| Field | Detail |
|---|---|
| **Description** | The chat UI shall optionally display the trace metadata from the query response (routing decision, authorized chunk count, denied count). |
| **Priority** | P2 |
| **Inputs** | `trace` field from query API response |
| **Outputs** | Collapsible trace panel in the chat interface |
| **Failure Conditions** | Missing trace data → hide trace panel. |
| **Security Considerations** | Trace data shown to non-admin users must not include any denied chunk content. |

---

### 3.11 Frontend Upload Module

#### UPLOAD-001 — Document Upload Interface

| Field | Detail |
|---|---|
| **Description** | The upload UI shall allow admin users to specify a file path, source type, and RBAC metadata, and submit an ingestion request to `POST /ingest`. |
| **Priority** | P1 |
| **Inputs** | Upload form fields; admin JWT |
| **Outputs** | Ingestion confirmation or error message |
| **Failure Conditions** | API error → display error detail. Non-admin → redirect or disable form. |
| **Security Considerations** | Upload UI must be gated behind admin role check. |

---

### 3.12 API Endpoints Summary

| Endpoint | Method | Auth Required | Role Required | Description |
|---|---|---|---|---|
| `/login` | POST | No | — | Authenticate and receive JWT |
| `/query` | POST | Yes | Any authenticated | Submit RAG query |
| `/ingest` | POST | Yes | Admin | Ingest a document source |
| `/audit-logs` | GET | Yes | Admin, Compliance | Retrieve audit log entries |
| `/health` | GET | No | — | Service health check |
| `/metrics` | GET | No (network-restrict in prod) | — | Prometheus metrics |
| `/docs` | GET | No (disable in prod) | — | FastAPI interactive API docs |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-PERF-001 | End-to-end query API latency (p95) | < 3 seconds under normal load (assumption; not defined in repository) |
| NFR-PERF-002 | Document ingestion throughput | Capable of processing typical enterprise documents (< 100 pages) within 60 seconds per document (assumption) |
| NFR-PERF-003 | FAISS index query latency | < 100ms for top-K retrieval on indexes up to 100K chunks (assumption) |
| NFR-PERF-004 | Metrics endpoint latency | < 50ms |

### 4.2 Scalability

| ID | Requirement |
|---|---|
| NFR-SCALE-001 | Backend API must be stateless to support horizontal scaling behind a load balancer |
| NFR-SCALE-002 | FAISS index must be persistable to shared storage to support multi-replica API pods in Kubernetes |
| NFR-SCALE-003 | Ingestion pipeline must support concurrent ingestion jobs without index corruption (locking strategy is an implementation detail not yet defined in repository) |

### 4.3 Availability

| ID | Requirement |
|---|---|
| NFR-AVAIL-001 | Backend health check endpoint must respond within 2 seconds for liveness probe compliance |
| NFR-AVAIL-002 | Single-instance deployment target: best-effort uptime. HA configuration requires Kubernetes with replicas ≥ 2 |
| NFR-AVAIL-003 | Observability stack (Prometheus, Grafana) failure must not cause API unavailability |

### 4.4 Security

| ID | Requirement |
|---|---|
| NFR-SEC-001 | All API communication must be over TLS in staging and production environments |
| NFR-SEC-002 | JWT secrets, LLM API keys, and database credentials must not be hardcoded; must be injected via environment variables or Kubernetes secrets |
| NFR-SEC-003 | Demo credentials in `auth.py` (`DEMO_USERS`) must be replaced before any shared or production deployment |
| NFR-SEC-004 | RBAC filtering must occur before prompt construction on every query request without exception |

### 4.5 Compliance

| ID | Requirement |
|---|---|
| NFR-COMP-001 | All query, ingestion, and authentication events must be captured in the audit log |
| NFR-COMP-002 | Audit logs must be retained for a minimum period defined by the organization's data retention policy (implementation detail not yet defined in repository) |
| NFR-COMP-003 | System must support RBAC metadata on all indexed documents to enable access-controlled data segregation |

### 4.6 Observability

| ID | Requirement |
|---|---|
| NFR-OBS-001 | Prometheus metrics must be exposed at `/metrics` in standard exposition format |
| NFR-OBS-002 | Application must emit structured logs (JSON format) to support log aggregation pipelines |
| NFR-OBS-003 | All pipeline stage timings must be measurable via trace metadata and/or Prometheus histograms |

### 4.7 Reliability

| ID | Requirement |
|---|---|
| NFR-REL-001 | Retrieval failures in one source (FAISS or BM25) must degrade gracefully to the other source |
| NFR-REL-002 | Audit log write failures must not fail the query response |
| NFR-REL-003 | Reranker unavailability must fall back to fused score ordering |

### 4.8 Maintainability

| ID | Requirement |
|---|---|
| NFR-MAINT-001 | Backend must maintain modular structure: `api`, `core`, `ingestion`, `retrieval`, `security`, `generation`, `explainability`, `observability` |
| NFR-MAINT-002 | Frontend must maintain modular structure: `login`, `chat`, `upload`, `admin` |
| NFR-MAINT-003 | All public modules must have corresponding unit tests |

### 4.9 Extensibility

| ID | Requirement |
|---|---|
| NFR-EXT-001 | Ingestion pipeline must be extensible to support new source formats via new loader modules without modifying core pipeline logic |
| NFR-EXT-002 | Retrieval layer must be extensible to support alternative vector stores or ranking algorithms |

### 4.10 API Latency Expectations

These are engineering assumptions in the absence of explicit targets in the repository:

| Scenario | Target (p95) |
|---|---|
| Login | < 200ms |
| Query (end-to-end, with LLM) | < 5s |
| Query (retrieval only, no LLM) | < 500ms |
| Audit log fetch (paginated) | < 500ms |
| Health check | < 100ms |

---

## 5. Security Requirements

### 5.1 JWT Authentication

- SEC-001: JWTs must be signed with a secret of at least 256 bits. Signing algorithm must be `HS256` or stronger.
- SEC-002: JWT expiry (`exp` claim) must be set to a short window (e.g., 1 hour). Implementation detail: exact expiry not defined in repository.
- SEC-003: JWT secrets must be injected via environment variable (`JWT_SECRET` or equivalent), never committed to source control.

### 5.2 RBAC Pre-Filtering

- SEC-004: RBAC filtering must execute as a synchronous step in the query pipeline before the prompt builder receives any chunk content.
- SEC-005: RBAC logic must be implemented in the `security` module and invoked via a dedicated FastAPI dependency.

### 5.3 Rate Limiting

- SEC-006: The `core` module includes rate limiting support. Rate limits must be applied to `/login` to prevent credential stuffing and to `/query` to prevent abuse. Rate limit thresholds are implementation details not yet defined in the repository.

### 5.4 Prompt Injection Mitigation

- SEC-007: Prompt templates must be static or parameterized structures defined in `examples/prompts/`. User query text must be inserted as a bounded, labeled parameter, not interpolated into instruction sections of the prompt.
- SEC-008: The guardrail stage (GEN-003) provides a secondary defense against injection-induced hallucination.

### 5.5 Data Isolation

- SEC-009: Documents with `confidentiality: "confidential"` and restricted `allowed_roles` must never appear in responses to users whose role is not in the `allowed_roles` list.
- SEC-010: Chunk content must not be exposed in trace or error responses.

### 5.6 Audit Logging

- SEC-011: Audit logs are append-only. No API endpoint permits modification or deletion of audit records.
- SEC-012: Audit log access is restricted to `Admin` and `Compliance` roles.

### 5.7 Secure Ingestion

- SEC-013: The `path` parameter in ingestion requests must be validated against an allowlist of safe directories to prevent path traversal attacks.
- SEC-014: `allowed_roles` metadata values must be validated against the known role enumeration.

### 5.8 Secure Deployment

- SEC-015: Kubernetes secrets must be used for all sensitive configuration in Kubernetes deployments (see `deploy/k8s/secrets.example.yaml`).
- SEC-016: Grafana default credentials (`admin`/`admin`) must be changed before any non-local deployment.
- SEC-017: `/docs` (FastAPI Swagger UI) must be disabled or network-restricted in production environments.
- SEC-018: `/metrics` must be restricted to the internal Prometheus scrape network in production.

### 5.9 Input Validation

- SEC-019: All API inputs must be validated using Pydantic models. Validation failures must return HTTP 422 with structured error details, never unhandled 500 errors.
- SEC-020: Query text length must be bounded to prevent token overflow attacks on the LLM.

---

## 6. System Constraints

### 6.1 Technical Constraints

| Constraint | Detail |
|---|---|
| Python version | 3.12 required |
| Node.js version | 22 required |
| Vector store | FAISS only in v1.0.0; no managed vector DB |
| Identity provider | Demo user store in `auth.py` only; no IdP/SSO integration in v1.0.0 |
| LLM provider | Integration target not specified in repository; assumed to be a configurable external LLM API |
| FAISS persistence | Index stored on local filesystem at `runtime/faiss_index/`; shared volume required for multi-replica deployments |
| Token refresh | No token refresh endpoint defined in v1.0.0 |
| Database | No relational database specified; audit log and metadata persistence mechanism not fully defined in repository |

### 6.2 Deployment Assumptions

- Local development requires manual FAISS index creation via example data script or manual ingestion.
- Docker Compose is the recommended full-stack development environment.
- Kubernetes deployment assumes an existing cluster with `kubectl` access.
- No CI/CD pipeline is specified in the repository beyond the GitHub Actions CI badge (workflow: `ci.yml`). CI/CD pipeline design is out of scope for this document.

### 6.3 Dependency Assumptions

- Python dependencies are managed via `backend/requirements.txt`. Exact library versions are not reproduced here.
- Frontend dependencies are managed via `package.json` under `frontend/`.
- The LLM API client library is assumed to be included in `requirements.txt` but is not explicitly named in the repository README.

---

## 7. External Interfaces

### 7.1 FastAPI REST API

- Base URL (local): `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs` (development only)
- Content type: `application/json`
- Authentication: `Authorization: Bearer <JWT>` header

### 7.2 Frontend (Next.js)

- Frontend URL (local): `http://localhost:3000`
- Communicates with backend via `NEXT_PUBLIC_API_BASE_URL` environment variable.
- Session management: implementation detail not fully defined in repository (assumed JWT stored in memory or httpOnly cookie).

### 7.3 Prometheus Metrics

- Endpoint: `http://localhost:8000/metrics`
- Scrape config: `deploy/prometheus.yml`
- Format: Prometheus text exposition format

### 7.4 Grafana

- URL (Docker Compose): `http://localhost:3001`
- Default credentials: `admin` / `admin` (must be changed before shared use)
- Data source: Prometheus instance in Docker Compose network

### 7.5 Kubernetes

- Manifests: `deploy/k8s/`
- Secrets: `deploy/k8s/secrets.example.yaml` (must be replaced with real secrets before deployment)
- Services: `backend.yaml`, `frontend.yaml`

---

## 8. Acceptance Criteria

### 8.1 Query Pipeline

| Criterion | Pass Condition |
|---|---|
| Authenticated user receives a grounded response | `answer`, `citations`, `confidence`, and `trace` fields present in response |
| RBAC filtering prevents data leak | User with `Guest` role receives no `Finance`-restricted chunk content |
| Insufficient evidence fallback | Query with no authorized chunks returns `"Insufficient authorized data available."` |
| Trace includes denied count | `trace.denied_count` reflects correct count of filtered chunks |

### 8.2 Security

| Criterion | Pass Condition |
|---|---|
| Unauthenticated request rejected | `POST /query` without JWT returns HTTP 401 |
| Expired token rejected | Request with expired JWT returns HTTP 401 |
| Non-admin ingest rejected | `POST /ingest` with `fin_user` JWT returns HTTP 403 |
| Non-admin audit log access rejected | `GET /audit-logs` with `eng_user` JWT returns HTTP 403 |
| RBAC filter is pre-generation | Denied chunks never appear in `answer` or `citations` |

### 8.3 Retrieval

| Criterion | Pass Condition |
|---|---|
| Hybrid retrieval returns results | Query against populated index returns non-empty candidate list |
| FAISS-only fallback | BM25 index disabled → query succeeds using dense results only |
| BM25-only fallback | FAISS index empty → query succeeds using BM25 results only |

### 8.4 Explainability

| Criterion | Pass Condition |
|---|---|
| Citations present | Every non-empty response includes at least one citation |
| Confidence score bounded | `confidence` value is between 0.0 and 1.0 inclusive |
| Trace routing field present | `trace.route` or equivalent field populated in response |

### 8.5 Deployment

| Criterion | Pass Condition |
|---|---|
| Docker Compose stack starts | All four services start; backend health check passes before frontend starts |
| Kubernetes apply succeeds | `kubectl apply` on all manifests completes without errors |
| Frontend connects to backend | Chat UI successfully submits a query and renders response |

### 8.6 Monitoring

| Criterion | Pass Condition |
|---|---|
| `/metrics` responds | HTTP 200 with Prometheus-format response body |
| `/health` responds | HTTP 200 with `{ "status": "ok" }` under normal operation |
| Grafana reachable | `http://localhost:3001` accessible after Docker Compose startup |

---

## 9. Risks and Assumptions

### 9.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| FAISS index not thread-safe under concurrent writes | Medium | High | Implement write locking; document limitation |
| LLM provider API outage | Medium | High | Implement retry logic with circuit breaker; return HTTP 503 |
| Chunk quality degradation on large PDF/DOCX files | Medium | Medium | Test chunking on representative enterprise documents |
| FAISS index file growth unbounded | Low | Medium | Implement index size monitoring; document rebuild procedure |
| JWT secret rotation causes session invalidation | Low | Medium | Document rotation procedure; short token TTL reduces impact window |

### 9.2 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Demo credentials deployed to shared environment | Medium | Critical | Pre-deployment checklist; CI check for `DEMO_USERS` in production config |
| Audit log store fills up | Low | High | Implement log rotation policy; monitor disk usage |
| `/metrics` exposed to internet | Low | Medium | Network policy enforcement in Kubernetes; documentation warning |

### 9.3 AI-Related Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hallucination guard bypass | Low | High | Multi-layer grounding: prompt design + guard + confidence threshold |
| Prompt injection via document content | Low | High | Input sanitization at ingestion; static prompt templates |
| Low-quality retrieval reduces answer quality | Medium | Medium | Monitor confidence scores; implement feedback mechanism in future |

### 9.4 Assumptions

1. An external LLM API is required and is not included in the deployment stack. API credentials are provided via environment variables.
2. The FAISS index is persisted to the local filesystem. Multi-replica Kubernetes deployments require a shared persistent volume.
3. Token refresh is not implemented in v1.0.0. Users must re-authenticate when tokens expire.
4. The audit log persistence mechanism (file, database, etc.) is not fully specified in the repository and is treated as an implementation detail.
5. TLS termination is handled by a reverse proxy or ingress controller in production; the FastAPI backend serves HTTP internally.
6. The CI workflow (`ci.yml`) runs `pytest backend/tests` and `npm run build`. CD pipeline design is the operator's responsibility.
7. Score fusion and reranking algorithm specifics are not defined in the README and are treated as implementation details within the `retrieval` module.
