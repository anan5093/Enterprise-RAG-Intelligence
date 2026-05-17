from dataclasses import dataclass

from app.models.domain import DocumentChunk, Principal, Role
from app.security.permissions import sensitivity_allows


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


class PolicyEngine:
    """Centralized RBAC/ABAC policy engine used before any LLM context assembly."""

    def can_access_chunk(self, principal: Principal, chunk: DocumentChunk) -> PolicyDecision:
        metadata = chunk.metadata
        if Role.admin in principal.roles:
            return PolicyDecision(True, "Admin role bypass granted")
        if not set(principal.roles).intersection(metadata.allowed_roles):
            return PolicyDecision(False, "Principal role is not in allowed_roles")
        if metadata.department not in principal.departments and metadata.department != "global":
            return PolicyDecision(False, "Principal department does not match document department")
        if not sensitivity_allows(principal.clearance, metadata.sensitivity_level):
            return PolicyDecision(False, "Principal clearance below sensitivity_level")
        return PolicyDecision(True, "Role, department, and sensitivity checks passed")

