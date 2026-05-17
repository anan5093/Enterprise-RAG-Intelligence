from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.ingestion.chunking import Chunker
from app.models.domain import DocumentChunk, DocumentMetadata


class SQLLoader:
    def __init__(self, database_url: str | None = None, chunker: Chunker | None = None) -> None:
        self.database_url = database_url or get_settings().sql_database_url
        self.chunker = chunker or Chunker()

    async def load_table(self, table: str, metadata: DocumentMetadata, limit: int = 5000) -> list[DocumentChunk]:
        engine = create_async_engine(self.database_url)
        async with engine.connect() as conn:
            result = await conn.execute(text(f"SELECT * FROM {table} LIMIT :limit"), {"limit": limit})
            rows = [dict(row._mapping) for row in result]
        await engine.dispose()
        return self.chunker.chunk_rows(rows, metadata.model_copy(update={"table": table}))

