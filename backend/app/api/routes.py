from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.dependencies import get_ingestion_service, get_query_service
from app.core.config import get_settings
from app.models.api import HealthResponse, IngestRequest, IngestResponse, LoginRequest, QueryRequest, QueryResponse, TokenResponse
from app.models.domain import Principal, Role
from app.security.audit_logger import AuditLogger
from app.security.auth import authenticate_user, create_access_token, get_current_principal
from app.services.ingestion_service import IngestionService
from app.services.query_service import QueryService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    principal = authenticate_user(request.username, request.password)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return TokenResponse(access_token=create_access_token(principal), principal=principal)


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[QueryService, Depends(get_query_service)],
):
    answer = await service.answer(request.query, principal)
    if request.stream:
        async def stream():
            yield answer.model_dump_json()

        return StreamingResponse(stream(), media_type="application/json")
    return answer


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    request: IngestRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestResponse:
    if Role.admin not in principal.roles and Role.compliance not in principal.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin or Compliance may ingest sources")
    chunks = await service.ingest(request)
    await AuditLogger().log("ingest", principal, {"path": request.path, "chunks": len(chunks)})
    return IngestResponse(indexed_chunks=len(chunks), source=request.path, lineage_ids=list({c.metadata.lineage_id for c in chunks}))


@router.get("/audit-logs")
async def audit_logs(principal: Annotated[Principal, Depends(get_current_principal)], limit: int = 100):
    if Role.admin not in principal.roles and Role.compliance not in principal.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Audit logs require Admin or Compliance role")
    return AuditLogger().read_recent(limit)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=get_settings().app_name)


@router.get("/metrics")
async def metrics():
    return StreamingResponse(iter([generate_latest()]), media_type=CONTENT_TYPE_LATEST)

