# Enterprise RAG Intelligence

[![CI](https://github.com/anan5093/Enterprise-RAG-Intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/anan5093/Enterprise-RAG-Intelligence/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

Secure, enterprise-ready Retrieval-Augmented Generation (RAG) platform with RBAC-first retrieval, multi-source ingestion, explainable responses, and audit-friendly operations.

## Table of Contents

- [What this project does](#what-this-project-does)
- [Why this project is useful](#why-this-project-is-useful)
- [Project structure](#project-structure)
- [How to get started](#how-to-get-started)
- [Usage examples](#usage-examples)
- [Documentation](#documentation)
- [Where to get help](#where-to-get-help)
- [Who maintains and contributes](#who-maintains-and-contributes)
- [License](#license)

## What this project does

This project provides a full-stack secure RAG system:

- **Backend**: FastAPI service for login, ingestion, query, metrics, and audit logs.
- **Retrieval**: Hybrid vector + keyword retrieval with reranking and source routing.
- **Security**: JWT auth and pre-generation RBAC filtering so unauthorized chunks are never sent to generation.
- **Generation**: Grounded answers with citations, confidence scoring, and retrieval trace metadata.
- **Frontend**: Next.js UI for login, secure chat, source ingestion, and admin audit monitoring.

## Why this project is useful

Key benefits for enterprise AI teams:

- **Security-first data access**: RBAC checks happen before generation.
- **Grounded outputs**: answers are tied to retrieved citations.
- **Explainability by default**: trace metadata includes routing and filter decisions.
- **Multi-source ingestion**: supports CSV, JSON, PDF, DOCX, SQL, and KB-style text/markdown.
- **Operational visibility**: Prometheus metrics and structured audit logs.
- **Deployment-ready assets**: Docker, Docker Compose, and Kubernetes manifests.

## Project structure

```text
backend/app/
  api/              FastAPI routes and dependencies
  core/             app config, logging, rate limiting
  ingestion/        loaders, chunking, metadata pipeline
  retrieval/        vector store, hybrid search, reranking, routing
  security/         auth, RBAC, policy checks, audit logging
  generation/       prompt building, guardrails, response synthesis
  explainability/   provenance, confidence, trace components
  observability/    Prometheus metrics
frontend/
  app/              Next.js App Router pages (login/chat/upload/admin)
  components/       UI components (trace, dashboard, shell, cards)
  lib/              API/session utilities
examples/
  data/             sample enterprise datasets
  prompts/          prompt templates
  policies/         sample RBAC policy
deploy/
  k8s/              Kubernetes manifests
docs/
  architecture.md   architecture overview
  api.md            endpoint docs and payloads
  security.md       RBAC/security model
```

## How to get started

### Prerequisites

- Python **3.12**
- Node.js **22**
- npm

### 1) Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend base URL: `http://localhost:8000`

### 2) Start the frontend

In a new terminal:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Frontend URL: `http://localhost:3000`

### 3) (Optional) Preload bundled example data

```bash
cd backend
python -m app.scripts.ingest_examples
```

This writes/updates the local FAISS index under `runtime/faiss_index/`.

### 4) Run checks

From repository root:

```bash
pytest backend/tests
cd frontend && npm run build
```

## Usage examples

### Login and query via API

> ⚠️ Demo credentials shown below are for local development only and must be replaced before any shared or production deployment.

```bash
# Login
curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin-change-me"}'

# Copy the access_token value from the response and export it
export TOKEN="<PASTE_ACCESS_TOKEN>"

# Query
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Show critical security alerts"}'
```

### Ingest a source

```bash
curl -s -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"path":"examples/data/security_alerts.json","source_type":"json","department":"compliance","owner":"compliance","confidentiality":"confidential","allowed_roles":["Admin","Compliance"],"rbac_tags":["compliance","alerts"]}'
```

### Run with Docker Compose

```bash
docker compose up --build
```

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Security](docs/security.md)
- [Deployment manifests](deploy/k8s/)

## Where to get help

- Open a repository issue with reproduction steps and logs.
- Check `docs/api.md` for endpoint payloads and response formats.
- Check `docs/security.md` for RBAC behavior and denial semantics.
- Check `docs/architecture.md` for pipeline design and component responsibilities.

## Who maintains and contributes

### Maintainer

- [Anand Raj (@anan5093)](https://github.com/anan5093)

### Contributing

Contributions are welcome via pull requests:

1. Fork the repository.
2. Create a feature branch.
3. Run backend tests and frontend build locally.
4. Submit a PR with a clear summary and validation notes.

If you plan a major change, please open an issue first to align on scope.

## License

This repository currently does not include a `LICENSE` file.
Until a license is explicitly published, treat all rights as reserved by the repository owner.
