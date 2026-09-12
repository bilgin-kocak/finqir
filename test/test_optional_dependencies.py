# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for FinQIR's optional dependency boundary."""

from __future__ import annotations

import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as tomllib_loader
else:
    import tomli as tomllib_loader


class TestOptionalDependencies(unittest.TestCase):
    """The structured modeling layer must not require legacy integrations."""

    def test_dependency_groups(self) -> None:
        """Heavy integrations belong to explicit extras, not core requirements."""
        project = tomllib_loader.loads(Path("pyproject.toml").read_text(encoding="utf8"))["project"]
        dependencies = project["dependencies"]
        extras = project["optional-dependencies"]

        self.assertTrue(any(item.startswith("qiskit-addon-opt-mapper") for item in dependencies))
        self.assertIn("numpy>=2.0", dependencies)
        self.assertIn("scipy>=1.14", dependencies)
        self.assertFalse(any(item.startswith("qiskit-algorithms") for item in dependencies))
        self.assertFalse(any(item.startswith("qiskit-optimization") for item in dependencies))
        self.assertIn("algorithms", extras)
        self.assertIn("data", extras)
        self.assertIn("legacy", extras)

    def test_core_import_does_not_import_optional_packages(self) -> None:
        """A clean core import must not reach optional integration packages."""
        source = textwrap.dedent("""
            import importlib.abc

            BLOCKED = {
                "qiskit_algorithms",
                "qiskit_optimization",
                "pandas",
                "yfinance",
            }

            class BlockOptional(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname.split(".", maxsplit=1)[0] in BLOCKED:
                        raise ImportError(f"blocked optional import: {fullname}")
                    return None

            import sys
            sys.meta_path.insert(0, BlockOptional())

            import finqir
            assert "qiskit_algorithms" not in sys.modules
            assert "qiskit_optimization" not in sys.modules
            """)
        completed = subprocess.run(
            [sys.executable, "-c", source],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
