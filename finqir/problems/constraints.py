# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Named financial constraints with direct feasibility evaluation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol, Sequence, runtime_checkable

from finqir._typing import JSONValue
from finqir.exceptions import InvalidFinanceProblemError

from .evaluation import ConstraintValue


def _name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidFinanceProblemError("Constraint name must be a non-empty string")
    return value


def _nonnegative_integer(value: int | None, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidFinanceProblemError(f"{label} must be a non-negative integer")
    return value


def _bounds(minimum: float | None, maximum: float | None) -> tuple[float | None, float | None]:
    if minimum is None and maximum is None:
        raise InvalidFinanceProblemError("At least one bound is required")
    low = None if minimum is None else float(minimum)
    high = None if maximum is None else float(maximum)
    if (low is not None and not math.isfinite(low)) or (
        high is not None and not math.isfinite(high)
    ):
        raise InvalidFinanceProblemError("Constraint bounds must be finite")
    if low is not None and high is not None and low > high:
        raise InvalidFinanceProblemError("Constraint minimum cannot exceed maximum")
    return low, high


def _vector(holdings: Sequence[int], asset_ids: Sequence[str]) -> tuple[int, ...]:
    result = tuple(holdings)
    if len(result) != len(asset_ids) or any(value not in (0, 1) for value in result):
        raise InvalidFinanceProblemError(f"Expected {len(asset_ids)} binary holdings")
    return result


def _unknown(requested: Sequence[str], asset_ids: Sequence[str], name: str) -> None:
    missing = sorted(set(requested) - set(asset_ids))
    if missing:
        raise InvalidFinanceProblemError(
            f"Constraint {name!r} references unknown assets {missing!r}"
        )


def _violation(value: float, minimum: float | None, maximum: float | None) -> float:
    return max(0.0, (minimum - value) if minimum is not None else 0.0) + max(
        0.0, (value - maximum) if maximum is not None else 0.0
    )


def _result(name: str, violation: float, value: float | int) -> ConstraintValue:
    satisfied = math.isclose(violation, 0.0, rel_tol=1e-10, abs_tol=1e-12)
    message = f"value={value!r}; " + ("satisfied" if satisfied else f"violation={violation:g}")
    return ConstraintValue(name, satisfied, 0.0 if satisfied else violation, message)


@runtime_checkable
class FinanceConstraint(Protocol):
    """Protocol implemented by named portfolio constraints."""

    @property
    def name(self) -> str:
        """Stable source constraint name."""

    def validate(self, asset_ids: Sequence[str]) -> None:
        """Validate references and dimensions."""

    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]:
        """Return source-ordered IDs touched by the constraint."""

    def evaluate(self, holdings: Sequence[int], asset_ids: Sequence[str]) -> ConstraintValue:
        """Evaluate this constraint."""

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize this constraint."""


@dataclass(frozen=True)
class Cardinality:
    """Minimum, maximum, or exact number of selected assets."""

    exactly: int | None = None
    minimum: int | None = None
    maximum: int | None = None
    name: str = "cardinality"

    def __post_init__(self) -> None:
        exact = _nonnegative_integer(self.exactly, "exactly")
        low = _nonnegative_integer(self.minimum, "minimum")
        high = _nonnegative_integer(self.maximum, "maximum")
        if exact is not None and (low is not None or high is not None):
            raise InvalidFinanceProblemError("Cardinality exactly cannot be combined with bounds")
        if exact is None and low is None and high is None:
            raise InvalidFinanceProblemError("Cardinality requires exactly, minimum, or maximum")
        if low is not None and high is not None and low > high:
            raise InvalidFinanceProblemError("Cardinality minimum cannot exceed maximum")
        object.__setattr__(self, "name", _name(self.name))

    @property
    def effective_minimum(self) -> int | None:
        """Return the exact value or the lower cardinality bound."""
        return self.exactly if self.exactly is not None else self.minimum

    @property
    def effective_maximum(self) -> int | None:
        """Return the exact value or the upper cardinality bound."""
        return self.exactly if self.exactly is not None else self.maximum

    def validate(self, asset_ids: Sequence[str]) -> None:
        """Validate the bound against the asset count."""
        if self.effective_maximum is not None and self.effective_maximum > len(asset_ids):
            raise InvalidFinanceProblemError("Cardinality exceeds the number of assets")

    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]:
        """Return all assets because cardinality is portfolio-wide."""
        return tuple(asset_ids)

    def evaluate(self, holdings: Sequence[int], asset_ids: Sequence[str]) -> ConstraintValue:
        """Evaluate the selected-asset count."""
        vector = _vector(holdings, asset_ids)
        value = sum(vector)
        return _result(
            self.name, _violation(value, self.effective_minimum, self.effective_maximum), value
        )

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize the cardinality constraint."""
        return {
            "type": "cardinality",
            "name": self.name,
            "exactly": self.exactly,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass(frozen=True)
class CapitalBudget:
    """Bounds on the capital-weighted sum of holdings."""

    coefficients: tuple[float, ...]
    minimum: float | None = None
    maximum: float | None = None
    name: str = "capital_budget"

    def __init__(
        self,
        coefficients: Sequence[float],
        minimum: float | None = None,
        maximum: float | None = None,
        name: str = "capital_budget",
    ):
        values = tuple(float(value) for value in coefficients)
        if not values or not all(math.isfinite(value) for value in values):
            raise InvalidFinanceProblemError("Capital coefficients must be non-empty and finite")
        low, high = _bounds(minimum, maximum)
        object.__setattr__(self, "coefficients", values)
        object.__setattr__(self, "minimum", low)
        object.__setattr__(self, "maximum", high)
        object.__setattr__(self, "name", _name(name))

    def validate(self, asset_ids: Sequence[str]) -> None:
        """Validate one capital coefficient per asset."""
        if len(self.coefficients) != len(asset_ids):
            raise InvalidFinanceProblemError("Capital coefficients must match the asset count")

    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]:
        """Return every asset in the capital sum."""
        return tuple(asset_ids)

    def evaluate(self, holdings: Sequence[int], asset_ids: Sequence[str]) -> ConstraintValue:
        """Evaluate the capital-weighted holding sum."""
        self.validate(asset_ids)
        vector = _vector(holdings, asset_ids)
        value = math.fsum(coefficient * bit for coefficient, bit in zip(self.coefficients, vector))
        return _result(self.name, _violation(value, self.minimum, self.maximum), value)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize the capital constraint."""
        return {
            "type": "capital_budget",
            "name": self.name,
            "coefficients": list(self.coefficients),
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass(frozen=True)
class MandatoryHoldings:
    """Assets that must be selected."""

    asset_ids: tuple[str, ...]
    name: str = "mandatory_holdings"

    def __init__(self, asset_ids: Sequence[str], name: str = "mandatory_holdings"):
        values = tuple(asset_ids)
        if not values or len(set(values)) != len(values):
            raise InvalidFinanceProblemError("Mandatory assets must be non-empty and unique")
        object.__setattr__(self, "asset_ids", values)
        object.__setattr__(self, "name", _name(name))

    def validate(self, asset_ids: Sequence[str]) -> None:
        """Validate that every mandatory asset exists."""
        _unknown(self.asset_ids, asset_ids, self.name)

    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]:
        """Return mandatory assets in source order."""
        self.validate(asset_ids)
        requested = set(self.asset_ids)
        return tuple(asset_id for asset_id in asset_ids if asset_id in requested)

    def evaluate(self, holdings: Sequence[int], asset_ids: Sequence[str]) -> ConstraintValue:
        """Count mandatory assets that are not selected."""
        self.validate(asset_ids)
        vector = _vector(holdings, asset_ids)
        index = dict(zip(asset_ids, vector))
        violation = float(sum(index[asset_id] != 1 for asset_id in self.asset_ids))
        return _result(self.name, violation, len(self.asset_ids) - int(violation))

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize mandatory holdings."""
        return {"type": "mandatory_holdings", "name": self.name, "asset_ids": list(self.asset_ids)}


