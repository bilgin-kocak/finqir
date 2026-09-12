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


"""Optimization applications for finance."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from qiskit.exceptions import MissingOptionalLibraryError

from .conflict_graph_portfolio import ConflictGraphPortfolio

if TYPE_CHECKING:
    from .portfolio_diversification import PortfolioDiversification
    from .portfolio_optimization import PortfolioOptimization

_LEGACY_NAMES = {"PortfolioOptimization", "PortfolioDiversification"}


def __getattr__(name: str) -> Any:
    if name in _LEGACY_NAMES:
        module_name = (
            ".portfolio_optimization"
            if name == "PortfolioOptimization"
            else ".portfolio_diversification"
        )
        try:
            module = import_module(module_name, __name__)
        except ImportError as exc:
            raise MissingOptionalLibraryError(
                "qiskit-optimization", name, "pip install 'finqir[legacy]'"
            ) from exc
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ConflictGraphPortfolio", "PortfolioOptimization", "PortfolioDiversification"]
