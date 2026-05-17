from app.models.domain import DataSourceType, QueryRoute, QueryType, RetrievalStrategy


class QueryRouter:
    async def route(self, query: str) -> QueryRoute:
        lowered = query.lower()
        sources: list[DataSourceType] = []
        query_type = QueryType.factual
        needs_sql = False
        needs_summarization = "summarize" in lowered or "summary" in lowered

        if any(term in lowered for term in ["login", "anomaly", "audit", "failed", "trail"]):
            sources.extend([DataSourceType.json, DataSourceType.audit])
            query_type = QueryType.audit
        if any(term in lowered for term in ["compliance", "policy", "finding", "sox", "gdpr"]):
            sources.extend([DataSourceType.pdf, DataSourceType.docx, DataSourceType.sql])
            query_type = QueryType.compliance
        if any(term in lowered for term in ["revenue", "payroll", "invoice", "finance", "q4"]):
            sources.extend([DataSourceType.sql, DataSourceType.csv, DataSourceType.pdf])
            query_type = QueryType.analytical
            needs_sql = True
        if any(term in lowered for term in ["incident", "outage", "infrastructure", "latency"]):
            sources.extend([DataSourceType.json, DataSourceType.csv, DataSourceType.pdf])
            query_type = QueryType.operational

        if not sources:
            sources = [DataSourceType.pdf, DataSourceType.docx, DataSourceType.csv, DataSourceType.json, DataSourceType.knowledge_base]

        unique_sources = list(dict.fromkeys(sources))
        return QueryRoute(
            query_type=query_type,
            sources=unique_sources,
            strategy=RetrievalStrategy.hybrid,
            needs_sql=needs_sql,
            needs_summarization=needs_summarization,
            confidence=0.78 if unique_sources else 0.45,
            rationale="Rule-based enterprise router selected sources and retrieval strategy",
        )

