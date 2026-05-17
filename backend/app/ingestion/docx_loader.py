from pathlib import Path

from app.ingestion.chunking import Chunker
from app.models.domain import DocumentChunk, DocumentMetadata


class DOCXLoader:
    def __init__(self, chunker: Chunker | None = None) -> None:
        self.chunker = chunker or Chunker()

    async def load(self, path: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        from docx import Document

        document = Document(Path(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
        return self.chunker.chunk_text(text, metadata)

