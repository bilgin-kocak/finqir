# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Deferred classifications for constraint-preserving and penalty workflows."""

from __future__ import annotations

from finqir.exceptions import CompilationError
from finqir.problems import Cardinality, StructuredPortfolioProblem

from .base import ConstraintHandling, MappingContext, MappingOutput
from .trace import MappingTraceEntry


def _identity(values):
    return tuple(values)


def _with_trace(current: MappingOutput, entry: MappingTraceEntry) -> MappingOutput:
    return MappingOutput(
        optimization_problem=current.optimization_problem,
        variable_map=current.variable_map,
        constraint_map=current.constraint_map,
        constraint_modes=current.constraint_modes,
        trace=current.trace.append(entry),
    )


class FixedCardinalityMapping:
    """Record exact-cardinality invariants selected for feasible-subspace handling."""

    name = "fixed_cardinality"

    def apply(self, problem: StructuredPortfolioProblem, context: MappingContext) -> MappingOutput:
        """Append an exact-cardinality invariant when requested."""
        if context.current is None:
            raise CompilationError("fixed_cardinality requires an existing mapped model")
        selected = [
            constraint
            for constraint in problem.constraints
            if isinstance(constraint, Cardinality)
            and constraint.exactly is not None
            and context.constraint_policy.for_constraint(constraint.name)
            == ConstraintHandling.FEASIBLE_SUBSPACE
        ]
        if not selected:
            return context.current
        variables = context.current.variable_map.backend_variable_names
        return _with_trace(
            context.current,
            MappingTraceEntry(
                self.name,
                variables,
                variables,
                {
                    "invariants": [
                        {"constraint": constraint.name, "exactly": constraint.exactly}
                        for constraint in selected
                    ]
                },
                _identity,
            ),
        )


class FeasibleSubspaceMapping:
    """Validate feasible-subspace selections while retaining source constraints."""

    name = "feasible_subspace"

    def apply(self, problem: StructuredPortfolioProblem, context: MappingContext) -> MappingOutput:
        """Validate assets involved in feasible-subspace constraints."""
        if context.current is None:
            raise CompilationError("feasible_subspace requires an existing mapped model")
        for constraint in problem.constraints:
            if (
                context.constraint_policy.for_constraint(constraint.name)
                == ConstraintHandling.FEASIBLE_SUBSPACE
            ):
                constraint.involved_asset_ids(problem.asset_ids)
        return context.current


class PenaltyConstraintMapping:
    """Record which constraints will be materialized as calibrated penalties later."""

    name = "constraint_handling"

    def apply(self, problem: StructuredPortfolioProblem, context: MappingContext) -> MappingOutput:
        """Append one audit entry describing all constraint decisions."""
        if context.current is None:
            raise CompilationError("constraint_handling requires an existing mapped model")
        if not problem.constraints:
            return context.current
        variables = context.current.variable_map.backend_variable_names
        decisions = {
            constraint.name: {
                "mode": context.constraint_policy.for_constraint(constraint.name).value,
                "asset_ids": list(constraint.involved_asset_ids(problem.asset_ids)),
                "materialization": (
                    "deferred_penalty"
                    if context.constraint_policy.for_constraint(constraint.name)
                    == ConstraintHandling.PENALTY
                    else "mixer_invariant"
                ),
            }
            for constraint in problem.constraints
        }
        return _with_trace(
            context.current,
            MappingTraceEntry(
                self.name,
                variables,
                variables,
                {"constraints": decisions},
                _identity,
            ),
        )
