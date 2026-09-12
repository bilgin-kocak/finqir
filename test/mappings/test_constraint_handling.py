# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for constraint strategy classification."""

# pylint: disable=missing-function-docstring

import unittest

from finqir.mappings import ConstraintHandling, ConstraintPolicy


class TestConstraintHandling(unittest.TestCase):
    """Named overrides take precedence over the default strategy."""

    def test_policy_override_wins(self):
        policy = ConstraintPolicy(
            default=ConstraintHandling.PENALTY,
            overrides={"cardinality": ConstraintHandling.FEASIBLE_SUBSPACE},
        )
        self.assertEqual(policy.for_constraint("cardinality"), ConstraintHandling.FEASIBLE_SUBSPACE)
        self.assertEqual(policy.for_constraint("capital"), ConstraintHandling.PENALTY)


if __name__ == "__main__":
    unittest.main()
