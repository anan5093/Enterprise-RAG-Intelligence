# Security and RBAC

The security boundary is implemented in `backend/app/security` and called by `HybridRetriever` before context assembly.

## Enforcement Invariant

The LLM receives only `authorized` chunks. Candidate retrieval may find restricted chunks, but those chunks are removed by `RBACFilter` before reranking and before `PromptBuilder`.

## Policy Inputs

Each chunk carries:

- `access_level`
- `allowed_roles`
- `sensitivity_level`
- `department`
- `rbac_tags`
- `owner`
- `lineage_id`

Each principal carries:

- `roles`
- `departments`
- `clearance`
- `user_id`

## Denial Behavior

If an Engineering employee asks for payroll data:

1. Retrieval may find finance payroll candidates.
2. RBAC rejects them because Engineering is not in `allowed_roles`, department does not match, and clearance is too low.
3. The denied chunks are excluded from the prompt.
4. The answer is `Insufficient authorized data available.`
5. The attempt is logged with denied count and route metadata.

## Production Hardening

- Replace demo users with OIDC/SAML identity provider claims.
- Store policies in versioned policy-as-code, such as OPA/Rego.
- Encrypt audit logs and configure immutable retention.
- Use managed vector DB with private networking and tenant-scoped namespaces.
- Apply API gateway rate limits and WAF controls.
- Rotate JWT signing keys and use short-lived access tokens.

