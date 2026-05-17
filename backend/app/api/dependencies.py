from functools import lru_cache

from app.core.config import get_settings
from app.retrieval.hybrid_search import HybridRetriever
from app.retrieval.vector_store import FAISSVectorStore, InMemoryVectorStore
from app.services.ingestion_service import IngestionService
from app.services.query_service import QueryService


@lru_cache
def get_vector_store():
    settings = get_settings()
    if settings.vector_backend == "faiss":
        return FAISSVectorStore(settings.faiss_index_path)
    return InMemoryVectorStore()


def get_ingestion_service() -> IngestionService:
    return IngestionService(get_vector_store())


def get_query_service() -> QueryService:
    return QueryService(HybridRetriever(get_vector_store()))
