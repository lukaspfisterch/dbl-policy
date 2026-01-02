from __future__ import annotations

from dataclasses import dataclass

from ..model import DecisionOutcome, PolicyContext, PolicyDecision, PolicyId, PolicyVersion
from .. import reason_codes


@dataclass(frozen=True)
class CostGuardPolicy:
    policy_id: PolicyId
    policy_version: PolicyVersion
    config: dict[str, object]

    def evaluate(self, context: PolicyContext) -> PolicyDecision | None:
        cfg = self.config.get("caps", {})
        max_output = cfg.get("max_output_tokens") if isinstance(cfg, dict) else None
        max_input_bytes = cfg.get("max_input_bytes") if isinstance(cfg, dict) else None
        max_input_chars = cfg.get("max_input_chars") if isinstance(cfg, dict) else None
        inputs = context.inputs
        max_tokens = inputs.get("max_output_tokens")
        if isinstance(max_tokens, int) and isinstance(max_output, int) and max_tokens > max_output:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.COST_OUTPUT_TOKENS_CAP,
                reason_message="output tokens cap exceeded",
                policy_id=self.policy_id,
                policy_version=self.policy_version,
                tenant_id=context.tenant_id,
                authoritative_digest=context.compute_authoritative_digest(),
            )
        input_bytes = inputs.get("input_bytes")
        if isinstance(input_bytes, int) and isinstance(max_input_bytes, int) and input_bytes > max_input_bytes:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.COST_INPUT_BYTES_CAP,
                reason_message="input bytes cap exceeded",
                policy_id=self.policy_id,
                policy_version=self.policy_version,
                tenant_id=context.tenant_id,
                authoritative_digest=context.compute_authoritative_digest(),
            )
        input_chars = inputs.get("input_chars")
        if isinstance(input_chars, int) and isinstance(max_input_chars, int) and input_chars > max_input_chars:
            return PolicyDecision(
                outcome=DecisionOutcome.DENY,
                reason_code=reason_codes.COST_INPUT_CHARS_CAP,
                reason_message="input chars cap exceeded",
                policy_id=self.policy_id,
                policy_version=self.policy_version,
                tenant_id=context.tenant_id,
                authoritative_digest=context.compute_authoritative_digest(),
            )
        return None
