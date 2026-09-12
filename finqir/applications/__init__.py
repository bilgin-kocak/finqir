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

"""
Finance applications (:mod:`finqir.applications`)
=========================================================

.. currentmodule:: finqir.applications

FinQIR ready-made applications.

Optimization Applications
-------------------------

.. autosummary::
   :toctree: ../stubs/
   :nosignatures:

   PortfolioOptimization
   PortfolioDiversification
   ConflictGraphPortfolio

Estimation Applications
-----------------------

.. autosummary::
   :toctree: ../stubs/
   :nosignatures:

   EstimationApplication
   EuropeanCallDelta
   EuropeanCallPricing
   FixedIncomePricing


"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from qiskit.exceptions import MissingOptionalLibraryError

if TYPE_CHECKING:
    from .estimation import (
        EstimationApplication,
        EuropeanCallDelta,
        EuropeanCallPricing,
        FixedIncomePricing,
    )
    from .optimization import (
        ConflictGraphPortfolio,
        PortfolioDiversification,
        PortfolioOptimization,
    )

_ESTIMATION_NAMES = {
    "EstimationApplication",
    "EuropeanCallDelta",
    "EuropeanCallPricing",
    "FixedIncomePricing",
}
_OPTIMIZATION_NAMES = {"PortfolioOptimization", "PortfolioDiversification"}


def __getattr__(name: str) -> Any:
    """Load legacy applications only when their optional dependency is installed."""
    if name == "ConflictGraphPortfolio":
        module = import_module(".optimization", __name__)
        return getattr(module, name)
    if name in _ESTIMATION_NAMES:
        try:
            module = import_module(".estimation", __name__)
        except ImportError as exc:
            raise MissingOptionalLibraryError(
                "qiskit-algorithms", name, "pip install 'finqir[algorithms]'"
            ) from exc
        return getattr(module, name)
    if name in _OPTIMIZATION_NAMES:
        try:
            module = import_module(".optimization", __name__)
        except ImportError as exc:
            raise MissingOptionalLibraryError(
                "qiskit-optimization", name, "pip install 'finqir[legacy]'"
            ) from exc
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PortfolioOptimization",
    "PortfolioDiversification",
    "EstimationApplication",
    "EuropeanCallDelta",
    "EuropeanCallPricing",
    "FixedIncomePricing",
    "ConflictGraphPortfolio",
]
