# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for conflict-graph portfolio applications."""

# pylint: disable=missing-function-docstring

import math
import unittest

from finqir import InvalidFinanceProblemError
from finqir.applications.optimization import ConflictGraphPortfolio


class TestConflictGraphPortfolio(unittest.TestCase):
    """Conflict graphs become weighted independent-set finance models."""

    def test_conflict_graph_becomes_weighted_maximization(self):
        application = ConflictGraphPortfolio(
            vertices=["loan-a", "loan-b", "loan-c"],
            edges=[("loan-a", "loan-b")],
            weights={"loan-a": 2.0, "loan-b": 1.0, "loan-c": 3.0},
            mandatory=["loan-c"],
            maximum_cardinality=2,
        )
        problem = application.to_structured_problem()
        self.assertEqual(problem.objective_sense, "maximize")
        self.assertEqual(problem.evaluate((1, 0, 1)).total, 5.0)
        self.assertTrue(problem.check_feasibility((1, 0, 1)).is_feasible)
        self.assertFalse(problem.check_feasibility((1, 1, 1)).is_feasible)
        self.assertEqual(application.interpret((1, 0, 1)), ("loan-a", "loan-c"))

    def test_graph_and_additional_conflicts_remain_separate(self):
        application = ConflictGraphPortfolio(
            ["a", "b", "c"],
            [("b", "a")],
            additional_conflicts=[("a", "c")],
        )
        self.assertEqual(application.edges, (("a", "b"),))
        self.assertEqual(
            [item.name for item in application.to_structured_problem().constraints],
            ["graph_conflicts", "additional_conflicts"],
        )

    def test_invalid_graph_definitions_are_rejected(self):
        invalid = [
            lambda: ConflictGraphPortfolio(["a", "a"], []),
            lambda: ConflictGraphPortfolio(["a"], [("a", "a")]),
            lambda: ConflictGraphPortfolio(["a"], [("a", "missing")]),
            lambda: ConflictGraphPortfolio(["a", "b"], [("a", "b"), ("b", "a")]),
            lambda: ConflictGraphPortfolio(["a"], [], weights={"a": math.inf}),
            lambda: ConflictGraphPortfolio(["a"], [], mandatory=["a"], excluded=["a"]),
            lambda: ConflictGraphPortfolio(["a", "b"], [("a", "b")], mandatory=["a", "b"]),
        ]
        for constructor in invalid:
            with self.subTest(constructor=constructor):
                with self.assertRaises(InvalidFinanceProblemError):
                    constructor()


if __name__ == "__main__":
    unittest.main()
