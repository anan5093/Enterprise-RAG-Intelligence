import pytest

from app.generation.response_generator import ResponseGenerator
from app.models.domain import DataSourceType, DocumentChunk, DocumentMetadata, Principal, Role, SensitivityLevel
from app.retrieval.hybrid_search import HybridRetriever
from app.retrieval.vector_store import InMemoryVectorStore
from app.services.query_service import QueryService


@pytest.mark.asyncio
async def test_unauthorized_query_returns_insufficient_data(tmp_path):
    store = InMemoryVectorStore()
    chunk = DocumentChunk(
        text="Payroll data: executive bonus pool is 1000000.",
        metadata=DocumentMetadata(
            source="payroll.csv",
            source_type=DataSourceType.csv,
            department="finance",
            confidentiality=SensitivityLevel.confidential,
            owner="finance",
            allowed_roles=[Role.finance],
            sensitivity_level=SensitivityLevel.confidential,
            access_level=SensitivityLevel.confidential,
        ),
    )
    await store.upsert([chunk])
    principal = Principal(
        user_id="eng_user",
        username="eng_user",
        roles=[Role.engineering],
        departments=["engineering"],
        clearance=SensitivityLevel.internal,
    )
    service = QueryService(HybridRetriever(store), audit_logger=None)
    service.audit_logger.path = tmp_path / "audit.log"

    answer = await service.answer("Show payroll data", principal)

    assert answer.answer == "Insufficient authorized data available."
    assert answer.citations == []
    assert chunk.chunk_id in answer.trace.denied_chunk_ids
    assert chunk.chunk_id not in answer.trace.authorized_chunk_ids


@pytest.mark.asyncio
async def test_authorized_query_returns_citations(tmp_path):
    store = InMemoryVectorStore()
    chunk = DocumentChunk(
        text="Q4 finance compliance finding: vendor review cadence improved to monthly.",
        metadata=DocumentMetadata(
            source="finance_q4_report.pdf",
            source_type=DataSourceType.pdf,
            department="finance",
            confidentiality=SensitivityLevel.confidential,
            owner="compliance",
            allowed_roles=[Role.finance, Role.compliance],
            sensitivity_level=SensitivityLevel.confidential,
            access_level=SensitivityLevel.confidential,
            page=8,
        ),
    )
    await store.upsert([chunk])
    principal = Principal(
        user_id="fin_user",
        username="fin_user",
        roles=[Role.finance],
        departments=["finance"],
        clearance=SensitivityLevel.confidential,
    )
    service = QueryService(HybridRetriever(store), ResponseGenerator(), audit_logger=None)
    service.audit_logger.path = tmp_path / "audit.log"

    answer = await service.answer("Summarize Q4 finance compliance findings", principal)

    assert "vendor review cadence" in answer.answer
    assert chunk.chunk_id not in answer.answer
    assert answer.citations[0].source == "finance_q4_report.pdf"
    assert answer.trace.authorized_chunk_ids == [chunk.chunk_id]
