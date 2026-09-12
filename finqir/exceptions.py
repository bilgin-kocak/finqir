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

"""Exceptions raised by FinQIR."""

from qiskit.exceptions import QiskitError


class FinQIRError(QiskitError):
    """Class for errors returned by FinQIR module."""


class InvalidFinanceProblemError(FinQIRError):
    """Raised when a finance model is malformed or internally contradictory."""


class InfeasiblePortfolioError(FinQIRError):
    """Raised when no feasible portfolio can satisfy the requested constraints."""


class UnsupportedMappingError(FinQIRError):
    """Raised when a mapping cannot represent a finance model."""


class ConstraintPreservationError(FinQIRError):
    """Raised when compilation cannot preserve a requested constraint."""


class CompilationError(FinQIRError):
    """Raised when finance compilation fails."""


class InterpretationError(FinQIRError):
    """Raised when a backend result cannot be interpreted safely."""
