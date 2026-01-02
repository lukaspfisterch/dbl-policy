from __future__ import annotations

from dataclasses import dataclass

from ..model import DecisionOutcome, PolicyContext, PolicyDecision, PolicyId, PolicyVersion
from .. import reason_codes


REQUIRED_KEYS = ("principal_id", "intent_type", "capability", "model_id")


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _non_negative_int(value: object) -> bool:
    return isinstance(value, int) and value >= 0


@dataclass(frozen=True)
class AdmissionPolicy:
    policy_id: PolicyId
    policy_version: PolicyVersion

    def evaluate(self, context: PolicyContext) -> PolicyDecision | None:
        inputs = context.inputs
        for key in REQUIRED_KEYS:
            if not _non_empty_str(inputs.get(key)):
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    reason_code=reason_codes.ADMISSION_MISSING_REQUIRED,
                    reason_message=f"missing {key}",
                    policy_id=self.policy_id,
                    policy_version=self.policy_version,
                    tenant_id=context.tenant_id,
                    authoritative_digest=context.compute_authoritative_digest(),
                )

        for key in ("workspace_id", "provider", "risk_tier"):
            if key in inputs and not _non_empty_str(inputs.get(key)):
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    reason_code=reason_codes.ADMISSION_INVALID_VALUE,
                    reason_message=f"invalid {key}",
                    policy_id=self.policy_id,
                    policy_version=self.policy_version,
                    tenant_id=context.tenant_id,
                    authoritative_digest=context.compute_authoritative_digest(),
                )

        for key in ("max_output_tokens", "input_bytes", "input_chars"):
            if key in inputs and not _non_negative_int(inputs.get(key)):
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    reason_code=reason_codes.ADMISSION_INVALID_VALUE,
                    reason_message=f"invalid {key}",
                    policy_id=self.policy_id,
                    policy_version=self.policy_version,
                    tenant_id=context.tenant_id,
                    authoritative_digest=context.compute_authoritative_digest(),
                )

        tags = inputs.get("request_tags")
        if tags is not None:
            if not isinstance(tags, list) or not all(_non_empty_str(tag) for tag in tags):
                return PolicyDecision(
                    outcome=DecisionOutcome.DENY,
                    reason_code=reason_codes.ADMISSION_INVALID_VALUE,
                    reason_message="invalid request_tags",
                    policy_id=self.policy_id,
                    policy_version=self.policy_version,
                    tenant_id=context.tenant_id,
                    authoritative_digest=context.compute_authoritative_digest(),
                )

        return None
