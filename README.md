# DBL Policy

DBL Policy provides deterministic, tenant-scoped policy evaluation that produces DECISION events only. It does not execute tasks.

## Scope
- Policy decisions derived only from authoritative inputs.
- No execution, no orchestration, no IO side effects.

## Contract
- docs/dbl_policy_contract.md

## Install

```bash
pip install dbl-policy
```

Requires `dbl-core>=0.3.0`, Python 3.11+.

## Usage

```python
from dbl_policy import (
    PolicyContext,
    PolicyDecision,
    PolicyId,
    PolicyVersion,
    TenantId,
    DecisionOutcome,
    decision_to_dbl_event,
)

context = PolicyContext(
    tenant_id=TenantId("tenant-1"),
    inputs={"use_case": "llm-generate"},
)

decision = PolicyDecision(
    outcome=DecisionOutcome.ALLOW,
    reason_code="ok",
    policy_id=PolicyId("example"),
    policy_version=PolicyVersion("1.0.0"),
    tenant_id=context.tenant_id,
)

event = decision_to_dbl_event(decision, correlation_id="c1")
```

## License

MIT License. See LICENSE.
