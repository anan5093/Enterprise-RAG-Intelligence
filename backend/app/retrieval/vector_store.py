import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Protocol

from app.models.domain import DocumentChunk


class VectorStoreProtocol(Protocol):
    async def upsert(self, chunks: list[DocumentChunk]) -> None:
        ...

    async def semantic_search(self, query: str, top_k: int = 20) -> list[DocumentChunk]:
        ...

    async def keyword_search(self, query: str, top_k: int = 20) -> list[DocumentChunk]:
        ...


class EmbeddingService:
    def embed(self, text: str, dimensions: int = 384) -> list[float]:
        vector = [0.0] * dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % dimensions
            vector[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class InMemoryVectorStore:
    def __init__(self, embedder: EmbeddingService | None = None) -> None:
        self.embedder = embedder or EmbeddingService()
        self._chunks: dict[str, DocumentChunk] = {}
        self._inverted: dict[str, set[str]] = defaultdict(set)

    async def upsert(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            chunk.embedding = self.embedder.embed(chunk.text)
            self._chunks[chunk.chunk_id] = chunk
            for token in set(chunk.text.lower().split()):
                self._inverted[token].add(chunk.chunk_id)

    async def semantic_search(self, query: str, top_k: int = 20) -> list[DocumentChunk]:
        query_embedding = self.embedder.embed(query)
        scored: list[DocumentChunk] = []
        for chunk in self._chunks.values():
            score = sum(a * b for a, b in zip(query_embedding, chunk.embedding or []))
            scored.append(chunk.model_copy(update={"score": score}))
        return sorted(scored, key=lambda item: item.score or 0, reverse=True)[:top_k]

    async def keyword_search(self, query: str, top_k: int = 20) -> list[DocumentChunk]:
        scores: dict[str, float] = defaultdict(float)
        for token in query.lower().split():
            for chunk_id in self._inverted.get(token, set()):
                scores[chunk_id] += 1.0
        chunks = [self._chunks[cid].model_copy(update={"score": score}) for cid, score in scores.items()]
        return sorted(chunks, key=lambda item: item.score or 0, reverse=True)[:top_k]


class FAISSVectorStore:
    """LangChain FAISS-backed vector store with local persistence for Windows-friendly RAG."""

    def __init__(
        self,
        index_path: str = "./runtime/faiss_index",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        self.index_path = Path(index_path)
        self.embedding_model = embedding_model
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self._faiss = None
        self._chunks: dict[str, DocumentChunk] = {}
        self._inverted: dict[str, set[str]] = defaultdict(set)
        self.load_local()

    def load_local(self) -> None:
        if not self.index_path.exists():
            return
        try:
            from langchain_community.vectorstores import FAISS

            self._faiss = FAISS.load_local(
                str(self.index_path),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self._rebuild_keyword_index()
        except Exception:
            self._faiss = None
            self._chunks = {}
            self._inverted = defaultdict(set)

    def save_local(self) -> None:
        if self._faiss is None:
            return
        self.index_path.mkdir(parents=True, exist_ok=True)
        self._faiss.save_local(str(self.index_path))

    async def upsert(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document

        documents = [
            Document(
                page_content=chunk.text,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "source": chunk.metadata.source,
                    "source_type": chunk.metadata.source_type.value,
                    "department": chunk.metadata.department,
                    "sensitivity_level": chunk.metadata.sensitivity_level.value,
                    "allowed_roles": ",".join(role.value for role in chunk.metadata.allowed_roles),
                    "chunk_json": chunk.model_dump_json(),
                },
            )
            for chunk in chunks
        ]
        if self._faiss is None:
            self._faiss = FAISS.from_documents(documents, self.embeddings)
        else:
            self._faiss.add_documents(documents)
        for chunk in chunks:
            self._index_chunk(chunk)
        self.save_local()

    async def semantic_search(self, query: str, top_k: int = 20) -> list[DocumentChunk]:
        if self._faiss is None:
            self.load_local()
        if self._faiss is None:
            return []
        results = self._faiss.similarity_search_with_score(query, k=top_k)
        chunks: list[DocumentChunk] = []
        for document, distance in results:
            chunk = self._document_to_chunk(document.metadata)
            if chunk is not None:
                score = 1.0 / (1.0 + float(distance))
                chunks.append(chunk.model_copy(update={"score": score}))
        return chunks

    async def keyword_search(self, query: str, top_k: int = 20) -> list[DocumentChunk]:
        if not self._chunks:
            self.load_local()
        scores: dict[str, float] = defaultdict(float)
        for token in query.lower().split():
            for chunk_id in self._inverted.get(token, set()):
                scores[chunk_id] += 1.0
        chunks = [self._chunks[cid].model_copy(update={"score": score}) for cid, score in scores.items()]
        return sorted(chunks, key=lambda item: item.score or 0, reverse=True)[:top_k]

    def _rebuild_keyword_index(self) -> None:
        self._chunks = {}
        self._inverted = defaultdict(set)
        if self._faiss is None:
            return
        for document in self._faiss.docstore._dict.values():
            chunk = self._document_to_chunk(document.metadata)
            if chunk is not None:
                self._index_chunk(chunk)

    def _index_chunk(self, chunk: DocumentChunk) -> None:
        self._chunks[chunk.chunk_id] = chunk
        for token in set(chunk.text.lower().split()):
            self._inverted[token].add(chunk.chunk_id)

    def _document_to_chunk(self, metadata: dict[str, object]) -> DocumentChunk | None:
        payload = metadata.get("chunk_json")
        if not isinstance(payload, str):
            return None
        return DocumentChunk(**json.loads(payload))
