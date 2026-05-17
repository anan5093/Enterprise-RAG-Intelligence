from app.generation.response_generator import ResponseGenerator
from app.models.domain import Principal, RAGAnswer
from app.observability.metrics import ACCESS_DENIED_COUNTER, HALLUCINATION_REFUSALS, QUERY_COUNTER, QUERY_LATENCY
from app.retrieval.hybrid_search import HybridRetriever
from app.security.audit_logger import AuditLogger


class QueryService:
    def __init__(self, retriever: HybridRetriever, generator: ResponseGenerator | None = None, audit_logger: AuditLogger | None = None) -> None:
        self.retriever = retriever
        self.generator = generator or ResponseGenerator()
        self.audit_logger = audit_logger or AuditLogger()

    async def answer(self, query: str, principal: Principal) -> RAGAnswer:
        with QUERY_LATENCY.time():
            chunks, trace = await self.retriever.retrieve(query, principal)
            ACCESS_DENIED_COUNTER.inc(len(trace.denied_chunk_ids))
            role_label = ",".join(role.value for role in principal.roles)
            QUERY_COUNTER.labels(role=role_label, query_type=trace.route.query_type.value).inc()
            answer = await self.generator.generate(query, chunks, principal, trace)
            if not chunks:
                HALLUCINATION_REFUSALS.inc()
            await self.audit_logger.log(
                "query",
                principal,
                {
                    "query": query,
                    "route": trace.route.model_dump(mode="json"),
                    "authorized_chunks": trace.authorized_chunk_ids,
                    "denied_count": len(trace.denied_chunk_ids),
                    "confidence": answer.confidence,
                },
            )
            return answer

