# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Reversible mapping trace values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from finqir._typing import JSONValue, freeze_json, thaw_json
from finqir.exceptions import InterpretationError


@dataclass(frozen=True)
class MappingTraceEntry:
    """One mapping transformation and its reverse decoder."""

    name: str
    input_variables: tuple[str, ...]
    output_variables: tuple[str, ...]
    metadata: Mapping[str, Any]
    decoder: Callable[[Sequence[int]], tuple[int, ...]] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_variables", tuple(self.input_variables))
        object.__setattr__(self, "output_variables", tuple(self.output_variables))
        object.__setattr__(self, "metadata", freeze_json(dict(self.metadata)))

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize trace metadata while intentionally omitting the callable."""
        return {
            "name": self.name,
            "input_variables": list(self.input_variables),
            "output_variables": list(self.output_variables),
            "metadata": thaw_json(self.metadata),
        }


@dataclass(frozen=True)
class MappingTrace:
    """Ordered transformations whose decoders restore source holdings."""

    entries: tuple[MappingTraceEntry, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))

    def append(self, entry: MappingTraceEntry) -> "MappingTrace":
        """Return a trace with one additional entry."""
        return MappingTrace((*self.entries, entry))

    def interpret(self, values: Sequence[int]) -> tuple[int, ...]:
        """Decode a backend bit vector by applying entries in reverse."""
        result = tuple(values)
        try:
            for entry in reversed(self.entries):
                result = tuple(entry.decoder(result))
        except Exception as exc:
            raise InterpretationError("Mapping trace could not decode backend values") from exc
        return result

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize every trace entry."""
        return {"entries": [entry.to_dict() for entry in self.entries]}
