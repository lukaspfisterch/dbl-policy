from __future__ import annotations

from dataclasses import dataclass

from ..model import DecisionOutcome, PolicyContext, PolicyDecision, PolicyId, PolicyVersion
from .. import reason_codes
from .admission import AdmissionPolicy
from .capability_allowlist import CapabilityAllowlistPolicy
from .model_allowlist import ModelAllowlistPolicy
from .cost_guard import CostGuardPolicy
from .risk_gate import RiskGatePolicy


POLICY_CONFIG = {
    "capabilities": {
        "default": ["chat"],
        "per_workspace": {},
    },
    "models": {
        "per_capability": {
            "chat": ["gpt-4o-mini", "claude-3-haiku-20240307"],
        },
        "providers_per_capability": {
            "chat": ["openai", "anthropic"],
        },
    },
    "caps": {
        "max_output_tokens": 8192,
        "max_input_bytes": 200_000,
        "max_input_chars": 200_000,
    },
    "risk": {
        "override_tag": "override_ack",
        "privileged_principals": [],
    },
}


@dataclass(frozen=True)
class ComposePolicy:
    policy_id: PolicyId = PolicyId("dbl_policy.compose")
    policy_version: PolicyVersion = PolicyVersion("0.2.2")

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        for policy in (
            AdmissionPolicy(self.policy_id, self.policy_version),
            CapabilityAllowlistPolicy(self.policy_id, self.policy_version, POLICY_CONFIG),
            ModelAllowlistPolicy(self.policy_id, self.policy_version, POLICY_CONFIG),
            CostGuardPolicy(self.policy_id, self.policy_version, POLICY_CONFIG),
            RiskGatePolicy(self.policy_id, self.policy_version, POLICY_CONFIG),
        ):
            decision = policy.evaluate(context)
            if decision is not None:
                return decision
        return PolicyDecision(
            outcome=DecisionOutcome.ALLOW,
            reason_code=reason_codes.OK,
            policy_id=self.policy_id,
            policy_version=self.policy_version,
            tenant_id=context.tenant_id,
            authoritative_digest=context.compute_authoritative_digest(),
        )


POLICY = ComposePolicy()
policy = POLICY
