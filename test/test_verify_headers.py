# This file is part of FinQIR.
#
# (C) Copyright Bilgin Kocak 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for the source-header validation tool."""

from pathlib import Path
import tempfile
import unittest

from tools.verify_headers import validate_header


class TestVerifyHeaders(unittest.TestCase):
    """Verify inherited and independent source notices are accepted."""

    def test_accepts_finqir_header(self):
        """New FinQIR files use their own project and copyright identity."""
        source = """# This file is part of FinQIR.
#
# (C) Copyright Bilgin Kocak 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

\"\"\"Example.\"\"\"
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "example.py")
            path.write_text(source, encoding="utf8")
            _, valid, reason = validate_header(path)

        self.assertTrue(valid, reason)

    def test_accepts_derived_header(self):
        """Derived files identify FinQIR while retaining IBM copyright."""
        source = """# This file is derived from Qiskit Finance for use in FinQIR.
#
# (C) Copyright IBM 2020, 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

\"\"\"Example.\"\"\"
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "derived.py")
            path.write_text(source, encoding="utf8")
            _, valid, reason = validate_header(path)

        self.assertTrue(valid, reason)


if __name__ == "__main__":
    unittest.main()
