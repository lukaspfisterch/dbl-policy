from __future__ import annotations

import pytest
from collections.abc import Mapping

from dbl_core import DblEventKind
from dbl_policy import Policy, PolicyContext, PolicyDecision, decide_safe
from dbl_policy.bridge import decision_to_dbl_event
from dbl_policy.model import (
    DecisionOutcome,
    PolicyId,
    PolicyVersion,
    TenantId,
)
import dbl_policy.reason_codes as reason_codes
from dbl_policy.allow_all import POLICY as ALLOW_POLICY
from dbl_policy.deny_all import POLICY as DENY_POLICY


class ExamplePolicy(Policy):
    def __init__(self, policy_id: PolicyId, policy_version: PolicyVersion) -> None:
        self._policy_id = policy_id
        self._policy_version = policy_version

    @property
    def policy_id(self) -> PolicyId:
        return self._policy_id

    @property
    def policy_version(self) -> PolicyVersion:
        return self._policy_version

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        if context.tenant_id.value == "tenant-deny":
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.TENANT_BLOCKED,
                policy_id=self._policy_id,
                policy_version=self._policy_version,
                tenant_id=context.tenant_id,
            )
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            reason_code=reason_codes.OK,
            policy_id=self._policy_id,
            policy_version=self._policy_version,
            tenant_id=context.tenant_id,
        )


def test_determinism_same_context_same_decision():
    policy = ExamplePolicy(PolicyId("example"), PolicyVersion("1.0.0"))
    context = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"intent_type": "x"})
    d1 = policy.evaluate(context)
    d2 = policy.evaluate(context)
    assert d1 == d2


def test_tenant_scoping_changes_decision():
    policy = ExamplePolicy(PolicyId("example"), PolicyVersion("1.0.0"))
    allow_ctx = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"intent_type": "x"})
    deny_ctx = PolicyContext(tenant_id=TenantId("tenant-deny"), inputs={"intent_type": "x"})
    assert policy.evaluate(allow_ctx).outcome == DecisionOutcome.ALLOW
    assert policy.evaluate(deny_ctx).outcome == DecisionOutcome.DENY


def test_no_observables_in_context():
    with pytest.raises(ValueError, match="context key not whitelisted"):
        PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"runtime": 1})


def test_decision_to_dbl_event():
    decision = PolicyDecision(
        outcome=DecisionOutcome.ALLOW,
        reason_code=reason_codes.OK,
        policy_id=PolicyId("example"),
        policy_version=PolicyVersion("1.0.0"),
        tenant_id=TenantId("tenant-1"),
    )
    event = decision_to_dbl_event(decision, correlation_id="c1")
    assert event.event_kind == DblEventKind.DECISION
    assert isinstance(event.data, Mapping)
    assert event.data["gate"]["decision"] == "ALLOW"
    assert event.data["gate"]["reason_code"] == reason_codes.OK
    assert event.data["policy_id"] == "example"
    assert event.data["policy_version"] == "1.0.0"


def test_allow_all_policy() -> None:
    ctx = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"intent_type": "x"})
    d = ALLOW_POLICY.evaluate(ctx)
    assert d.outcome == DecisionOutcome.ALLOW
    assert d.reason_code == reason_codes.ALLOW_ALL


def test_deny_all_policy() -> None:
    ctx = PolicyContext(tenant_id=TenantId("tenant-1"), inputs={"intent_type": "x"})
    d = DENY_POLICY.evaluate(ctx)
    assert d.outcome == DecisionOutcome.DENY
    assert d.reason_code == reason_codes.DENY_ALL


def test_decide_safe():
    policy = ExamplePolicy(PolicyId("example"), PolicyVersion("1.0.0"))
    
    # Valid input
    d = decide_safe(policy, "t1", {"intent_type": "x"})
    assert d.outcome == DecisionOutcome.ALLOW
    assert d.authoritative_digest != ""
    
    # Invalid context key
    d = decide_safe(policy, "t1", {"unknown": "x"})
    assert d.outcome == DecisionOutcome.DENY
    assert d.reason_code == reason_codes.UNKNOWN_CONTEXT_KEY
    
    # Invalid type (float)
    d = decide_safe(policy, "t1", {"intent_type": 1.5})
    assert d.outcome == DecisionOutcome.DENY
    assert d.reason_code == reason_codes.INVALID_INPUT
    assert "float not allowed" in (d.reason_message or "")


def test_decide_safe_fills_digest_when_policy_omits_it():
    policy = ExamplePolicy(PolicyId("example"), PolicyVersion("1.0.0"))
    d1 = decide_safe(policy, "t1", {"intent_type": "x"})
    d2 = decide_safe(policy, "t1", {"intent_type": "x"})
    assert d1.authoritative_digest != ""
    assert d1.authoritative_digest == d2.authoritative_digest


def test_decide_safe_maps_unexpected_exception():
    class BoomPolicy(ExamplePolicy):
        def evaluate(self, context: PolicyContext) -> PolicyDecision:
            raise RuntimeError("boom")

    policy = BoomPolicy(PolicyId("example"), PolicyVersion("1.0.0"))
    d = decide_safe(policy, "t1", {"intent_type": "x"})
    assert d.outcome == DecisionOutcome.DENY
    assert d.reason_code == reason_codes.EVALUATION_ERROR
