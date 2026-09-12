# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Asset value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from finqir._typing import JSONValue, freeze_json, require_exact_fields, thaw_json
from finqir.exceptions import InvalidFinanceProblemError


@dataclass(frozen=True)
class Asset:
    """An asset with a stable source identifier and immutable metadata."""

    id: str  # pylint: disable=invalid-name
    name: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise InvalidFinanceProblemError("Asset id must be a non-empty string")
        if self.name is not None and (not isinstance(self.name, str) or not self.name.strip()):
            raise InvalidFinanceProblemError("Asset name must be a non-empty string when supplied")
        frozen = freeze_json(dict(self.metadata))
        object.__setattr__(self, "metadata", frozen)

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize this asset."""
        return {"id": self.id, "name": self.name, "metadata": thaw_json(self.metadata)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Asset":
        """Deserialize a validated asset."""
        require_exact_fields(payload, {"id", "name", "metadata"}, "asset")
        metadata = payload["metadata"]
        if not isinstance(metadata, Mapping):
            raise InvalidFinanceProblemError("Asset metadata must be an object")
        return cls(id=payload["id"], name=payload["name"], metadata=metadata)
