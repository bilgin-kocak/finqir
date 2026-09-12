# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Ordered finance mapping pipeline."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Sequence

from finqir.exceptions import CompilationError, InvalidFinanceProblemError
from finqir.problems import StructuredPortfolioProblem

from .base import ConstraintPolicy, FinancialMapping, MappingContext, MappingOutput
from .binary_holdings import BinaryHoldingsMapping
from .constraint_handling import (
    FeasibleSubspaceMapping,
    FixedCardinalityMapping,
    PenaltyConstraintMapping,
)

if TYPE_CHECKING:
    from finqir.compilation import CompiledFinanceProblem


class FinanceMappingPipeline:
    """Apply deterministic financial mappings and return a compiled problem."""

    def __init__(self, mappings: Sequence[FinancialMapping] | None = None):
        selected = (
            tuple(mappings)
            if mappings is not None
            else (
                BinaryHoldingsMapping(),
                FixedCardinalityMapping(),
                FeasibleSubspaceMapping(),
                PenaltyConstraintMapping(),
            )
        )
        if not selected:
            raise InvalidFinanceProblemError("A mapping pipeline cannot be empty")
        names = [mapping.name for mapping in selected]
        if len(set(names)) != len(names):
            raise InvalidFinanceProblemError("Mapping names must be unique within a pipeline")
        self._mappings = selected

    @property
    def mappings(self) -> tuple[FinancialMapping, ...]:
        """Immutable ordered mapping passes."""
        return self._mappings

    def compile(
        self,
        problem: StructuredPortfolioProblem,
        *,
        context: MappingContext | None = None,
    ) -> "CompiledFinanceProblem":
        """Run all passes and construct a ``CompiledFinanceProblem``."""
        from finqir.compilation import CompiledFinanceProblem

        active = context or MappingContext(ConstraintPolicy())
        unknown_overrides = set(active.constraint_policy.overrides) - {
            constraint.name for constraint in problem.constraints
        }
        if unknown_overrides:
            raise InvalidFinanceProblemError(
                f"Constraint policy references unknown constraints {sorted(unknown_overrides)!r}"
            )
        output: MappingOutput | None = None
        for mapping in self._mappings:
            output = mapping.apply(problem, replace(active, current=output))
            if not isinstance(output, MappingOutput):
                raise CompilationError(f"Mapping {mapping.name!r} did not produce a mapped model")
        if output is None:
            raise CompilationError("Mapping pipeline produced no output")
        return CompiledFinanceProblem.from_mapping_output(problem, output)
