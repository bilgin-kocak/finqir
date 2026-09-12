# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Finance-aware objective components."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

from finqir._typing import JSONValue
from finqir.exceptions import InvalidFinanceProblemError

from .evaluation import ObjectiveComponentValue


def _name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidFinanceProblemError("Objective name must be a non-empty string")
    return value


def _number_tuple(
    values: Sequence[float], label: str, *, nonnegative: bool = False
) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result:
        raise InvalidFinanceProblemError(f"{label} must not be empty")
    if not all(math.isfinite(value) for value in result):
        raise InvalidFinanceProblemError(f"{label} must contain finite values")
    if nonnegative and any(value < 0 for value in result):
        raise InvalidFinanceProblemError(f"{label} must contain non-negative values")
    return result


def _weight(value: float) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise InvalidFinanceProblemError("Objective weight must be finite")
    return result


def _holdings(values: Sequence[int], dimension: int) -> tuple[int, ...]:
    result = tuple(values)
    if len(result) != dimension or any(value not in (0, 1) for value in result):
        raise InvalidFinanceProblemError(f"Expected {dimension} binary holdings")
    return result


@dataclass(frozen=True)
class PolynomialCoefficients:
    """Raw constant, linear, and full-matrix quadratic coefficients."""

    constant: float = 0.0
    linear: tuple[float, ...] = ()
    quadratic: tuple[tuple[float, ...], ...] = ()


@runtime_checkable
class FinanceObjective(Protocol):
    """Protocol implemented by all structured objective components."""

    @property
    def name(self) -> str:
        """Stable source objective name."""

    @property
    def weight(self) -> float:
        """Signed contribution weight."""

    @property
    def dimension(self) -> int:
        """Number of source holding variables."""

    def evaluate(self, holdings: Sequence[int]) -> ObjectiveComponentValue:
        """Evaluate raw and weighted values."""

    def coefficients(self) -> PolynomialCoefficients:
        """Return raw polynomial coefficients."""

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize this objective."""


@dataclass(frozen=True)
class ExpectedReturn:
    """Linear expected portfolio return."""

    expected_returns: tuple[float, ...]
    weight: float = -1.0
    name: str = "expected_return"

    def __init__(
        self, expected_returns: Sequence[float], weight: float = -1.0, name: str = "expected_return"
    ):
        object.__setattr__(
            self, "expected_returns", _number_tuple(expected_returns, "expected_returns")
        )
        object.__setattr__(self, "weight", _weight(weight))
        object.__setattr__(self, "name", _name(name))

    @property
    def dimension(self) -> int:
        """Number of expected-return coefficients."""
        return len(self.expected_returns)

    def evaluate(self, holdings: Sequence[int]) -> ObjectiveComponentValue:
        """Evaluate expected return and its weighted contribution."""
        vector = _holdings(holdings, self.dimension)
        raw = math.fsum(value * bit for value, bit in zip(self.expected_returns, vector))
        return ObjectiveComponentValue(self.name, raw, self.weight, self.weight * raw)

    def coefficients(self) -> PolynomialCoefficients:
        """Return raw linear expected-return coefficients."""
        return PolynomialCoefficients(linear=self.expected_returns)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize expected return."""
        return {
            "type": "expected_return",
            "name": self.name,
            "weight": self.weight,
            "expected_returns": list(self.expected_returns),
        }


