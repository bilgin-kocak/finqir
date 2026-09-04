# This file is part of FinQIR.
#
# (C) Copyright Bilgin Kocak 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Validation for the tutorial notebooks distributed with the repository."""

import json
from pathlib import Path
import unittest


class TestTutorialNotebooks(unittest.TestCase):
    """Keep rebranded tutorials internally consistent and reproducible."""

    def test_notebooks_use_current_sampler_and_have_clean_outputs(self):
        """Tutorials use the Qiskit V2 sampler and contain no stale results."""
        tutorial_dir = Path(__file__).parent.parent.joinpath("docs", "tutorials")

        for notebook_path in tutorial_dir.glob("*.ipynb"):
            with self.subTest(notebook=notebook_path.name):
                notebook = json.loads(notebook_path.read_text(encoding="utf8"))
                source = "".join(
                    "".join(cell.get("source", [])) for cell in notebook.get("cells", [])
                )

                self.assertNotIn("from qiskit.primitives import Sampler", source)
                self.assertNotIn("from qiskit_aer.primitives import Sampler", source)
                self.assertNotIn(".quasi_dists", source)
                if "StatevectorSampler(" in source:
                    self.assertIn("from qiskit.primitives import StatevectorSampler", source)

                for cell in notebook.get("cells", []):
                    self.assertFalse(cell.get("outputs", []))
                    self.assertNotIn("nbsphinx-thumbnail", cell.get("metadata", {}).get("tags", []))


if __name__ == "__main__":
    unittest.main()
