# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Financial decision-variable definitions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal, Mapping

from finqir._typing import JSONValue, require_exact_fields
from finqir.exceptions import InvalidFinanceProblemError


@dataclass(frozen=True)
class HoldingVariable:
    """A binary decision identifying whether one asset is held."""

    asset_id: str
    domain: Literal["binary"] = "binary"
    lower_bound: int = 0
    upper_bound: int = 1
    lot_size: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.asset_id, str) or not self.asset_id.strip():
            raise InvalidFinanceProblemError("Holding variable asset_id must be non-empty")
        if self.domain != "binary" or self.lower_bound != 0 or self.upper_bound != 1:
            raise InvalidFinanceProblemError("FinQIR 0.2 supports exact binary holding variables")
        if not isinstance(self.lot_size, (int, float)) or not math.isfinite(float(self.lot_size)):
            raise InvalidFinanceProblemError("Holding lot_size must be finite")
        if float(self.lot_size) <= 0:
            raise InvalidFinanceProblemError("Holding lot_size must be positive")
        object.__setattr__(self, "lot_size", float(self.lot_size))

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize this variable."""
        return {
            "asset_id": self.asset_id,
            "domain": self.domain,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "lot_size": self.lot_size,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HoldingVariable":
        """Deserialize a validated holding variable."""
        require_exact_fields(
            payload,
            {"asset_id", "domain", "lower_bound", "upper_bound", "lot_size"},
            "holding variable",
        )
        return cls(
            asset_id=payload["asset_id"],
            domain=payload["domain"],
            lower_bound=payload["lower_bound"],
            upper_bound=payload["upper_bound"],
            lot_size=payload["lot_size"],
        )