@dataclass(frozen=True)
class ExcludedHoldings:
    """Assets that must not be selected."""

    asset_ids: tuple[str, ...]
    name: str = "excluded_holdings"

    def __init__(self, asset_ids: Sequence[str], name: str = "excluded_holdings"):
        values = tuple(asset_ids)
        if not values or len(set(values)) != len(values):
            raise InvalidFinanceProblemError("Excluded assets must be non-empty and unique")
        object.__setattr__(self, "asset_ids", values)
        object.__setattr__(self, "name", _name(name))

    def validate(self, asset_ids: Sequence[str]) -> None:
        """Validate that every excluded asset exists."""
        _unknown(self.asset_ids, asset_ids, self.name)

    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]:
        """Return excluded assets in source order."""
        self.validate(asset_ids)
        requested = set(self.asset_ids)
        return tuple(asset_id for asset_id in asset_ids if asset_id in requested)

    def evaluate(self, holdings: Sequence[int], asset_ids: Sequence[str]) -> ConstraintValue:
        """Count excluded assets that are selected."""
        self.validate(asset_ids)
        vector = _vector(holdings, asset_ids)
        index = dict(zip(asset_ids, vector))
        violation = float(sum(index[asset_id] != 0 for asset_id in self.asset_ids))
        return _result(self.name, violation, int(violation))

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize excluded holdings."""
        return {"type": "excluded_holdings", "name": self.name, "asset_ids": list(self.asset_ids)}


@dataclass(frozen=True)
class MutualExclusions:
    """Pairs of assets that cannot be selected together."""

    pairs: tuple[tuple[str, str], ...]
    name: str = "mutual_exclusions"

    def __init__(self, pairs: Sequence[tuple[str, str]], name: str = "mutual_exclusions"):
        canonical: list[tuple[str, str]] = []
        for pair in pairs:
            if len(pair) != 2 or pair[0] == pair[1]:
                raise InvalidFinanceProblemError("Mutual exclusions require distinct asset pairs")
            canonical.append((min(pair), max(pair)))
        if not canonical or len(set(canonical)) != len(canonical):
            raise InvalidFinanceProblemError("Mutual exclusion pairs must be non-empty and unique")
        object.__setattr__(self, "pairs", tuple(canonical))
        object.__setattr__(self, "name", _name(name))

    def validate(self, asset_ids: Sequence[str]) -> None:
        """Validate both endpoints of every pair."""
        _unknown(tuple(item for pair in self.pairs for item in pair), asset_ids, self.name)

    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]:
        """Return all pair endpoints in source order."""
        self.validate(asset_ids)
        requested = {item for pair in self.pairs for item in pair}
        return tuple(asset_id for asset_id in asset_ids if asset_id in requested)

    def evaluate(self, holdings: Sequence[int], asset_ids: Sequence[str]) -> ConstraintValue:
        """Count selected conflicting pairs."""
        self.validate(asset_ids)
        vector = _vector(holdings, asset_ids)
        index = dict(zip(asset_ids, vector))
        violation = float(sum(index[left] == 1 and index[right] == 1 for left, right in self.pairs))
        return _result(self.name, violation, int(violation))

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize mutual exclusions."""
        return {
            "type": "mutual_exclusions",
            "name": self.name,
            "pairs": [list(pair) for pair in self.pairs],
        }


