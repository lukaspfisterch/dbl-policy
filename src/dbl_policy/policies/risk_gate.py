from __future__ import annotations

from dataclasses import dataclass

from ..model import DecisionOutcome, PolicyContext, PolicyDecision, PolicyId, PolicyVersion
from .. import reason_codes


@dataclass(frozen=True)
class RiskGatePolicy:
    policy_id: PolicyId
    policy_version: PolicyVersion
    config: dict[str, object]

    def evaluate(self, context: PolicyContext) -> PolicyDecision | None:
        inputs = context.inputs
        risk_tier = inputs.get("risk_tier")
        if risk_tier != "high":
            return None
        cfg = self.config.get("risk", {})
        override_tag = cfg.get("override_tag") if isinstance(cfg, dict) else None
        privileged = cfg.get("privileged_principals") if isinstance(cfg, dict) else None
        tags = inputs.get("request_tags")
        principal_id = inputs.get("principal_id")
        if (
            isinstance(principal_id, str)
            and isinstance(privileged, list)
            and principal_id in privileged
        ):
            return None
        if isinstance(tags, list) and isinstance(override_tag, str) and override_tag in tags:
            return None
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code=reason_codes.RISK_HIGH_REQUIRES_OVERRIDE,
            reason_message="high risk requires override",
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            tenant_id=context.tenant_id,
            authoritative_digest=context.compute_authoritative_digest(),
        )
