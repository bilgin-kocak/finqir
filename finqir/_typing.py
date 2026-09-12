# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Shared serialization types and defensive-copy helpers."""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Mapping, TypeAlias

from .exceptions import InvalidFinanceProblemError

JSONValue: TypeAlias = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]


def freeze_json(value: Any) -> Any:
    """Validate and recursively freeze a JSON-compatible value."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidFinanceProblemError("JSON metadata numbers must be finite")
        return value
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise InvalidFinanceProblemError("JSON metadata object keys must be strings")
        return MappingProxyType({key: freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    raise InvalidFinanceProblemError(f"Value of type {type(value).__name__} is not JSON compatible")


def thaw_json(value: Any) -> JSONValue:
    """Return a mutable JSON-compatible copy of a frozen value."""
    if isinstance(value, Mapping):
        return {str(key): thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return value


def require_exact_fields(payload: Mapping[str, Any], expected: set[str], kind: str) -> None:
    """Reject missing and unknown serialized fields."""
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise InvalidFinanceProblemError(
            f"Invalid {kind} fields; missing={missing!r}, unknown={unknown!r}"
        )
