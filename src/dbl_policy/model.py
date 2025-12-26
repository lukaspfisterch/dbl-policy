from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping, Protocol

from dbl_core import DblEvent, DblEventKind, GateDecision


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


_FORBIDDEN_INPUT_KEYS = {
    "trace",
    "trace_digest",
    "execution",
    "execution_trace",
    "success",
    "failure_code",
    "exception_type",
    "exception",
    "runtime",
    "runtime_ms",
}


def _canonicalize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    items: dict[str, Any] = {}
    for key in sorted(value.keys(), key=lambda k: str(k)):
        items[str(key)] = value[key]
    return items


@dataclass(frozen=True)
class PolicyContext:
    tenant_id: TenantId
    inputs: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.inputs, Mapping):
            raise TypeError("inputs must be a mapping")
        for key in self.inputs.keys():
            key_str = str(key).lower()
            if key_str in _FORBIDDEN_INPUT_KEYS or key_str.startswith("trace") or key_str.startswith("execution"):
                raise ValueError(f"observational key not allowed: {key}")
        json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id.value,
            "inputs": _canonicalize_mapping(self.inputs),
        }


@dataclass(frozen=True)
class PolicyDecision:
    outcome: DecisionOutcome
    reason_code: str
    policy_id: PolicyId
    policy_version: PolicyVersion
    tenant_id: TenantId
    reason_message: str | None = None

    def __post_init__(self) -> None:
        if self.outcome not in (DecisionOutcome.ALLOW, DecisionOutcome.DENY):
            raise ValueError("invalid decision outcome")
        if not self.reason_code:
            raise ValueError("reason_code is required")


class Policy(Protocol):
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        ...


def decision_to_dbl_event(decision: PolicyDecision, correlation_id: str) -> DblEvent:
    gate = GateDecision(decision.outcome.value, decision.reason_code, decision.reason_message)
    return DblEvent(DblEventKind.DECISION, correlation_id=correlation_id, data=gate)
