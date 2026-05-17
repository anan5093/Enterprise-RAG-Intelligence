import csv
from pathlib import Path

from app.ingestion.chunking import Chunker
from app.models.domain import DocumentChunk, DocumentMetadata


class CSVLoader:
    def __init__(self, chunker: Chunker | None = None) -> None:
        self.chunker = chunker or Chunker()

    async def load(self, path: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        with Path(path).open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        return self.chunker.chunk_rows(rows, metadata)

