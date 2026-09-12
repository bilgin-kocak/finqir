# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for the strict TRUBA input adapter."""

# pylint: disable=missing-function-docstring

import json
import tempfile
import unittest
from pathlib import Path

from finqir import InvalidFinanceProblemError
from finqir.benchmarks.truba import load_truba_instance
from finqir.mappings import ConstraintHandling


class TestTrubaAdapter(unittest.TestCase):
    """Turkish contest fields map to source-preserving finance concepts."""

    def test_adapter_maps_turkish_fields(self):
        path = Path("test/resources/truba/soru2_girdi_synthetic.json")
        instance = load_truba_instance(path)
        self.assertEqual((instance.question_id, instance.case_id), (2, 99))
        self.assertEqual(instance.application.edges, (("0", "1"), ("1", "2")))
        self.assertEqual(instance.application.mandatory, ("0",))
        self.assertEqual(len(instance.source_sha256), 64)

    def test_question_four_uses_feasible_subspace_for_extra_pairs(self):
        instance = self._load(
            {
                "question_id": 4,
                "case_id": 1,
                "cizge": [[0, 0], [0, 0]],
                "yasak_ikililer": [[0, 1]],
            }
        )
        self.assertEqual(
            instance.constraint_policy.for_constraint("additional_conflicts"),
            ConstraintHandling.FEASIBLE_SUBSPACE,
        )

    def test_invalid_inputs_are_rejected(self):
        base = {"question_id": 1, "case_id": 1, "cizge": [[0, 1], [1, 0]]}
        invalid = [
            {**base, "question_id": 9},
            {**base, "cizge": [[0, 1]]},
            {**base, "cizge": [[0, 0], [1, 0]]},
            {**base, "cizge": [[1, 0], [0, 0]]},
            {**base, "cizge": [[0, 2], [2, 0]]},
            {**base, "question_id": 2},
            {**base, "question_id": 1, "zorunlu_dugumler": [0]},
            {
                **base,
                "question_id": 3,
                "yasak_ikililer": [[0, 2]],
            },
        ]
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(InvalidFinanceProblemError):
                    self._load(payload)

    @staticmethod
    def _load(payload):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "instance.json")
            path.write_text(json.dumps(payload), encoding="utf8")
            return load_truba_instance(path)


if __name__ == "__main__":
    unittest.main()
