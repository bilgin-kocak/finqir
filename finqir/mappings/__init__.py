# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Pluggable mappings from financial semantics to optimization models."""

from .base import (
    ConstraintHandling,
    ConstraintPolicy,
    FinancialMapping,
    MappingContext,
    MappingOutput,
    VariableMap,
)
from .trace import MappingTrace, MappingTraceEntry
from .binary_holdings import BinaryHoldingsMapping
from .constraint_handling import (
    FeasibleSubspaceMapping,
    FixedCardinalityMapping,
    PenaltyConstraintMapping,
)
from .pipeline import FinanceMappingPipeline

__all__ = [
    "ConstraintHandling",
    "ConstraintPolicy",
    "FinancialMapping",
    "MappingContext",
    "MappingOutput",
    "MappingTrace",
    "MappingTraceEntry",
    "VariableMap",
    "BinaryHoldingsMapping",
    "FeasibleSubspaceMapping",
    "FinanceMappingPipeline",
    "FixedCardinalityMapping",
    "PenaltyConstraintMapping",
]
