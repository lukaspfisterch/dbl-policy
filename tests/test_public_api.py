from __future__ import annotations

import dbl_policy


def test_root_public_surface_is_minimal() -> None:
    assert dbl_policy.__all__ == [
        "Policy",
        "PolicyContext",
        "PolicyDecision",
        "decide_safe",
        "bridge",
        "validation",
    ]


def test_removed_root_exports_stay_internal() -> None:
    assert not hasattr(dbl_policy, "DecisionOutcome")
    assert not hasattr(dbl_policy, "PolicyId")
    assert not hasattr(dbl_policy, "PolicyVersion")
    assert not hasattr(dbl_policy, "TenantId")
    assert not hasattr(dbl_policy, "decision_to_dbl_event")
