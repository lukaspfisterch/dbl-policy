from __future__ import annotations

from dataclasses import dataclass

from ..model import DecisionOutcome, PolicyContext, PolicyDecision, PolicyId, PolicyVersion
from .. import reason_codes


@dataclass(frozen=True)
class ModelAllowlistPolicy:
    policy_id: PolicyId
    policy_version: PolicyVersion
    config: dict[str, object]

    def evaluate(self, context: PolicyContext) -> PolicyDecision | None:
        inputs = context.inputs
        capability = inputs.get("capability")
        model_id = inputs.get("model_id")
        provider = inputs.get("provider")
        if not isinstance(capability, str) or not isinstance(model_id, str):
            return None
        cfg = self.config.get("models", {})
        per_capability = cfg.get("per_capability", {}) if isinstance(cfg, dict) else {}
        provider_map = cfg.get("providers_per_capability", {}) if isinstance(cfg, dict) else {}
        allowed_models = per_capability.get(capability) if isinstance(per_capability, dict) else None
        if not isinstance(allowed_models, list) or model_id not in allowed_models:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.MODEL_DENIED,
                reason_message=f"model {model_id} denied",
                policy_id=self.policy_id,
                policy_version=self.policy_version,
                tenant_id=context.tenant_id,
                authoritative_digest=context.compute_authoritative_digest(),
            )
        if isinstance(provider, str):
            allowed_providers = provider_map.get(capability) if isinstance(provider_map, dict) else None
            if isinstance(allowed_providers, list) and provider not in allowed_providers:
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    reason_code=reason_codes.MODEL_DENIED,
                    reason_message=f"provider {provider} denied",
                    policy_id=self.policy_id,
                    policy_version=self.policy_version,
                    tenant_id=context.tenant_id,
                    authoritative_digest=context.compute_authoritative_digest(),
                )
        return None
