# This file is derived from Qiskit Finance for use in FinQIR.
#
# (C) Copyright IBM 2019, 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Expose the FinQIR package version."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = Path(__file__).with_name("VERSION.txt").read_text(encoding="utf8").strip()
except OSError:
    try:
        __version__ = version("finqir")
    except PackageNotFoundError:
        __version__ = "unknown"
