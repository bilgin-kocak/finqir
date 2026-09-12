# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for exact classical benchmark baselines."""

# pylint: disable=missing-function-docstring

import unittest

from finqir.applications.optimization import ConflictGraphPortfolio
from finqir.benchmarks import solve_conflict_graph_classically


class TestBaselines(unittest.TestCase):
    """MILP supplies an auditable optimum for graph applications."""

    def test_weighted_graph_optimum(self):
        application = ConflictGraphPortfolio(
            ["a", "b", "c"],
            [("a", "b"), ("b", "c")],
            weights={"a": 2, "b": 5, "c": 4},
        )
        result = solve_conflict_graph_classically(application)
        self.assertTrue(result.is_optimal)
        self.assertEqual(result.selected_assets, ("a", "c"))
        self.assertEqual(result.holdings, (1, 0, 1))
        self.assertEqual(result.objective_value, 6.0)
        self.assertTrue(
            application.to_structured_problem().check_feasibility(result.holdings).is_feasible
        )

    def test_mandatory_and_additional_conflicts(self):
        application = ConflictGraphPortfolio(
            ["a", "b", "c"],
            [],
            mandatory=["a"],
            additional_conflicts=[("a", "b")],
        )
        result = solve_conflict_graph_classically(application)
        self.assertIn("a", result.selected_assets)
        self.assertNotIn("b", result.selected_assets)


if __name__ == "__main__":
    unittest.main()
