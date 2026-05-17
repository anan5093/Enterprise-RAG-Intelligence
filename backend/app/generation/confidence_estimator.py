from app.models.domain import DocumentChunk, RetrievalTrace

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "from",
    "in",
    "of",
    "on",
    "show",
    "the",
    "to",
    "were",
    "with",
}


class ConfidenceEstimator:
    def estimate(self, chunks: list[DocumentChunk], trace: RetrievalTrace, query: str | None = None) -> float:
        if not chunks:
            return 0.0

        scores = [max(0.0, chunk.score or 0.0) for chunk in chunks]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        retrieval_quality = min(1.0, ((avg_score + max_score) / 2) / 0.14)

        sources = {chunk.metadata.source for chunk in chunks}
        source_agreement = min(1.0, len(sources) / 3)
        evidence_count = min(1.0, len(chunks) / 4)
        direct_coverage = self._direct_coverage(chunks, query or trace.query)
        consistency = self._evidence_consistency(chunks)
        routing_quality = max(0.0, min(trace.route.confidence, 1.0))

        confidence = (
            0.12
            + retrieval_quality * 0.24
            + direct_coverage * 0.24
            + evidence_count * 0.14
            + source_agreement * 0.12
            + consistency * 0.09
            + routing_quality * 0.05
        )

        if max_score < 0.025 and direct_coverage < 0.35:
            confidence = min(confidence, 0.45)
        if len(chunks) == 1:
            confidence = min(confidence, 0.72)
        if consistency < 0.55:
            confidence *= 0.85

        return round(max(0.0, min(confidence, 0.95)), 2)

    def _direct_coverage(self, chunks: list[DocumentChunk], query: str) -> float:
        query_terms = {
            term.strip(".,:;!?()[]{}").lower()
            for term in query.split()
            if term.lower() not in STOPWORDS and len(term) > 2
        }
        if not query_terms:
            return 0.5
        searchable = " ".join(f"{chunk.metadata.source} {chunk.text}" for chunk in chunks).lower()
        matched = sum(1 for term in query_terms if term in searchable)
        return min(1.0, matched / len(query_terms))

    def _evidence_consistency(self, chunks: list[DocumentChunk]) -> float:
        severities = {self._field_value(chunk.text, "severity").lower() for chunk in chunks if self._field_value(chunk.text, "severity")}
        statuses = {self._field_value(chunk.text, "status").lower() for chunk in chunks if self._field_value(chunk.text, "status")}

        if len(severities) > 2:
            return 0.72
        if {"open", "resolved"}.issubset(statuses):
            return 0.82
        return 0.92

    def _field_value(self, text: str, field: str) -> str:
        prefix = f"{field.lower()}:"
        for line in text.splitlines():
            if line.lower().startswith(prefix):
                return line.split(":", 1)[1].strip()
        return ""
