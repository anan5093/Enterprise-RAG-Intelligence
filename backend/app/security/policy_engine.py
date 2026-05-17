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

        principal_roles = {
            str(getattr(r, "value", r)).lower()
            for r in principal.roles
        }

        allowed_roles = {
            str(getattr(r, "value", r)).lower()
            for r in metadata.allowed_roles
        }

        # Admin bypass
        if "admin" in principal_roles:
            return PolicyDecision(True, "Admin role bypass granted")

        # RBAC role check
        if not principal_roles.intersection(allowed_roles):
            return PolicyDecision(False, "Principal role is not in allowed_roles")

        # Department check
        if metadata.department not in principal.departments and metadata.department != "global":
            return PolicyDecision(False, "Principal department does not match document department")

        # Sensitivity clearance check
        if not sensitivity_allows(principal.clearance, metadata.sensitivity_level):
            return PolicyDecision(False, "Principal clearance below sensitivity_level")

        return PolicyDecision(True, "Role, department, and sensitivity checks passed")

