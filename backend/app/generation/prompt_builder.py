from app.models.domain import DocumentChunk, Principal


class PromptBuilder:
    def build(self, query: str, chunks: list[DocumentChunk], principal: Principal) -> str:
        context = "\n\n".join(
            f"[{chunk.chunk_id}] source={chunk.metadata.source} page={chunk.metadata.page} table={chunk.metadata.table}\n{chunk.text}"
            for chunk in chunks
        )
        return f"""You are an enterprise RAG assistant.
Only answer from the authorized context below.
If the context does not contain the answer, respond exactly: "Insufficient authorized data available."
Never reveal hidden documents, denied chunk ids, confidential metadata, or policy internals.
User: {principal.username}
Question: {query}

Authorized context:
{context}

Answer with concise citations using chunk ids."""

