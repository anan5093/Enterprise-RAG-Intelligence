import pytest

from app.models.domain import DataSourceType, DocumentChunk, DocumentMetadata, Principal, Role, SensitivityLevel
from app.security.rbac import RBACFilter


def make_chunk(allowed_roles: list[Role], department: str, sensitivity: SensitivityLevel) -> DocumentChunk:
    return DocumentChunk(
        text="Payroll data for finance leadership only",
        metadata=DocumentMetadata(
            source="payroll.csv",
            source_type=DataSourceType.csv,
            department=department,
            confidentiality=sensitivity,
            owner="finance",
            allowed_roles=allowed_roles,
            sensitivity_level=sensitivity,
            access_level=sensitivity,
        ),
    )


def test_engineering_cannot_access_finance_payroll_chunk():
    principal = Principal(
        user_id="eng_user",
        username="eng_user",
        roles=[Role.engineering],
        departments=["engineering"],
        clearance=SensitivityLevel.internal,
    )
    chunk = make_chunk([Role.finance], "finance", SensitivityLevel.confidential)

    allowed, denied, explanations = RBACFilter().filter_chunks(principal, [chunk])

    assert allowed == []
    assert denied == [chunk]
    assert "allowed_roles" in explanations[0]


def test_admin_can_access_restricted_chunks():
    principal = Principal(
        user_id="admin",
        username="admin",
        roles=[Role.admin],
        departments=["global"],
        clearance=SensitivityLevel.restricted,
    )
    chunk = make_chunk([Role.finance], "finance", SensitivityLevel.restricted)

    allowed, denied, _ = RBACFilter().filter_chunks(principal, [chunk])

    assert allowed == [chunk]
    assert denied == []

