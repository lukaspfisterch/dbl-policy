# DBL Policy

[![Tests](https://github.com/lukaspfisterch/dbl-policy/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/lukaspfisterch/dbl-policy/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/dbl-policy.svg)](https://pypi.org/project/dbl-policy/)
[![Python >=3.11](https://img.shields.io/pypi/pyversions/dbl-policy.svg?label=Python)](https://pypi.org/project/dbl-policy/)
[![Typing: Typed](https://img.shields.io/badge/typing-typed-2d7f5e.svg)](https://pypi.org/project/dbl-policy/)

Deterministic, tenant-scoped policy evaluation for DBL.
This package produces DECISION events only. It does not execute tasks.
Status: Stable

## Why this exists

Governance needs two separate things:

- a decision contract
- a decision algebra

`dbl-policy` is the first part.

It does not define how governance logic is assembled.
It defines what a policy decision is:

- `PolicyContext` in
- `PolicyDecision` out
- pure evaluation
- authoritative inputs only
- deterministic output

`dbl-policy-gates` is the second part.
It defines how decisions are built.

In DBL terms, `dbl-policy` is the normative boundary of the stack.
It is the point where execution mechanics end and authoritative decisions begin.

## What it is

`dbl-policy` is the contract layer for policy in the DBL stack:

- It evaluates a policy from authoritative inputs only
- It returns ALLOW or DENY with stable reason codes
- It can be bridged into a `dbl-core` DECISION event with a strict, contract-shaped `data` mapping
- It is pure: no IO, no time, no randomness, no env, no network, no trace-dependence

## Position in the stack

```text
execution mechanics
    -> dbl-core

policy contract
    -> dbl-policy

policy algebra
    -> dbl-policy-gates

domain policies
```

Short version:

`dbl-policy` defines what a decision is.
`dbl-policy-gates` defines how decisions are built.

Execution can exist without governance.
Normativity enters the system here.

## Non-goals

- No execution
- No orchestration
- No reading or depending on observational fields (trace, runtime, exceptions, etc.)
- No mutation of event streams

## Contract

The authoritative specification is in:
- `docs/dbl_policy_contract.md`
- `docs/ARCHITECTURE.md`

Architecture direction:

- `dbl-policy` is the contract and bridge layer
- `dbl-policy-gates` is the gate algebra layer
- domain policies are root-level assemblies built on top

Composition lives in `dbl-policy-gates`.

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
from dbl_policy import PolicyContext
from dbl_policy.model import TenantId
from dbl_policy.allow_all import POLICY as ALLOW_ALL

ctx = PolicyContext(
    tenant_id=TenantId("tenant-1"),
    inputs={"intent_type": "chat.message"},
)

decision = ALLOW_ALL.evaluate(ctx)
```

2) Convert a decision to a DBL DECISION event

```python
from dbl_policy.bridge import decision_to_dbl_event

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
from dbl_policy import PolicyContext, PolicyDecision
from dbl_policy.model import DecisionOutcome, PolicyId, PolicyVersion
import dbl_policy.reason_codes as reason_codes


@dataclass(frozen=True)
class ExamplePolicy:
    policy_id: PolicyId = PolicyId("example")
    policy_version: PolicyVersion = PolicyVersion("1.0.0")

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        intent_type = context.inputs.get("intent_type")
        if intent_type == "blocked":
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.TENANT_BLOCKED,
                reason_message="blocked intent_type",
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

In practice, most domain policies should now be assembled with
`dbl-policy-gates` and exposed through a root policy object.
Use a handwritten `Policy` implementation only when you need custom logic that
does not fit the gate algebra.

## Safe evaluation (recommended)

`decide_safe` wraps context validation and converts failures into a stable DENY.

- Valid inputs: evaluates policy, ensures `authoritative_digest` is populated
- Invalid inputs: DENY with stable reason_code
- Exceptions during evaluation: DENY with `evaluation_error`

```python
from dbl_policy import decide_safe
from dbl_policy.allow_all import POLICY

d1 = decide_safe(POLICY, "tenant-1", {"intent_type": "x"})
d2 = decide_safe(POLICY, "tenant-1", {"unknown_key": "x"})  # -> DENY
```

## Allowed context keys

The contract enforces a strict whitelist:
- principal_id
- workspace_id
- intent_type
- capability
- model_id
- provider
- max_output_tokens
- input_bytes
- input_chars
- risk_tier
- request_tags
- extensions

## Legacy removal

The pre-alignment starter policy pack from `dbl_policy.policies` has been
removed in `0.3.0`.

- It is superseded by the `dbl-policy-gates` algebra layer.
- `dbl-policy` now focuses on protocol, validation, and bridge concerns only.
- See `docs/ARCHITECTURE.md` and `docs/MIGRATION_0_3.md`.

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
- admission.missing_required
- admission.invalid_value
- capability.denied
- model.denied
- cost.output_tokens_cap
- cost.input_bytes_cap
- cost.input_chars_cap
- risk.high_requires_override

See [src/dbl_policy/reason_codes.py](/mnt/d/DEV/projects/dbl-policy/src/dbl_policy/reason_codes.py).

## Development

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```
