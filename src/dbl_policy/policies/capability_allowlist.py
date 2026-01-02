from __future__ import annotations

from dataclasses import dataclass

from ..model import DecisionOutcome, PolicyContext, PolicyDecision, PolicyId, PolicyVersion
from .. import reason_codes


@dataclass(frozen=True)
class CapabilityAllowlistPolicy:
    policy_id: PolicyId
    policy_version: PolicyVersion
    config: dict[str, object]

    def evaluate(self, context: PolicyContext) -> PolicyDecision | None:
        inputs = context.inputs
        capability = inputs.get("capability")
        workspace_id = inputs.get("workspace_id")
        if not isinstance(capability, str):
            return None
        cfg = self.config.get("capabilities", {})
        default = set(cfg.get("default", [])) if isinstance(cfg, dict) else set()
        workspace_caps = cfg.get("per_workspace", {}) if isinstance(cfg, dict) else {}
        allowed = default
        if isinstance(workspace_id, str) and isinstance(workspace_caps, dict):
            workspace_allowed = workspace_caps.get(workspace_id)
            if isinstance(workspace_allowed, list):
                allowed = set(workspace_allowed)
        if capability not in allowed:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.CAPABILITY_DENIED,
                reason_message=f"capability {capability} denied",
                policy_id=self.policy_id,
                policy_version=self.policy_version,
                tenant_id=context.tenant_id,
                authoritative_digest=context.compute_authoritative_digest(),
            )
        return None
