# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Stable artifacts produced by finance-aware compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

from qiskit import QuantumCircuit
from qiskit_addon_opt_mapper import OptimizationProblem

from finqir.mappings.base import ConstraintHandling, MappingOutput, VariableMap
from finqir.mappings.trace import MappingTrace
from finqir.problems import StructuredPortfolioProblem

if TYPE_CHECKING:
    from finqir.qaoa import FinanceQAOASpec
    from finqir.transpiler import QubitLayout


@dataclass(frozen=True)
class AuditEvent:
    """One human-readable compiler event and its measured facts."""

    stage: str
    message: str
    metrics: Mapping[str, int | float | str | bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))


@dataclass(frozen=True)
class CircuitMetrics:
    """Small reproducible circuit-quality summary."""

    depth: int
    two_qubit_gate_count: int
    operation_counts: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "operation_counts", MappingProxyType(dict(sorted(self.operation_counts.items())))
        )

    @classmethod
    def from_circuit(cls, circuit: QuantumCircuit) -> "CircuitMetrics":
        """Measure depth, two-qubit instructions, and operation counts."""
        return cls(
            depth=circuit.depth(),
            two_qubit_gate_count=sum(
                instruction.operation.num_qubits == 2 for instruction in circuit.data
            ),
            operation_counts=dict(circuit.count_ops()),
        )


@dataclass(frozen=True)
class CompiledFinanceProblem:
    """Source financial model paired with a mapped backend model."""

    source: StructuredPortfolioProblem
    optimization_problem: OptimizationProblem
    variable_map: VariableMap
    constraint_map: Mapping[str, tuple[str, ...]]
    constraint_modes: Mapping[str, ConstraintHandling]
    trace: MappingTrace
    analyses: Mapping[str, object] = field(default_factory=dict)
    audit: tuple[AuditEvent, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "constraint_map",
            MappingProxyType({name: tuple(values) for name, values in self.constraint_map.items()}),
        )
        object.__setattr__(
            self,
            "constraint_modes",
            MappingProxyType(
                {name: ConstraintHandling(value) for name, value in self.constraint_modes.items()}
            ),
        )
        object.__setattr__(self, "analyses", MappingProxyType(dict(self.analyses)))
        object.__setattr__(self, "audit", tuple(self.audit))

    @classmethod
    def from_mapping_output(
        cls, source: StructuredPortfolioProblem, output: MappingOutput
    ) -> "CompiledFinanceProblem":
        """Create the stable compiled form from the last pipeline output."""
        return cls(
            source=source,
            optimization_problem=output.optimization_problem,
            variable_map=output.variable_map,
            constraint_map=output.constraint_map,
            constraint_modes=output.constraint_modes,
            trace=output.trace,
        )


@dataclass(frozen=True)
class FinanceCompilationArtifact:
    """Optional QAOA, circuit, layout, and metrics built from a compiled model."""

    compiled_problem: CompiledFinanceProblem
    qaoa_spec: "FinanceQAOASpec | None" = None
    circuit: QuantumCircuit | None = None
    layout: "QubitLayout | None" = None
    metrics: CircuitMetrics | None = None
