# Enterprise Secure Multi-Source RAG Intelligence Platform

Production-oriented secure RAG platform with strict RBAC, FAISS-backed hybrid retrieval, multi-source ingestion, grounded generation, explainability, audit logging, and cloud deployment assets.

## Folder Structure

```text
backend/app/
  ingestion/        PDF, CSV, JSON, SQL loaders; metadata and chunking
  retrieval/        vector store, hybrid search, reranking, routing, metadata filters
  security/         JWT auth, RBAC, policy engine, permissions, audit logger
  generation/       prompts, citations, confidence, hallucination guard, response generation
  explainability/   trace, provenance, confidence exports
  observability/    Prometheus metrics
  api/              FastAPI routes and dependencies
frontend/
  app/              Next.js App Router pages
  components/       Shell, trace panel, confidence indicator
  lib/              API client and session helpers
examples/
  data/             Seed CSV, JSON, and knowledge-base files
  policies/         Example RBAC policy
  prompts/          Router and grounded-generation prompts
deploy/
  k8s/              Kubernetes manifests
docs/               Architecture, API, and security docs
```

## Quick Start

Linux/macOS:

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

Windows PowerShell:

```powershell
copy .env.example .env
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In another shell:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Demo Workflow

1. Login as `admin` with `admin-change-me`.
2. Go to Upload and index `examples/data/finance_controls.csv` for `Finance,Compliance`.
3. Ask `Summarize Q4 finance compliance findings`.
4. Sign out and login as `eng_user` with `engineering-change-me`.
5. Ask `Show payroll data`.
6. The system refuses with `Insufficient authorized data available.` and logs the attempt.

To index all bundled examples into the local FAISS store:

```bash
cd backend
python -m app.scripts.ingest_examples
```

## Core Security Design

RBAC filtering occurs in `HybridRetriever.retrieve()` before reranking and generation. Denied chunks are never passed to `PromptBuilder`, so unauthorized documents cannot leak through the LLM context window.

Policy checks require:

- role intersection with `allowed_roles`
- matching department or global document
- principal clearance greater than or equal to `sensitivity_level`

## Retrieval Pipeline

1. Query router classifies task type and source families.
2. Dense FAISS search and keyword search run over indexed chunks.
3. Reciprocal rank fusion combines results.
4. Source routing narrows candidate sources.
5. RBAC filter removes unauthorized chunks.
6. Reranker orders authorized chunks.
7. Generator answers only from authorized context and emits citations.

## FAISS Vector Storage

The project uses `langchain_community.vectorstores.FAISS` with `sentence-transformers/all-MiniLM-L6-v2` via HuggingFace embeddings. This avoids the Windows `chroma-hnswlib` build-tool issue and keeps the hackathon setup lightweight.

Vectors persist locally in:

```text
runtime/faiss_index/
```

On ingestion, the backend chunks documents, attaches metadata/RBAC tags, embeds chunks, upserts them into FAISS, and calls `save_local()`. On startup, the vector store calls `load_local()` when the index exists.

## Deployment

Docker Compose:

```bash
docker compose up --build
```

Kubernetes:

```bash
kubectl apply -f deploy/k8s/secrets.example.yaml
kubectl apply -f deploy/k8s/backend.yaml
kubectl apply -f deploy/k8s/frontend.yaml
```

Prometheus scrapes `/metrics`; Grafana runs on port `3001` in Compose.

## Testing

```bash
pip install -r backend/requirements.txt
pytest backend/tests
```

Tests cover RBAC denial, Admin override, authorized citations, and hallucination-prevention refusal.

## Production Improvements

- Swap demo auth for enterprise OIDC/SAML with SCIM-driven group sync.
- Use managed FAISS-compatible artifact storage or a hosted vector database with private networking for larger deployments.
- Add OCR image extraction for scanned PDFs using Tesseract workers.
- Add SQL query generation behind an allowlisted semantic layer.
- Add OpenTelemetry traces exported to a managed collector.
- Move policies to OPA/Rego with approval workflow and policy tests.
- Add async ingestion workers using Celery, Dramatiq, or managed queues.
