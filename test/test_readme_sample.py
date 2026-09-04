# This file is derived from Qiskit Finance for use in FinQIR.
#
# (C) Copyright IBM 2020, 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Execute and validate the first Python example in the README."""

from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import re
import unittest

from test import FinQIRTestCase


class TestReadmeSample(FinQIRTestCase):
    """Ensure the documented quick start remains executable."""

    def test_readme_sample(self):
        """The README example builds the documented portfolio model."""
        readme_path = Path(__file__).parent.parent.joinpath("README.md")
        self.assertTrue(readme_path.is_file(), f"README.md not found at {readme_path}")

        match = re.search(
            r"```python\n(.*?)```", readme_path.read_text(encoding="utf8"), flags=re.S
        )
        self.assertIsNotNone(match, "No Python sample found in README.md")

        namespace = {}
        try:
            with redirect_stdout(StringIO()):
                exec(match.group(1), namespace)  # pylint: disable=exec-used
        except Exception as ex:  # pylint: disable=broad-except
            self.fail(str(ex))

        quadratic_program = namespace["quadratic_program"]
        self.assertEqual(quadratic_program.get_num_vars(), 3)
        self.assertEqual(quadratic_program.get_num_linear_constraints(), 1)


if __name__ == "__main__":
    unittest.main()
