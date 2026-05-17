from app.core.config import get_settings
from app.models.domain import DocumentChunk


class HallucinationGuard:
    insufficient_message = "Insufficient authorized data available."

    def should_refuse(self, chunks: list[DocumentChunk], confidence: float) -> bool:
        return not chunks or confidence < get_settings().min_answer_confidence

    def sanitize(self, answer: str) -> str:
        if not answer.strip():
            return self.insufficient_message
        return answer.strip()

