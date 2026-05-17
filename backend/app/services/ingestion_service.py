from pathlib import Path

from app.ingestion.csv_loader import CSVLoader
from app.ingestion.docx_loader import DOCXLoader
from app.ingestion.json_loader import JSONLoader
from app.ingestion.metadata_pipeline import MetadataPipeline
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.sql_loader import SQLLoader
from app.models.api import IngestRequest
from app.models.domain import DataSourceType, DocumentChunk
from app.retrieval.vector_store import VectorStoreProtocol


class IngestionService:
    def __init__(self, store: VectorStoreProtocol, metadata_pipeline: MetadataPipeline | None = None) -> None:
        self.store = store
        self.metadata_pipeline = metadata_pipeline or MetadataPipeline()

    async def ingest(self, request: IngestRequest) -> list[DocumentChunk]:
        metadata = self.metadata_pipeline.build(request)
        if request.source_type == DataSourceType.pdf:
            chunks = await PDFLoader().load(request.path, metadata)
        elif request.source_type == DataSourceType.docx:
            chunks = await DOCXLoader().load(request.path, metadata)
        elif request.source_type == DataSourceType.json or request.source_type == DataSourceType.audit:
            chunks = await JSONLoader().load(request.path, metadata)
        elif request.source_type == DataSourceType.csv:
            chunks = await CSVLoader().load(request.path, metadata)
        elif request.source_type == DataSourceType.sql:
            chunks = await SQLLoader().load_table(Path(request.path).stem, metadata)
        else:
            text = Path(request.path).read_text(encoding="utf-8")
            from app.ingestion.chunking import Chunker

            chunks = Chunker().chunk_text(text, metadata)
        await self.store.upsert(chunks)
        return chunks
