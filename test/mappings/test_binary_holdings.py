# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for binary-holdings mapping."""

# pylint: disable=missing-function-docstring

import itertools
import unittest

from hypothesis import given, strategies as st
from qiskit_addon_opt_mapper.problems import Constraint

from finqir.mappings import BinaryHoldingsMapping, ConstraintPolicy, MappingContext
from finqir import UnsupportedMappingError
from finqir.problems import (
    Asset,
    CapitalBudget,
    Cardinality,
    ExcludedHoldings,
    ExpectedReturn,
    ExposureBounds,
    MandatoryHoldings,
    MutualExclusions,
    StructuredPortfolioProblem,
    TransactionCost,
    VarianceRisk,
)
from finqir.problems.evaluation import ConstraintValue


def _source_problem():
    return StructuredPortfolioProblem(
        assets=[Asset("Asset A!?"), Asset("asset/b")],
        objectives=[
            ExpectedReturn([0.1, 0.2], weight=-1),
            VarianceRisk([[1, 0.25], [0.25, 2]], weight=0.5),
            TransactionCost([1, 0], [0.4, 0.5], [0.2, 0.3]),
        ],
        constraints=[
            Cardinality(minimum=1, maximum=2),
            CapitalBudget([3, 5], minimum=2, maximum=6, name="capital"),
            MandatoryHoldings(["Asset A!?"], name="mandatory"),
            ExcludedHoldings(["asset/b"], name="excluded"),
            MutualExclusions([("Asset A!?", "asset/b")], name="conflicts"),
            ExposureBounds({"Asset A!?": 0.6, "asset/b": 0.5}, maximum=1, name="sector"),
        ],
    )


def _constraint_satisfied(constraint, vector):
    value = constraint.evaluate(list(vector))
    if constraint.sense == Constraint.Sense.EQ:
        return abs(value - constraint.rhs) <= 1e-10
    if constraint.sense == Constraint.Sense.LE:
        return value <= constraint.rhs + 1e-10
    return value >= constraint.rhs - 1e-10


@st.composite
def _portfolio_cases(draw):
    dimension = draw(st.integers(min_value=1, max_value=6))
    values = st.lists(st.integers(-20, 20), min_size=dimension, max_size=dimension)
    expected_returns = [value / 10 for value in draw(values)]
    diagonal = [abs(value) / 10 for value in draw(values)]
    current = draw(st.lists(st.integers(0, 1), min_size=dimension, max_size=dimension))
    buy_costs = [abs(value) / 10 for value in draw(values)]
    sell_costs = [abs(value) / 10 for value in draw(values)]
    holdings = tuple(draw(st.lists(st.integers(0, 1), min_size=dimension, max_size=dimension)))
    covariance = [
        [diagonal[row] if row == column else 0.0 for column in range(dimension)]
        for row in range(dimension)
    ]
    return (
        dimension,
        expected_returns,
        covariance,
        current,
        buy_costs,
        sell_costs,
        holdings,
        draw(st.integers(0, dimension)),
    )


class TestBinaryHoldingsMapping(unittest.TestCase):
    """The mapper preserves source objective values and named constraints."""

    def test_binary_mapping_preserves_objective_and_names(self):
        problem = _source_problem()
        output = BinaryHoldingsMapping().apply(problem, MappingContext(ConstraintPolicy()))
        model = output.optimization_problem
        self.assertEqual([variable.name for variable in model.variables], ["x_0", "x_1"])
        self.assertEqual(output.variable_map.asset_to_backend["Asset A!?"], "x_0")
        self.assertEqual(
            output.constraint_map["cardinality"],
            ("cardinality:minimum", "cardinality:maximum"),
        )
        self.assertEqual(output.constraint_map["capital"], ("capital:minimum", "capital:maximum"))
        self.assertEqual(output.trace.interpret((1, 0)), (1, 0))

    def test_every_binary_assignment_has_equivalent_objective_and_constraints(self):
        problem = _source_problem()
        output = BinaryHoldingsMapping().apply(problem, MappingContext())
        model = output.optimization_problem
        backend_constraints = {item.name: item for item in model.linear_constraints}
        for vector in itertools.product((0, 1), repeat=2):
            with self.subTest(vector=vector):
                self.assertAlmostEqual(
                    model.objective.evaluate(list(vector)), problem.evaluate(vector).total
                )
                report = problem.check_feasibility(vector)
                for source_value in report.constraints:
                    mapped_names = output.constraint_map[source_value.name]
                    mapped_satisfied = all(
                        _constraint_satisfied(backend_constraints[name], vector)
                        for name in mapped_names
                    )
                    self.assertEqual(mapped_satisfied, source_value.satisfied)

    def test_unknown_constraint_is_rejected_instead_of_dropped(self):
        class CustomConstraint:
            """Protocol-compatible constraint with no built-in mapping."""

            name = "custom"

            @staticmethod
            def validate(asset_ids):
                del asset_ids

            @staticmethod
            def involved_asset_ids(asset_ids):
                return tuple(asset_ids)

            def evaluate(self, holdings, asset_ids):
                del self, holdings, asset_ids
                return ConstraintValue("custom", True, 0.0, "satisfied")

            @staticmethod
            def to_dict():
                return {"type": "custom"}

        problem = StructuredPortfolioProblem(
            [Asset("a")], [ExpectedReturn([1])], constraints=[CustomConstraint()]
        )
        with self.assertRaises(UnsupportedMappingError):
            BinaryHoldingsMapping().apply(problem, MappingContext())

    @given(_portfolio_cases())
    def test_property_mapping_preserves_values_for_one_to_six_assets(self, case):
        (
            dimension,
            expected_returns,
            covariance,
            current,
            buy_costs,
            sell_costs,
            holdings,
            cardinality,
        ) = case
        problem = StructuredPortfolioProblem(
            assets=[Asset(f"asset-{index}") for index in range(dimension)],
            objectives=[
                ExpectedReturn(expected_returns, weight=-1.0),
                VarianceRisk(covariance, weight=0.5),
                TransactionCost(current, buy_costs, sell_costs),
            ],
            constraints=[Cardinality(exactly=cardinality)],
        )
        output = BinaryHoldingsMapping().apply(problem, MappingContext())
        model = output.optimization_problem
        self.assertAlmostEqual(
            model.objective.evaluate(list(holdings)), problem.evaluate(holdings).total
        )
        source_feasible = problem.check_feasibility(holdings).is_feasible
        backend_feasible = all(
            _constraint_satisfied(constraint, holdings) for constraint in model.linear_constraints
        )
        self.assertEqual(backend_feasible, source_feasible)


if __name__ == "__main__":
    unittest.main()