@dataclass(frozen=True)
class VarianceRisk:
    """Full symmetric portfolio variance ``x.T @ covariance @ x``."""

    covariance: tuple[tuple[float, ...], ...]
    weight: float = 1.0
    name: str = "variance"

    def __init__(
        self, covariance: Sequence[Sequence[float]], weight: float = 1.0, name: str = "variance"
    ):
        matrix = tuple(_number_tuple(row, "covariance row") for row in covariance)
        if not matrix or any(len(row) != len(matrix) for row in matrix):
            raise InvalidFinanceProblemError("Covariance must be a non-empty square matrix")
        for row_index, row in enumerate(matrix):
            for column_index, value in enumerate(row):
                if not math.isclose(
                    value, matrix[column_index][row_index], rel_tol=1e-10, abs_tol=1e-12
                ):
                    raise InvalidFinanceProblemError("Covariance matrix must be symmetric")
        object.__setattr__(self, "covariance", matrix)
        object.__setattr__(self, "weight", _weight(weight))
        object.__setattr__(self, "name", _name(name))

    @property
    def dimension(self) -> int:
        """Number of covariance rows and holdings."""
        return len(self.covariance)

    def evaluate(self, holdings: Sequence[int]) -> ObjectiveComponentValue:
        """Evaluate the full symmetric quadratic form."""
        vector = _holdings(holdings, self.dimension)
        raw = math.fsum(
            self.covariance[row][column] * vector[row] * vector[column]
            for row in range(self.dimension)
            for column in range(self.dimension)
        )
        return ObjectiveComponentValue(self.name, raw, self.weight, self.weight * raw)

    def coefficients(self) -> PolynomialCoefficients:
        """Return the raw covariance matrix."""
        return PolynomialCoefficients(quadratic=self.covariance)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize variance risk."""
        return {
            "type": "variance_risk",
            "name": self.name,
            "weight": self.weight,
            "covariance": [list(row) for row in self.covariance],
        }


@dataclass(frozen=True)
class TransactionCost:
    """Linear cost of buying and selling binary holdings."""

    current_holdings: tuple[int, ...]
    buy_costs: tuple[float, ...]
    sell_costs: tuple[float, ...]
    weight: float = 1.0
    name: str = "transaction_cost"

    def __init__(
        self,
        current_holdings: Sequence[int],
        buy_costs: Sequence[float],
        sell_costs: Sequence[float],
        weight: float = 1.0,
        name: str = "transaction_cost",
    ):
        current = tuple(current_holdings)
        buy = _number_tuple(buy_costs, "buy_costs", nonnegative=True)
        sell = _number_tuple(sell_costs, "sell_costs", nonnegative=True)
        if len(current) != len(buy) or len(sell) != len(buy):
            raise InvalidFinanceProblemError("Transaction cost vectors must have equal lengths")
        if any(value not in (0, 1) for value in current):
            raise InvalidFinanceProblemError("current_holdings must be binary")
        object.__setattr__(self, "current_holdings", current)
        object.__setattr__(self, "buy_costs", buy)
        object.__setattr__(self, "sell_costs", sell)
        object.__setattr__(self, "weight", _weight(weight))
        object.__setattr__(self, "name", _name(name))

    @property
    def dimension(self) -> int:
        """Number of current holdings."""
        return len(self.current_holdings)

    def evaluate(self, holdings: Sequence[int]) -> ObjectiveComponentValue:
        """Evaluate buy and sell costs against current holdings."""
        vector = _holdings(holdings, self.dimension)
        raw = math.fsum(
            (
                self.buy_costs[index]
                if current == 0 and vector[index] == 1
                else self.sell_costs[index] if current == 1 and vector[index] == 0 else 0.0
            )
            for index, current in enumerate(self.current_holdings)
        )
        return ObjectiveComponentValue(self.name, raw, self.weight, self.weight * raw)

    def coefficients(self) -> PolynomialCoefficients:
        """Return the equivalent binary linear expression."""
        constant = math.fsum(
            self.sell_costs[index]
            for index, current in enumerate(self.current_holdings)
            if current == 1
        )
        linear = tuple(
            -self.sell_costs[index] if current == 1 else self.buy_costs[index]
            for index, current in enumerate(self.current_holdings)
        )
        return PolynomialCoefficients(constant=constant, linear=linear)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize transaction costs."""
        return {
            "type": "transaction_cost",
            "name": self.name,
            "weight": self.weight,
            "current_holdings": list(self.current_holdings),
            "buy_costs": list(self.buy_costs),
            "sell_costs": list(self.sell_costs),
        }
