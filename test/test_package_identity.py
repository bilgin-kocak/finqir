# This file is part of FinQIR.
#
# (C) Copyright Bilgin Kocak 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for FinQIR's independent distribution and import identity."""

from pathlib import Path
import unittest

from qiskit.exceptions import QiskitError
import tomli


class TestPackageIdentity(unittest.TestCase):
    """Verify the public package is FinQIR rather than Qiskit Finance."""

    def test_finqir_is_the_public_import(self):
        """The package exposes the FinQIR name and exception."""
        import finqir

        self.assertEqual(finqir.__title__, "FinQIR")
        self.assertEqual(finqir.__version__, "0.2.0")
        self.assertTrue(issubclass(finqir.FinQIRError, QiskitError))

    def test_legacy_namespace_is_not_part_of_the_source_tree(self):
        """The independent library must not collide with qiskit-finance."""
        project_root = Path(__file__).resolve().parent.parent
        self.assertFalse(project_root.joinpath("qiskit_finance").exists())

    def test_pyproject_declares_finqir_distribution(self):
        """Build metadata uses the independent name and supported runtime."""
        project_root = Path(__file__).resolve().parent.parent
        with project_root.joinpath("pyproject.toml").open("rb") as pyproject_file:
            project = tomli.load(pyproject_file)["project"]

        self.assertEqual(project["name"], "finqir")
        self.assertEqual(project["version"], "0.2.0")
        self.assertEqual(
            project["version"],
            project_root.joinpath("finqir", "VERSION.txt").read_text(encoding="utf8").strip(),
        )
        self.assertEqual(project["requires-python"], ">=3.10")
        self.assertIn("qiskit>=2.5.2,<3", project["dependencies"])


if __name__ == "__main__":
    unittest.main()
