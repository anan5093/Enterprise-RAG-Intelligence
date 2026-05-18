# Enterprise RAG Intelligence

[![CI](https://github.com/anan5093/Enterprise-RAG-Intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/anan5093/Enterprise-RAG-Intelligence/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Enterprise RAG Intelligence is a full-stack, security-first Retrieval-Augmented Generation (RAG) platform for internal enterprise knowledge. It combines RBAC-aware retrieval, grounded answer generation with citations, and a web UI for chat, ingestion, and audit visibility.

## Table of Contents

- [What the project does](#what-the-project-does)
- [Why the project is useful](#why-the-project-is-useful)
- [How users can get started](#how-users-can-get-started)
- [Usage examples](#usage-examples)
- [Where users can get help](#where-users-can-get-help)
- [Who maintains and contributes](#who-maintains-and-contributes)
- [License](#license)

## What the project does

This repository provides an enterprise-ready secure RAG system:

- **Backend (FastAPI)**: authentication, ingestion, query pipeline, health, metrics, and audit endpoints
- **Security model**: JWT auth + role-based access control (RBAC) filtering before prompt construction
- **Retrieval pipeline**: hybrid retrieval (dense + BM25), query routing, reranking, trace metadata
- **Generation layer**: grounded responses with citations and confidence scoring
- **Frontend (Next.js)**: login, secure chat, source ingestion, and admin/audit pages
- **Ops assets**: Dockerfiles, `docker-compose.yml`, Kubernetes manifests, Prometheus config

See [docs/architecture.md](docs/architecture.md) and [docs/security.md](docs/security.md) for deeper design details.

## Why the project is useful

- **Pre-LLM authorization**: unauthorized chunks are removed before generation
- **Grounded responses**: answer output includes citations and confidence metadata
- **Auditability**: query and ingest actions are logged and reviewable
- **Multi-source ingestion**: supports CSV, JSON, PDF, DOCX, SQL, and Markdown/KB content
- **Deployment flexibility**: run locally, with Docker Compose, or on Kubernetes

## How users can get started

### Prerequisites

- Python 3.12+
- Node.js 22+
- npm
- Docker + Docker Compose (optional)

### Option A: Local development

1. **Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`

2. **Frontend** (new terminal)

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Frontend URL: `http://localhost:3000`

3. **Optional: ingest bundled sample data**

```bash
cd backend
python -m app.scripts.ingest_examples
```

### Option B: Full stack with Docker Compose

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001` (default `admin` / `admin`)

### Option C: Kubernetes

```bash
kubectl apply -f deploy/k8s/secrets.example.yaml
kubectl apply -f deploy/k8s/backend.yaml
kubectl apply -f deploy/k8s/frontend.yaml
```

### Validate your setup

From repository root:

```bash
pytest backend/tests
cd frontend && npm install && npm run build
```

## Usage examples

### 1) Get a JWT token

```bash
curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin-change-me"}'
```

### 2) Run a query

```bash
TOKEN="<paste_access_token>"
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"Show critical security alerts"}'
```

### 3) Ingest data

```bash
curl -s -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "examples/data/security_alerts.json",
    "source_type": "json",
    "department": "compliance",
    "owner": "compliance",
    "confidentiality": "confidential",
    "allowed_roles": ["Admin", "Compliance"],
    "rbac_tags": ["compliance", "alerts"]
  }'
```

Demo credentials and endpoint details are documented in [docs/api.md](docs/api.md).

## Screenshots

### Login
![Login](docs/screenshots/Enterprise%20Secure%20RAG%20-%20login.png)

### Chat
![Chat](docs/screenshots/Enterprise%20Secure%20RAG%20-chat.png)

### Ingest
![Ingest](docs/screenshots/Enterprise%20Secure%20RAG%20-%20ingest.png)

### Admin
![Admin](docs/screenshots/Enterprise%20Secure%20RAG%20-%20admin.png)

## Where users can get help

- API reference: [docs/api.md](docs/api.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- Security/RBAC model: [docs/security.md](docs/security.md)
- Design notes: [docs/Design.md](docs/Design.md)
- Open issues / support requests: https://github.com/anan5093/Enterprise-RAG-Intelligence/issues

## Who maintains and contributes

### Maintainer

- Anand Raj ([@anan5093](https://github.com/anan5093))

### Contributing

Contributions are welcome:

1. Create a branch from the latest default branch.
2. Keep changes focused and include tests/docs updates when relevant.
3. Validate with:
   - `pytest backend/tests`
   - `cd frontend && npm install && npm run build`
4. Open a pull request with a clear summary and validation notes.

For major features or architectural changes, open an issue first to align on scope.

## License

Licensed under the [MIT License](LICENSE).
