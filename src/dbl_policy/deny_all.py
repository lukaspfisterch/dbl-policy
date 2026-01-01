from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .model import (
    DecisionOutcome,
    PolicyContext,
    PolicyDecision,
    PolicyId,
    PolicyVersion,
    TenantId,
)


@dataclass(frozen=True)
class DenyAllPolicy:
    policy_id: PolicyId = PolicyId("dbl_policy.deny_all")
    policy_version: PolicyVersion = PolicyVersion("1.0.0")

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code="deny_all",
            reason_message="default deny-all policy",
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            tenant_id=context.tenant_id,
        )


POLICY = DenyAllPolicy()
policy = POLICY


def evaluate(context: PolicyContext) -> PolicyDecision:
    return POLICY.evaluate(context)


def decide(*, tenant_id: str, inputs: Mapping[str, Any]) -> PolicyDecision:
    ctx = PolicyContext(tenant_id=TenantId(tenant_id), inputs=inputs)
    return POLICY.evaluate(ctx)
