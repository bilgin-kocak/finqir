# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for evaluation value objects."""

# pylint: disable=missing-function-docstring

import unittest

from finqir.problems import ConstraintValue, FeasibilityReport


class TestEvaluation(unittest.TestCase):
    """Named constraint results remain easy to audit."""

    def test_feasibility_report_indexes_named_constraints(self):
        values = (ConstraintValue("mandatory", True, 0.0, "satisfied"),)
        report = FeasibilityReport(values)
        self.assertTrue(report.is_feasible)
        self.assertTrue(report.by_name("mandatory").satisfied)
        with self.assertRaises(KeyError):
            report.by_name("missing")


if __name__ == "__main__":
    unittest.main()
