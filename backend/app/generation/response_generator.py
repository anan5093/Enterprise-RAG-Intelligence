from app.generation.citation_engine import CitationEngine
from app.generation.confidence_estimator import ConfidenceEstimator
from app.generation.hallucination_guard import HallucinationGuard
from app.generation.prompt_builder import PromptBuilder
from app.models.domain import DocumentChunk, Principal, RAGAnswer, RetrievalTrace


class ResponseGenerator:
    def __init__(
        self,
        prompt_builder: PromptBuilder | None = None,
        citation_engine: CitationEngine | None = None,
        confidence_estimator: ConfidenceEstimator | None = None,
        guard: HallucinationGuard | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.citation_engine = citation_engine or CitationEngine()
        self.confidence_estimator = confidence_estimator or ConfidenceEstimator()
        self.guard = guard or HallucinationGuard()

    async def generate(self, query: str, chunks: list[DocumentChunk], principal: Principal, trace: RetrievalTrace) -> RAGAnswer:
        confidence = self.confidence_estimator.estimate(chunks, trace)
        if self.guard.should_refuse(chunks, confidence):
            return RAGAnswer(
                answer=self.guard.insufficient_message,
                citations=[],
                confidence=confidence,
                trace=trace,
                access_filter_explanation=self._filter_explanation(trace),
            )
        answer = self._extractive_answer(query, chunks)
        return RAGAnswer(
            answer=self.guard.sanitize(answer),
            citations=self.citation_engine.build(chunks),
            confidence=confidence,
            trace=trace,
            access_filter_explanation=self._filter_explanation(trace),
        )

    def _extractive_answer(self, query: str, chunks: list[DocumentChunk]) -> str:
        evidence = []
        for chunk in chunks[:5]:
            sentence = chunk.text[:600].strip()
            evidence.append(f"{sentence} [{chunk.chunk_id}]")
        return " ".join(evidence)

    def _filter_explanation(self, trace: RetrievalTrace) -> str:
        denied = len(trace.denied_chunk_ids)
        allowed = len(trace.authorized_chunk_ids)
        return f"Applied source routing and RBAC filters before generation. Authorized chunks: {allowed}; denied chunks excluded: {denied}."

