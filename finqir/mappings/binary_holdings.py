# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Mapping from binary finance holdings to Optimization Mapper models."""

from __future__ import annotations

from qiskit_addon_opt_mapper import OptimizationProblem

from finqir.exceptions import UnsupportedMappingError
from finqir.problems import (
    CapitalBudget,
    Cardinality,
    ExcludedHoldings,
    ExposureBounds,
    MandatoryHoldings,
    MutualExclusions,
    StructuredPortfolioProblem,
)

from .base import MappingContext, MappingOutput, VariableMap
from .trace import MappingTrace, MappingTraceEntry


class BinaryHoldingsMapping:
    """Build a binary ``OptimizationProblem`` while retaining finance names."""

    name = "binary_holdings"

    def apply(self, problem: StructuredPortfolioProblem, context: MappingContext) -> MappingOutput:
        """Map every source holding, objective component, and constraint."""
        model = OptimizationProblem(problem.name)
        variable_names = tuple(f"x_{index}" for index in range(len(problem.assets)))
        for variable_name in variable_names:
            model.binary_var(variable_name)

        constant = 0.0
        linear = [0.0] * len(variable_names)
        quadratic = [[0.0] * len(variable_names) for _ in variable_names]
        for objective in problem.objectives:
            objective_coefficients = objective.coefficients()
            constant += objective.weight * objective_coefficients.constant
            for index, coefficient in enumerate(objective_coefficients.linear):
                linear[index] += objective.weight * coefficient
            for row_index, row in enumerate(objective_coefficients.quadratic):
                for column_index, coefficient in enumerate(row):
                    quadratic[row_index][column_index] += objective.weight * coefficient
        objective_builder = (
            model.minimize if problem.objective_sense == "minimize" else model.maximize
        )
        objective_builder(constant=constant, linear=linear, quadratic=quadratic)

        index_by_asset = {asset_id: index for index, asset_id in enumerate(problem.asset_ids)}
        constraint_map: dict[str, tuple[str, ...]] = {}
        for constraint in problem.constraints:
            backend_names: list[str] = []
            if isinstance(constraint, Cardinality):
                constraint_coefficients = {name: 1.0 for name in variable_names}
                if constraint.exactly is not None:
                    model.linear_constraint(
                        constraint_coefficients, "==", constraint.exactly, constraint.name
                    )
                    backend_names.append(constraint.name)
                else:
                    self._add_bounds(
                        model,
                        constraint_coefficients,
                        constraint.minimum,
                        constraint.maximum,
                        constraint.name,
                        backend_names,
                    )
            elif isinstance(constraint, CapitalBudget):
                constraint_coefficients = {
                    variable_names[index]: value
                    for index, value in enumerate(constraint.coefficients)
                }
                self._add_bounds(
                    model,
                    constraint_coefficients,
                    constraint.minimum,
                    constraint.maximum,
                    constraint.name,
                    backend_names,
                )
            elif isinstance(constraint, MandatoryHoldings):
                for asset_id in constraint.asset_ids:
                    backend_name = f"{constraint.name}:{asset_id}"
                    model.linear_constraint(
                        {variable_names[index_by_asset[asset_id]]: 1.0},
                        "==",
                        1,
                        backend_name,
                    )
                    backend_names.append(backend_name)
            elif isinstance(constraint, ExcludedHoldings):
                for asset_id in constraint.asset_ids:
                    backend_name = f"{constraint.name}:{asset_id}"
                    model.linear_constraint(
                        {variable_names[index_by_asset[asset_id]]: 1.0},
                        "==",
                        0,
                        backend_name,
                    )
                    backend_names.append(backend_name)
            elif isinstance(constraint, MutualExclusions):
                for pair_index, (left, right) in enumerate(constraint.pairs):
                    backend_name = f"{constraint.name}:{pair_index}"
                    model.linear_constraint(
                        {
                            variable_names[index_by_asset[left]]: 1.0,
                            variable_names[index_by_asset[right]]: 1.0,
                        },
                        "<=",
                        1,
                        backend_name,
                    )
                    backend_names.append(backend_name)
            elif isinstance(constraint, ExposureBounds):
                constraint_coefficients = {
                    variable_names[index_by_asset[asset_id]]: value
                    for asset_id, value in constraint.coefficients.items()
                }
                self._add_bounds(
                    model,
                    constraint_coefficients,
                    constraint.minimum,
                    constraint.maximum,
                    constraint.name,
                    backend_names,
                )
            else:
                raise UnsupportedMappingError(
                    f"Binary holdings cannot map constraint type " f"{type(constraint).__name__!r}"
                )
            constraint_map[constraint.name] = tuple(backend_names)

        dimension = len(variable_names)

        def decode(values):
            return tuple(values[:dimension])

        trace = MappingTrace(
            (
                MappingTraceEntry(
                    self.name,
                    problem.asset_ids,
                    variable_names,
                    {"variable_domain": "binary"},
                    decode,
                ),
            )
        )
        return MappingOutput(
            optimization_problem=model,
            variable_map=VariableMap(
                source_asset_ids=problem.asset_ids,
                backend_variable_names=variable_names,
                asset_to_backend=dict(zip(problem.asset_ids, variable_names)),
            ),
            constraint_map=constraint_map,
            constraint_modes={
                constraint.name: context.constraint_policy.for_constraint(constraint.name)
                for constraint in problem.constraints
            },
            trace=trace,
        )

    @staticmethod
    def _add_bounds(
        model: OptimizationProblem,
        coefficients: dict[str, float],
        minimum: float | int | None,
        maximum: float | int | None,
        source_name: str,
        backend_names: list[str],
    ) -> None:
        if minimum is not None:
            backend_name = f"{source_name}:minimum"
            model.linear_constraint(coefficients, ">=", minimum, backend_name)
            backend_names.append(backend_name)
        if maximum is not None:
            backend_name = f"{source_name}:maximum"
            model.linear_constraint(coefficients, "<=", maximum, backend_name)
            backend_names.append(backend_name)
