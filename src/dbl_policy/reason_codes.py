"""Stable reason codes for policy decisions."""

OK = "ok"
ALLOW_ALL = "allow_all"
DENY_ALL = "deny_all"

# Rejection codes
INVALID_INPUT = "invalid_input"
UNKNOWN_CONTEXT_KEY = "unknown_context_key"
TENANT_BLOCKED = "tenant_blocked"
MISSING_REQUIRED_INPUT = "missing_required_input"
EVALUATION_ERROR = "evaluation_error"

# Policy pack reason codes
ADMISSION_MISSING_REQUIRED = "admission.missing_required"
ADMISSION_INVALID_VALUE = "admission.invalid_value"
CAPABILITY_DENIED = "capability.denied"
MODEL_DENIED = "model.denied"
COST_OUTPUT_TOKENS_CAP = "cost.output_tokens_cap"
COST_INPUT_BYTES_CAP = "cost.input_bytes_cap"
COST_INPUT_CHARS_CAP = "cost.input_chars_cap"
RISK_HIGH_REQUIRES_OVERRIDE = "risk.high_requires_override"
