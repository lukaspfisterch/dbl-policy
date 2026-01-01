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
class AllowAllPolicy:
    policy_id: PolicyId = PolicyId("dbl_policy.allow_all")
    policy_version: PolicyVersion = PolicyVersion("1.0.0")

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            reason_code="allow_all",
            reason_message="development allow-all policy",
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            tenant_id=context.tenant_id,
        )


POLICY = AllowAllPolicy()
policy = POLICY


def evaluate(context: PolicyContext) -> PolicyDecision:
    return POLICY.evaluate(context)


def decide(*, tenant_id: str, inputs: Mapping[str, Any]) -> PolicyDecision:
    ctx = PolicyContext(tenant_id=TenantId(tenant_id), inputs=inputs)
    return POLICY.evaluate(ctx)
