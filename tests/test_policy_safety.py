from __future__ import annotations

import pytest
from collections.abc import Mapping
from dbl_policy import (
    PolicyContext,
    PolicyDecision,
    PolicyId,
    PolicyVersion,
    TenantId,
    DecisionOutcome,
    decision_to_dbl_event,
    reason_codes,
)
from dbl_policy.validate import ValidationError


def test_rejects_float_inputs():
    # Lücke B: Canonical-safety (floats verboten)
    tenant_id = TenantId("t1")
    with pytest.raises(ValidationError, match="float not allowed"):
        PolicyContext(tenant_id=tenant_id, inputs={"use_case": 1.5})
    
    with pytest.raises(ValidationError, match="float not allowed"):
        PolicyContext(tenant_id=tenant_id, inputs={"use_case": [1, 2, 3.0]})


def test_rejects_unknown_context_key():
    # Lücke A: Context-Policy Whitelist
    tenant_id = TenantId("t1")
    with pytest.raises(ValueError, match="context key not whitelisted"):
        PolicyContext(tenant_id=tenant_id, inputs={"unknown_key": "some value"})


def test_decision_event_contains_policy_identity():
    # Lücke C: Entscheidungs-Event verliert Policy-Identität
    decision = PolicyDecision(
        outcome=DecisionOutcome.ALLOW,
        reason_code=reason_codes.OK,
        policy_id=PolicyId("example-policy"),
        policy_version=PolicyVersion("1.2.3"),
        tenant_id=TenantId("tenant-1"),
    )
    
    event = decision_to_dbl_event(decision, correlation_id="c1")
    
    assert event.correlation_id == "c1"
    assert isinstance(event.data, Mapping)
    assert event.data["policy_id"] == "example-policy"
    assert event.data["policy_version"] == "1.2.3"
    assert event.data["tenant_id"] == "tenant-1"
    
    gate = event.data["gate"]
    assert isinstance(gate, Mapping)
    assert gate["decision"] == "ALLOW"
    assert gate["reason_code"] == reason_codes.OK


def test_rejects_non_string_context_keys():
    # Harden: ensure_json_safe falls before whitelist
    tenant_id = TenantId("t1")
    with pytest.raises(ValidationError, match="mapping keys must be str"):
        PolicyContext(tenant_id=tenant_id, inputs={123: "val"})  # type: ignore


def test_rejects_str_subclass_keys():
    from collections import UserString

    tenant_id = TenantId("t1")
    with pytest.raises(ValidationError, match="mapping keys must be str"):
        PolicyContext(tenant_id=tenant_id, inputs={UserString("k"): "val"})  # type: ignore


def test_bridge_is_normative_pure():
    # Lücke C + Harden: Manual construction ensures no observational leak
    decision = PolicyDecision(
        outcome=DecisionOutcome.ALLOW,
        reason_code=reason_codes.OK,
        policy_id=PolicyId("p1"),
        policy_version=PolicyVersion("1.0.0"),
        tenant_id=TenantId("t1"),
        reason_message="explainable hint"
    )
    
    event = decision_to_dbl_event(decision, correlation_id="c1")
    data = event.data
    
    # Check that it's a plain dict, no GateDecision object remnants
    assert isinstance(data["gate"], Mapping)
    assert "reason_message" in data["gate"]
    assert data["gate"]["reason_message"] == "explainable hint"
    
    # Ensure no hidden observational leakage if dbl-core were to change
    # The bridge must only include what we explicitly put there.
    assert set(data.keys()) == {"gate", "policy_id", "policy_version", "tenant_id"}
    assert set(data["gate"].keys()) == {"decision", "reason_code", "reason_message"}


def test_version_alignment():
    import tomllib
    from pathlib import Path
    import dbl_policy
    
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)
    
    project_version = config["project"]["version"]
    assert dbl_policy.__version__ == project_version
    assert project_version == "0.2.1"


def test_authoritative_digest_is_stable_under_nested_key_ordering():
    tenant_id = TenantId("t1")
    ctx1 = PolicyContext(
        tenant_id=tenant_id,
        inputs={"use_case": "x", "metadata": {"b": 2, "a": 1}},
    )
    ctx2 = PolicyContext(
        tenant_id=tenant_id,
        inputs={"use_case": "x", "metadata": {"a": 1, "b": 2}},
    )
    assert ctx1.compute_authoritative_digest() == ctx2.compute_authoritative_digest()


def test_context_is_snapshot_not_alias():
    tenant_id = TenantId("t1")
    raw = {"use_case": "x", "metadata": {"a": 1}}
    ctx = PolicyContext(tenant_id=tenant_id, inputs=raw)

    raw["metadata"]["a"] = 2

    assert ctx.to_dict()["inputs"]["metadata"]["a"] == 1
    assert ctx.compute_authoritative_digest() == PolicyContext(
        tenant_id=tenant_id,
        inputs={"use_case": "x", "metadata": {"a": 1}},
    ).compute_authoritative_digest()
