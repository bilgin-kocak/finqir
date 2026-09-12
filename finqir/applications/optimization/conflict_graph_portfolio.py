# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Weighted independent-set applications expressed as finance problems."""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from finqir.exceptions import InterpretationError, InvalidFinanceProblemError
from finqir.problems import (
    Asset,
    Cardinality,
    ExcludedHoldings,
    ExpectedReturn,
    FinanceConstraint,
    MandatoryHoldings,
    MutualExclusions,
    StructuredPortfolioProblem,
)


@dataclass(frozen=True)
class ConflictGraphPortfolio:
    """Select maximum-weight mutually compatible vertices."""

    vertices: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    weights: Mapping[str, float]
    mandatory: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()
    additional_conflicts: tuple[tuple[str, str], ...] = ()
    maximum_cardinality: int | None = None
    name: str = "conflict_graph_portfolio"

    def __init__(
        self,
        vertices: Sequence[str],
        edges: Sequence[tuple[str, str]],
        weights: Mapping[str, float] | None = None,
        mandatory: Sequence[str] = (),
        excluded: Sequence[str] = (),
        additional_conflicts: Sequence[tuple[str, str]] = (),
        maximum_cardinality: int | None = None,
        name: str = "conflict_graph_portfolio",
    ):
        vertex_values = tuple(vertices)
        if not vertex_values or any(
            not isinstance(item, str) or not item for item in vertex_values
        ):
            raise InvalidFinanceProblemError("Graph vertices must be non-empty strings")
        if len(set(vertex_values)) != len(vertex_values):
            raise InvalidFinanceProblemError("Graph vertices must be unique")
        position = {vertex: index for index, vertex in enumerate(vertex_values)}

        def canonicalize(
            pairs: Sequence[tuple[str, str]], label: str
        ) -> tuple[tuple[str, str], ...]:
            canonical = []
            for pair in pairs:
                if len(pair) != 2 or pair[0] not in position or pair[1] not in position:
                    raise InvalidFinanceProblemError(f"{label} contains an unknown endpoint")
                if pair[0] == pair[1]:
                    raise InvalidFinanceProblemError(f"{label} cannot contain self-loops")
                ordered = (
                    (pair[0], pair[1])
                    if position[pair[0]] < position[pair[1]]
                    else (pair[1], pair[0])
                )
                canonical.append(ordered)
            if len(set(canonical)) != len(canonical):
                raise InvalidFinanceProblemError(f"{label} contains duplicate edges")
            return tuple(sorted(canonical, key=lambda pair: (position[pair[0]], position[pair[1]])))

        edge_values = canonicalize(edges, "edges")
        additional_values = canonicalize(additional_conflicts, "additional_conflicts")
        weight_values = {vertex: 1.0 for vertex in vertex_values}
        if weights is not None:
            unknown_weights = set(weights) - set(vertex_values)
            if unknown_weights:
                raise InvalidFinanceProblemError(
                    f"Weights reference unknown vertices {sorted(unknown_weights)!r}"
                )
            weight_values.update({vertex: float(value) for vertex, value in weights.items()})
        if not all(math.isfinite(value) for value in weight_values.values()):
            raise InvalidFinanceProblemError("Graph weights must be finite")

        def normalize_vertices(values: Sequence[str], label: str) -> tuple[str, ...]:
            requested = tuple(values)
            if len(set(requested)) != len(requested) or set(requested) - set(vertex_values):
                raise InvalidFinanceProblemError(f"{label} vertices must be known and unique")
            requested_set = set(requested)
            return tuple(vertex for vertex in vertex_values if vertex in requested_set)

        mandatory_values = normalize_vertices(mandatory, "mandatory")
        excluded_values = normalize_vertices(excluded, "excluded")
        if set(mandatory_values) & set(excluded_values):
            raise InvalidFinanceProblemError("A vertex cannot be mandatory and excluded")
        all_conflicts = set(edge_values) | set(additional_values)
        if any(
            left in mandatory_values and right in mandatory_values for left, right in all_conflicts
        ):
            raise InvalidFinanceProblemError("Mandatory vertices contain a conflicting pair")
        if maximum_cardinality is not None:
            if (
                isinstance(maximum_cardinality, bool)
                or not isinstance(maximum_cardinality, int)
                or maximum_cardinality < 0
                or maximum_cardinality > len(vertex_values)
            ):
                raise InvalidFinanceProblemError("maximum_cardinality is outside the vertex range")
            if len(mandatory_values) > maximum_cardinality:
                raise InvalidFinanceProblemError("Mandatory vertices exceed maximum_cardinality")
        if not isinstance(name, str) or not name.strip():
            raise InvalidFinanceProblemError("Application name must be non-empty")
        object.__setattr__(self, "vertices", vertex_values)
        object.__setattr__(self, "edges", edge_values)
        object.__setattr__(self, "weights", MappingProxyType(weight_values))
        object.__setattr__(self, "mandatory", mandatory_values)
        object.__setattr__(self, "excluded", excluded_values)
        object.__setattr__(self, "additional_conflicts", additional_values)
        object.__setattr__(self, "maximum_cardinality", maximum_cardinality)
        object.__setattr__(self, "name", name)

    def to_structured_problem(self) -> StructuredPortfolioProblem:
        """Convert this graph into a weighted-maximization structured problem."""
        constraints: list[FinanceConstraint] = []
        if self.edges:
            constraints.append(MutualExclusions(self.edges, name="graph_conflicts"))
        if self.additional_conflicts:
            constraints.append(
                MutualExclusions(self.additional_conflicts, name="additional_conflicts")
            )
        if self.mandatory:
            constraints.append(MandatoryHoldings(self.mandatory))
        if self.excluded:
            constraints.append(ExcludedHoldings(self.excluded))
        if self.maximum_cardinality is not None:
            constraints.append(Cardinality(maximum=self.maximum_cardinality))
        return StructuredPortfolioProblem(
            assets=[Asset(vertex) for vertex in self.vertices],
            objectives=[
                ExpectedReturn([self.weights[vertex] for vertex in self.vertices], weight=1.0)
            ],
            constraints=constraints,
            objective_sense="maximize",
            name=self.name,
            metadata={"application": "conflict_graph"},
        )

    def interpret(self, result) -> tuple[str, ...]:
        """Return source vertex IDs selected by holdings without repairing infeasibility."""
        holdings = getattr(result, "holdings", result)
        try:
            vector = tuple(holdings)
        except TypeError as exc:
            raise InterpretationError(
                "Result must be holdings or expose a holdings attribute"
            ) from exc
        if len(vector) != len(self.vertices) or any(value not in (0, 1) for value in vector):
            raise InterpretationError(f"Expected {len(self.vertices)} binary holdings")
        return tuple(vertex for vertex, selected in zip(self.vertices, vector) if selected)
