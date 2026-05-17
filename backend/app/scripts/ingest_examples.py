import asyncio
import logging
from pathlib import Path

from app.ingestion.chunking import Chunker
from app.ingestion.csv_loader import CSVLoader
from app.ingestion.docx_loader import DOCXLoader
from app.ingestion.json_loader import JSONLoader
from app.ingestion.metadata_pipeline import MetadataPipeline
from app.ingestion.pdf_loader import PDFLoader
from app.models.api import IngestRequest
from app.models.domain import DataSourceType, DocumentChunk, Role, SensitivityLevel
from app.retrieval.vector_store import FAISSVectorStore

logger = logging.getLogger("ingest_examples")

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = REPO_ROOT / "examples" / "data"
DEFAULT_FAISS_DIR = REPO_ROOT / "runtime" / "faiss_index"

SUPPORTED_EXTENSIONS = {
    ".csv": DataSourceType.csv,
    ".json": DataSourceType.json,
    ".pdf": DataSourceType.pdf,
    ".docx": DataSourceType.docx,
    ".md": DataSourceType.knowledge_base,
    ".txt": DataSourceType.knowledge_base,
}

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def main() -> None:
    configure_logging()
    data_dir = DEFAULT_DATA_DIR
    index_dir = DEFAULT_FAISS_DIR

    logger.info("starting_example_ingestion data_dir=%s index_dir=%s", data_dir, index_dir)
    if not data_dir.exists():
        logger.error("examples data directory not found: %s", data_dir)
        return

    store = FAISSVectorStore(index_path=str(index_dir), embedding_model="sentence-transformers/all-MiniLM-L6-v2")
    metadata_pipeline = MetadataPipeline()

    files_loaded = 0
    total_chunks = 0
    for file_path in sorted(path for path in data_dir.iterdir() if path.is_file()):
        source_type = detect_source_type(file_path)
        if source_type is None:
            logger.info("skipping_unsupported_file file=%s", file_path.name)
            continue

        try:
            chunks = await load_file(file_path, source_type, metadata_pipeline)
            if not chunks:
                logger.warning("no_chunks_created file=%s", file_path.name)
                continue
            await store.upsert(chunks)
            files_loaded += 1
            total_chunks += len(chunks)
            logger.info(
                "indexed_file file=%s source_type=%s chunks=%s status=persisted",
                file_path.name,
                source_type.value,
                len(chunks),
            )
        except Exception as exc:
            logger.exception("failed_to_ingest_file file=%s error=%s", file_path.name, exc)

    store.save_local()
    logger.info("ingestion_complete files_loaded=%s chunks_created=%s index_dir=%s", files_loaded, total_chunks, index_dir)


def detect_source_type(file_path: Path) -> DataSourceType | None:
    return SUPPORTED_EXTENSIONS.get(file_path.suffix.lower())


async def load_file(file_path: Path, source_type: DataSourceType, metadata_pipeline: MetadataPipeline) -> list[DocumentChunk]:
    request = build_ingest_request(file_path, source_type)
    metadata = metadata_pipeline.build(request)

    if source_type == DataSourceType.csv:
        return await CSVLoader().load(str(file_path), metadata)
    if source_type == DataSourceType.json:
        return await JSONLoader().load(str(file_path), metadata)
    if source_type == DataSourceType.pdf:
        return await PDFLoader().load(str(file_path), metadata)
    if source_type == DataSourceType.docx:
        return await DOCXLoader().load(str(file_path), metadata)
    if source_type == DataSourceType.knowledge_base:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return Chunker().chunk_text(text, metadata)

    logger.info("skipping_unsupported_source_type file=%s source_type=%s", file_path.name, source_type.value)
    return []


def build_ingest_request(file_path: Path, source_type: DataSourceType) -> IngestRequest:
    department, confidentiality, roles = infer_rbac_defaults(file_path.name, source_type)
    return IngestRequest(
        path=str(file_path),
        source_type=source_type,
        department=department,
        owner=department,
        confidentiality=confidentiality,
        allowed_roles=roles,
        rbac_tags=[department, source_type.value, "example-data"],
    )


def infer_rbac_defaults(file_name: str, source_type: DataSourceType) -> tuple[str, SensitivityLevel, list[Role]]:
    lowered = file_name.lower()

    if "payroll" in lowered:
        return "finance", SensitivityLevel.confidential, [Role.finance, Role.admin]
    if "employee" in lowered or "hr" in lowered:
        return "hr", SensitivityLevel.confidential, [Role.hr, Role.admin]
    if "engineering" in lowered or source_type == DataSourceType.knowledge_base:
        return "engineering", SensitivityLevel.internal, [Role.engineering, Role.admin]
    if "incident" in lowered or "infrastructure" in lowered:
        return "operations", SensitivityLevel.confidential, [Role.operations, Role.compliance, Role.admin]
    if "audit" in lowered or "alert" in lowered or "security" in lowered or "access" in lowered:
        return "compliance", SensitivityLevel.restricted, [Role.compliance, Role.admin]

    return "global", SensitivityLevel.internal, [Role.admin, Role.compliance, Role.operations]


if __name__ == "__main__":
    asyncio.run(main())
