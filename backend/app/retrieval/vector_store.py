import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Protocol

from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.domain import DocumentChunk

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

Base = declarative_base()


# =========================================================
# PGVECTOR TABLE
# =========================================================


class DocumentVector(Base):
    __tablename__ = "document_vectors"

    id = Column(Integer, primary_key=True)

    document_id = Column(Text)

    chunk_id = Column(Text, unique=True)

    chunk_text = Column(Text)

    embedding = Column(Vector(384))

    metadata_json = Column(JSONB)


# =========================================================
# VECTOR STORE PROTOCOL
# =========================================================


class VectorStoreProtocol(Protocol):

    async def upsert(
        self,
        chunks: list[DocumentChunk]
    ) -> None:
        ...

    async def semantic_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:
        ...

    async def keyword_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:
        ...


# =========================================================
# EMBEDDING SERVICE
# =========================================================


class EmbeddingService:

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5"
    ) -> None:

        logger.info(
            "loading_embedding_model model=%s",
            model_name
        )

        self.model = SentenceTransformer(model_name)

    def embed(
        self,
        text: str
    ) -> list[float]:

        embedding = self.model.encode(text)

        return embedding.tolist()


# =========================================================
# IN MEMORY VECTOR STORE
# =========================================================


class InMemoryVectorStore:

    def __init__(
        self,
        embedder: EmbeddingService | None = None
    ) -> None:

        self.embedder = embedder or EmbeddingService()

        self._chunks: dict[str, DocumentChunk] = {}

        self._inverted: dict[str, set[str]] = defaultdict(set)

    async def upsert(
        self,
        chunks: list[DocumentChunk]
    ) -> None:

        for chunk in chunks:

            chunk.embedding = self.embedder.embed(chunk.text)

            self._chunks[chunk.chunk_id] = chunk

            for token in set(chunk.text.lower().split()):

                self._inverted[token].add(chunk.chunk_id)

    async def semantic_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:

        query_embedding = self.embedder.embed(query)

        scored: list[DocumentChunk] = []

        for chunk in self._chunks.values():

            similarity = sum(
                a * b
                for a, b in zip(
                    query_embedding,
                    chunk.embedding or []
                )
            )

            scored.append(
                chunk.model_copy(
                    update={
                        "score": similarity
                    }
                )
            )

        return sorted(
            scored,
            key=lambda item: item.score or 0,
            reverse=True
        )[:top_k]

    async def keyword_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:

        scores: dict[str, float] = defaultdict(float)

        for token in query.lower().split():

            for chunk_id in self._inverted.get(token, set()):

                scores[chunk_id] += 1.0

        chunks = [
            self._chunks[cid].model_copy(
                update={
                    "score": score
                }
            )
            for cid, score in scores.items()
        ]

        return sorted(
            chunks,
            key=lambda item: item.score or 0,
            reverse=True
        )[:top_k]


# =========================================================
# FAISS VECTOR STORE
# =========================================================


