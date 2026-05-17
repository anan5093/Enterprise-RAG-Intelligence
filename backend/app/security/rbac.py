from app.models.domain import DocumentChunk, Principal
from app.security.policy_engine import PolicyEngine


class RBACFilter:
    def __init__(self, policy_engine: PolicyEngine | None = None) -> None:
        self.policy_engine = policy_engine or PolicyEngine()

    def filter_chunks(self, principal: Principal, chunks: list[DocumentChunk]) -> tuple[list[DocumentChunk], list[DocumentChunk], list[str]]:
        allowed: list[DocumentChunk] = []
        denied: list[DocumentChunk] = []
        explanations: list[str] = []
        for chunk in chunks:
            decision = self.policy_engine.can_access_chunk(principal, chunk)
            if decision.allowed:
                allowed.append(chunk)
            else:
                denied.append(chunk)
                explanations.append(f"{chunk.chunk_id}: {decision.reason}")
        return allowed, denied, explanations

