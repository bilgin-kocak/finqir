# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for the structured portfolio aggregate."""

# pylint: disable=missing-function-docstring

import json
import unittest

from finqir import InvalidFinanceProblemError, StructuredPortfolioProblem
from finqir.problems import (
    Asset,
    Cardinality,
    ExcludedHoldings,
    ExpectedReturn,
    HoldingVariable,
    MandatoryHoldings,
    MutualExclusions,
    VarianceRisk,
)


def _problem():
    return StructuredPortfolioProblem(
        assets=[Asset("a", metadata={"sector": "energy"}), Asset("b")],
        objective_sense="minimize",
        holding_variables=[
            HoldingVariable("a", lot_size=10.0),
            HoldingVariable("b", lot_size=5.0),
        ],
        objectives=[
            ExpectedReturn([0.1, 0.2], weight=-1.0),
            VarianceRisk([[1.0, 0.0], [0.0, 2.0]], weight=0.5),
        ],
        constraints=[Cardinality(exactly=1)],
        metadata={"source": "unit-test"},
    )


class TestStructuredPortfolioProblem(unittest.TestCase):
    """The aggregate validates, evaluates, and serializes financial meaning."""

    def test_mean_variance_breakdown_and_feasibility(self):
        problem = _problem()
        value = problem.evaluate((0, 1))
        self.assertAlmostEqual(value.total, 0.8)
        self.assertEqual([part.name for part in value.components], ["expected_return", "variance"])
        self.assertTrue(problem.check_feasibility((0, 1)).is_feasible)
        self.assertFalse(problem.check_feasibility((1, 1)).is_feasible)

    def test_serialization_is_deterministic_and_round_trips(self):
        problem = _problem()
        encoded = json.dumps(problem.to_dict(), sort_keys=True, separators=(",", ":"))
        decoded = StructuredPortfolioProblem.from_dict(json.loads(encoded))
        self.assertEqual(decoded.to_dict(), problem.to_dict())

    def test_constructor_inputs_cannot_mutate_problem(self):
        assets = [Asset("a"), Asset("b")]
        objectives = [ExpectedReturn([1, 2])]
        problem = StructuredPortfolioProblem(assets=assets, objectives=objectives)
        assets.clear()
        objectives.clear()
        self.assertEqual(problem.asset_ids, ("a", "b"))
        self.assertEqual(len(problem.objectives), 1)

    def test_direct_contradictions_are_rejected(self):
        cases = (
            [MandatoryHoldings(["a"]), ExcludedHoldings(["a"])],
            [MandatoryHoldings(["a", "b"]), MutualExclusions([("a", "b")])],
            [MandatoryHoldings(["a", "b"]), Cardinality(maximum=1)],
            [ExcludedHoldings(["a", "b"]), Cardinality(minimum=1)],
        )
        for constraints in cases:
            with self.subTest(constraints=constraints):
                with self.assertRaises(InvalidFinanceProblemError):
                    StructuredPortfolioProblem(
                        assets=[Asset("a"), Asset("b")],
                        objectives=[ExpectedReturn([1, 2])],
                        constraints=constraints,
                    )

    def test_duplicate_ids_names_dimensions_and_holdings_are_rejected(self):
        invalid = [
            lambda: StructuredPortfolioProblem(
                assets=[Asset("a"), Asset("a")], objectives=[ExpectedReturn([1, 2])]
            ),
            lambda: StructuredPortfolioProblem(
                assets=[Asset("a")],
                objectives=[ExpectedReturn([1], name="same"), VarianceRisk([[1]], name="same")],
            ),
            lambda: StructuredPortfolioProblem(
                assets=[Asset("a"), Asset("b")], objectives=[ExpectedReturn([1])]
            ),
            lambda: StructuredPortfolioProblem(
                assets=[Asset("a")],
                objectives=[ExpectedReturn([1])],
                holding_variables=[object()],
            ),
        ]
        for constructor in invalid:
            with self.assertRaises(InvalidFinanceProblemError):
                constructor()
        with self.assertRaises(InvalidFinanceProblemError):
            _problem().evaluate((2, 0))

    def test_unknown_schema_and_fields_are_rejected(self):
        payload = _problem().to_dict()
        payload["schema_version"] = 99
        with self.assertRaises(InvalidFinanceProblemError):
            StructuredPortfolioProblem.from_dict(payload)
        payload = _problem().to_dict()
        payload["unexpected"] = True
        with self.assertRaises(InvalidFinanceProblemError):
            StructuredPortfolioProblem.from_dict(payload)
        payload = _problem().to_dict()
        payload["objectives"][0]["expected_returns"] = ["not-a-number", 0.2]
        with self.assertRaises(InvalidFinanceProblemError):
            StructuredPortfolioProblem.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