class FAISSVectorStore:

    def __init__(
        self,
        index_path: str,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
    ) -> None:

        from langchain_community.embeddings import HuggingFaceEmbeddings

        self.index_path = Path(index_path)

        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model
        )

        self._faiss = None

        self._chunks: dict[str, DocumentChunk] = {}

        self._inverted: dict[str, set[str]] = defaultdict(set)

        self.load_local()

    def load_local(self) -> None:

        from langchain_community.vectorstores import FAISS

        index_file = self.index_path / "index.faiss"

        docstore_file = self.index_path / "index.pkl"

        if not index_file.exists() or not docstore_file.exists():

            logger.warning(
                "faiss_index_missing path=%s",
                self.index_path
            )

            return

        try:

            self._faiss = FAISS.load_local(
                str(self.index_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )

            logger.info(
                "faiss_loaded path=%s",
                self.index_path
            )

        except Exception:

            logger.exception(
                "faiss_load_failed"
            )

    def save_local(self) -> None:

        if self._faiss is None:
            return

        self.index_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self._faiss.save_local(
            str(self.index_path)
        )

    async def upsert(
        self,
        chunks: list[DocumentChunk]
    ) -> None:

        from langchain_community.vectorstores import FAISS

        from langchain_core.documents import Document

        documents = []

        for chunk in chunks:

            documents.append(
                Document(
                    page_content=chunk.text,
                    metadata={
                        "chunk_json": chunk.model_dump_json()
                    },
                )
            )

        if self._faiss is None:

            self._faiss = FAISS.from_documents(
                documents,
                self.embeddings
            )

        else:

            self._faiss.add_documents(documents)

        self.save_local()

    async def semantic_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:

        if self._faiss is None:

            self.load_local()

        if self._faiss is None:

            return []

        results = self._faiss.similarity_search_with_score(
            query,
            k=top_k
        )

        chunks = []

        for document, distance in results:

            payload = document.metadata.get(
                "chunk_json"
            )

            if not payload:
                continue

            chunk = DocumentChunk(
                **json.loads(payload)
            )

            score = 1.0 / (1.0 + float(distance))

            chunks.append(
                chunk.model_copy(
                    update={
                        "score": score
                    }
                )
            )

        return chunks

    async def keyword_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:

        return []


# =========================================================
# PGVECTOR STORE
# =========================================================


class PGVectorStore:

    def __init__(
        self,
        database_url: str,
        embedder: EmbeddingService | None = None,
    ) -> None:

        self.embedder = embedder or EmbeddingService()

        self.engine = create_engine(database_url)

        self.SessionLocal = sessionmaker(
            bind=self.engine
        )

        Base.metadata.create_all(self.engine)

    async def upsert(
        self,
        chunks: list[DocumentChunk]
    ) -> None:

        with self.SessionLocal() as session:

            for chunk in chunks:

                embedding = self.embedder.embed(
                    chunk.text
                )

                record = DocumentVector(
                    document_id=chunk.metadata.source,
                    chunk_id=chunk.chunk_id,
                    chunk_text=chunk.text,
                    embedding=embedding,
                    metadata_json=chunk.metadata.model_dump(),
                )

                session.merge(record)

            session.commit()

    async def semantic_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:

        query_embedding = self.embedder.embed(
            query
        )

        sql = text(
            """
            SELECT
                chunk_id,
                chunk_text,
                metadata_json,
                embedding <=> :embedding AS distance
            FROM document_vectors
            ORDER BY embedding <=> :embedding
            LIMIT :top_k
            """
        )

        with self.SessionLocal() as session:

            results = session.execute(
                sql,
                {
                    "embedding": query_embedding,
                    "top_k": top_k,
                },
            )

            rows = results.fetchall()

        chunks = []

        for row in rows:

            chunk = DocumentChunk(
                chunk_id=row.chunk_id,
                text=row.chunk_text,
                metadata=row.metadata_json,
                score=1.0 - float(row.distance),
            )

            chunks.append(chunk)

        return chunks

    async def keyword_search(
        self,
        query: str,
        top_k: int = 20
    ) -> list[DocumentChunk]:

        sql = text(
            """
            SELECT
                chunk_id,
                chunk_text,
                metadata_json
            FROM document_vectors
            WHERE chunk_text ILIKE :query
            LIMIT :top_k
            """
        )

        with self.SessionLocal() as session:

            results = session.execute(
                sql,
                {
                    "query": f"%{query}%",
                    "top_k": top_k,
                },
            )

            rows = results.fetchall()

        chunks = []

        for row in rows:

            chunk = DocumentChunk(
                chunk_id=row.chunk_id,
                text=row.chunk_text,
                metadata=row.metadata_json,
                score=0.5,
            )

            chunks.append(chunk)

        return chunks


# =========================================================
# FACTORY
# =========================================================


def get_vector_store():

    settings = get_settings()

    logger.info(
        "initializing_vector_store backend=%s",
        settings.vector_backend
    )

    if settings.vector_backend == "pgvector":

        return PGVectorStore(
            database_url=settings.pgvector_database_url
        )

    if settings.vector_backend == "faiss":

        return FAISSVectorStore(
            index_path=settings.faiss_index_path
        )

    return InMemoryVectorStore()
