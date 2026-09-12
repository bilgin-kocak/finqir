# This file is derived from Qiskit Finance for use in FinQIR.
#
# (C) Copyright IBM 2019, 2024.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
=============================================
FinQIR module (:mod:`finqir`)
=============================================

.. currentmodule:: finqir

FinQIR provides a structured financial problem representation, auditable
compiler mappings, exact classical baselines, and applications based on
`Amplitude Estimation
<https://qiskit-community.github.io/qiskit-algorithms/apidocs/qiskit_algorithms.html#amplitude-estimators>`__
alongside library circuits and financial data providers.

.. autosummary::
   :toctree: ../stubs/
   :nosignatures:

    FinQIRError

In addition to standard Python errors the FinQIR module will raise this error
if circumstances are that it cannot proceed to completion.

Submodules
==========

.. autosummary::
   :toctree:

   applications
   benchmarks
   circuit
   compilation
   data_providers
   mappings
   problems

"""

from .version import __version__
from .exceptions import (
    CompilationError,
    ConstraintPreservationError,
    FinQIRError,
    InfeasiblePortfolioError,
    InterpretationError,
    InvalidFinanceProblemError,
    UnsupportedMappingError,
)
from .problems import (
    Asset,
    CapitalBudget,
    Cardinality,
    ExcludedHoldings,
    ExpectedReturn,
    ExposureBounds,
    HoldingVariable,
    MandatoryHoldings,
    MutualExclusions,
    StructuredPortfolioProblem,
    TransactionCost,
    VarianceRisk,
)
from .applications.optimization import ConflictGraphPortfolio

__title__ = "FinQIR"

__all__ = [
    "__title__",
    "__version__",
    "Asset",
    "CapitalBudget",
    "Cardinality",
    "CompilationError",
    "ConflictGraphPortfolio",
    "ConstraintPreservationError",
    "ExcludedHoldings",
    "ExpectedReturn",
    "ExposureBounds",
    "FinQIRError",
    "HoldingVariable",
    "InfeasiblePortfolioError",
    "InterpretationError",
    "InvalidFinanceProblemError",
    "MandatoryHoldings",
    "MutualExclusions",
    "StructuredPortfolioProblem",
    "TransactionCost",
    "UnsupportedMappingError",
    "VarianceRisk",
]
