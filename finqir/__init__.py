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

This is the FinQIR module. It has applications based on
`Amplitude Estimation
<https://qiskit-community.github.io/qiskit-algorithms/apidocs/qiskit_algorithms.html#amplitude-estimators>`__
and optimization using
`Qiskit Optimization <https://qiskit-community.github.io/qiskit-optimization/>`__,
some library circuits useful for finance applications,
and data providers which supply a source of financial data.

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
   circuit
   data_providers

"""

from .version import __version__
from .exceptions import FinQIRError

__title__ = "FinQIR"

__all__ = ["__title__", "__version__", "FinQIRError"]
