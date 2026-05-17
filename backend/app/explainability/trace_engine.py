from app.models.domain import RAGAnswer


class TraceEngine:
    def summarize(self, answer: RAGAnswer) -> dict[str, object]:
        return {
            "route": answer.trace.route.model_dump(mode="json"),
            "retrieved_chunks": answer.trace.authorized_chunk_ids,
            "filters_applied": answer.trace.filters_applied,
            "latency_ms": answer.trace.latency_ms,
        }

