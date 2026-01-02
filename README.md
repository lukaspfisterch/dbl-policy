# DBL Policy

Deterministic, tenant-scoped policy evaluation for DBL.
This package produces DECISION events only. It does not execute tasks.

## What it is

`dbl-policy` is the normative gate in the DBL stack:

- It evaluates a policy from authoritative inputs only
- It returns ALLOW or DENY with stable reason codes
- It can be bridged into a `dbl-core` DECISION event with a strict, contract-shaped `data` mapping
- It is pure: no IO, no time, no randomness, no env, no network, no trace-dependence

## Non-goals

- No execution
- No orchestration
- No reading or depending on observational fields (trace, runtime, exceptions, etc.)
- No mutation of event streams

## Contract

The authoritative specification is in:
- `docs/dbl_policy_contract.md`

Key invariants enforced by this package:

- Inputs must be JSON-safe and deterministic
  - No floats (including nested)
  - Mapping keys must be exact `str` (no subclasses)
- Policy input is whitelisted
  - Unknown keys are rejected
- `PolicyContext` is snapshotted
  - Caller mutation after construction cannot affect evaluation or digest
- Output can be converted into a `dbl-core` DECISION event
  - `DECISION.data` is a Mapping with a strict shape
  - Includes policy lineage: `policy_id`, `policy_version`, `tenant_id`

## Install

```bash
pip install dbl-policy
```

Requires Python 3.11+ and `dbl-core>=0.3,<0.4`.

## Quickstart

1) Use a built-in policy

```python
from dbl_policy import PolicyContext, TenantId
from dbl_policy.allow_all import POLICY as ALLOW_ALL

ctx = PolicyContext(
    tenant_id=TenantId("tenant-1"),
    inputs={"use_case": "llm-generate"},
)

decision = ALLOW_ALL.evaluate(ctx)
```

2) Convert a decision to a DBL DECISION event

```python
from dbl_policy import decision_to_dbl_event

event = decision_to_dbl_event(decision, correlation_id="c1")
```

`event.data` will be shaped like:

```python
{
  "policy_id": "...",
  "policy_version": "...",
  "tenant_id": "...",
  "gate": {
    "decision": "ALLOW" | "DENY",
    "reason_code": "...",
    # "reason_message": "..." (optional)
  }
}
```

## Writing your own policy

Policies only implement `evaluate(context)` and must be deterministic.

```python
from dataclasses import dataclass
from dbl_policy import (
    PolicyContext,
    PolicyDecision,
    PolicyId,
    PolicyVersion,
    DecisionOutcome,
)
from dbl_policy import reason_codes


@dataclass(frozen=True)
class ExamplePolicy:
    policy_id: PolicyId = PolicyId("example")
    policy_version: PolicyVersion = PolicyVersion("1.0.0")

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        use_case = context.inputs.get("use_case")
        if use_case == "blocked":
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.TENANT_BLOCKED,
                reason_message="blocked use_case",
                policy_id=self.policy_id,
                policy_version=self.policy_version,
                tenant_id=context.tenant_id,
            )
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            reason_code=reason_codes.OK,
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            tenant_id=context.tenant_id,
        )
```

## Safe evaluation (recommended)

`decide_safe` wraps context validation and converts failures into a stable DENY.

- Valid inputs: evaluates policy, ensures `authoritative_digest` is populated
- Invalid inputs: DENY with stable reason_code
- Exceptions during evaluation: DENY with `evaluation_error`

```python
from dbl_policy import decide_safe
from dbl_policy.allow_all import POLICY

d1 = decide_safe(POLICY, "tenant-1", {"use_case": "x"})
d2 = decide_safe(POLICY, "tenant-1", {"unknown_key": "x"})  # -> DENY
```

## Reason codes

Reason codes are stable semantic identifiers:

- ok
- allow_all
- deny_all
- invalid_input
- unknown_context_key
- tenant_blocked
- missing_required_input
- evaluation_error

See `src/dbl_policy/reason_codes.py`.

## Development

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

