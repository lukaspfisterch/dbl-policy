# DBL Policy Contract (v0.2.0)

Status: Draft
Scope: dbl-policy tenant-scoped policy evaluation that produces DECISION events only.
Contract version may lag package patch versions.

## Scope
- Evaluate policy decisions deterministically from authoritative inputs.
- Emit ALLOW or DENY decisions as dbl-core DECISION events.

## Non-Goals
- dbl-policy MUST NOT execute tasks.
- dbl-policy MUST NOT call kl-kernel-logic.
- dbl-policy MUST NOT orchestrate pipelines or workflows.
- dbl-policy MUST NOT read or depend on execution traces or observational fields.
- dbl-policy MUST NOT mutate V or other event streams.

## Tenant scoping
- All decisions MUST be scoped to a tenant_id.
- A policy MAY return different decisions for different tenant_id values.

## Authoritative inputs
- PolicyContext contains only authoritative inputs.
- PolicyContext inputs MUST be JSON-serializable.
- Mapping keys MUST be exact str (no subclasses).
- PolicyContext inputs are snapshotted at construction time; caller mutation MUST NOT affect evaluation or digest.
- Observational fields (trace, success, failure_code, exception_type, trace_digest, runtime) MUST NOT appear in PolicyContext.

## Policy identity and versioning
- Every decision MUST include policy_id and policy_version.
- Policy version changes that alter decisions for identical inputs are breaking changes.
- policy_version refers to the policy definition version, not the Python package version.

## Output
- A policy returns PolicyDecision with:
  - outcome: ALLOW or DENY
  - reason_code: stable, semantic identifier
  - policy_id, policy_version
  - tenant_id
- Policy decisions MUST be converted to a dbl-core DECISION event with data as a Mapping:
  DblEvent(kind=DECISION, data=Mapping)
- The DECISION.data MUST contain exactly these fields:
  - policy_id: str
  - policy_version: str
  - tenant_id: str
  - gate: mapping
    - decision: "ALLOW" | "DENY"
    - reason_code: str
    - reason_message: str (optional)
- No other fields are allowed in DECISION.data.

## Authoritative digest (PolicyDecision.authoritative_digest)
- authoritative_digest is a deterministic digest of PolicyContext.inputs only.
- It is optional for policies to set, but decide_safe MUST populate it for valid inputs.
- For invalid inputs, authoritative_digest MUST be empty.
- authoritative_digest MUST NOT be emitted into DECISION.data.

## Explicit ban on observational fields
- Decisions MUST NOT depend on EXECUTION or PROOF events.
- Decisions MUST NOT depend on any execution trace fields or error text.

## Missing or invalid inputs
- If required inputs are missing or invalid, the policy MUST return DENY.
- The reason_code MUST be stable, e.g. "invalid_input".
  - invalid_input for input validation failures.
  - evaluation_error for unexpected exceptions during policy evaluation.
reason_message MAY be included but MUST NOT alter the decision outcome.

## Determinism
- Given the same PolicyContext, a policy MUST return the same PolicyDecision.
- No time, randomness, IO, network, environment variables, or mutable globals.
Stable ordering is enforced for mapping keys.
Canonicalization sorts mapping keys recursively (nested mappings), lists preserve order.
