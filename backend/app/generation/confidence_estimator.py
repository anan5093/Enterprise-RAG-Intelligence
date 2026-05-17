from app.models.domain import DocumentChunk, RetrievalTrace


class ConfidenceEstimator:
    def estimate(self, chunks: list[DocumentChunk], trace: RetrievalTrace) -> float:
        if not chunks:
            return 0.0
        avg_score = sum(chunk.score or 0.0 for chunk in chunks) / len(chunks)
        evidence_factor = min(1.0, len(chunks) / 5)
        routing_factor = trace.route.confidence
        confidence = 0.35 + min(avg_score, 1.0) * 0.30 + evidence_factor * 0.22 + routing_factor * 0.13
        return round(max(0.0, min(confidence, 0.98)), 2)
