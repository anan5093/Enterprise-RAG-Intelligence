from collections.abc import Iterable

from app.models.domain import DocumentChunk, DocumentMetadata


class Chunker:
    def __init__(self, chunk_size: int = 1200, overlap: int = 160) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        normalized = " ".join(text.split())
        if not normalized:
            return []
        chunks: list[DocumentChunk] = []
        start = 0
        while start < len(normalized):
            end = min(start + self.chunk_size, len(normalized))
            chunks.append(DocumentChunk(text=normalized[start:end], metadata=metadata))
            if end == len(normalized):
                break
            start = max(0, end - self.overlap)
        return chunks

    def chunk_rows(self, rows: Iterable[dict[str, object]], metadata: DocumentMetadata) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for idx, row in enumerate(rows):
            row_metadata = metadata.model_copy(update={"row_id": str(row.get("id", idx))})
            body = "\n".join(f"{key}: {value}" for key, value in row.items())
            chunks.append(DocumentChunk(text=body, metadata=row_metadata))
        return chunks

