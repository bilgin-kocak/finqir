# FinQIR

**Financial Quantum Intermediate Representation**

FinQIR is an independent, Apache-2.0-licensed Python toolkit for structured
quantum-finance modeling, compilation, and optimization on Qiskit. It is built
for finance engineers who need recognizable financial concepts and quantum
engineers who need inspectable mappings, constraints, circuits, and results.

> [!IMPORTANT]
> FinQIR is an independent community project. It is not an IBM product and is
> not affiliated with or endorsed by IBM or the Qiskit project.

FinQIR begins with useful portfolio, pricing, probability-distribution, and
market-data components derived from the Apache-licensed Qiskit Finance project.
Its roadmap adds structured portfolio problems, traceable financial mappings,
finance-aware compilation passes, constraint-preserving QAOA, and reproducible
benchmarks.

## Installation

After the first PyPI release, install FinQIR with:

```bash
pip install finqir
```

Until then, install the development version from source:

```bash
git clone https://github.com/bilgin-kocak/finqir.git
cd finqir
python -m pip install -e ".[test,dev]"
```

FinQIR 0.1 targets Python 3.10 or newer and Qiskit 2.5.2.

## Example

```python
import numpy as np

from finqir.applications.optimization import PortfolioOptimization

problem = PortfolioOptimization(
    expected_returns=np.array([0.10, 0.08, 0.12]),
    covariances=np.array(
        [
            [0.10, 0.02, 0.03],
            [0.02, 0.08, 0.01],
            [0.03, 0.01, 0.09],
        ]
    ),
    risk_factor=0.5,
    budget=2,
)

quadratic_program = problem.to_quadratic_program()
print(quadratic_program.prettyprint())
```

## Planned structured API

The design and implementation roadmap cover:

- `StructuredPortfolioProblem` with named financial constraints;
- binary, integer, unary, domain-wall, and fixed-cardinality mappings;
- finance-aware problem and circuit compilation passes;
- constraint-preserving QAOA mixers;
- conflict-graph portfolios and constrained MIS problems;
- multi-period rebalancing, risk, pricing, and benchmarking extensions.

These APIs are roadmap items and are not part of the initial package foundation.
See the [approved design](docs/superpowers/specs/2026-09-04-structured-quantum-finance-design.md)
and [implementation plan](docs/superpowers/plans/2026-09-04-structured-quantum-finance.md).

## Development

```bash
python -m pip install -e ".[test,dev]"
python -m unittest discover -s test -v
python -m build
python -m twine check dist/*
```

## Project history and license

FinQIR is an independent derivative of
[Qiskit Finance](https://github.com/qiskit-community/qiskit-finance). Existing
copyright notices are retained in derived files. New FinQIR work is released
under the same [Apache License 2.0](LICENSE.txt).

FinQIR is research software. It does not provide investment advice and must not
be treated as a guarantee of financial performance or quantum advantage.
