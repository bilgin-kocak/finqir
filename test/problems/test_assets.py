# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for asset and holding value objects."""

# pylint: disable=missing-function-docstring

import unittest

from finqir import InvalidFinanceProblemError
from finqir.problems import Asset, HoldingVariable


class TestAssets(unittest.TestCase):
    """Asset values are validated and immutable."""

    def test_asset_rejects_empty_id_and_freezes_nested_metadata(self):
        with self.assertRaises(InvalidFinanceProblemError):
            Asset("")
        source = {"sector": "energy", "tags": ["liquid"], "nested": {"rank": 1}}
        asset = Asset("asset-a", metadata=source)
        source["sector"] = "changed"
        source["tags"].append("changed")
        self.assertEqual(asset.metadata["sector"], "energy")
        self.assertEqual(asset.metadata["tags"], ("liquid",))
        with self.assertRaises(TypeError):
            asset.metadata["sector"] = "banking"

    def test_asset_rejects_non_json_metadata(self):
        with self.assertRaises(InvalidFinanceProblemError):
            Asset("a", metadata={"bad": object()})

    def test_holding_variable_preserves_lot_size(self):
        variable = HoldingVariable("asset-a", lot_size=100.0)
        self.assertEqual(
            (variable.domain, variable.lower_bound, variable.upper_bound),
            ("binary", 0, 1),
        )
        self.assertEqual(variable.lot_size, 100.0)

    def test_holding_variable_rejects_unsupported_domain(self):
        with self.assertRaises(InvalidFinanceProblemError):
            HoldingVariable("a", domain="integer")
        with self.assertRaises(InvalidFinanceProblemError):
            HoldingVariable("a", lot_size=0)


if __name__ == "__main__":
    unittest.main()
