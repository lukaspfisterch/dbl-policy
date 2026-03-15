from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .model import Policy, PolicyContext, PolicyDecision, decide_safe

if TYPE_CHECKING:
    from . import bridge
    from . import validation

__all__ = [
    "Policy",
    "PolicyContext",
    "PolicyDecision",
    "decide_safe",
    "bridge",
    "validation",
]

__version__ = "0.3.1"


def __getattr__(name: str) -> Any:
    if name == "bridge":
        return import_module(".bridge", __name__)
    if name == "validation":
        return import_module(".validation", __name__)
    raise AttributeError(name)
