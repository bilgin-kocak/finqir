# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for reversible mapping traces."""

# pylint: disable=missing-function-docstring

import unittest

from finqir import InvalidFinanceProblemError
from finqir.mappings import MappingContext, MappingTrace, MappingTraceEntry, VariableMap


def _identity(values):
    return tuple(values)


def _insert_first(values):
    return (1, *values)


class TestMappingTrace(unittest.TestCase):
    """Trace decoders invert mappings from last to first."""

    def test_trace_decodes_in_reverse_order(self):
        trace = MappingTrace(
            (
                MappingTraceEntry("binary", ("a", "b"), ("x0", "x1"), {}, _identity),
                MappingTraceEntry(
                    "fixed",
                    ("x0", "x1"),
                    ("x1",),
                    {"fixed": {"x0": 1}},
                    _insert_first,
                ),
            )
        )
        self.assertEqual(trace.interpret((0,)), (1, 0))
        self.assertEqual(trace.to_dict()["entries"][1]["name"], "fixed")

    def test_metadata_is_defensively_frozen(self):
        metadata = {"fixed": [1]}
        entry = MappingTraceEntry("fixed", ("x",), (), metadata, _identity)
        metadata["fixed"].append(2)
        self.assertEqual(entry.metadata["fixed"], (1,))

    def test_variable_map_requires_one_location_per_source_asset(self):
        invalid = (
            lambda: VariableMap(("a", "b"), ("x_0", "x_1"), {"a": "x_0"}),
            lambda: VariableMap(("a", "b"), ("x_0",), {"a": "x_0", "b": "x_0"}),
        )
        for constructor in invalid:
            with self.subTest(constructor=constructor):
                with self.assertRaises(InvalidFinanceProblemError):
                    constructor()

    def test_mapping_context_rejects_nonfinite_penalties(self):
        for penalty in (float("nan"), float("inf")):
            with self.subTest(penalty=penalty):
                with self.assertRaises(InvalidFinanceProblemError):
                    MappingContext(penalty=penalty)


if __name__ == "__main__":
    unittest.main()
