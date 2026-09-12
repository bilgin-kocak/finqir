# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Contracts shared by finance-to-optimization mappings."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Protocol, runtime_checkable

from qiskit_addon_opt_mapper import OptimizationProblem

from finqir.exceptions import InvalidFinanceProblemError
from finqir.problems import StructuredPortfolioProblem

from .trace import MappingTrace


class ConstraintHandling(str, Enum):
    """How a source constraint must be represented by the quantum workflow."""

    PENALTY = "penalty"
    FEASIBLE_SUBSPACE = "feasible_subspace"


@dataclass(frozen=True)
class ConstraintPolicy:
    """Default and per-constraint handling policy."""

    default: ConstraintHandling = ConstraintHandling.PENALTY
    overrides: Mapping[str, ConstraintHandling] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            default = ConstraintHandling(self.default)
            overrides = {
                name: ConstraintHandling(value) for name, value in dict(self.overrides).items()
            }
        except (TypeError, ValueError) as exc:
            raise InvalidFinanceProblemError("Invalid constraint handling policy") from exc
        if any(not isinstance(name, str) or not name for name in overrides):
            raise InvalidFinanceProblemError("Constraint policy names must be non-empty strings")
        object.__setattr__(self, "default", default)
        object.__setattr__(self, "overrides", MappingProxyType(overrides))

    def for_constraint(self, name: str) -> ConstraintHandling:
        """Resolve the policy for a named source constraint."""
        return self.overrides.get(name, self.default)


@dataclass(frozen=True)
class VariableMap:
    """Reversible association between source assets and backend variables."""

    source_asset_ids: tuple[str, ...]
    backend_variable_names: tuple[str, ...]
    asset_to_backend: Mapping[str, str]
    fixed_values: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source = tuple(self.source_asset_ids)
        backend = tuple(self.backend_variable_names)
        association = dict(self.asset_to_backend)
        fixed = dict(self.fixed_values)
        if len(set(source)) != len(source) or len(set(backend)) != len(backend):
            raise InvalidFinanceProblemError("Variable map names must be unique")
        if any(not isinstance(name, str) or not name for name in (*source, *backend)):
            raise InvalidFinanceProblemError("Variable map names must be non-empty strings")
        unknown = (set(association) | set(fixed)) - set(source)
        if unknown:
            raise InvalidFinanceProblemError(
                f"Variable map contains unknown assets {sorted(unknown)!r}"
            )
        if any(value not in backend for value in association.values()):
            raise InvalidFinanceProblemError("Mapped backend variable is absent from backend order")
        missing = set(source) - (set(association) | set(fixed))
        if missing:
            raise InvalidFinanceProblemError(
                f"Variable map is missing source assets {sorted(missing)!r}"
            )
        if len(set(association.values())) != len(association):
            raise InvalidFinanceProblemError("Source assets must map to distinct backend variables")
        if any(value not in (0, 1) for value in fixed.values()):
            raise InvalidFinanceProblemError("Fixed holdings must be binary")
        if set(association) & set(fixed):
            raise InvalidFinanceProblemError("An asset cannot be mapped and fixed")
        object.__setattr__(self, "source_asset_ids", source)
        object.__setattr__(self, "backend_variable_names", backend)
        object.__setattr__(self, "asset_to_backend", MappingProxyType(association))
        object.__setattr__(self, "fixed_values", MappingProxyType(fixed))


@dataclass(frozen=True)
class MappingContext:
    """Policy and accumulated state supplied to a mapping pass."""

    constraint_policy: ConstraintPolicy = field(default_factory=ConstraintPolicy)
    penalty: float | None = None
    current: "MappingOutput | None" = None

    def __post_init__(self) -> None:
        if self.penalty is not None:
            if isinstance(self.penalty, bool):
                raise InvalidFinanceProblemError("Mapping penalty must be finite and positive")
            try:
                penalty = float(self.penalty)
            except (TypeError, ValueError) as exc:
                raise InvalidFinanceProblemError(
                    "Mapping penalty must be finite and positive"
                ) from exc
            if not math.isfinite(penalty) or penalty <= 0:
                raise InvalidFinanceProblemError("Mapping penalty must be finite and positive")
            object.__setattr__(self, "penalty", penalty)


@dataclass(frozen=True)
class MappingOutput:
    """Backend model plus all information required to interpret it."""

    optimization_problem: OptimizationProblem
    variable_map: VariableMap
    constraint_map: Mapping[str, tuple[str, ...]]
    constraint_modes: Mapping[str, ConstraintHandling]
    trace: MappingTrace

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "constraint_map",
            MappingProxyType({name: tuple(values) for name, values in self.constraint_map.items()}),
        )
        object.__setattr__(
            self,
            "constraint_modes",
            MappingProxyType(
                {name: ConstraintHandling(value) for name, value in self.constraint_modes.items()}
            ),
        )


@runtime_checkable
class FinancialMapping(Protocol):
    """Protocol for one deterministic financial mapping pass."""

    name: str

    def apply(self, problem: StructuredPortfolioProblem, context: MappingContext) -> MappingOutput:
        """Apply the mapping to a source problem or current mapping output."""
