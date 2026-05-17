from app.models.domain import Citation, DocumentChunk


class CitationEngine:
    def build(self, chunks: list[DocumentChunk]) -> list[Citation]:
        return [
            Citation(
                chunk_id=chunk.chunk_id,
                source=chunk.metadata.source,
                page=chunk.metadata.page,
                table=chunk.metadata.table,
                row_id=chunk.metadata.row_id,
                score=chunk.score,
            )
            for chunk in chunks
        ]

