# Enterprise Secure Multi-Source RAG Architecture

```mermaid
flowchart LR
  U["Authenticated User"] --> API["FastAPI API"]
  API --> Auth["JWT Auth + RBAC Middleware"]
  Auth --> Router["Query Router"]
  Router --> Hybrid["Hybrid Retrieval"]
  Hybrid --> Dense["Dense Vector Search"]
  Hybrid --> Sparse["BM25 Keyword Search"]
  Dense --> Filter["Pre-LLM RBAC Filter"]
  Sparse --> Filter
  Filter --> Rerank["Reranker"]
  Rerank --> Prompt["Prompt Builder"]
  Prompt --> Guard["Hallucination Guard"]
  Guard --> Gen["Grounded Generator"]
  Gen --> Explain["Citations + Trace + Confidence"]
  Explain --> API
  Ingest["Async Ingestion"] --> Meta["Metadata + Lineage"]
  Meta --> Chunk["Chunking"]
  Chunk --> Store["Vector/Hybrid Store"]
  Store --> Dense
  Store --> Sparse
```

## Layer Responsibilities

- Ingestion loads PDF, CSV, JSON, SQL, and knowledge-base files, extracts metadata, assigns lineage IDs, and chunks content.
- Retrieval combines semantic search and keyword search with reciprocal rank fusion, source routing, metadata filtering, and reranking.
- Security is enforced before generation. Unauthorized chunks are excluded before prompt construction, so the LLM never sees restricted evidence.
- Generation is grounded and extractive by default. Missing or low-confidence evidence returns `Insufficient authorized data available.`
- Explainability returns route decisions, authorized chunk IDs, denied counts, filters applied, citations, and confidence.
- Observability exposes Prometheus metrics and appends structured audit events.

