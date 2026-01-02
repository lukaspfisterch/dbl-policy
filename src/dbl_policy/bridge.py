"""Bridge logic to convert policy decisions to DBL events."""

from __future__ import annotations

from typing import Any

from dbl_core import DblEvent, DblEventKind
from .model import PolicyDecision


def decision_to_dbl_event(decision: PolicyDecision, correlation_id: str) -> DblEvent:
    """
    Convert a PolicyDecision into a DblEvent(kind=DECISION).
    
    This preserves policy lineage by including policy_id, policy_version, 
    and tenant_id in the event data.
    """
    # We wrap the decision in a dict to carry the policy identity/lineage.
    # The dbl-policy contract requires DECISION.data to be a Mapping with the specified shape.
    # By using a Mapping, we can include the normative gate decision AND the lineage.
    # dbl-core GateDecision MAY be used for mapping but we use explicit dict construction
    # to avoid any risk of observational leakage and ensure absolute normative purity.
    
    # We construct the gate dict manually.
    gate_dict: dict[str, Any] = {
        "decision": decision.outcome.value,
        "reason_code": decision.reason_code,
    }
    if decision.reason_message is not None:
        gate_dict["reason_message"] = decision.reason_message

    data: dict[str, Any] = {
        "gate": gate_dict,
        "policy_id": decision.policy_id.value,
        "policy_version": decision.policy_version.value,
        "tenant_id": decision.tenant_id.value,
    }
    
    return DblEvent(DblEventKind.DECISION, correlation_id=correlation_id, data=data)
