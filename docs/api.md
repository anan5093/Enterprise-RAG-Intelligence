# API

## `POST /login`

Authenticates a user and returns a JWT.

Demo credentials:

- `admin` / `admin-change-me`
- `fin_user` / `finance-change-me`
- `eng_user` / `engineering-change-me`
- `comp_user` / `compliance-change-me`
- `guest` / `guest-change-me`

## `POST /ingest`

Requires Admin or Compliance.

```json
{
  "path": "/mnt/d/rag_project/examples/data/finance_controls.csv",
  "source_type": "csv",
  "department": "finance",
  "owner": "finance",
  "confidentiality": "confidential",
  "allowed_roles": ["Finance", "Compliance"],
  "rbac_tags": ["finance", "controls"]
}
```

## `POST /query`

Requires JWT. Returns answer, citations, confidence, trace, and access-filter explanation.

```json
{
  "query": "Summarize Q4 finance compliance findings"
}
```

## `GET /audit-logs`

Requires Admin or Compliance.

## `GET /health`

Returns service status.

## `GET /metrics`

Prometheus metrics.

