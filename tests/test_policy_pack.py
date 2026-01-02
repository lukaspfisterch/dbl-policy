from __future__ import annotations

from dbl_policy import DecisionOutcome, PolicyContext, TenantId, reason_codes
from dbl_policy.policies.compose import POLICY


def _base_inputs() -> dict[str, object]:
    return {
        "principal_id": "p1",
        "intent_type": "chat.message",
        "capability": "chat",
        "model_id": "gpt-4o-mini",
        "provider": "openai",
        "max_output_tokens": 256,
        "input_bytes": 100,
        "input_chars": 100,
        "request_tags": [],
    }


def test_capability_allowlist_denies() -> None:
    inputs = _base_inputs()
    inputs["capability"] = "other"
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=inputs)
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.DENY
    assert decision.reason_code == reason_codes.CAPABILITY_DENIED


def test_capability_allowlist_allows() -> None:
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=_base_inputs())
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.ALLOW


def test_model_allowlist_denies() -> None:
    inputs = _base_inputs()
    inputs["model_id"] = "unknown"
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=inputs)
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.DENY
    assert decision.reason_code == reason_codes.MODEL_DENIED


def test_model_allowlist_allows() -> None:
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=_base_inputs())
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.ALLOW


def test_cost_guard_denies_output_tokens() -> None:
    inputs = _base_inputs()
    inputs["max_output_tokens"] = 9000
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=inputs)
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.DENY
    assert decision.reason_code == reason_codes.COST_OUTPUT_TOKENS_CAP


def test_cost_guard_denies_input_bytes() -> None:
    inputs = _base_inputs()
    inputs["input_bytes"] = 500_000
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=inputs)
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.DENY
    assert decision.reason_code == reason_codes.COST_INPUT_BYTES_CAP


def test_cost_guard_denies_input_chars() -> None:
    inputs = _base_inputs()
    inputs["input_chars"] = 500_000
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=inputs)
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.DENY
    assert decision.reason_code == reason_codes.COST_INPUT_CHARS_CAP


def test_risk_gate_denies_without_override() -> None:
    inputs = _base_inputs()
    inputs["risk_tier"] = "high"
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=inputs)
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.DENY
    assert decision.reason_code == reason_codes.RISK_HIGH_REQUIRES_OVERRIDE


def test_risk_gate_allows_with_override() -> None:
    inputs = _base_inputs()
    inputs["risk_tier"] = "high"
    inputs["request_tags"] = ["override_ack"]
    ctx = PolicyContext(tenant_id=TenantId("t1"), inputs=inputs)
    decision = POLICY.evaluate(ctx)
    assert decision.outcome == DecisionOutcome.ALLOW
