# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Reproducible classical baselines for finance applications."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from finqir.applications.optimization import ConflictGraphPortfolio
from finqir.exceptions import InfeasiblePortfolioError


@dataclass(frozen=True)
class ClassicalPortfolioResult:
    """Exact mixed-integer result in source-asset order."""

    holdings: tuple[int, ...]
    selected_assets: tuple[str, ...]
    objective_value: float
    is_optimal: bool
    status: int
    message: str
    solver: str = "scipy.optimize.milp"


def solve_conflict_graph_classically(  # pylint: disable=invalid-name
    application: ConflictGraphPortfolio, *, time_limit: float | None = None
) -> ClassicalPortfolioResult:
    """Solve a conflict graph exactly as a binary linear program."""
    count = len(application.vertices)
    position = {vertex: index for index, vertex in enumerate(application.vertices)}
    rows: list[list[float]] = []
    lower_bounds: list[float] = []
    upper_bounds: list[float] = []

    for left, right in (*application.edges, *application.additional_conflicts):
        row = [0.0] * count
        row[position[left]] = 1.0
        row[position[right]] = 1.0
        rows.append(row)
        lower_bounds.append(-np.inf)
        upper_bounds.append(1.0)
    for vertex in application.mandatory:
        row = [0.0] * count
        row[position[vertex]] = 1.0
        rows.append(row)
        lower_bounds.append(1.0)
        upper_bounds.append(1.0)
    for vertex in application.excluded:
        row = [0.0] * count
        row[position[vertex]] = 1.0
        rows.append(row)
        lower_bounds.append(0.0)
        upper_bounds.append(0.0)
    if application.maximum_cardinality is not None:
        rows.append([1.0] * count)
        lower_bounds.append(-np.inf)
        upper_bounds.append(float(application.maximum_cardinality))

    constraints = None
    if rows:
        constraints = LinearConstraint(
            np.asarray(rows), np.asarray(lower_bounds), np.asarray(upper_bounds)
        )
    options = {} if time_limit is None else {"time_limit": float(time_limit)}
    result = milp(
        c=-np.asarray([application.weights[vertex] for vertex in application.vertices]),
        integrality=np.ones(count),
        bounds=Bounds(np.zeros(count), np.ones(count)),
        constraints=constraints,
        options=options,
    )
    if result.x is None:
        raise InfeasiblePortfolioError(f"Classical solver failed: {result.message}")
    holdings = tuple(int(value >= 0.5) for value in result.x)
    problem = application.to_structured_problem()
    if not problem.check_feasibility(holdings).is_feasible:
        raise InfeasiblePortfolioError("Classical solver returned an infeasible rounded solution")
    return ClassicalPortfolioResult(
        holdings=holdings,
        selected_assets=application.interpret(holdings),
        objective_value=problem.evaluate(holdings).total,
        is_optimal=result.status == 0,
        status=int(result.status),
        message=str(result.message),
    )
