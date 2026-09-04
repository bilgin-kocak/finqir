# Structured Quantum Finance Design

**Status:** Approved

**Date:** 2026-09-04

**Target:** A modern, upstream-first evolution of `qiskit-finance` for Qiskit 2.5+

## 1. Summary

This design evolves `qiskit-finance` from a collection of finance applications,
circuits, and data providers into a structured finance modeling and compilation
toolbox. Financial meaning is preserved until late in the workflow instead of
being discarded when a problem is converted immediately to a generic QUBO or
qubit circuit.

The design serves two primary audiences:

- finance engineers, who work with assets, returns, risk models, transaction
  costs, holdings, and named financial constraints;
- quantum-computing engineers, who inspect and customize encodings, mappings,
  compiler passes, mixers, circuit synthesis, and backend placement.

Both audiences use the same immutable problem model and receive a traceable
result describing how the original financial problem became an executable
quantum circuit.

The first end-to-end application is `ConflictGraphPortfolio`. It models assets,
projects, loans, or trades that cannot be selected together. It also provides a
direct, independently testable bridge to the four constrained Maximum
Independent Set problems in the TRUBA quantum-algorithm competition.

## 2. Goals

1. Preserve financial semantics through modeling, mapping, compilation, and
   result interpretation.
2. Make mappings, constraint strategies, compiler passes, and QAOA mixers
   independently replaceable.
3. Provide a high-level API for finance engineers and an inspectable compiler
   API for quantum engineers.
4. Build on `qiskit-addon-opt-mapper` rather than duplicating generic
   optimization modeling and conversion.
5. Target the maintained Qiskit 2.x API and test upcoming Qiskit releases.
6. Make transformations auditable, reversible where required, and measurable.
7. Demonstrate measurable circuit improvements without changing problem
   semantics.

## 3. Non-goals

The first implementation will not:

- preserve compatibility with every `qiskit-finance` 0.4.1 API;
- provide a new generic optimization modeling language;
- implement general-purpose quantum optimizers already owned by other Qiskit
  packages;
- claim quantum advantage or superior investment performance;
- provide live trading, brokerage integration, or investment advice;
- initially support multi-period optimization, tax lots, derivative pricing,
  credit risk, VaR, or CVaR;
- use a Rust core before the Python interfaces and profiling evidence justify
  one.

Existing APIs may remain temporarily while the new modules are developed, but
they are not architectural dependencies of the new design.

## 4. Version and dependency policy

The first release targets:

- Python 3.10 or newer;
- Qiskit `>=2.5.2,<3`;
- `qiskit-addon-opt-mapper>=0.1.0`;
- NumPy and SciPy versions compatible with the supported Python versions;
- `qiskit-algorithms>=0.4.0` as an optional dependency for reference workflows.

Core modeling and mapping must not require a simulator, cloud account, or
Qiskit Runtime. Execution integrations are optional extras. Continuous
integration tests the minimum supported versions, the newest stable versions,
and an allowed-to-fail prerelease or development Qiskit job.

## 5. Architecture

The workflow has six layers:

```text
Financial inputs
    -> StructuredPortfolioProblem
    -> FinanceMappingPipeline
    -> CompiledFinanceProblem
    -> FinancePassManager
    -> FinanceQAOASpec / synthesized circuit
    -> FinanceExecutionResult
```

### 5.1 Domain model

`StructuredPortfolioProblem` is the immutable source of truth. It owns financial
meaning but does not own a circuit or a particular binary encoding.

It contains:

- an ordered asset universe;
- holding-variable definitions;
- one or more named objective components;
- named constraints;
- optional market and risk-model metadata;
- an objective sense;
- stable identifiers used throughout mapping and interpretation.

The initial implementation supports binary holding variables. Interfaces are
designed so integer holdings can be introduced later without changing the
meaning of existing models.

`Cardinality` and `CapitalBudget` are distinct constraints. `Cardinality`
limits the number of selected positions. `CapitalBudget` constrains a weighted
sum of holding quantities or notionals. The API never uses the word "budget"
as shorthand for the number of selected assets.

All objective components contribute to one declared objective sense. Each
component exposes both its raw financial value and its signed, weighted
contribution. For example, a mean-variance problem expressed as minimization
uses a negative expected-return contribution and a positive variance
contribution.

The minimum public construction style is:

```python
problem = StructuredPortfolioProblem(
    assets=assets,
    objective_sense="minimize",
    objectives=[
        ExpectedReturn(mu, weight=-1.0),
        VarianceRisk(covariance, weight=0.5),
    ],
    constraints=[Cardinality(exactly=5), MandatoryHoldings(["asset-a"])],
)
```

Domain objects validate dimensions, identifier uniqueness, finite numeric
values, symmetric covariance matrices, and immediately detectable constraint
contradictions. Objects expose read-only arrays or defensive copies so a model
cannot silently change after compilation.

### 5.2 Mapping layer

`FinanceMappingPipeline` converts a structured financial problem into a
`CompiledFinanceProblem`. Each mapping is a small component implementing a
common protocol:

```python
class FinancialMapping(Protocol):
    def apply(
        self,
        problem: StructuredPortfolioProblem,
        context: MappingContext,
    ) -> MappingOutput: ...
```

`MappingOutput` contains the updated representation plus one or more reversible
interpretation records. The initial mappings are:

- `BinaryHoldingsMapping`;
- `FixedCardinalityMapping`;
- `PenaltyConstraintMapping`;
- `FeasibleSubspaceMapping`.

The mapping pipeline produces a
`qiskit_addon_opt_mapper.OptimizationProblem`. The generic optimization object
is embedded in `CompiledFinanceProblem` together with retained finance metadata,
constraint classifications, and `MappingTrace`; it does not replace the domain
model.

### 5.3 Compilation layer

`FinancePassManager` accepts `CompiledFinanceProblem` and applies ordered
analysis or transformation passes. It follows Qiskit's pass-manager vocabulary
without requiring every finance pass to operate on a `DAGCircuit`.

Each pass declares:

- required analyses;
- preserved analyses;
- whether it changes the optimization model, QAOA specification, or layout;
- an audit message and quantitative before/after metrics.

The first pass set is:

1. `ValidateFinanceProblem`
2. `PropagateFixedHoldings`
3. `EliminateFixedVariables`
4. `CalibratePenalties`
5. `AnalyzeInteractionGraph`
6. `ScheduleCommutingInteractions`
7. `SelectQubitLayout`

`PropagateFixedHoldings` derives variables fixed by mandatory, excluded, and
conflict constraints. `EliminateFixedVariables` simplifies objective and
constraint expressions while recording enough information to reconstruct a
full holding vector. It must never change the number of output variables
reported to the user.

`ScheduleCommutingInteractions` groups diagonal two-variable cost terms into
disjoint matchings. Terms in a matching can execute in parallel. Reordering is
allowed only after a commutation analysis proves that the transformation
preserves the cost unitary.

`SelectQubitLayout` is optional when the target is all-to-all connected. On
restricted hardware it uses interaction weights and constraint-component
membership when selecting a layout.

### 5.4 QAOA specification and synthesis

`FinanceQAOASpec` describes a QAOA-family computation before it is lowered to a
`QuantumCircuit`. It contains:

- the cost representation;
- parameterized layer structure;
- initial-state strategy;
- mixer strategy;
- constraint invariants;
- scheduled interaction groups;
- parameter conventions;
- requested layer count.

The initial mixer implementations are:

- `TransverseFieldMixer` for unconstrained binary problems;
- `FixedCardinalityMixer` for exact-cardinality portfolios;
- `FixedHoldingMixer` for mandatory and excluded holdings;
- `ConflictGraphMixer` for mutually exclusive selections;
- `ComponentGroverMixer` for small feasible-subspace components.

Mixer construction must expose a method that checks whether the initial state
is feasible and whether the mixer preserves its declared constraints. A mixer
selection policy may recommend a mixer, but an explicit user choice always
wins if it is compatible with the problem.

Circuit synthesis occurs only after the financial model, mapping decisions,
constraint invariants, and interaction schedule are known. The synthesized
circuit then enters the normal Qiskit transpilation workflow.

### 5.5 Execution and results

The core package compiles problems but does not require a particular execution
service. A small reference workflow accepts a Qiskit sampler-compatible object
and an optimizer supplied by the caller.

The high-level facade is intentionally small:

```python
from qiskit_finance.workflows import solve

result = solve(
    problem,
    sampler=sampler,
    optimizer=optimizer,
    target=target,
)
```

Keeping execution in `workflows` prevents the immutable domain model from
depending on simulators, optimizers, or backend services.

The expert workflow is explicit:

```python
artifact = compiler.compile(problem, target=target)
circuit = artifact.circuit
result = interpreter.interpret(samples, artifact)
```

`FinanceExecutionResult` contains:

- the full holding vector and selected asset identifiers;
- total objective value and per-component financial breakdown;
- feasibility and per-constraint diagnostics;
- approximation metrics when a reference value exists;
- circuit depth, two-qubit gate count, and operation counts;
- shot count, seed, optimizer budget, and runtime metadata;
- the complete mapping and compilation trace.

The result never repairs an infeasible measured bitstring silently. Optional
repair utilities, if added later, must return a distinct result marked as
repaired and preserve the original sample.

## 6. Package layout

The proposed modules are:

```text
qiskit_finance/
    problems/
        structured_portfolio_problem.py
        assets.py
        variables.py
        objectives/
        constraints/
    mappings/
        base.py
        binary_holdings.py
        fixed_cardinality.py
        penalty_constraints.py
        feasible_subspace.py
        trace.py
    compilation/
        artifact.py
        pass_manager.py
        passes/
    qaoa/
        specification.py
        synthesis.py
        mixers/
    applications/
        optimization/
            conflict_graph_portfolio.py
    workflows/
        sampling_qaoa.py
    results/
        finance_execution_result.py
    benchmarks/
        metrics.py
        baselines.py
```

Only stable, intentionally supported classes are re-exported from package
`__init__.py` files. Compiler internals remain importable from their defining
modules but are not promoted prematurely.

New modules are additive through the 0.1-0.6 development sequence. Existing
0.4.1 modules may remain present, but the new implementation does not depend on
them and does not promise behavioral compatibility. Removing or redirecting an
existing public API requires a separate deprecation and major-version proposal.

## 7. `ConflictGraphPortfolio`

`ConflictGraphPortfolio` is the first reference application. A vertex
represents a selectable asset, project, loan, or trade. A graph edge means the
two vertices cannot be selected together. Vertex weights represent value; an
unweighted graph uses weight one.

Supported constraints are:

- mandatory vertices;
- excluded vertices;
- additional mutually exclusive pairs;
- optional exact or maximum cardinality.

The application provides:

```python
application.to_structured_problem()
application.interpret(result)
```

The graph is validated as undirected, loop-free, and consistent with all
mandatory selections. Direct contradictions raise `InfeasiblePortfolioError`
before mapping.

### 7.1 TRUBA adapter

An example-only adapter reads the competition JSON fields:

- `cizge` -> conflict graph;
- `zorunlu_dugumler` -> mandatory holdings;
- `yasak_ikililer` -> additional conflicts.

The adapter is kept outside the stable public API unless a more general external
schema is later justified.

The benchmark reproduces all four problem variants:

1. penalty-based conflict selection;
2. mandatory selections represented as named constraints;
3. additional pair conflicts;
4. constraint-preserving component Grover mixers.

The first compiler performance target is to preserve the cost unitary while
reducing depth through commuting-interaction scheduling. The supplied
competition instances provide regression targets, not universal performance
claims.

## 8. Errors and diagnostics

The new modules use a small exception hierarchy rooted at
`QiskitFinanceError`:

- `InvalidFinanceProblemError` for malformed dimensions, identifiers, or
  numeric inputs;
- `InfeasiblePortfolioError` for contradictions proven during validation or
  propagation;
- `UnsupportedMappingError` when a selected encoding cannot represent the
  problem;
- `ConstraintPreservationError` when an initial state or mixer violates its
  declared invariant;
- `CompilationError` when a pass cannot satisfy its preconditions;
- `InterpretationError` when samples cannot be mapped back reliably.

Warnings are used for non-fatal conditions such as weak penalty separation,
poor numerical scaling, dense interaction graphs, or a compiler recommendation
being overridden. Diagnostics include actionable context but do not expose
credentials or backend secrets.

## 9. Testing strategy

### 9.1 Unit tests

- dimensional and semantic validation of domain objects;
- every constraint's evaluation behavior;
- mapping trace inversion;
- fixed-variable propagation and objective simplification;
- penalty bounds and scale diagnostics;
- pass dependency and preservation declarations;
- deterministic interaction scheduling;
- result interpretation and bit ordering.

### 9.2 Property tests

For small random instances:

- original and mapped objectives agree for every assignment;
- eliminating fixed variables preserves every feasible objective value;
- mapping followed by interpretation reconstructs the original holding vector;
- reordered commuting cost blocks have equal operators up to global phase;
- constraint-preserving mixers have zero transition amplitude from feasible to
  infeasible basis states.

### 9.3 Integration tests

- compile a conflict portfolio from the domain API to a Qiskit circuit;
- execute small problems with a local sampler;
- compare results with a classical reference solver;
- verify exact-cardinality and conflict constraints in sampled results;
- verify circuit metrics are computed from the final transpiled circuit.

### 9.4 Regression benchmarks

- the eight supplied TRUBA instances;
- sparse, dense, disconnected, and contradictory conflict graphs;
- deterministic comparisons of unscheduled and scheduled cost layers;
- tests across minimum and latest supported dependency versions.

Stochastic tests assert distributions, feasibility rates, or deterministic
seeded results with tolerances. They do not require a particular optimum to be
sampled unless the circuit prepares that outcome deterministically.

## 10. Documentation

The documentation begins with two parallel entry points:

- **Finance engineer:** model and solve a constrained portfolio without writing
  a Hamiltonian or circuit;
- **Quantum engineer:** inspect mappings, replace the mixer, add a compiler
  pass, and compare synthesized circuits.

The first tutorials are:

1. Build a structured mean-variance portfolio.
2. Build and solve a conflict-graph portfolio.
3. Compare penalty and feasible-subspace constraint handling.
4. Reduce cost-layer depth using commuting-interaction scheduling.
5. Implement and register a custom mapping or compiler pass.

Documentation examples use synthetic data by default so they are reproducible
and do not depend on network data providers.

## 11. Delivery sequence

The implementation is divided into independently reviewable releases:

### 0.1: Structured modeling

Domain types, objectives, named constraints, `StructuredPortfolioProblem`,
validation, serialization, and documentation.

### 0.2: Mappings

Mapping protocol, `CompiledFinanceProblem`, `MappingTrace`, binary holdings,
fixed cardinality, penalty mapping, and Optimization Mapper integration.

### 0.3: Conflict graph vertical slice

`ConflictGraphPortfolio`, classical validation, TRUBA adapter, result
interpretation, and initial benchmarks.

### 0.4: Finance compiler

Pass manager, fixed-holding propagation, fixed-variable elimination, penalty
calibration, interaction-graph analysis, commuting scheduling, and audit data.

### 0.5: Constraint-preserving QAOA

QAOA specification, initial-state strategies, initial mixer library, late
circuit synthesis, and sampler-based reference workflow.

### 0.6: Benchmarking and stabilization

Standard metrics, benchmark runner, dependency-version CI, performance
regressions, API review, and complete dual-audience tutorials.

Integer encodings, covariance/factor optimizations, multi-period portfolios,
and risk/pricing modernization begin only after 0.6 stabilizes the foundational
interfaces.

## 12. Acceptance criteria for the first stable vertical slice

The first stable vertical slice is complete when:

1. A finance engineer can define and validate a conflict-graph portfolio using
   finance terminology only.
2. A quantum engineer can inspect or replace every mapping, pass, initial state,
   and mixer used by that problem.
3. Every transformation is present in a machine-readable and human-readable
   trace.
4. Small mapped instances are exhaustively proven equivalent to their source
   models in tests.
5. Constraint-preserving mixers are verified not to leave their declared
   feasible subspaces.
6. The same compiler reproduces the four TRUBA variants through configuration,
   not four copied solver implementations.
7. Commuting-interaction scheduling reduces depth on the supplied benchmark
   instances without worsening approximation behavior in statistically
   controlled comparisons.
8. Documentation contains working finance-engineer and quantum-engineer paths.
9. The package passes CI on the minimum and latest supported Python and Qiskit
   versions.

## 13. Future extensions

After the foundational APIs stabilize, later designs may add:

- integer, unary, and domain-wall encodings;
- low-rank factor-model and covariance-clustering passes;
- multi-period rebalancing, turnover, transaction-cost, and tax-lot models;
- minimum holding periods and time-coupled constraints;
- scenario-based and distributionally robust optimization;
- VaR, CVaR, credit-risk, and loss-distribution workflows;
- modular payoff and uncertainty encoders for amplitude estimation;
- optional accelerated implementations where profiling demonstrates a need.

Each extension must use the same structured model, traceable mapping, and
auditable result principles rather than bypassing them with a one-off circuit.