@dataclass(frozen=True)
class ExposureBounds:
    """Bounds on a named factor, sector, or other linear exposure."""

    coefficients: Mapping[str, float]
    minimum: float | None = None
    maximum: float | None = None
    name: str = "exposure"

    def __init__(
        self,
        coefficients: Mapping[str, float],
        minimum: float | None = None,
        maximum: float | None = None,
        name: str = "exposure",
    ):
        values = {key: float(value) for key, value in coefficients.items()}
        if not values or not all(isinstance(key, str) and key for key in values):
            raise InvalidFinanceProblemError("Exposure coefficients require non-empty asset IDs")
        if not all(math.isfinite(value) for value in values.values()):
            raise InvalidFinanceProblemError("Exposure coefficients must be finite")
        low, high = _bounds(minimum, maximum)
        object.__setattr__(self, "coefficients", MappingProxyType(values))
        object.__setattr__(self, "minimum", low)
        object.__setattr__(self, "maximum", high)
        object.__setattr__(self, "name", _name(name))

    def validate(self, asset_ids: Sequence[str]) -> None:
        """Validate every exposure coefficient asset."""
        _unknown(tuple(self.coefficients), asset_ids, self.name)

    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]:
        """Return assets with nonzero exposure in source order."""
        self.validate(asset_ids)
        return tuple(
            asset_id for asset_id in asset_ids if self.coefficients.get(asset_id, 0.0) != 0.0
        )

    def evaluate(self, holdings: Sequence[int], asset_ids: Sequence[str]) -> ConstraintValue:
        """Evaluate the named linear exposure."""
        self.validate(asset_ids)
        vector = _vector(holdings, asset_ids)
        value = math.fsum(
            self.coefficients.get(asset_id, 0.0) * bit for asset_id, bit in zip(asset_ids, vector)
        )
        return _result(self.name, _violation(value, self.minimum, self.maximum), value)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize the exposure constraint."""
        return {
            "type": "exposure_bounds",
            "name": self.name,
            "coefficients": dict(self.coefficients),
            "minimum": self.minimum,
            "maximum": self.maximum,
        }
