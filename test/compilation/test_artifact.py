# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Tests for compiled finance artifacts."""

# pylint: disable=missing-function-docstring

import unittest

from qiskit import QuantumCircuit
from qiskit_addon_opt_mapper import OptimizationProblem

from finqir.compilation import CircuitMetrics, CompiledFinanceProblem
from finqir.mappings import MappingTrace, VariableMap
from finqir.problems import Asset, ExpectedReturn, StructuredPortfolioProblem


class TestArtifact(unittest.TestCase):
    """Compiled artifacts retain source and backend models."""

    def test_compiled_problem_keeps_both_models(self):
        problem = StructuredPortfolioProblem([Asset("a")], [ExpectedReturn([1])])
        model = OptimizationProblem("backend")
        model.binary_var("x_0")
        variable_map = VariableMap(("a",), ("x_0",), {"a": "x_0"})
        compiled = CompiledFinanceProblem(
            source=problem,
            optimization_problem=model,
            variable_map=variable_map,
            constraint_map={},
            constraint_modes={},
            trace=MappingTrace(()),
        )
        self.assertIs(compiled.source, problem)
        self.assertIs(compiled.optimization_problem, model)

    def test_circuit_metrics_count_two_qubit_instructions(self):
        circuit = QuantumCircuit(3)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cz(1, 2)
        metrics = CircuitMetrics.from_circuit(circuit)
        self.assertEqual(metrics.two_qubit_gate_count, 2)
        self.assertEqual(metrics.operation_counts, {"cx": 1, "cz": 1, "h": 1})


if __name__ == "__main__":
    unittest.main()
