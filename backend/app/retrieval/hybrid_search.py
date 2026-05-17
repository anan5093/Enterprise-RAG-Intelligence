import time

from app.core.config import get_settings
from app.models.domain import DocumentChunk, Principal, RetrievalTrace
from app.retrieval.metadata_filters import MetadataFilterBuilder, SecureMetadataFilter
from app.retrieval.query_router import QueryRouter
from app.retrieval.reranker import Reranker
from app.retrieval.vector_store import VectorStoreProtocol


class HybridRetriever:
    def __init__(
        self,
        store: VectorStoreProtocol,
        router: QueryRouter | None = None,
        reranker: Reranker | None = None,
        secure_filter: SecureMetadataFilter | None = None,
    ) -> None:
        self.store = store
        self.router = router or QueryRouter()
        self.reranker = reranker or Reranker()
        self.secure_filter = secure_filter or SecureMetadataFilter()
        self.filter_builder = MetadataFilterBuilder()

    async def retrieve(self, query: str, principal: Principal) -> tuple[list[DocumentChunk], RetrievalTrace]:
        started = time.perf_counter()
        route = await self.router.route(query)
        dense = await self.store.semantic_search(query, top_k=30)
        sparse = await self.store.keyword_search(query, top_k=30)
        fused = self._reciprocal_rank_fusion([dense, sparse])
        source_filtered = [chunk for chunk in fused if chunk.metadata.source_type in route.sources]
        candidates = source_filtered or fused
        authorized, denied, denial_reasons = self.secure_filter.apply(principal, candidates)
        reranked = await self.reranker.rerank(query, authorized, top_k=get_settings().max_context_chunks)
        trace = RetrievalTrace(
            query=query,
            route=route,
            candidate_chunk_ids=[chunk.chunk_id for chunk in candidates],
            authorized_chunk_ids=[chunk.chunk_id for chunk in reranked],
            denied_chunk_ids=[chunk.chunk_id for chunk in denied],
            filters_applied=[
                self.filter_builder.source_filter(route.sources),
                "RBAC role/department/sensitivity pre-generation filter",
                *denial_reasons[:10],
            ],
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        return reranked, trace

    def _reciprocal_rank_fusion(self, result_sets: list[list[DocumentChunk]], k: int = 60) -> list[DocumentChunk]:
        scores: dict[str, float] = {}
        by_id: dict[str, DocumentChunk] = {}
        for results in result_sets:
            for rank, chunk in enumerate(results, start=1):
                by_id[chunk.chunk_id] = chunk
                scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)
        return [
            by_id[chunk_id].model_copy(update={"score": score})
            for chunk_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
        ]
