# DBL Policy Contract (v0.1.0)

Status: Draft
Scope: dbl-policy tenant-scoped policy evaluation that produces DECISION events only.

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
- Observational fields (trace, success, failure_code, exception_type, trace_digest, runtime) MUST NOT appear in PolicyContext.

## Policy identity and versioning
- Every decision MUST include policy_id and policy_version.
- Policy version changes that alter decisions for identical inputs are breaking changes.

## Output
- A policy returns PolicyDecision with:
  - outcome: ALLOW or DENY
  - reason_code: stable, semantic identifier
  - policy_id, policy_version
  - tenant_id
- Policy decisions MUST be convertible to a dbl-core DECISION event:
  DblEvent(kind=DECISION, data=GateDecision(...))

## Explicit ban on observational fields
- Decisions MUST NOT depend on EXECUTION or PROOF events.
- Decisions MUST NOT depend on any execution trace fields or error text.

## Missing or invalid inputs
- If required inputs are missing or invalid, the policy MUST return DENY.
- The reason_code MUST be stable, e.g. "invalid_input".
reason_message MAY be included but MUST NOT alter the decision outcome.

## Determinism
- Given the same PolicyContext, a policy MUST return the same PolicyDecision.
- No time, randomness, IO, network, environment variables, or mutable globals.
Stable ordering is enforced for top-level input keys only.
