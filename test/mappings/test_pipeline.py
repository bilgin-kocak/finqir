# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for the financial mapping pipeline."""

# pylint: disable=missing-function-docstring

import unittest

from finqir import InvalidFinanceProblemError
from finqir.mappings import (
    ConstraintHandling,
    ConstraintPolicy,
    FinanceMappingPipeline,
    MappingContext,
)
from finqir.problems import (
    Asset,
    CapitalBudget,
    Cardinality,
    ExpectedReturn,
    StructuredPortfolioProblem,
)


class TestPipeline(unittest.TestCase):
    """The default pipeline records reversible policy decisions."""

    def test_pipeline_records_deferred_strategies(self):
        problem = StructuredPortfolioProblem(
            [Asset("a"), Asset("b")],
            [ExpectedReturn([1, 2])],
            constraints=[Cardinality(exactly=1), CapitalBudget([2, 3], maximum=3, name="capital")],
        )
        policy = ConstraintPolicy(overrides={"cardinality": ConstraintHandling.FEASIBLE_SUBSPACE})
        compiled = FinanceMappingPipeline().compile(problem, context=MappingContext(policy))
        self.assertEqual(
            compiled.constraint_modes["cardinality"],
            ConstraintHandling.FEASIBLE_SUBSPACE,
        )
        self.assertEqual(compiled.constraint_modes["capital"], ConstraintHandling.PENALTY)
        self.assertEqual(
            [entry.name for entry in compiled.trace.entries],
            ["binary_holdings", "fixed_cardinality", "constraint_handling"],
        )
        self.assertGreater(len(compiled.optimization_problem.linear_constraints), 0)
        self.assertEqual(compiled.trace.interpret((0, 1)), (0, 1))

    def test_duplicate_mapping_names_are_rejected(self):
        from finqir.mappings import BinaryHoldingsMapping

        with self.assertRaises(InvalidFinanceProblemError):
            FinanceMappingPipeline([BinaryHoldingsMapping(), BinaryHoldingsMapping()])

    def test_empty_explicit_pipeline_is_rejected(self):
        with self.assertRaises(InvalidFinanceProblemError):
            FinanceMappingPipeline([])


if __name__ == "__main__":
    unittest.main()
