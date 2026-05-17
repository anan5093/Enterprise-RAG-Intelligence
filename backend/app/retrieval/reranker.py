from app.models.domain import DocumentChunk


class Reranker:
    async def rerank(self, query: str, chunks: list[DocumentChunk], top_k: int = 8) -> list[DocumentChunk]:
        query_terms = set(query.lower().split())
        reranked: list[DocumentChunk] = []
        for chunk in chunks:
            overlap = len(query_terms.intersection(chunk.text.lower().split()))
            combined = (chunk.score or 0.0) + overlap * 0.05
            reranked.append(chunk.model_copy(update={"score": combined}))
        return sorted(reranked, key=lambda item: item.score or 0, reverse=True)[:top_k]

