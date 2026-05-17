from app.models.domain import Role, SensitivityLevel


SENSITIVITY_ORDER = {
    SensitivityLevel.public: 0,
    SensitivityLevel.internal: 1,
    SensitivityLevel.confidential: 2,
    SensitivityLevel.restricted: 3,
}

DEFAULT_ROLE_CLEARANCE = {
    Role.admin: SensitivityLevel.restricted,
    Role.hr: SensitivityLevel.confidential,
    Role.finance: SensitivityLevel.confidential,
    Role.engineering: SensitivityLevel.internal,
    Role.compliance: SensitivityLevel.restricted,
    Role.operations: SensitivityLevel.confidential,
    Role.guest: SensitivityLevel.public,
}


def max_clearance_for_roles(roles: list[Role]) -> SensitivityLevel:
    return max((DEFAULT_ROLE_CLEARANCE[r] for r in roles), key=lambda level: SENSITIVITY_ORDER[level])


def sensitivity_allows(clearance: SensitivityLevel, required: SensitivityLevel) -> bool:
    return SENSITIVITY_ORDER[clearance] >= SENSITIVITY_ORDER[required]

