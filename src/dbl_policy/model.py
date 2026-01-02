from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import copy
import hashlib
import json
from typing import Any, Mapping, Protocol

from .validate import ensure_json_safe, ValidationError


from . import reason_codes


@dataclass(frozen=True)
class PolicyId:
    value: str


@dataclass(frozen=True)
class PolicyVersion:
    value: str


@dataclass(frozen=True)
class TenantId:
    value: str


class DecisionOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


# Explicit whitelist of allowed keys in PolicyContext.
# This ensures that policies never "accidentally" see observational or unvetted inputs.
ALLOWED_CONTEXT_KEYS = {
    "use_case",
    "resource_id",
    "action",
    "subject_id",
    "subject_roles",
    "metadata",
    "extensions",
}


def _canonicalize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    items: dict[str, Any] = {}
    for key in sorted(value.keys()):
        items[key] = value[key]
    return items


def _canonicalize_for_digest(value: Any) -> Any:
    if isinstance(value, Mapping):
        items: dict[str, Any] = {}
        for k in sorted(value.keys(), key=str):
            sk = str(k)
            items[sk] = _canonicalize_for_digest(value[k])
        return items
    if isinstance(value, list):
        return [_canonicalize_for_digest(item) for item in value]
    return value


def _json_dumps(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("utf-8")


def _digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class PolicyContext:
    tenant_id: TenantId
    inputs: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.inputs, Mapping):
            raise TypeError("inputs must be a mapping")
        
        # 1. Enforce JSON-safe / Canonical-safety FIRST (Lücke B + Harden)
        # This recursively checks for floats, NaN, and crucially verifies 
        # that all keys are strings.
        ensure_json_safe(self.inputs)

        # 2. Enforce whitelist (Lücke A)
        # Since we now know all keys are strings, this check is clean.
        for key in self.inputs.keys():
            if key not in ALLOWED_CONTEXT_KEYS:
                raise ValueError(f"context key not whitelisted: {key}")

        # Snapshot: canonicalize + deep copy to prevent caller mutation.
        canonical = _canonicalize_for_digest(self.inputs)
        object.__setattr__(self, "inputs", copy.deepcopy(canonical))

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id.value,
            "inputs": _canonicalize_mapping(self.inputs),
        }

    def compute_authoritative_digest(self) -> str:
        """
        Compute the sha256 digest of the canonicalized inputs.
        This provides the optional anchor for the decision.

        Canonicalization assumes inputs were validated with ensure_json_safe:
        - dict keys sorted
        - lists preserved
        - JSON encoded with ensure_ascii=True, compact separators, UTF-8 bytes
        """
        payload = _json_dumps(self.inputs)
        return _digest_bytes(payload)


@dataclass(frozen=True)
class PolicyDecision:
    outcome: DecisionOutcome
    reason_code: str
    policy_id: PolicyId
    policy_version: PolicyVersion
    tenant_id: TenantId
    authoritative_digest: str = ""
    reason_message: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in (DecisionOutcome.ALLOW, DecisionOutcome.DENY):
            raise ValueError("invalid decision outcome")
        if not self.reason_code:
            raise ValueError("reason_code is required")


class Policy(Protocol):
    @property
    def policy_id(self) -> PolicyId: ...
    @property
    def policy_version(self) -> PolicyVersion: ...

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        ...


def decide_safe(
    policy: Policy, tenant_id: str, inputs: Mapping[str, Any]
) -> PolicyDecision:
    """
    Evaluate policy safely according to contract.
    
    If inputs are invalid or missing, returns DENY with a stable reason_code
    instead of raising exceptions. The authoritative_digest is empty in those cases.
    """
    tid = TenantId(tenant_id)
    try:
        ctx = PolicyContext(tenant_id=tid, inputs=inputs)
        decision = policy.evaluate(ctx)
        if decision.authoritative_digest:
            return decision
        return replace(decision, authoritative_digest=ctx.compute_authoritative_digest())
    except ValidationError as e:
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code=reason_codes.INVALID_INPUT,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            tenant_id=tid,
            authoritative_digest="",  # No digest for invalid input
            reason_message=str(e),
        )
    except ValueError as e:
        message = str(e)
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code=(
                reason_codes.UNKNOWN_CONTEXT_KEY
                if "context key not whitelisted" in message
                else reason_codes.INVALID_INPUT
            ),
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            tenant_id=tid,
            authoritative_digest="",  # No digest for invalid input
            reason_message=message,
        )
    except TypeError as e:
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code=reason_codes.INVALID_INPUT,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            tenant_id=tid,
            authoritative_digest="",  # No digest for invalid input
            reason_message=str(e),
        )
    except Exception as e:
        # Fallback for any other unexpected safety violations
        return PolicyDecision(
            outcome=DecisionOutcome.DENY,
            reason_code=reason_codes.EVALUATION_ERROR,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            tenant_id=tid,
            authoritative_digest="",  # No digest for invalid input
            reason_message=f"Unexpected evaluation error: {str(e)}",
        )
