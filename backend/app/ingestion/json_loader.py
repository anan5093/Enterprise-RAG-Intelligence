import json
from pathlib import Path
from typing import Any

from app.ingestion.chunking import Chunker
from app.models.domain import DocumentChunk, DocumentMetadata


class JSONLoader:
    def __init__(self, chunker: Chunker | None = None) -> None:
        self.chunker = chunker or Chunker()

    async def load(self, path: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        records = data if isinstance(data, list) else data.get("records", [data])
        return self.chunker.chunk_rows([self._flatten(record) for record in records], metadata)

    def _flatten(self, payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in payload.items():
            compound = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten(value, compound))
            else:
                result[compound] = value
        return result

