# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for structured financial objectives."""

# pylint: disable=missing-function-docstring

import math
import unittest

from finqir import InvalidFinanceProblemError
from finqir.problems import ExpectedReturn, TransactionCost, VarianceRisk


class TestObjectives(unittest.TestCase):
    """Objective coefficients retain financial meaning."""

    def test_expected_return_exposes_raw_and_weighted_values(self):
        objective = ExpectedReturn([0.1, 0.2], weight=-1.0)
        value = objective.evaluate((1, 0))
        self.assertEqual(value.raw_value, 0.1)
        self.assertEqual(value.contribution, -0.1)
        self.assertEqual(objective.coefficients().linear, (0.1, 0.2))

    def test_variance_uses_full_symmetric_quadratic_form(self):
        objective = VarianceRisk([[1.0, 0.25], [0.25, 2.0]], weight=0.5)
        value = objective.evaluate((1, 1))
        self.assertEqual(value.raw_value, 3.5)
        self.assertEqual(value.contribution, 1.75)

    def test_transaction_cost_is_a_linear_binary_objective(self):
        objective = TransactionCost(
            current_holdings=[1, 0], buy_costs=[0.4, 0.5], sell_costs=[0.2, 0.3]
        )
        self.assertAlmostEqual(objective.evaluate((0, 1)).raw_value, 0.7)
        self.assertEqual(objective.coefficients().constant, 0.2)
        self.assertEqual(objective.coefficients().linear, (-0.2, 0.5))

    def test_invalid_objective_inputs_are_rejected(self):
        invalid = [
            lambda: ExpectedReturn([]),
            lambda: ExpectedReturn([math.nan]),
            lambda: ExpectedReturn([1.0], weight=math.inf),
            lambda: VarianceRisk([[1.0, 0.2], [0.3, 1.0]]),
            lambda: VarianceRisk([[1.0, 0.0]]),
            lambda: TransactionCost([2], [0.1], [0.1]),
            lambda: TransactionCost([0], [-0.1], [0.1]),
            lambda: TransactionCost([0, 1], [0.1], [0.1]),
        ]
        for constructor in invalid:
            with self.subTest(constructor=constructor):
                with self.assertRaises(InvalidFinanceProblemError):
                    constructor()

    def test_wrong_holding_length_is_rejected(self):
        with self.assertRaises(InvalidFinanceProblemError):
            ExpectedReturn([0.1, 0.2]).evaluate((1,))


if __name__ == "__main__":
    unittest.main()
