# FinQIR

**Financial Quantum Intermediate Representation**

FinQIR is an independent, Apache-2.0-licensed Python toolkit for structured
quantum-finance modeling, compilation, and optimization on Qiskit. It is built
for finance engineers who need recognizable financial concepts and quantum
engineers who need inspectable mappings, constraints, circuits, and results.

> [!IMPORTANT]
> FinQIR is an independent community project. It is not an IBM product and is
> not affiliated with or endorsed by IBM or the Qiskit project.

FinQIR combines structured portfolio problems, traceable financial mappings,
conflict-graph applications, exact classical baselines, and selected pricing,
probability-distribution, and market-data components derived from the
Apache-licensed Qiskit Finance project.

## Installation

Install FinQIR from PyPI with:

```bash
pip install finqir
```

Optional integrations are installed explicitly:

```bash
pip install "finqir[algorithms]"  # amplitude-estimation workflows
pip install "finqir[data]"        # market-data providers
pip install "finqir[legacy]"      # qiskit-optimization compatibility apps
```

Install the development version from source with:

```bash
git clone https://github.com/bilgin-kocak/finqir.git
cd finqir
python -m pip install -e ".[test,dev]"
```

FinQIR 0.2 targets Python 3.10 or newer and Qiskit 2.5.2 or newer within the
Qiskit 2.x series.

## Example

```python
from finqir import Asset, Cardinality, ExpectedReturn, StructuredPortfolioProblem, VarianceRisk
from finqir.mappings import FinanceMappingPipeline

problem = StructuredPortfolioProblem(
    assets=[Asset("bond"), Asset("equity"), Asset("gold")],
    objectives=[
        ExpectedReturn([0.04, 0.10, 0.06], weight=-1.0),
        VarianceRisk(
            [[0.01, 0.00, 0.00], [0.00, 0.09, 0.01], [0.00, 0.01, 0.04]],
            weight=0.5,
        ),
    ],
    constraints=[Cardinality(exactly=2)],
)

compiled = FinanceMappingPipeline().compile(problem)
print(problem.evaluate((1, 0, 1)))
print(compiled.optimization_problem)
```

## Included in 0.2

The first structured release includes:

- `StructuredPortfolioProblem` with named financial constraints;
- binary holdings mapped to IBM's supported Optimization Mapper;
- penalty and feasible-subspace constraint policies with reversible traces;
- conflict-graph portfolios and constrained MIS inputs;
- exact SciPy MILP baselines and a strict TRUBA adapter.

Integer, unary, domain-wall, and fully synthesized fixed-cardinality mappings,
compiler optimization passes, constraint-preserving QAOA mixers, and
multi-period rebalancing remain planned. See the
[approved design](docs/superpowers/specs/2026-09-04-structured-quantum-finance-design.md)
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
