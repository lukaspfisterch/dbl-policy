from __future__ import annotations

import pytest

from dbl_core import DblEventKind, GateDecision
from dbl_policy import (
    DecisionOutcome,
    PolicyContext,
    PolicyDecision,
    PolicyId,
    PolicyVersion,
    TenantId,
    decision_to_dbl_event,
)
from dbl_policy.allow_all import POLICY as ALLOW_POLICY
from dbl_policy.deny_all import POLICY as DENY_POLICY


class ExamplePolicy:
    def __init__(self, policy_id: PolicyId, policy_version: PolicyVersion) -> None:
        self._policy_id = policy_id
        self._policy_version = policy_version

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if context.tenant_id.value == "tenant-deny":
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code="tenant_blocked",
                policy_id=self._policy_id,
                policy_version=self._policy_version,
                tenant_id=context.tenant_id,
            )
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            reason_code="ok",
            policy_id=self._policy_id,
            policy_version=self._policy_version,
            tenant_id=context.tenant_id,
        )


def test_determinism_same_context_same_decision():
    policy = ExamplePolicy(PolicyId("example"), PolicyVersion("1.0.0"))
    context = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"use_case": "x"})
    d1 = policy.evaluate(context)
    d2 = policy.evaluate(context)
    assert d1 == d2


def test_tenant_scoping_changes_decision():
    policy = ExamplePolicy(PolicyId("example"), PolicyVersion("1.0.0"))
    allow_ctx = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"use_case": "x"})
    deny_ctx = PolicyContext(tenant_id=TenantId("tenant-deny"), inputs={"use_case": "x"})
    assert policy.evaluate(allow_ctx).outcome == DecisionOutcome.ALLOW
    assert policy.evaluate(deny_ctx).outcome == DecisionOutcome.DENY


def test_no_observables_in_context():
    with pytest.raises(ValueError, match="observational key not allowed"):
        PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"trace": {"x": 1}})


def test_decision_to_dbl_event():
    decision = PolicyDecision(
        outcome=DecisionOutcome.ALLOW,
        reason_code="ok",
        policy_id=PolicyId("example"),
        policy_version=PolicyVersion("1.0.0"),
        tenant_id=TenantId("tenant-1"),
    )
    event = decision_to_dbl_event(decision, correlation_id="c1")
    assert event.event_kind == DblEventKind.DECISION
    assert isinstance(event.data, GateDecision)
    assert event.data.decision == "ALLOW"
    assert event.data.reason_code == "ok"


def test_allow_all_policy() -> None:
    ctx = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"use_case": "x"})
    d = ALLOW_POLICY.evaluate(ctx)
    assert d.outcome == DecisionOutcome.ALLOW
    assert d.reason_code == "allow_all"


def test_deny_all_policy() -> None:
    ctx = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"use_case": "x"})
    d = DENY_POLICY.evaluate(ctx)
    assert d.outcome == DecisionOutcome.DENY
    assert d.reason_code == "deny_all"
