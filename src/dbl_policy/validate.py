"""JSON-safe validation for deterministic policy inputs."""

from __future__ import annotations

from typing import Any, Mapping


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def ensure_json_safe(value: Any) -> Any:
    """
    Recursively check that the value is strictly JSON-safe.
    
    Allowed types:
    - None
    - bool
    - int (not float)
    - str
    - list
    - dict (keys must be str)
    
    Explicitly rejected:
    - float, NaN, inf
    - set, bytes
    - Custom objects
    
    Returns the value if safe, or raises ValidationError.
    """
    if value is None:
        return value
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, int):
        # Python bool is a subclass of int, but we handle it above.
        return value
    
    if isinstance(value, float):
        raise ValidationError(f"float not allowed in deterministic context: {value}")
    
    if isinstance(value, str):
        return value
    
    if isinstance(value, list):
        for item in value:
            ensure_json_safe(item)
        return value
    
    if isinstance(value, Mapping):
        for k, v in value.items():
            if type(k) is not str:
                raise ValidationError(f"mapping keys must be str, found: {type(k).__name__}")
            ensure_json_safe(v)
        return value
    
    raise ValidationError(f"type not allowed in deterministic context: {type(value).__name__}")
