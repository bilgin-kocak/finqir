# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for named finance constraints."""

# pylint: disable=missing-function-docstring,unnecessary-lambda

import math
import unittest

from finqir import InvalidFinanceProblemError
from finqir.problems import (
    CapitalBudget,
    Cardinality,
    ExcludedHoldings,
    ExposureBounds,
    MandatoryHoldings,
    MutualExclusions,
)


class TestConstraints(unittest.TestCase):
    """Constraints report named feasibility and violation magnitudes."""

    def test_constraint_evaluation(self):
        cases = (
            (Cardinality(exactly=2), (1, 0, 1), ("a", "b", "c"), True, 0.0),
            (Cardinality(maximum=1), (1, 0, 1), ("a", "b", "c"), False, 1.0),
            (CapitalBudget([3.0, 5.0], maximum=6.0), (0, 1), ("a", "b"), True, 0.0),
            (MandatoryHoldings(["a"]), (0, 1), ("a", "b"), False, 1.0),
            (ExcludedHoldings(["b"]), (1, 1), ("a", "b"), False, 1.0),
            (MutualExclusions([("a", "b")]), (1, 1), ("a", "b"), False, 1.0),
            (
                ExposureBounds({"a": 0.6, "b": 0.5}, maximum=1.0, name="sector:tech"),
                (1, 1),
                ("a", "b"),
                False,
                0.1,
            ),
        )
        for constraint, holdings, ids, satisfied, violation in cases:
            with self.subTest(constraint=constraint.name):
                actual = constraint.evaluate(holdings, ids)
                self.assertEqual(actual.satisfied, satisfied)
                self.assertAlmostEqual(actual.violation, violation)

    def test_involved_ids_keep_source_order(self):
        constraint = ExposureBounds({"c": 0.5, "a": 0.2, "b": 0.0}, maximum=1)
        self.assertEqual(constraint.involved_asset_ids(("a", "b", "c")), ("a", "c"))

    def test_invalid_constraint_definitions_are_rejected(self):
        invalid = [
            lambda: Cardinality(),
            lambda: Cardinality(exactly=1, maximum=2),
            lambda: Cardinality(minimum=2, maximum=1),
            lambda: CapitalBudget([1], name=""),
            lambda: CapitalBudget([math.inf], maximum=1),
            lambda: MutualExclusions([("a", "a")]),
            lambda: MutualExclusions([("a", "b"), ("b", "a")]),
            lambda: ExposureBounds({"a": math.nan}, maximum=1),
        ]
        for constructor in invalid:
            with self.subTest(constructor=constructor):
                with self.assertRaises(InvalidFinanceProblemError):
                    constructor()

    def test_unknown_asset_is_rejected_during_validation(self):
        with self.assertRaises(InvalidFinanceProblemError):
            MandatoryHoldings(["missing"]).validate(("a", "b"))


if __name__ == "__main__":
    unittest.main()
