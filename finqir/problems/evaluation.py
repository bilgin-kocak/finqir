# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Auditable objective and constraint evaluation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ObjectiveComponentValue:
    """One objective's raw financial value and weighted contribution."""

    name: str
    raw_value: float
    weight: float
    contribution: float


@dataclass(frozen=True)
class ConstraintValue:
    """The satisfaction and violation of one named source constraint."""

    name: str
    satisfied: bool
    violation: float
    message: str


@dataclass(frozen=True)
class PortfolioEvaluation:
    """An objective total with its finance-aware decomposition."""

    objective_sense: Literal["minimize", "maximize"]
    total: float
    components: tuple[ObjectiveComponentValue, ...]


@dataclass(frozen=True)
class FeasibilityReport:
    """Named constraint outcomes for one candidate portfolio."""

    constraints: tuple[ConstraintValue, ...]

    @property
    def is_feasible(self) -> bool:
        """Whether every source constraint is satisfied."""
        return all(item.satisfied for item in self.constraints)

    def by_name(self, name: str) -> ConstraintValue:
        """Return a constraint result by source name."""
        for item in self.constraints:
            if item.name == name:
                return item
        raise KeyError(name)
