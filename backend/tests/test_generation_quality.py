import pytest

from app.generation.response_generator import ResponseGenerator
from app.models.domain import DataSourceType, DocumentChunk, DocumentMetadata, Principal, QueryRoute, QueryType, RetrievalStrategy, RetrievalTrace, Role, SensitivityLevel


def make_chunk(text: str, source: str, score: float, row_id: str | None = None) -> DocumentChunk:
    source_type = DataSourceType.knowledge_base if source.endswith(".md") else DataSourceType.json
    return DocumentChunk(
        text=text,
        score=score,
        metadata=DocumentMetadata(
            source=source,
            source_type=source_type,
            department="compliance",
            confidentiality=SensitivityLevel.restricted,
            owner="compliance",
            allowed_roles=[Role.admin, Role.compliance],
            sensitivity_level=SensitivityLevel.restricted,
            access_level=SensitivityLevel.restricted,
            row_id=row_id,
        ),
    )


def make_trace(query: str, chunks: list[DocumentChunk]) -> RetrievalTrace:
    return RetrievalTrace(
        query=query,
        route=QueryRoute(
            query_type=QueryType.factual,
            sources=[DataSourceType.json, DataSourceType.knowledge_base],
            strategy=RetrievalStrategy.hybrid,
            confidence=0.78,
        ),
        candidate_chunk_ids=[chunk.chunk_id for chunk in chunks],
        authorized_chunk_ids=[chunk.chunk_id for chunk in chunks],
        filters_applied=["RBAC role/department/sensitivity pre-generation filter"],
    )


@pytest.mark.asyncio
async def test_generation_quality_security_alert_summary():
    query = "Show critical security alerts"
    chunks = [
        make_chunk(
            "alert_id: ALT-001\nseverity: Critical\nsystem: VPN Gateway\ndescription: Multiple failed login attempts detected\nstatus: Open",
            "security_alerts.json",
            0.08,
            "0",
        ),
        make_chunk(
            "alert_id: ALT-002\nseverity: High\nsystem: Production API\ndescription: Suspicious API traffic detected\nstatus: Investigating",
            "security_alerts.json",
            0.02,
            "1",
        ),
        make_chunk(
            "incident_id: INC-001\nseverity: Critical\nsystem: Authentication API\nstatus: Resolved",
            "infrastructure_incidents.csv",
            0.08,
            "0",
        ),
        make_chunk(
            "# Engineering Knowledge Base\n## Deployment Policy\nAll production deployments require:\n- Security approval\n- Compliance review\n- CI/CD validation\n## Incident Response\nCritical incidents must be acknowledged within 15 minutes.",
            "engineering_kb.md",
            0.13,
        ),
    ]
    principal = Principal(user_id="admin", username="admin", roles=[Role.admin], departments=["global"], clearance=SensitivityLevel.restricted)

    answer = await ResponseGenerator().generate(query, chunks, principal, make_trace(query, chunks))

    assert "chunk_" not in answer.answer
    assert "Engineering Knowledge Base" not in answer.answer
    assert "Operational policy states" in answer.answer
    assert "security approval, compliance review, and CI/CD validation" in answer.answer
    assert 0.0 <= answer.confidence <= 1.0
    assert [citation.source for citation in answer.citations] == [
        "security_alerts.json",
        "security_alerts.json",
        "infrastructure_incidents.csv",
        "engineering_kb.md",
    ]
