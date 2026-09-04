# Structured Quantum Finance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the 0.1-0.6 structured quantum-finance vertical slice: immutable portfolio modeling, pluggable Optimization Mapper lowering, finance-aware compilation, conflict-graph portfolios, constraint-preserving QAOA, auditable results, and reproducible TRUBA benchmarks.

**Architecture:** Keep `StructuredPortfolioProblem` as the immutable source of financial truth. Lower it through a traceable `FinanceMappingPipeline` into `qiskit_addon_opt_mapper.OptimizationProblem`, refine it with a finance pass manager, and synthesize a QAOA circuit only after constraint and scheduling decisions are known. Keep execution behind a sampler-compatible workflow and reconstruct finance-domain results through the mapping trace.

**Tech Stack:** Python 3.10+, NumPy, SciPy, Qiskit 2.5.2+, qiskit-addon-opt-mapper 0.1.0+, optional qiskit-algorithms 0.4.0+, unittest, ddt, Hypothesis, stestr, Sphinx.

**Spec:** `docs/superpowers/specs/2026-09-04-structured-quantum-finance-design.md`

## Global Constraints

- Support Python `>=3.10`.
- Support Qiskit `>=2.5.2,<3`.
- Require `qiskit-addon-opt-mapper>=0.1.0` for the new mapping layer.
- Treat `qiskit-algorithms>=0.4.0` as the algorithms extra; the new modeling, mapping, compilation, QAOA synthesis, and result modules must import without it.
- Keep the new implementation additive. Do not remove or redirect existing 0.4.1 public APIs in this work.
- Preserve original asset order, identifiers, objective components, and named constraints through every transformation.
- Never silently repair an infeasible sample. Report the original sample and its constraint diagnostics.
- Use deterministic ordering for assets, constraint names, trace records, graph edges, interaction groups, samples, and serialized data.
- Use public Qiskit 2.x APIs only; do not import private Qiskit or Optimization Mapper names beginning with `_`.
- Every Python source and test file must carry the repository Apache 2.0 copyright header with the current year.
- Each task follows red-green-refactor: write the focused failing test, observe the expected failure, implement the smallest coherent behavior, run focused tests, run affected suites, then commit.

## Execution Boundaries

Stop for maintainer review at each independently testable release gate:

1. 0.1 structured modeling: Tasks 1-5.
2. 0.2 mappings: Tasks 6-8.
3. 0.3 conflict-graph vertical slice: Tasks 9-10.
4. 0.4 finance compiler: Tasks 11-16.
5. 0.5 constraint-preserving QAOA: Tasks 17-20.
6. 0.6 benchmarking and stabilization: Tasks 21-22.

The TRUBA input JSON files remain external because their redistribution terms are not part of this repository. Tests use small schema-equivalent fixtures. The release benchmark command points to the eight inputs already available in `/Users/bilginkocak/hackathon/q-prehackathon/truba/ssb_exam/final`.

## Public Interface Map

These names are the cross-task contract. A signature changes only when this plan and every consuming task are updated together.

```python
Asset(asset_id: str, label: str | None = None, metadata: Mapping[str, JSONValue] | None = None)
HoldingVariable(asset_id: str, *, domain: Literal["binary"] = "binary",
                lower_bound: int = 0, upper_bound: int = 1,
                lot_size: float = 1.0)

ExpectedReturn(values: Sequence[float], *, weight: float = 1.0, name: str = "expected_return")
VarianceRisk(covariance: Sequence[Sequence[float]], *, weight: float = 1.0, name: str = "variance")
TransactionCost(current_holdings: Sequence[int], buy_costs: Sequence[float],
                sell_costs: Sequence[float] | None = None, *,
                weight: float = 1.0, name: str = "transaction_cost")

Cardinality(*, exactly: int | None = None, minimum: int | None = None,
            maximum: int | None = None, name: str = "cardinality")
CapitalBudget(notionals: Sequence[float], *, minimum: float | None = None,
              maximum: float | None = None, name: str = "capital_budget")
MandatoryHoldings(asset_ids: Iterable[str], *, name: str = "mandatory_holdings")
ExcludedHoldings(asset_ids: Iterable[str], *, name: str = "excluded_holdings")
MutualExclusions(pairs: Iterable[tuple[str, str]], *, name: str = "mutual_exclusions")
ExposureBounds(exposures: Mapping[str, float], *, minimum: float | None = None,
               maximum: float | None = None, name: str)

StructuredPortfolioProblem(
    assets: Sequence[Asset], objectives: Sequence[FinanceObjective],
    constraints: Sequence[FinanceConstraint] = (), *,
    holding_variables: Sequence[HoldingVariable] | None = None,
    objective_sense: Literal["minimize", "maximize"] = "minimize",
    name: str = "structured_portfolio",
    metadata: Mapping[str, JSONValue] | None = None,
)
problem.evaluate(holdings: Sequence[int]) -> PortfolioEvaluation
problem.check_feasibility(holdings: Sequence[int]) -> FeasibilityReport
problem.to_dict() -> dict[str, JSONValue]
StructuredPortfolioProblem.from_dict(payload: Mapping[str, JSONValue]) -> StructuredPortfolioProblem

MappingContext(constraint_policy: ConstraintPolicy, penalty: float | None = None,
               current: MappingOutput | None = None)
FinancialMapping.apply(problem: StructuredPortfolioProblem, context: MappingContext) -> MappingOutput
FinanceMappingPipeline.compile(problem, *, context: MappingContext | None = None) -> CompiledFinanceProblem
MappingTrace.interpret(values: Sequence[int]) -> tuple[int, ...]

FinancePassManager(passes: Sequence[FinancePass]).run(
    problem: CompiledFinanceProblem, *, target: Target | None = None
) -> CompiledFinanceProblem

FinanceCompiler.compile(
    problem: StructuredPortfolioProblem, *,
    constraint_policy: ConstraintPolicy | None = None,
    mixer: FinanceMixer | None = None,
    initial_state: InitialStateStrategy | None = None,
    reps: int = 1,
    target: Target | None = None,
) -> FinanceCompilationArtifact

solve(
    problem: StructuredPortfolioProblem, *, sampler: BaseSamplerV2,
    optimizer: Minimizer, target: Target | None = None, reps: int = 1,
    shots: int = 4096, seed: int | None = None,
    compiler: FinanceCompiler | None = None,
) -> FinanceExecutionResult
```

## File Responsibility Map

```text
qiskit_finance/problems/assets.py                  asset identity and JSON metadata
qiskit_finance/problems/variables.py               holding domains, bounds, and lot size
qiskit_finance/_typing.py                          shared JSON type aliases
qiskit_finance/problems/objectives.py              objective components and coefficients
qiskit_finance/problems/constraints.py             named constraints and evaluation
qiskit_finance/problems/evaluation.py              objective/feasibility value objects
qiskit_finance/problems/structured_portfolio_problem.py aggregate and serialization
qiskit_finance/mappings/base.py                     mapping protocols, policies, and context
qiskit_finance/mappings/trace.py                    reversible codecs and audit records
qiskit_finance/mappings/binary_holdings.py          binary OptimizationProblem construction
qiskit_finance/mappings/constraint_handling.py      strategy classification
qiskit_finance/mappings/pipeline.py                 ordered mapping orchestration
qiskit_finance/compilation/artifact.py              compiled and final artifacts
qiskit_finance/compilation/base.py                  pass protocol and context
qiskit_finance/compilation/pass_manager.py          dependency-aware pass execution
qiskit_finance/compilation/passes/validation.py     structural validation
qiskit_finance/compilation/passes/fixed_holdings.py fixed inference and elimination
qiskit_finance/compilation/passes/penalties.py      calibration and QUBO materialization
qiskit_finance/compilation/passes/interactions.py   graph and commuting schedule
qiskit_finance/compilation/passes/layout.py         target-aware placement
qiskit_finance/qaoa/specification.py                pre-circuit QAOA value objects
qiskit_finance/qaoa/initial_states.py               basis and feasible state preparation
qiskit_finance/qaoa/mixers/base.py                  mixer protocol and verification
qiskit_finance/qaoa/mixers/standard.py              transverse, fixed, cardinality mixers
qiskit_finance/qaoa/mixers/conflict_graph.py        conflict and Grover mixers
qiskit_finance/qaoa/synthesis.py                    late circuit generation
qiskit_finance/compiler.py                          end-to-end compile facade
qiskit_finance/results/finance_execution_result.py  finance samples and results
qiskit_finance/results/interpreter.py               decoding and result selection
qiskit_finance/workflows/sampling_qaoa.py            sampler/optimizer workflow
qiskit_finance/applications/optimization/conflict_graph_portfolio.py application
qiskit_finance/benchmarks/metrics.py                 circuit and finance metrics
qiskit_finance/benchmarks/baselines.py               exact SciPy baseline
qiskit_finance/benchmarks/truba.py                   external TRUBA adapter and runner
```

---

## Release 0.1: Structured Modeling

### Task 1: Establish the supported runtime and dependency boundary

**Files:**

- Modify: `setup.py`
- Modify: `requirements.txt`
- Modify: `requirements-dev.txt`
- Modify: `tox.ini`
- Modify: `.github/workflows/main.yml`
- Modify: `qiskit_finance/data_providers/_base_data_provider.py`
- Modify: `qiskit_finance/applications/__init__.py`
- Modify: `test/circuit/test_european_call_delta_objective.py`
- Modify: `test/circuit/test_european_call_pricing_objective.py`
- Modify: `test/circuit/test_fixed_income_pricing_objective.py`
- Create: `test/test_optional_dependencies.py`

**Interfaces:**

- Consumes: existing setuptools, stestr, and GitHub Actions configuration.
- Produces: Python 3.10+ metadata, Qiskit 2.5.2+ bounds, Optimization Mapper dependency, algorithms extra, and an importable core without `qiskit_algorithms`.

- [ ] **Step 1: Add dependency-boundary tests**

```python
def test_core_imports_without_qiskit_algorithms(self):
    code = """
import builtins
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == 'qiskit_algorithms' or name.startswith('qiskit_algorithms.'):
        raise ImportError('blocked by test')
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
import qiskit_finance
import qiskit_finance.applications.optimization
"""
    completed = subprocess.run([sys.executable, "-c", code], check=False, capture_output=True)
    self.assertEqual(completed.returncode, 0, completed.stderr.decode())
```

Also load `setup.py` through a mocked `setuptools.setup` and assert:

```python
self.assertEqual(setup_kwargs["python_requires"], ">=3.10")
self.assertEqual(setup_kwargs["extras_require"]["algorithms"],
                 ["qiskit-algorithms>=0.4.0"])
self.assertIn("qiskit>=2.5.2,<3", requirements)
self.assertIn("qiskit-addon-opt-mapper>=0.1.0", requirements)
self.assertNotIn("qiskit-algorithms>=0.4.0", requirements)
```

- [ ] **Step 2: Run the focused test and observe the metadata failures**

Run: `python -m unittest test.test_optional_dependencies -v`

Expected: the core import passes; Python/Qiskit/extra assertions fail against the old metadata.

- [ ] **Step 3: Update metadata and isolate the legacy random helper**

Set `python_requires=">=3.10"`, classifiers 3.10-3.14, and `extras_require={"algorithms": ["qiskit-algorithms>=0.4.0"]}`. Set these core requirement lines exactly, retaining the provider dependencies and `qiskit-optimization` needed by existing applications:

```text
qiskit>=2.5.2,<3
qiskit-addon-opt-mapper>=0.1.0
qiskit-optimization>=0.7.0
scipy>=1.10
numpy>=1.23
```

Add `qiskit-algorithms>=0.4.0` to `requirements-dev.txt` so the full legacy test suite still runs. Change `qiskit_finance.applications.__init__` to import optimization applications eagerly and load estimation names through module `__getattr__`; when the extra is absent, raise `MissingOptionalLibraryError` with install command `pip install 'qiskit-finance[algorithms]'`. This keeps the new optimization namespace usable in a core installation without deleting a legacy symbol.

Replace the data-provider-only `algorithm_globals.random` use with:

```python
_RNG = np.random.default_rng()

def _set_default_rng_seed(seed: int | None) -> None:
    global _RNG
    _RNG = np.random.default_rng(seed)
```

Use `_RNG.random(self._n)` in `get_coordinates()`. Existing tests may call the private seed hook, but it is not exported.

Update the three amplitude-estimation tests from removed Sampler V1 construction to:

```python
from qiskit.primitives import StatevectorSampler

sampler = StatevectorSampler(seed=12, default_shots=1024)
```

Keep their existing confidence/tolerance assertions so this is an API migration, not a weakening of behavior.

- [ ] **Step 4: Update local and CI version matrices**

Set tox environments to `py310,py311,py312,py313,py314,lint`. Make CI test 3.10 and the newest stable interpreter on Linux, plus Linux/Windows/macOS on 3.12. Add jobs `minimum-dependencies`, `latest-dependencies`, and `qiskit-prerelease`; install exact lower bounds in the minimum job and mark only the prerelease job `continue-on-error: true`.

- [ ] **Step 5: Verify and commit**

Run:

```bash
python -m unittest test.test_optional_dependencies -v
python -m unittest test.circuit.test_european_call_delta_objective test.circuit.test_european_call_pricing_objective test.circuit.test_fixed_income_pricing_objective -v
python -m pip check
python -c "import qiskit; import qiskit_addon_opt_mapper; print(qiskit.__version__)"
```

Expected: tests pass, `pip check` reports no broken requirements, and Qiskit is in `[2.5.2,3)`.

```bash
git add setup.py requirements.txt requirements-dev.txt tox.ini .github/workflows/main.yml qiskit_finance/data_providers/_base_data_provider.py qiskit_finance/applications/__init__.py test/test_optional_dependencies.py test/circuit/test_european_call_delta_objective.py test/circuit/test_european_call_pricing_objective.py test/circuit/test_fixed_income_pricing_objective.py
git commit -m "build: target Qiskit 2.5 and Optimization Mapper"
```

### Task 2: Add errors, assets, and evaluation value objects

**Files:**

- Modify: `qiskit_finance/exceptions.py`
- Create: `qiskit_finance/_typing.py`
- Create: `qiskit_finance/problems/__init__.py`
- Create: `qiskit_finance/problems/assets.py`
- Create: `qiskit_finance/problems/variables.py`
- Create: `qiskit_finance/problems/evaluation.py`
- Create: `test/problems/__init__.py`
- Create: `test/problems/test_assets.py`
- Create: `test/problems/test_evaluation.py`

**Interfaces:**

- Consumes: `QiskitFinanceError`.
- Produces: recursive `JSONValue`, `Asset`, binary `HoldingVariable`, `ObjectiveComponentValue`, `ConstraintValue`, `PortfolioEvaluation`, `FeasibilityReport`, and the six specified exception subclasses.

- [ ] **Step 1: Write failing immutable-value tests**

```python
def test_asset_rejects_empty_id_and_freezes_metadata(self):
    with self.assertRaises(InvalidFinanceProblemError):
        Asset("")
    source = {"sector": "energy"}
    asset = Asset("asset-a", metadata=source)
    source["sector"] = "changed"
    self.assertEqual(asset.metadata["sector"], "energy")
    with self.assertRaises(TypeError):
        asset.metadata["sector"] = "banking"

def test_holding_variable_preserves_lot_size(self):
    variable = HoldingVariable("asset-a", lot_size=100.0)
    self.assertEqual((variable.domain, variable.lower_bound, variable.upper_bound),
                     ("binary", 0, 1))
    self.assertEqual(variable.lot_size, 100.0)

def test_feasibility_report_indexes_named_constraints(self):
    values = (ConstraintValue("mandatory", True, 0.0, "satisfied"),)
    report = FeasibilityReport(values)
    self.assertTrue(report.is_feasible)
    self.assertTrue(report.by_name("mandatory").satisfied)
```

- [ ] **Step 2: Run the tests to verify the missing module**

Run: `python -m unittest test.problems.test_assets test.problems.test_evaluation -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'qiskit_finance.problems'`.

- [ ] **Step 3: Implement frozen domain values**

Add direct subclasses of `QiskitFinanceError`: `InvalidFinanceProblemError`, `InfeasiblePortfolioError`, `UnsupportedMappingError`, `ConstraintPreservationError`, `CompilationError`, and `InterpretationError`.

Define the shared serialization type in `_typing.py`:

```python
JSONValue: TypeAlias = (
    None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
)
```

```python
@dataclass(frozen=True)
class ObjectiveComponentValue:
    name: str
    raw_value: float
    weight: float
    contribution: float

@dataclass(frozen=True)
class ConstraintValue:
    name: str
    satisfied: bool
    violation: float
    message: str

@dataclass(frozen=True)
class PortfolioEvaluation:
    objective_sense: Literal["minimize", "maximize"]
    total: float
    components: tuple[ObjectiveComponentValue, ...]

@dataclass(frozen=True)
class FeasibilityReport:
    constraints: tuple[ConstraintValue, ...]

    @property
    def is_feasible(self) -> bool:
        return all(item.satisfied for item in self.constraints)
```

Normalize `Asset.metadata` by recursively validating JSON-compatible values, defensively copying nested lists/dicts, and wrapping mappings with `MappingProxyType`. `HoldingVariable` accepts only domain `"binary"`, exact bounds `[0,1]`, and a finite positive lot size; keeping the domain field makes future integer variables additive. `FeasibilityReport.by_name(name)` raises `KeyError(name)` when absent.

- [ ] **Step 4: Verify and commit**

Run: `python -m unittest test.problems.test_assets test.problems.test_evaluation -v`

Expected: PASS.

```bash
git add qiskit_finance/exceptions.py qiskit_finance/_typing.py qiskit_finance/problems test/problems
git commit -m "feat: add immutable finance domain primitives"
```

### Task 3: Implement expected-return, variance, and transaction-cost objectives

**Files:**

- Create: `qiskit_finance/problems/objectives.py`
- Modify: `qiskit_finance/problems/__init__.py`
- Create: `test/problems/test_objectives.py`

**Interfaces:**

- Consumes: `ObjectiveComponentValue`, `InvalidFinanceProblemError`.
- Produces: runtime-checkable `FinanceObjective`, `PolynomialCoefficients`, `ExpectedReturn`, `VarianceRisk`, and binary `TransactionCost`.

- [ ] **Step 1: Write objective tests**

```python
def test_expected_return_exposes_raw_and_weighted_values(self):
    objective = ExpectedReturn([0.1, 0.2], weight=-1.0)
    value = objective.evaluate((1, 0))
    self.assertEqual(value.raw_value, 0.1)
    self.assertEqual(value.contribution, -0.1)
    self.assertEqual(objective.coefficients().linear, (0.1, 0.2))

def test_variance_uses_full_symmetric_quadratic_form(self):
    objective = VarianceRisk([[1.0, 0.25], [0.25, 2.0]], weight=0.5)
    value = objective.evaluate((1, 1))
    self.assertEqual(value.raw_value, 3.5)
    self.assertEqual(value.contribution, 1.75)

def test_transaction_cost_is_a_linear_binary_objective(self):
    objective = TransactionCost(
        current_holdings=[1, 0], buy_costs=[0.4, 0.5], sell_costs=[0.2, 0.3]
    )
    self.assertEqual(objective.evaluate((0, 1)).raw_value, 0.7)
    self.assertEqual(objective.coefficients().constant, 0.2)
    self.assertEqual(objective.coefficients().linear, (-0.2, 0.5))
```

Add rejection cases for NaN, infinity, non-square/asymmetric covariance, empty data, non-binary current holdings, negative transaction costs, mismatched buy/sell lengths, duplicate names, and wrong holding length.

- [ ] **Step 2: Run the tests to verify failure**

Run: `python -m unittest test.problems.test_objectives -v`

Expected: FAIL because `objectives.py` is absent.

- [ ] **Step 3: Implement normalized objective components**

```python
@dataclass(frozen=True)
class PolynomialCoefficients:
    constant: float = 0.0
    linear: tuple[float, ...] = ()
    quadratic: tuple[tuple[float, ...], ...] = ()

@runtime_checkable
class FinanceObjective(Protocol):
    name: str
    weight: float
    dimension: int
    def evaluate(self, holdings: Sequence[int]) -> ObjectiveComponentValue: ...
    def coefficients(self) -> PolynomialCoefficients: ...
    def to_dict(self) -> dict[str, JSONValue]: ...
```

Store values as Python-float tuples. `ExpectedReturn` computes `mu @ x`; `VarianceRisk` computes `x.T @ covariance @ x`. `TransactionCost` computes per-asset buy cost for `0 -> 1` and sell cost for `1 -> 0`; for a current one it emits constant `sell_cost` and linear coefficient `-sell_cost`, while for a current zero it emits linear coefficient `buy_cost`. `coefficients()` returns raw financial coefficients, and the component's `evaluate()` applies its weight once.

- [ ] **Step 4: Verify and commit**

Run:

```bash
python -m unittest test.problems.test_objectives -v
python -m mypy qiskit_finance/problems/objectives.py
```

Expected: PASS with no type errors.

```bash
git add qiskit_finance/problems/objectives.py qiskit_finance/problems/__init__.py test/problems/test_objectives.py
git commit -m "feat: add structured portfolio objectives"
```

### Task 4: Implement named portfolio constraints

**Files:**

- Create: `qiskit_finance/problems/constraints.py`
- Modify: `qiskit_finance/problems/__init__.py`
- Create: `test/problems/test_constraints.py`

**Interfaces:**

- Consumes: `ConstraintValue`, `InvalidFinanceProblemError`.
- Produces: `FinanceConstraint`, `Cardinality`, `CapitalBudget`, `MandatoryHoldings`, `ExcludedHoldings`, `MutualExclusions`, and `ExposureBounds`.

- [ ] **Step 1: Write table-driven tests**

```python
@data(
    (Cardinality(exactly=2), (1, 0, 1), True, 0.0),
    (Cardinality(maximum=1), (1, 0, 1), False, 1.0),
    (CapitalBudget([3.0, 5.0], maximum=6.0), (0, 1), True, 0.0),
    (MandatoryHoldings(["a"]), (0, 1), False, 1.0),
    (ExcludedHoldings(["b"]), (1, 1), False, 1.0),
    (MutualExclusions([("a", "b")]), (1, 1), False, 1.0),
    (ExposureBounds({"a": 0.6, "b": 0.5}, maximum=1.0, name="sector:tech"),
     (1, 1), False, 0.1),
)
@unpack
def test_constraint_evaluation(self, constraint, holdings, satisfied, violation):
    ids = ("a", "b", "c")[:len(holdings)]
    actual = constraint.evaluate(holdings, ids)
    self.assertEqual(actual.satisfied, satisfied)
    self.assertAlmostEqual(actual.violation, violation)
```

Add constructor cases for empty names, ambiguous `Cardinality` modes, incoherent bounds, duplicate/self-pairs, non-finite coefficients, and unknown IDs during `validate(asset_ids)`.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.problems.test_constraints -v`

Expected: FAIL because the constraint types are absent.

- [ ] **Step 3: Implement constraint evaluation**

```python
@runtime_checkable
class FinanceConstraint(Protocol):
    name: str
    def validate(self, asset_ids: Sequence[str]) -> None: ...
    def involved_asset_ids(self, asset_ids: Sequence[str]) -> tuple[str, ...]: ...
    def evaluate(self, holdings: Sequence[int],
                 asset_ids: Sequence[str]) -> ConstraintValue: ...
    def to_dict(self) -> dict[str, JSONValue]: ...
```

For numeric bounds, use `max(0, minimum-value) + max(0, value-maximum)`. Mandatory/excluded violation is the number of incorrect bits; mutual-exclusion violation is the number of selected forbidden pairs. Compare floats with `rel_tol=1e-10, abs_tol=1e-12`. `involved_asset_ids()` returns source-ordered IDs touched by a constraint; cardinality and capital budget touch every asset, while exposure constraints return only nonzero exposure IDs.

- [ ] **Step 4: Verify and commit**

Run: `python -m unittest discover -s test/problems -p 'test_*.py' -v`

Expected: PASS.

```bash
git add qiskit_finance/problems/constraints.py qiskit_finance/problems/__init__.py test/problems/test_constraints.py
git commit -m "feat: add named financial constraints"
```

### Task 5: Assemble and serialize `StructuredPortfolioProblem`

**Files:**

- Create: `qiskit_finance/problems/structured_portfolio_problem.py`
- Modify: `qiskit_finance/problems/__init__.py`
- Modify: `qiskit_finance/__init__.py`
- Create: `test/problems/test_structured_portfolio_problem.py`
- Create: `docs/apidocs/qiskit_finance.problems.rst`
- Modify: `docs/apidocs/qiskit_finance.rst`
- Create: `releasenotes/notes/structured-portfolio-problem-a73f0c214d9b8e65.yaml`

**Interfaces:**

- Consumes: release 0.1 domain types.
- Produces: immutable aggregate, validation, evaluation, deterministic schema-version-1 serialization, and stable exports.

- [ ] **Step 1: Write aggregate and round-trip tests**

```python
def test_mean_variance_breakdown_and_feasibility(self):
    problem = StructuredPortfolioProblem(
        assets=[Asset("a"), Asset("b")], objective_sense="minimize",
        holding_variables=[HoldingVariable("a", lot_size=10.0),
                           HoldingVariable("b", lot_size=5.0)],
        objectives=[ExpectedReturn([0.1, 0.2], weight=-1.0),
                    VarianceRisk([[1.0, 0.0], [0.0, 2.0]], weight=0.5)],
        constraints=[Cardinality(exactly=1)],
    )
    value = problem.evaluate((0, 1))
    self.assertAlmostEqual(value.total, 0.8)
    self.assertEqual([part.name for part in value.components],
                     ["expected_return", "variance"])
    self.assertTrue(problem.check_feasibility((0, 1)).is_feasible)

def test_serialization_is_deterministic_and_round_trips(self):
    encoded = json.dumps(problem.to_dict(), sort_keys=True, separators=(",", ":"))
    decoded = StructuredPortfolioProblem.from_dict(json.loads(encoded))
    self.assertEqual(decoded.to_dict(), problem.to_dict())
```

Add cases for duplicate IDs/names, wrong dimensions, non-binary holdings, mandatory/excluded overlap, mutually exclusive mandatory assets, impossible cardinality, unknown schema versions, and constructor-input mutation.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.problems.test_structured_portfolio_problem -v`

Expected: FAIL because the aggregate is absent.

- [ ] **Step 3: Implement aggregate behavior**

Normalize collections to tuples, create one default `HoldingVariable` per asset when none are supplied, validate exact asset-variable alignment plus every dimension/name/constraint, and prove the direct contradictions listed in Step 1. Aggregate weighted component values with:

```python
def evaluate(self, holdings: Sequence[int]) -> PortfolioEvaluation:
    vector = self._validate_holdings(holdings)
    components = tuple(item.evaluate(vector) for item in self.objectives)
    return PortfolioEvaluation(
        self.objective_sense,
        sum(item.contribution for item in components),
        components,
    )
```

Serialization uses `schema_version: 1` plus type discriminators for each objective and constraint. Preserve ordered assets, holding variables, objectives, and constraints and reject unknown typed payload fields.

- [ ] **Step 4: Add API docs and release note**

Add autosummary entries for every stable domain class and a literal mean-variance example. Create `releasenotes/notes/structured-portfolio-problem-a73f0c214d9b8e65.yaml` with a `features` entry stating that binary holdings are the supported variable domain.

- [ ] **Step 5: Verify, commit, and request the 0.1 gate**

Run:

```bash
python -m unittest discover -s test/problems -p 'test_*.py' -v
python -m stestr run
python -m sphinx -W -T -b html docs docs/_build/html
```

Expected: all problem tests, existing tests, and documentation pass.

```bash
git add qiskit_finance/problems qiskit_finance/__init__.py test/problems docs/apidocs releasenotes/notes
git commit -m "feat: add structured portfolio problem"
```

---

## Release 0.2: Pluggable Financial Mappings

### Task 6: Define mapping policies, reversible traces, and compiled artifacts

**Files:**

- Create: `qiskit_finance/mappings/__init__.py`
- Create: `qiskit_finance/mappings/base.py`
- Create: `qiskit_finance/mappings/trace.py`
- Create: `qiskit_finance/compilation/__init__.py`
- Create: `qiskit_finance/compilation/artifact.py`
- Create: `test/mappings/__init__.py`
- Create: `test/mappings/test_trace.py`
- Create: `test/compilation/__init__.py`
- Create: `test/compilation/test_artifact.py`

**Interfaces:**

- Consumes: `StructuredPortfolioProblem` and `OptimizationProblem`.
- Produces: `ConstraintHandling`, `ConstraintPolicy`, `MappingContext`, `VariableMap`, `MappingTraceEntry`, `MappingTrace`, `MappingOutput`, `CompiledFinanceProblem`, `AuditEvent`, and `FinanceCompilationArtifact`.

- [ ] **Step 1: Write trace inversion and artifact tests**

```python
def test_trace_decodes_in_reverse_order(self):
    trace = MappingTrace((
        MappingTraceEntry("binary", ("a", "b"), ("x0", "x1"), {}, identity_decoder),
        MappingTraceEntry("fixed", ("x0", "x1"), ("x1",),
                          {"fixed": {"x0": 1}}, insert_x0_decoder),
    ))
    self.assertEqual(trace.interpret((0,)), (1, 0))
    self.assertEqual(trace.to_dict()["entries"][1]["name"], "fixed")

def test_compiled_problem_keeps_both_models(self):
    compiled = CompiledFinanceProblem(
        source=problem, optimization_problem=model, variable_map=variable_map,
        constraint_map={}, constraint_modes={}, trace=MappingTrace(()),
    )
    self.assertIs(compiled.source, problem)
    self.assertIs(compiled.optimization_problem, model)
```

- [ ] **Step 2: Run tests and observe missing modules**

Run: `python -m unittest test.mappings.test_trace test.compilation.test_artifact -v`

Expected: FAIL with missing mapping and compilation modules.

- [ ] **Step 3: Implement exact mapping contracts**

```python
class ConstraintHandling(str, Enum):
    PENALTY = "penalty"
    FEASIBLE_SUBSPACE = "feasible_subspace"

@dataclass(frozen=True)
class ConstraintPolicy:
    default: ConstraintHandling = ConstraintHandling.PENALTY
    overrides: Mapping[str, ConstraintHandling] = field(default_factory=dict)

    def for_constraint(self, name: str) -> ConstraintHandling:
        return self.overrides.get(name, self.default)

@dataclass(frozen=True)
class MappingContext:
    constraint_policy: ConstraintPolicy
    penalty: float | None = None
    current: "MappingOutput | None" = None

@dataclass(frozen=True)
class VariableMap:
    source_asset_ids: tuple[str, ...]
    backend_variable_names: tuple[str, ...]
    asset_to_backend: Mapping[str, str]
    fixed_values: Mapping[str, int] = field(default_factory=dict)

@dataclass(frozen=True)
class MappingTraceEntry:
    name: str
    input_variables: tuple[str, ...]
    output_variables: tuple[str, ...]
    metadata: Mapping[str, JSONValue]
    decoder: Callable[[Sequence[int]], tuple[int, ...]] = field(
        repr=False, compare=False
    )

@dataclass(frozen=True)
class MappingOutput:
    optimization_problem: OptimizationProblem
    variable_map: VariableMap
    constraint_map: Mapping[str, tuple[str, ...]]
    constraint_modes: Mapping[str, ConstraintHandling]
    trace: MappingTrace

@runtime_checkable
class FinancialMapping(Protocol):
    name: str
    def apply(self, problem: StructuredPortfolioProblem,
              context: MappingContext) -> MappingOutput: ...

@dataclass(frozen=True)
class AuditEvent:
    stage: str
    message: str
    metrics: Mapping[str, int | float | str | bool]

@dataclass(frozen=True)
class CircuitMetrics:
    depth: int
    two_qubit_gate_count: int
    operation_counts: Mapping[str, int]

@dataclass(frozen=True)
class CompiledFinanceProblem:
    source: StructuredPortfolioProblem
    optimization_problem: OptimizationProblem
    variable_map: VariableMap
    constraint_map: Mapping[str, tuple[str, ...]]
    constraint_modes: Mapping[str, ConstraintHandling]
    trace: MappingTrace
    analyses: Mapping[str, object] = field(default_factory=dict)
    audit: tuple[AuditEvent, ...] = ()

@dataclass(frozen=True)
class FinanceCompilationArtifact:
    compiled_problem: CompiledFinanceProblem
    qaoa_spec: FinanceQAOASpec | None = None
    circuit: QuantumCircuit | None = None
    layout: QubitLayout | None = None
    metrics: CircuitMetrics | None = None
```

Use postponed annotations plus `TYPE_CHECKING` imports for `FinanceQAOASpec` and `QubitLayout` to avoid import cycles. `VariableMap.source_asset_ids` always retains full source order; `asset_to_backend` contains only unfixed asset variables; `backend_variable_names` also includes converter-created auxiliary/slack variables in circuit order; and `fixed_values` is keyed by source asset ID. `constraint_map` maps each source constraint name to the backend constraint names it produced. `MappingTrace.interpret()` applies decoders from last entry to first. `MappingTrace.to_dict()` omits callables but includes all variable names and metadata. `CircuitMetrics.from_circuit()` uses `circuit.depth()`, counts instructions whose `num_qubits == 2`, and stores `count_ops()` sorted by operation name. Defensively copy every public mapping.

- [ ] **Step 4: Verify and commit**

Run: `python -m unittest test.mappings.test_trace test.compilation.test_artifact -v`

Expected: PASS.

```bash
git add qiskit_finance/mappings qiskit_finance/compilation test/mappings test/compilation
git commit -m "feat: define finance mapping artifacts"
```

### Task 7: Map binary holdings into `OptimizationProblem`

**Files:**

- Create: `qiskit_finance/mappings/binary_holdings.py`
- Modify: `qiskit_finance/mappings/__init__.py`
- Create: `test/mappings/test_binary_holdings.py`
- Modify: `requirements-dev.txt`

**Interfaces:**

- Consumes: objectives, constraints, `MappingContext`, `MappingOutput`.
- Produces: `BinaryHoldingsMapping.apply()` with variables `x_0...x_{n-1}` in source order and named linear constraints.

- [ ] **Step 1: Write exact construction tests**

```python
def test_binary_mapping_preserves_objective_and_names(self):
    output = BinaryHoldingsMapping().apply(problem, MappingContext(ConstraintPolicy()))
    model = output.optimization_problem
    self.assertEqual([var.name for var in model.variables], ["x_0", "x_1"])
    self.assertEqual(model.objective.linear.to_dict(use_name=True),
                     {"x_0": -0.1, "x_1": -0.2})
    np.testing.assert_allclose(
        model.objective.quadratic.to_array(symmetric=True),
        [[0.5, 0.0], [0.0, 1.0]],
    )
    self.assertEqual(model.linear_constraints[0].name, "cardinality")
```

Add one case per constraint class. A two-sided bound creates `<name>:minimum` and `<name>:maximum`. Asset IDs with spaces or punctuation must not become backend variable names.

- [ ] **Step 2: Run the focused test to verify failure**

Run: `python -m unittest test.mappings.test_binary_holdings -v`

Expected: FAIL because `BinaryHoldingsMapping` is absent.

- [ ] **Step 3: Construct the Optimization Mapper model directly**

```python
model = OptimizationProblem(problem.name)
for index in range(len(problem.assets)):
    model.binary_var(name=f"x_{index}")
if problem.objective_sense == "minimize":
    model.minimize(constant=constant, linear=linear, quadratic=quadratic)
else:
    model.maximize(constant=constant, linear=linear, quadratic=quadratic)
```

Aggregate objective weights once. Pass the full symmetric covariance contribution as the dense quadratic input and verify values instead of storage layout. Express conflicts as `x_i + x_j <= 1`; express mandatory/excluded holdings as equality constraints named `<group-name>:<asset-id>`. Populate `constraint_map` for every generated backend constraint, including both sides of numeric bounds. Set `source_asset_ids` to source order, `backend_variable_names` to `x_i` order, and `asset_to_backend` to every asset/`x_i` pair. The decoder returns source-order holdings.

- [ ] **Step 4: Add exhaustive property tests**

Add `hypothesis>=6.100` to `requirements-dev.txt`. Generate 1-6 assets, finite returns, covariance `A.T @ A`, and compatible constraints. For every binary assignment, compare domain total with `model.objective.evaluate(x)` using `rtol=1e-10, atol=1e-12`; compare each named constraint's satisfaction.

- [ ] **Step 5: Verify and commit**

Run:

```bash
python -m unittest test.mappings.test_binary_holdings -v
python -m unittest discover -s test/mappings -p 'test_*.py' -v
```

Expected: PASS, including generated examples.

```bash
git add qiskit_finance/mappings/binary_holdings.py qiskit_finance/mappings/__init__.py test/mappings/test_binary_holdings.py requirements-dev.txt
git commit -m "feat: map binary portfolios with Optimization Mapper"
```

### Task 8: Add constraint strategies and the mapping pipeline

**Files:**

- Create: `qiskit_finance/mappings/constraint_handling.py`
- Create: `qiskit_finance/mappings/pipeline.py`
- Modify: `qiskit_finance/mappings/__init__.py`
- Create: `test/mappings/test_constraint_handling.py`
- Create: `test/mappings/test_pipeline.py`
- Create: `docs/apidocs/qiskit_finance.mappings.rst`
- Modify: `docs/apidocs/qiskit_finance.rst`

**Interfaces:**

- Consumes: `BinaryHoldingsMapping` and mapping contracts.
- Produces: `FixedCardinalityMapping`, `PenaltyConstraintMapping`, `FeasibleSubspaceMapping`, and `FinanceMappingPipeline.compile()`.

- [ ] **Step 1: Write policy and ordering tests**

```python
def test_policy_override_wins(self):
    policy = ConstraintPolicy(
        default=ConstraintHandling.PENALTY,
        overrides={"cardinality": ConstraintHandling.FEASIBLE_SUBSPACE},
    )
    self.assertEqual(policy.for_constraint("cardinality"),
                     ConstraintHandling.FEASIBLE_SUBSPACE)

def test_pipeline_records_deferred_strategies(self):
    compiled = FinanceMappingPipeline().compile(problem, context=MappingContext(policy))
    self.assertEqual(compiled.constraint_modes["cardinality"],
                     ConstraintHandling.FEASIBLE_SUBSPACE)
    self.assertEqual(compiled.constraint_modes["capital"], ConstraintHandling.PENALTY)
    self.assertEqual([entry.name for entry in compiled.trace.entries],
                     ["binary_holdings", "fixed_cardinality", "constraint_handling"])
    self.assertGreater(len(compiled.optimization_problem.linear_constraints), 0)
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest test.mappings.test_constraint_handling test.mappings.test_pipeline -v`

Expected: FAIL because the strategies and pipeline are absent.

- [ ] **Step 3: Classify constraints without adding penalties yet**

`FixedCardinalityMapping` records exact-cardinality feasible-subspace invariants. `FeasibleSubspaceMapping` accepts every initial named constraint and records its `involved_asset_ids()` as an invariant component. Large or overlapping components are rejected only when the selected built-in mixer cannot preserve them; this leaves room for an explicit custom mixer. `PenaltyConstraintMapping` marks constraints for deferred conversion and retains them in the constrained model so fixed-variable propagation can simplify first.

```python
class FinanceMappingPipeline:
    def __init__(self, mappings: Sequence[FinancialMapping] | None = None):
        self._mappings = tuple(mappings or (
            BinaryHoldingsMapping(), FixedCardinalityMapping(),
            FeasibleSubspaceMapping(), PenaltyConstraintMapping(),
        ))

    def compile(self, problem, *, context=None):
        active = context or MappingContext(ConstraintPolicy())
        output = None
        for mapping in self._mappings:
            output = mapping.apply(problem, replace(active, current=output))
        return CompiledFinanceProblem.from_mapping_output(problem, output)
```

Append a trace entry only when a mapping changes state. Reject duplicate mappings and a pipeline whose first mapping does not create a model.

- [ ] **Step 4: Document the strategies**

State precisely: `PENALTY` is materialized by `CalibratePenalties` after fixed-variable elimination; `FEASIBLE_SUBSPACE` remains available to mixer validation and is excluded from the cost Hamiltonian.

- [ ] **Step 5: Verify, commit, and request the 0.2 gate**

Run:

```bash
python -m unittest discover -s test/mappings -p 'test_*.py' -v
python -m unittest discover -s test/compilation -p 'test_*.py' -v
python -m stestr run
python -m sphinx -W -T -b html docs docs/_build/html
```

Expected: all mapping, artifact, existing, and docs tests pass.

```bash
git add qiskit_finance/mappings test/mappings docs/apidocs
git commit -m "feat: add pluggable finance mapping pipeline"
```

---

## Release 0.3: Conflict-Graph Vertical Slice

### Task 9: Implement `ConflictGraphPortfolio`

**Files:**

- Create: `qiskit_finance/applications/optimization/conflict_graph_portfolio.py`
- Modify: `qiskit_finance/applications/optimization/__init__.py`
- Create: `test/applications/test_conflict_graph_portfolio.py`

**Interfaces:**

- Consumes: structured problem domain types.
- Produces: `ConflictGraphPortfolio.to_structured_problem()` and `interpret()`.

- [ ] **Step 1: Write validation and conversion tests**

```python
def test_conflict_graph_becomes_weighted_maximization(self):
    app = ConflictGraphPortfolio(
        vertices=["loan-a", "loan-b", "loan-c"],
        edges=[("loan-a", "loan-b")],
        weights={"loan-a": 2.0, "loan-b": 1.0, "loan-c": 3.0},
        mandatory=["loan-c"], maximum_cardinality=2,
    )
    problem = app.to_structured_problem()
    self.assertEqual(problem.objective_sense, "maximize")
    self.assertEqual(problem.evaluate((1, 0, 1)).total, 5.0)
    self.assertTrue(problem.check_feasibility((1, 0, 1)).is_feasible)
    self.assertFalse(problem.check_feasibility((1, 1, 1)).is_feasible)
```

Add rejection cases for duplicate vertices, unknown endpoints, loops, duplicate/reversed edges, non-finite weights, mandatory/excluded overlap, and conflicting mandatory vertices.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.applications.test_conflict_graph_portfolio -v`

Expected: FAIL because the application is absent.

- [ ] **Step 3: Implement canonical graph storage**

Store vertices in input order and edges sorted by vertex indices. Default weights to 1.0. Preserve graph edges and additional conflicts as separately named constraints so question 4 can choose a feasible-subspace strategy only for the additional pairs.

```python
def to_structured_problem(self) -> StructuredPortfolioProblem:
    constraints = [MutualExclusions(self.edges, name="graph_conflicts")]
    if self.additional_conflicts:
        constraints.append(MutualExclusions(
            self.additional_conflicts, name="additional_conflicts"
        ))
    if self.mandatory:
        constraints.append(MandatoryHoldings(self.mandatory))
    if self.excluded:
        constraints.append(ExcludedHoldings(self.excluded))
    if self.maximum_cardinality is not None:
        constraints.append(Cardinality(maximum=self.maximum_cardinality))
    return StructuredPortfolioProblem(
        assets=[Asset(vertex) for vertex in self.vertices],
        objectives=[ExpectedReturn([self.weights[v] for v in self.vertices])],
        constraints=constraints, objective_sense="maximize", name=self.name,
    )
```

`interpret()` accepts holdings or an object with `holdings`, returns selected IDs in source order, and leaves infeasibility visible.

- [ ] **Step 4: Verify and commit**

Run:

```bash
python -m unittest test.applications.test_conflict_graph_portfolio -v
python -m unittest test.mappings.test_binary_holdings -v
```

Expected: PASS.

```bash
git add qiskit_finance/applications/optimization test/applications/test_conflict_graph_portfolio.py
git commit -m "feat: add conflict graph portfolios"
```

### Task 10: Add the TRUBA adapter and exact classical baseline

**Files:**

- Create: `qiskit_finance/benchmarks/__init__.py`
- Create: `qiskit_finance/benchmarks/truba.py`
- Create: `qiskit_finance/benchmarks/baselines.py`
- Create: `test/benchmarks/__init__.py`
- Create: `test/benchmarks/test_truba.py`
- Create: `test/benchmarks/test_baselines.py`
- Create: `test/resources/truba/soru2_girdi_synthetic.json`

**Interfaces:**

- Consumes: `ConflictGraphPortfolio`, SciPy `milp`, and TRUBA JSON fields.
- Produces: non-public `TrubaInstance`, `load_truba_instance(path)`, and `solve_conflict_graph_classically(application)`.

- [ ] **Step 1: Add a complete synthetic fixture and failing tests**

```json
{
  "question_id": 2,
  "case_id": 99,
  "cizge": [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
  "zorunlu_dugumler": [0]
}
```

```python
def test_adapter_maps_turkish_fields(self):
    instance = load_truba_instance(self.get_resource_path(
        "soru2_girdi_synthetic.json", "resources/truba"))
    self.assertEqual((instance.question_id, instance.case_id), (2, 99))
    self.assertEqual(instance.application.edges, (("0", "1"), ("1", "2")))
    self.assertEqual(instance.application.mandatory, ("0",))
```

Add failures for non-square/asymmetric/nonzero-diagonal matrices, values outside zero/one, out-of-range indices, unknown question IDs, and question/field mismatches.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest test.benchmarks.test_truba test.benchmarks.test_baselines -v`

Expected: FAIL because the benchmark modules are absent.

- [ ] **Step 3: Implement strict loading and provenance**

Read UTF-8 JSON, preserve numeric vertex indices as strings, extract matrix edges for `i < j`, and map `yasak_ikililer` to additional conflicts. Question 4 has the same domain model as question 3; compile configuration selects its mixer.

```python
@dataclass(frozen=True)
class TrubaInstance:
    question_id: int
    case_id: int
    application: ConflictGraphPortfolio
    source_sha256: str
```

- [ ] **Step 4: Implement the SciPy MILP baseline**

Minimize `-weights @ x`, set `integrality=np.ones(n)`, bounds `[0,1]`, add `x_i+x_j<=1` per edge, enforce mandatory/excluded through variable bounds, and add cardinality when present.

```python
@dataclass(frozen=True)
class ClassicalPortfolioResult:
    holdings: tuple[int, ...]
    selected_assets: tuple[str, ...]
    objective_value: float
    is_optimal: bool
```

Threshold at 0.5, re-check the structured problem, and raise `CompilationError` on solver failure or an infeasible rounded result.

- [ ] **Step 5: Verify the synthetic suite and all eight supplied inputs**

Run:

```bash
python -m unittest discover -s test/benchmarks -p 'test_*.py' -v
python -m qiskit_finance.benchmarks.truba validate --input-dir /Users/bilginkocak/hackathon/q-prehackathon/truba/ssb_exam/final
```

Expected: tests pass; the command reports eight valid inputs, IDs `1:1` through `4:2`, and a feasible optimal reference for each.

- [ ] **Step 6: Commit and request the 0.3 gate**

```bash
git add qiskit_finance/benchmarks test/benchmarks test/resources/truba
git commit -m "feat: add TRUBA conflict graph adapter"
```

---

## Release 0.4: Finance-Aware Compilation

### Task 11: Implement the pass protocol and dependency-aware manager

**Files:**

- Create: `qiskit_finance/compilation/base.py`
- Create: `qiskit_finance/compilation/pass_manager.py`
- Create: `qiskit_finance/compilation/passes/__init__.py`
- Create: `qiskit_finance/compilation/passes/validation.py`
- Modify: `qiskit_finance/compilation/__init__.py`
- Create: `test/compilation/test_pass_manager.py`
- Create: `test/compilation/test_validation_pass.py`

**Interfaces:**

- Consumes: `CompiledFinanceProblem`, `AuditEvent`, optional Qiskit `Target`.
- Produces: `PassResult`, `FinancePass`, `PassContext`, `FinancePassManager`, and `ValidateFinanceProblem`.

- [ ] **Step 1: Write pass ordering and invalidation tests**

```python
def test_missing_analysis_fails_before_pass_runs(self):
    manager = FinancePassManager([RequiresGraphPass()])
    with self.assertRaisesRegex(CompilationError, "interaction_graph"):
        manager.run(compiled)

def test_manager_preserves_declared_analyses_and_audits_metrics(self):
    result = FinancePassManager([ProduceA(), ConsumeAToB()]).run(compiled)
    self.assertEqual(result.analyses["b"], 2)
    self.assertNotIn("discarded", result.analyses)
    self.assertEqual([event.stage for event in result.audit[-2:]],
                     ["produce_a", "consume_a_to_b"])
```

Add cases for duplicate pass names, a pass returning the wrong type, input immutability, and `ValidateFinanceProblem` detecting a variable-map/model mismatch.

- [ ] **Step 2: Run focused tests to verify failure**

Run: `python -m unittest test.compilation.test_pass_manager test.compilation.test_validation_pass -v`

Expected: FAIL because the pass framework is absent.

- [ ] **Step 3: Implement pass contracts and audit behavior**

```python
@dataclass(frozen=True)
class PassResult:
    problem: CompiledFinanceProblem
    produced: Mapping[str, object] = field(default_factory=dict)
    metrics: Mapping[str, int | float | str | bool] = field(default_factory=dict)
    message: str = ""

@runtime_checkable
class FinancePass(Protocol):
    name: str
    requires: frozenset[str]
    preserves: frozenset[str]
    def run(self, problem: CompiledFinanceProblem,
            context: PassContext) -> PassResult: ...

@dataclass(frozen=True)
class PassContext:
    target: Target | None
    analyses: Mapping[str, object]
```

For each pass, verify `requires <= analyses.keys()`. Retain only existing analyses named in `preserves`, merge `produced`, attach them to the returned compiled problem, and append an `AuditEvent(stage, message, metrics)`. A transformation that omits an analysis from `preserves` intentionally invalidates it.

`ValidateFinanceProblem` checks source validation, unique backend variables, variable-map consistency, that every `constraint_map` backend name exists, known constraint-mode names, and trace continuity; it produces `validation=True`.

Use these exact dependency declarations so the default pipeline cannot consume stale analysis:

| Pass | Requires | Preserves | Produces |
|---|---|---|---|
| `ValidateFinanceProblem` | none | none | `validation` |
| `PropagateFixedHoldings` | `validation` | `validation` | `fixed_holdings` |
| `EliminateFixedVariables` | `fixed_holdings` | `fixed_holdings` | `fixed_elimination` |
| `CalibratePenalties` | `fixed_elimination` | `fixed_holdings`, `fixed_elimination` | `penalty`, `penalized_constraints`, `constraint_invariants`, `qubo` |
| `AnalyzeInteractionGraph` | `qubo` | `fixed_holdings`, `fixed_elimination`, `penalty`, `penalized_constraints`, `constraint_invariants`, `qubo` | `interaction_graph` |
| `ScheduleCommutingInteractions` | `interaction_graph` | `fixed_holdings`, `fixed_elimination`, `penalty`, `penalized_constraints`, `constraint_invariants`, `qubo`, `interaction_graph` | `interaction_schedule` |
| `SelectQubitLayout` | `interaction_graph` | `fixed_holdings`, `fixed_elimination`, `penalty`, `penalized_constraints`, `constraint_invariants`, `qubo`, `interaction_graph`, `interaction_schedule` | `qubit_layout` |

- [ ] **Step 4: Verify and commit**

Run: `python -m unittest test.compilation.test_pass_manager test.compilation.test_validation_pass -v`

Expected: PASS.

```bash
git add qiskit_finance/compilation test/compilation
git commit -m "feat: add finance compilation pass manager"
```

### Task 12: Propagate mandatory, excluded, conflict, and cardinality values

**Files:**

- Create: `qiskit_finance/compilation/passes/fixed_holdings.py`
- Modify: `qiskit_finance/compilation/passes/__init__.py`
- Create: `test/compilation/test_fixed_holding_propagation.py`

**Interfaces:**

- Consumes: `CompiledFinanceProblem` with `validation` analysis.
- Produces: `PropagateFixedHoldings` and `FixedHoldingsAnalysis(values, reasons)` under analysis key `fixed_holdings`.

```python
@dataclass(frozen=True)
class FixedHoldingsAnalysis:
    values: Mapping[str, int]
    reasons: Mapping[str, str]
```

- [ ] **Step 1: Write inference and contradiction tests**

```python
def test_mandatory_vertex_excludes_all_conflicting_neighbors(self):
    result = run_propagation(vertices=("a", "b", "c"),
                             edges=(("a", "b"), ("a", "c")),
                             mandatory=("a",))
    analysis = result.analyses["fixed_holdings"]
    self.assertEqual(analysis.values, {"x_0": 1, "x_1": 0, "x_2": 0})
    self.assertEqual(analysis.reasons["x_1"],
                     "conflicts with mandatory holding a")

def test_exact_cardinality_saturates_remaining_values(self):
    result = run_propagation(vertices=("a", "b", "c"), mandatory=("a",),
                             cardinality=1)
    self.assertEqual(result.analyses["fixed_holdings"].values,
                     {"x_0": 1, "x_1": 0, "x_2": 0})
```

Add contradictions for fixed-to-both-values, two mandatory conflicting assets, mandatory count above exact/maximum, and too few non-excluded assets for minimum/exact cardinality.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.compilation.test_fixed_holding_propagation -v`

Expected: FAIL because propagation is absent.

- [ ] **Step 3: Implement deterministic fixed-point propagation**

Seed mandatory values with 1 and excluded values with 0. Repeatedly apply these rules until no value changes:

```python
if value[vertex] == 1:
    fix_each_conflicting_neighbor_to_zero(vertex)
if selected_count == exact_cardinality:
    fix_each_unassigned_vertex_to_zero()
if selected_count + unassigned_count == exact_cardinality:
    fix_each_unassigned_vertex_to_one()
```

Apply corresponding maximum/minimum rules. Iterate vertices and canonical edges in source order so reason strings are deterministic. Raise `InfeasiblePortfolioError` immediately when a rule conflicts with an existing value. Store backend variable names in `values` and finance-readable asset IDs in reasons.

- [ ] **Step 4: Verify and commit**

Run:

```bash
python -m unittest test.compilation.test_fixed_holding_propagation -v
python -m unittest test.applications.test_conflict_graph_portfolio -v
```

Expected: PASS.

```bash
git add qiskit_finance/compilation/passes/fixed_holdings.py qiskit_finance/compilation/passes/__init__.py test/compilation/test_fixed_holding_propagation.py
git commit -m "feat: propagate fixed portfolio holdings"
```

### Task 13: Eliminate fixed variables with reversible interpretation

**Files:**

- Modify: `qiskit_finance/compilation/passes/fixed_holdings.py`
- Create: `test/compilation/test_fixed_variable_elimination.py`

**Interfaces:**

- Consumes: `fixed_holdings` analysis and quadratic objective/linear constraints.
- Produces: `EliminateFixedVariables`, reduced `OptimizationProblem`, updated `VariableMap`, and a reversible `fixed_variables` trace entry.

- [ ] **Step 1: Write algebra and reconstruction tests**

```python
def test_elimination_substitutes_fixed_values_into_objective(self):
    reduced = eliminate(model_for("3 + 2*x_0 + 4*x_1 + 6*x_0*x_1"), {"x_0": 1})
    self.assertEqual(reduced.objective.constant, 5.0)
    self.assertEqual(reduced.objective.linear.to_dict(use_name=True), {"x_1": 10.0})

def test_trace_reconstructs_full_source_vector(self):
    compiled = eliminate_compiled(problem, fixed={"x_0": 1, "x_2": 0})
    self.assertEqual(compiled.trace.interpret((1,)), (1, 1, 0))
    self.assertEqual(compiled.variable_map.source_asset_ids, ("a", "b", "c"))
    self.assertEqual(compiled.variable_map.asset_to_backend, {"b": "x_1"})
```

Add cases for fixed terms in linear constraints, a constraint becoming satisfied and disappearing, a constraint becoming impossible, zero backend variables, and maximizing objectives.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.compilation.test_fixed_variable_elimination -v`

Expected: FAIL because elimination is absent.

- [ ] **Step 3: Rebuild the reduced model using substitution**

Read coefficients with `to_dict(use_name=True)`. For every term `q_ij*x_i*x_j`:

```python
if i in fixed and j in fixed:
    constant += coefficient * fixed[i] * fixed[j]
elif i in fixed:
    linear[j] += coefficient * fixed[i]
elif j in fixed:
    linear[i] += coefficient * fixed[j]
else:
    quadratic[(i, j)] += coefficient
```

For a linear constraint, subtract `a_i*fixed[i]` from its RHS and retain active coefficients. If no active coefficients remain, drop a satisfied constraint or raise `InfeasiblePortfolioError`. Recreate active binary variables in their prior order and retain objective sense.

Append a decoder that inserts fixed bits by original variable position. Retain `source_asset_ids`, remove fixed assets from `asset_to_backend`, update `backend_variable_names` to the reduced model order, and merge fixed source asset values. Remove dropped backend constraints from `constraint_map` while retaining a source key with an empty tuple when propagation proved it redundant. Record old/new variable counts and substituted terms in the audit metrics.

- [ ] **Step 4: Add a property equivalence test**

Generate compatible 1-7 variable models and fixed assignments. Enumerate every reduced vector, reconstruct its full vector, and assert equal objective and constraint values before and after elimination at `rtol=1e-10, atol=1e-12`.

- [ ] **Step 5: Verify and commit**

Run: `python -m unittest test.compilation.test_fixed_variable_elimination -v`

Expected: PASS, including generated examples.

```bash
git add qiskit_finance/compilation/passes/fixed_holdings.py test/compilation/test_fixed_variable_elimination.py
git commit -m "feat: eliminate fixed holdings reversibly"
```

### Task 14: Calibrate penalties and materialize a QUBO

**Files:**

- Create: `qiskit_finance/compilation/passes/penalties.py`
- Modify: `qiskit_finance/compilation/passes/__init__.py`
- Create: `test/compilation/test_penalties.py`

**Interfaces:**

- Consumes: simplified constrained model and `constraint_modes`.
- Produces: `PenaltyAnalysis`, `CalibratePenalties`, an unconstrained minimization QUBO, converter-backed trace decoding, and `constraint_invariants` analysis.

```python
@dataclass(frozen=True)
class PenaltyAnalysis:
    penalty: float
    objective_range_bound: float
    was_user_supplied: bool
    coefficient_dynamic_range: float
```

- [ ] **Step 1: Write calibration and strategy-separation tests**

```python
def test_automatic_penalty_strictly_exceeds_objective_range_bound(self):
    analysis = calibrate(model_with_coefficients(linear=[-2, 3], quadratic={(0, 1): 4}))
    self.assertEqual(analysis.objective_range_bound, 9.0)
    self.assertEqual(analysis.penalty, 10.0)

def test_only_penalty_constraints_enter_qubo(self):
    result = CalibratePenalties().run(compiled_with_mixed_modes, context)
    self.assertEqual(len(result.problem.optimization_problem.linear_constraints), 0)
    self.assertEqual(result.produced["constraint_invariants"], ("cardinality",))
    self.assertIn("capital_budget", result.produced["penalized_constraints"])
```

Add a manual penalty test, non-positive rejection, weak manual-penalty warning, max-to-min conversion, and converter trace reconstruction including slack bits.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.compilation.test_penalties -v`

Expected: FAIL because penalty compilation is absent.

- [ ] **Step 3: Implement deterministic penalty selection**

For the simplified objective, compute a bound on the assignment-dependent range; the constant is deliberately excluded because it shifts every assignment equally:

```python
bound = sum(abs(value) for value in linear.values())
bound += sum(abs(value) for value in quadratic.values())
automatic_penalty = bound + 1.0
```

Use `automatic_penalty` as the actual penalty and report `bound` as `objective_range_bound`. A manual penalty is accepted verbatim and emits `UserWarning` when it does not exceed the range bound. Warn when the coefficient dynamic range after conversion exceeds `1e6`.

- [ ] **Step 4: Materialize only penalty-mode constraints**

Use `constraint_map` to copy the simplified model with its objective and only backend constraints whose source names are marked `PENALTY`. Convert with:

```python
converter = OptimizationProblemToQubo(penalty=penalty)
qubo = converter.convert(penalty_model)
```

If no penalty constraints remain, use `MaximizeToMinimize` when necessary and copy the objective into an unconstrained model. Store feasible-subspace constraint names in `constraint_invariants`. Append a trace decoder calling `converter.interpret(values)` before earlier decoders.

After conversion, set `backend_variable_names` to every QUBO variable in model order, including auxiliary/slack names. Retain `asset_to_backend` entries for surviving asset variables. This separation is required by layout, mixers, and bitstring interpretation.

- [ ] **Step 5: Verify and commit**

Run:

```bash
python -m unittest test.compilation.test_penalties -v
python -m unittest discover -s test/mappings -p 'test_*.py' -v
```

Expected: PASS.

```bash
git add qiskit_finance/compilation/passes/penalties.py qiskit_finance/compilation/passes/__init__.py test/compilation/test_penalties.py
git commit -m "feat: calibrate portfolio constraint penalties"
```

### Task 15: Analyze and schedule diagonal cost interactions

**Files:**

- Create: `qiskit_finance/compilation/passes/interactions.py`
- Modify: `qiskit_finance/compilation/passes/__init__.py`
- Create: `test/compilation/test_interactions.py`

**Interfaces:**

- Consumes: unconstrained QUBO.
- Produces: `DiagonalTerm`, `InteractionAnalysis`, `AnalyzeInteractionGraph`, and `ScheduleCommutingInteractions` under keys `interaction_graph` and `interaction_schedule`.

```python
@dataclass(frozen=True, order=True)
class DiagonalTerm:
    qubits: tuple[int, ...]
    coefficient: float

@dataclass(frozen=True)
class InteractionAnalysis:
    operator: SparsePauliOp | None
    offset: float
    terms: tuple[DiagonalTerm, ...]
    weighted_degrees: tuple[float, ...]

@dataclass(frozen=True)
class InteractionSchedule:
    groups: tuple[tuple[DiagonalTerm, ...], ...]
```

- [ ] **Step 1: Write endianness, determinism, and equivalence tests**

```python
def test_ising_labels_use_qiskit_little_endian_qubit_indices(self):
    # f(x) = x_0 + 2*x_1 + 4*x_0*x_1
    analysis = analyze_qubo(two_variable_qubo())
    self.assertEqual(analysis.offset, 2.5)
    self.assertEqual(analysis.terms, (
        DiagonalTerm((0,), -1.5),
        DiagonalTerm((1,), -2.0),
        DiagonalTerm((0, 1), 1.0),
    ))

def test_schedule_is_deterministic_and_qubit_disjoint(self):
    first = schedule(weighted_terms)
    second = schedule(tuple(reversed(weighted_terms)))
    self.assertEqual(first, second)
    for group in first.groups:
        touched = [qubit for term in group for qubit in term.qubits]
        self.assertEqual(len(touched), len(set(touched)))
```

For every 2-6 qubit generated QUBO, construct serial and grouped cost circuits at fixed `gamma=0.37` and assert `Operator(serial).equiv(Operator(grouped))`.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.compilation.test_interactions -v`

Expected: FAIL because the analysis passes are absent.

- [ ] **Step 3: Extract Ising terms**

Call public Optimization Mapper translation:

```python
operator, offset = to_ising(problem.optimization_problem)
```

For a model with no backend variables, record `operator=None`, the constant objective as offset, and no terms. Otherwise convert `SparsePauliOp` labels into `DiagonalTerm(qubits, coefficient)` with the rightmost label character mapped to qubit 0. Reject X/Y terms and imaginary coefficients above `1e-12`. Combine duplicate supports, discard coefficients with absolute value at most `1e-12`, and store single-qubit weights plus absolute ZZ edge weights.

- [ ] **Step 4: Greedily edge-color interactions**

Sort ZZ terms by `(-abs(coefficient), qubits)` and place each into the first group disjoint from all group qubits. Put Z terms into the earliest group where their qubit is unused, creating another group if required. Store groups as tuples and report serial term count, group count, and maximum parallel width.

- [ ] **Step 5: Verify and commit**

Run: `python -m unittest test.compilation.test_interactions -v`

Expected: PASS, including operator equivalence properties.

```bash
git add qiskit_finance/compilation/passes/interactions.py qiskit_finance/compilation/passes/__init__.py test/compilation/test_interactions.py
git commit -m "feat: schedule commuting finance interactions"
```

### Task 16: Select a backend-aware asset-to-qubit layout

**Files:**

- Create: `qiskit_finance/compilation/passes/layout.py`
- Modify: `qiskit_finance/compilation/passes/__init__.py`
- Create: `test/compilation/test_layout.py`
- Create: `docs/apidocs/qiskit_finance.compilation.rst`
- Modify: `docs/apidocs/qiskit_finance.rst`

**Interfaces:**

- Consumes: `interaction_graph`, optional `Target`.
- Produces: `QubitLayout(logical_to_physical)` and `SelectQubitLayout` under analysis key `qubit_layout`.

```python
@dataclass(frozen=True)
class QubitLayout:
    logical_to_physical: tuple[int, ...]
    asset_to_physical: Mapping[str, int]
    weighted_distance_before: float
    weighted_distance_after: float
```

- [ ] **Step 1: Write all-to-all and restricted-target tests**

```python
def test_no_target_uses_identity_layout(self):
    result = SelectQubitLayout().run(compiled, context_without_target)
    self.assertEqual(result.produced["qubit_layout"].logical_to_physical,
                     tuple(range(number_of_variables)))

def test_high_weight_finance_edge_maps_to_connected_qubits(self):
    target = Target.from_configuration(
        num_qubits=4, basis_gates=["rz", "sx", "x", "cx"],
        coupling_map=CouplingMap([(0, 1), (1, 2), (2, 3)]),
    )
    layout = select_layout(graph_with_heavy_edge_0_2, target)
    self.assertIn((layout[0], layout[2]), {(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2)})
```

Add deterministic tie-breaking, insufficient-target-qubit failure, and disconnected-coupling warnings.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m unittest test.compilation.test_layout -v`

Expected: FAIL because layout selection is absent.

- [ ] **Step 3: Implement weighted greedy placement**

Build the physical graph using `target.build_coupling_map()`. Treat every `backend_variable_names` entry—including auxiliary variables—as a logical vertex. Sort logical vertices by descending weighted degree then logical index. Sort physical vertices by descending degree then physical index. Place the first logical vertex on the first physical vertex; for each remaining logical vertex, select the unused physical vertex minimizing weighted shortest-path distance to already placed neighbors, then break ties by negative physical degree and physical index.

Return identity for `target is None`. Record weighted logical distance before/after placement and derive `asset_to_physical` through `VariableMap.asset_to_backend`; auxiliary variables appear in `logical_to_physical` but not in the finance-facing asset map.

- [ ] **Step 4: Document compiler inspection**

Document pass requirements/preservation, audit events, how to replace the default pass list, and how a `Target` changes only layout—not financial semantics.

- [ ] **Step 5: Verify, commit, and request the 0.4 gate**

Run:

```bash
python -m unittest discover -s test/compilation -p 'test_*.py' -v
python -m stestr run
python -m sphinx -W -T -b html docs docs/_build/html
```

Expected: compiler tests, existing tests, and docs pass.

```bash
git add qiskit_finance/compilation test/compilation docs/apidocs
git commit -m "feat: add backend-aware finance layout"
```

---

## Release 0.5: Constraint-Preserving QAOA

### Task 17: Define the QAOA specification and initial-state strategies

**Files:**

- Create: `qiskit_finance/qaoa/__init__.py`
- Create: `qiskit_finance/qaoa/specification.py`
- Create: `qiskit_finance/qaoa/initial_states.py`
- Create: `qiskit_finance/qaoa/mixers/__init__.py`
- Create: `qiskit_finance/qaoa/mixers/base.py`
- Create: `test/qaoa/__init__.py`
- Create: `test/qaoa/test_specification.py`
- Create: `test/qaoa/test_initial_states.py`

**Interfaces:**

- Consumes: Ising operator/offset, `DiagonalTerm`, schedule, constraint invariants, fixed values.
- Produces: `PreparedInitialState`, `InitialStateStrategy`, the `FinanceMixer` protocol, `UniformSuperpositionInitialState`, `ComputationalBasisInitialState`, `FixedCardinalityInitialState`, `EnumeratedFeasibleInitialState`, and immutable `FinanceQAOASpec`.

- [ ] **Step 1: Write specification and initial-state tests**

```python
def test_qaoa_spec_rejects_invalid_repetitions_and_schedule(self):
    with self.assertRaises(InvalidFinanceProblemError):
        FinanceQAOASpec(compiled_problem=compiled, cost_operator=operator,
                        offset=0.0, terms=terms,
                        interaction_schedule=schedule, initial_state=prepared,
                        mixer=mixer, constraint_invariants=(), reps=0)

def test_cardinality_initial_state_is_deterministic_and_feasible(self):
    prepared = FixedCardinalityInitialState().build(compiled_exactly_two)
    self.assertEqual(prepared.support, ((1, 1, 0, 0),))
    state = Statevector.from_instruction(prepared.circuit)
    self.assertAlmostEqual(abs(state.data[3]) ** 2, 1.0)
```

Add cases for schedule terms missing/duplicated, wrong circuit width, a basis state violating an invariant, a requested cardinality exceeding asset-backed variables, enumeration above `max_component_qubits`, and deterministic support order.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest test.qaoa.test_specification test.qaoa.test_initial_states -v`

Expected: FAIL because `qiskit_finance.qaoa` is absent.

- [ ] **Step 3: Implement initial-state contracts**

```python
@dataclass(frozen=True)
class PreparedInitialState:
    circuit: QuantumCircuit
    support: tuple[tuple[int, ...], ...] | None

@runtime_checkable
class InitialStateStrategy(Protocol):
    name: str
    def build(self, problem: CompiledFinanceProblem) -> PreparedInitialState: ...

@runtime_checkable
class FinanceMixer(Protocol):
    name: str
    def validate(self, problem: CompiledFinanceProblem,
                 initial_state: PreparedInitialState) -> None: ...
    def append(self, circuit: QuantumCircuit, beta: ParameterExpression,
               problem: CompiledFinanceProblem) -> None: ...
```

`UniformSuperpositionInitialState` applies H to every backend qubit and sets `support=None` to avoid exponential materialization. `ComputationalBasisInitialState(bits=None)` uses the all-zero backend vector unless bits are supplied and applies X gates for ones. `FixedCardinalityInitialState` subtracts source fixed-one values from the requested exact cardinality, then sets the first required asset-backed qubits in source order; auxiliary qubits start at zero. `EnumeratedFeasibleInitialState(max_component_qubits=8)` enumerates asset-backed vectors lexicographically, retains invariant-feasible vectors, extends each with zero auxiliary bits, prepares normalized amplitudes with `StatePreparation`, and raises `ConstraintPreservationError` if the asset-backed width exceeds its limit or no feasible vector exists.

Any specification with active constraint invariants must have a non-`None` initial support, and every support vector must satisfy those invariants after trace reconstruction. A `None` support is valid only for unconstrained-subspace execution.

- [ ] **Step 4: Implement the immutable QAOA specification**

```python
@dataclass(frozen=True)
class FinanceQAOASpec:
    compiled_problem: CompiledFinanceProblem
    cost_operator: SparsePauliOp
    offset: float
    terms: tuple[DiagonalTerm, ...]
    interaction_schedule: tuple[tuple[DiagonalTerm, ...], ...]
    initial_state: PreparedInitialState
    mixer: FinanceMixer
    constraint_invariants: tuple[str, ...]
    reps: int
```

Validate that every non-identity term occurs exactly once in the schedule, all widths match, `reps >= 1`, and `mixer.validate(compiled_problem, initial_state)` passes before construction completes.

- [ ] **Step 5: Verify and commit**

Run: `python -m unittest discover -s test/qaoa -p 'test_*.py' -v`

Expected: PASS.

```bash
git add qiskit_finance/qaoa test/qaoa
git commit -m "feat: define finance QAOA specifications"
```

### Task 18: Implement the constraint-preserving mixer library

**Files:**

- Modify: `qiskit_finance/qaoa/mixers/__init__.py`
- Modify: `qiskit_finance/qaoa/mixers/base.py`
- Create: `qiskit_finance/qaoa/mixers/standard.py`
- Create: `qiskit_finance/qaoa/mixers/conflict_graph.py`
- Modify: `qiskit_finance/qaoa/__init__.py`
- Create: `test/qaoa/test_mixers.py`

**Interfaces:**

- Consumes: compiled problem, initial-state support, symbolic `beta`.
- Produces: `TransverseFieldMixer`, `FixedHoldingMixer`, `FixedCardinalityMixer`, `ConflictGraphMixer`, `ComponentGroverMixer`, and `verify_mixer_preservation()` implementing the Task 17 protocol.

```python
@dataclass(frozen=True)
class MixerPreservationReport:
    preserved: bool
    exhaustively_verified: bool
    maximum_leakage: float | None
    counterexample: tuple[int, ...] | None
```

- [ ] **Step 1: Write invariant-preservation tests**

```python
@data(
    (FixedCardinalityMixer(), exact_two_problem),
    (ConflictGraphMixer(), path_graph_problem),
    (ComponentGroverMixer(max_component_qubits=4), disconnected_graph_problem),
    (ComponentGroverMixer(max_component_qubits=4), bounded_sector_exposure_problem),
)
@unpack
def test_mixer_has_zero_probability_outside_feasible_space(self, mixer, compiled):
    report = verify_mixer_preservation(
        mixer, compiled, beta_values=(0.0, 0.19, 0.73), atol=1e-10
    )
    self.assertTrue(report.preserved, report.counterexample)
```

Add tests that transverse field is rejected for active invariants, fixed qubits receive no mixer instruction, a conflict mixer handles isolated vertices, Grover components over the size cap fail, and explicit compatible mixers override recommendations.

- [ ] **Step 2: Run the mixer test to verify failure**

Run: `python -m unittest test.qaoa.test_mixers -v`

Expected: FAIL because the mixer modules are absent.

- [ ] **Step 3: Implement standard mixers against the protocol**

`TransverseFieldMixer` applies `rx(2*beta)` to every backend qubit and accepts no feasible-subspace invariants. `FixedHoldingMixer(base)` delegates only to backend variables because fixed source assets were eliminated. `FixedCardinalityMixer` applies `XXPlusYYGate(2*beta)` to adjacent asset-backed qubits in a ring, using one edge for two asset qubits and no XY gates below two; it applies `rx(2*beta)` to every auxiliary qubit so QUBO slack variables remain explorable.

- [ ] **Step 4: Implement conflict and component Grover mixers**

For each invariant vertex in source order, `ConflictGraphMixer` applies a controlled `RXGate(2*beta)` to its asset-backed target, controlled on all asset-backed invariant neighbors being zero. Fixed-one neighbors make the target fixed zero during propagation; fixed-zero neighbors are omitted. Apply ordinary `rx(2*beta)` to auxiliary qubits and asset-backed qubits outside the invariant conflict graph.

Build an invariant hypergraph by connecting all asset-backed variables returned by each invariant constraint's `involved_asset_ids()`. For each connected component, `ComponentGroverMixer` enumerates feasible bitstrings, constructs a normalized preparation circuit `A` by appending `StatePreparation(amplitudes)` to a component-width `QuantumCircuit`, and applies:

```python
circuit.compose(A.inverse(), qubits=component, inplace=True)
for qubit in component:
    circuit.x(qubit)
phase = PhaseGate(-beta) if len(component) == 1 else PhaseGate(-beta).control(len(component) - 1)
circuit.append(phase, component)
for qubit in component:
    circuit.x(qubit)
circuit.compose(A, qubits=component, inplace=True)
```

This realizes `A exp(-i beta |0><0|) A†` and acts within the enumerated feasible support.

After processing all invariant components, apply `rx(2*beta)` to every backend qubit not present in a component, including auxiliary variables. If invariants overlap or include a global cardinality constraint, enumerate the combined asset component when it is within the configured cap; otherwise raise `ConstraintPreservationError` instead of selecting an incompatible mixer.

- [ ] **Step 5: Implement exhaustive verification for small systems**

For asset-backed width at most 10 and total backend width at most 12, build each invariant-feasible basis state (including auxiliary assignments), append one mixer layer at each supplied numeric beta, evolve with `Statevector`, and sum probabilities of invariant-infeasible states. Return a `MixerPreservationReport`; fail when leakage exceeds `atol`. For larger widths, `validate()` performs structural checks and the report marks exhaustive verification as unavailable rather than claiming it occurred.

- [ ] **Step 6: Verify and commit**

Run: `python -m unittest test.qaoa.test_mixers -v`

Expected: PASS with leakage below `1e-10` for every enumerated case.

```bash
git add qiskit_finance/qaoa/mixers qiskit_finance/qaoa/__init__.py test/qaoa/test_mixers.py
git commit -m "feat: add constraint-preserving finance mixers"
```

### Task 19: Synthesize scheduled QAOA circuits and add `FinanceCompiler`

**Files:**

- Create: `qiskit_finance/qaoa/synthesis.py`
- Create: `qiskit_finance/compiler.py`
- Modify: `qiskit_finance/qaoa/__init__.py`
- Modify: `qiskit_finance/__init__.py`
- Create: `test/qaoa/test_synthesis.py`
- Create: `test/test_compiler.py`

**Interfaces:**

- Consumes: mapping pipeline, default compiler passes, QAOA spec, mixers, initial states, optional `Target`.
- Produces: `SynthesizedFinanceCircuit(circuit, betas, gammas, parameter_order)`, `synthesize_qaoa(spec)`, and `FinanceCompiler.compile()`.

- [ ] **Step 1: Write synthesis semantics tests**

```python
def test_synthesis_uses_one_beta_and_gamma_per_repetition(self):
    built = synthesize_qaoa(spec_with_reps(2))
    self.assertEqual([p.name for p in built.gammas], ["gamma[0]", "gamma[1]"])
    self.assertEqual([p.name for p in built.betas], ["beta[0]", "beta[1]"])
    self.assertEqual(built.parameter_order, built.gammas + built.betas)

def test_one_layer_matches_cost_then_mixer_unitary(self):
    built = synthesize_qaoa(two_qubit_spec)
    bound = built.circuit.assign_parameters({built.gammas[0]: 0.31,
                                             built.betas[0]: 0.17})
    self.assertTrue(Operator(bound).equiv(reference_operator))
```

Add tests for RZ/RZZ coefficients, scheduled group order, initial-state prefix, no measurements in the parameterized circuit, explicit mixer override, incompatible override failure, and default pass audit order.

Add a fully fixed problem test asserting that compilation returns a zero-qubit circuit, `qaoa_spec is None`, and a trace that reconstructs the full fixed portfolio.

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m unittest test.qaoa.test_synthesis test.test_compiler -v`

Expected: FAIL because synthesis/compiler modules are absent.

- [ ] **Step 3: Implement late cost and mixer synthesis**

Create `ParameterVector("gamma", reps)` and `ParameterVector("beta", reps)`. Compose the initial-state circuit once. Define the result carrier before building layers:

```python
@dataclass(frozen=True)
class SynthesizedFinanceCircuit:
    circuit: QuantumCircuit
    betas: tuple[Parameter, ...]
    gammas: tuple[Parameter, ...]
    parameter_order: tuple[Parameter, ...]
```

For each repetition and scheduled group:

```python
for term in group:
    if len(term.qubits) == 1:
        circuit.rz(2 * gamma[layer] * term.coefficient, term.qubits[0])
    elif len(term.qubits) == 2:
        circuit.rzz(2 * gamma[layer] * term.coefficient, *term.qubits)
    spec.mixer.append(circuit, beta[layer], spec.compiled_problem)
```

Ignore identity terms in the circuit and retain them in the offset. Return gamma/beta tuples in optimization parameter order `(gamma..., beta...)`.

- [ ] **Step 4: Implement compiler defaults and override rules**

Use this pass order exactly:

```python
DEFAULT_PASSES = (
    ValidateFinanceProblem(), PropagateFixedHoldings(),
    EliminateFixedVariables(), CalibratePenalties(),
    AnalyzeInteractionGraph(), ScheduleCommutingInteractions(),
    SelectQubitLayout(),
)
```

The default policy is penalty handling. Use `TransverseFieldMixer` with `UniformSuperpositionInitialState` when there are no active invariants. When feasible-subspace constraints are requested, recommend `ConflictGraphMixer` with `ComputationalBasisInitialState` for conflicts and `FixedCardinalityMixer` with `FixedCardinalityInitialState` for exact cardinality. For `ComponentGroverMixer`, use the all-zero computational state when it satisfies every invariant; otherwise use `EnumeratedFeasibleInitialState` when the combined asset-backed width is within the configured cap. Raise `ConstraintPreservationError` when no built-in mixer supports the requested combination, and honor every explicit compatible choice.

If a target is present, call `generate_preset_pass_manager(target=target, optimization_level=1, initial_layout=list(layout.logical_to_physical))` on the synthesized circuit. Without a target, keep the logical circuit. Populate final circuit metrics from the resulting circuit.

When fixed-variable elimination leaves zero backend variables, skip QAOA-spec construction and transpilation, return `QuantumCircuit(0)`, and retain the constant objective plus reconstruction trace in the artifact.

- [ ] **Step 5: Verify end-to-end compilation**

Run:

```bash
python -m unittest test.qaoa.test_synthesis test.test_compiler -v
python -m unittest discover -s test/qaoa -p 'test_*.py' -v
```

Expected: PASS; a three-vertex conflict portfolio compiles from finance objects to a parameterized Qiskit circuit and retains its complete trace.

- [ ] **Step 6: Commit circuit compilation**

```bash
git add qiskit_finance/qaoa qiskit_finance/compiler.py qiskit_finance/__init__.py test/qaoa test/test_compiler.py
git commit -m "feat: compile structured portfolios to QAOA circuits"
```

### Task 20: Interpret sampler results and provide the reference workflow

**Files:**

- Create: `qiskit_finance/results/__init__.py`
- Create: `qiskit_finance/results/finance_execution_result.py`
- Create: `qiskit_finance/results/interpreter.py`
- Create: `qiskit_finance/workflows/__init__.py`
- Create: `qiskit_finance/workflows/sampling_qaoa.py`
- Create: `test/results/__init__.py`
- Create: `test/results/test_interpreter.py`
- Create: `test/workflows/__init__.py`
- Create: `test/workflows/test_sampling_qaoa.py`

**Interfaces:**

- Consumes: `FinanceCompilationArtifact`, V2 sampler, minimizer with `minimize(fun, x0)`, counts.
- Produces: `FinanceSample`, `FinanceExecutionResult`, `interpret_counts()`, and `solve()`; reuses `CircuitMetrics` from the compilation artifact contract.

```python
@runtime_checkable
class Minimizer(Protocol):
    def minimize(self, fun: Callable[[np.ndarray], float],
                 x0: np.ndarray) -> OptimizeResultLike: ...

def interpret_counts(
    counts: Mapping[str, int], artifact: FinanceCompilationArtifact, *,
    shots: int, seed: int | None = None,
    reference_value: float | None = None,
) -> FinanceExecutionResult: ...
```

`OptimizeResultLike` is a protocol with `x: np.ndarray` and optional values read through `getattr`, including `nfev`.

- [ ] **Step 1: Write deterministic interpretation tests**

```python
def test_interpreter_prefers_best_feasible_finance_value(self):
    counts = {"001": 20, "101": 5, "111": 100}
    result = interpret_counts(counts, artifact, shots=125)
    self.assertEqual(result.holdings, (1, 0, 1))
    self.assertTrue(result.feasibility.is_feasible)
    self.assertEqual(result.selected_assets, ("a", "c"))
    self.assertFalse(result.was_repaired)

def test_no_feasible_sample_remains_explicitly_infeasible(self):
    result = interpret_counts({"11": 10}, conflicting_two_asset_artifact, shots=10)
    self.assertFalse(result.feasibility.is_feasible)
    self.assertEqual(result.holdings, (1, 1))
    self.assertFalse(result.was_repaired)
```

Add Qiskit little-endian bit parsing, converter slack-bit decoding, fixed-variable reconstruction, maximizing/minimizing selection, probability tie-breaking, per-component values, empty counts, count/shot mismatch, and circuit metrics tests.

Add a zero-active-variable case proving `solve()` does not call the sampler or optimizer and returns the reconstructed deterministic holding vector with probability one.

- [ ] **Step 2: Run the result tests to verify failure**

Run: `python -m unittest test.results.test_interpreter -v`

Expected: FAIL because result modules are absent.

- [ ] **Step 3: Implement immutable result types and selection**

```python
@dataclass(frozen=True)
class FinanceSample:
    backend_bits: tuple[int, ...]
    holdings: tuple[int, ...]
    count: int
    probability: float
    evaluation: PortfolioEvaluation
    feasibility: FeasibilityReport

@dataclass(frozen=True)
class FinanceExecutionResult:
    holdings: tuple[int, ...]
    selected_assets: tuple[str, ...]
    evaluation: PortfolioEvaluation
    feasibility: FeasibilityReport
    samples: tuple[FinanceSample, ...]
    circuit_metrics: CircuitMetrics
    shots: int
    seed: int | None
    optimizer_budget: int | None
    optimizer_evaluations: int | None
    runtime_seconds: float
    runtime_metadata: Mapping[str, JSONValue]
    mapping_trace: Mapping[str, JSONValue]
    reference_value: float | None = None
    approximation_ratio: float | None = None
    objective_gap: float | None = None
    was_repaired: bool = False
```

Convert Qiskit's display-order count keys to variable order with `tuple(int(bit) for bit in reversed(key.replace(" ", "")))`, then decode each backend vector with `artifact.compiled_problem.trace.interpret`. If feasible samples exist, choose the best original-domain total according to objective sense, then higher probability, then lexicographic holdings. Otherwise choose highest probability then lexicographic holdings and keep its violations. Sort `samples` by descending count then backend bits. Leave reference metrics as `None` unless the caller supplied a classical reference.

- [ ] **Step 4: Write the workflow test with fake V2 sampler and minimizer**

```python
def test_solve_optimizes_expected_qubo_energy_and_returns_trace(self):
    sampler = RecordingSampler([{"00": 8, "01": 24}])
    optimizer = RecordingMinimizer(return_x=np.array([0.2, 0.4]))
    result = solve(problem, sampler=sampler, optimizer=optimizer,
                   reps=1, shots=32, seed=7)
    self.assertEqual(sampler.requested_shots, 32)
    self.assertEqual(result.shots, 32)
    self.assertEqual(result.seed, 7)
    self.assertGreater(len(result.mapping_trace["entries"]), 0)
```

- [ ] **Step 5: Implement V2 sampling and optimization**

Copy the parameterized circuit, call `measure_all()`, bind parameters in `(gamma..., beta...)` order, and submit `sampler.run([(circuit, parameter_values)], shots=shots)`. Read counts from `job.result()[0].data.meas.get_counts()`. The objective passed to the minimizer is the count-weighted mean of `compiled.optimization_problem.objective.evaluate(backend_bits)`.

Generate the initial point with `np.random.default_rng(seed).uniform(-np.pi, np.pi, 2*reps)`. Call `optimizer.minimize(fun=objective, x0=initial_point)`. Sample once more at `optimizer_result.x`, interpret all counts, and store `nfev` when the optimizer exposes it. Read `optimizer_budget` from a public `maxiter` attribute or public `settings["maxiter"]`, otherwise store `None`. Record sampler/optimizer class names, target description, and wall-clock timestamps in `runtime_metadata`; do not include object reprs, options that may contain credentials, or backend secrets. Do not modify sampler options or credentials.

For a zero-qubit artifact, bypass optimization and sampling, interpret the empty backend vector through the trace, and create one sample with `count=shots` and `probability=1.0`.

- [ ] **Step 6: Add a local primitive integration test**

Use `StatevectorSampler(seed=123, default_shots=2048)` and a deterministic one-evaluation minimizer on a two-asset conflict graph. Assert result probabilities sum to one within `1e-12`, holdings have source width, the selected result is feasible, and circuit metrics match the compiled circuit.

- [ ] **Step 7: Verify, commit, and request the 0.5 gate**

Run:

```bash
python -m unittest discover -s test/results -p 'test_*.py' -v
python -m unittest discover -s test/workflows -p 'test_*.py' -v
python -m unittest discover -s test/qaoa -p 'test_*.py' -v
python -m stestr run
```

Expected: all result, workflow, QAOA, and existing tests pass without a cloud account.

```bash
git add qiskit_finance/results qiskit_finance/workflows test/results test/workflows
git commit -m "feat: add auditable sampling QAOA workflow"
```

---

## Release 0.6: Benchmarking and Stabilization

### Task 21: Add reproducible metrics and the eight-instance TRUBA benchmark

**Files:**

- Create: `qiskit_finance/benchmarks/metrics.py`
- Modify: `qiskit_finance/benchmarks/truba.py`
- Modify: `qiskit_finance/benchmarks/__init__.py`
- Create: `test/benchmarks/test_metrics.py`
- Modify: `test/benchmarks/test_truba.py`
- Create: `benchmarks/README.md`
- Create: `benchmarks/truba_reference.json`

**Interfaces:**

- Consumes: TRUBA loader, classical baseline, compiler, workflow, execution results.
- Produces: `BenchmarkRecord`, `financial_quality_metrics()`, `circuit_metrics()`, paired comparison statistics, and `python -m qiskit_finance.benchmarks.truba benchmark`.

```python
@dataclass(frozen=True)
class FinancialQualityMetrics:
    feasibility_rate: float
    best_feasible_value: float | None
    objective_gap: float | None
    approximation_ratio: float | None

@dataclass(frozen=True)
class PairedComparison:
    mean_difference: float
    standard_error: float
    objective_range: float
    statistically_equivalent: bool
```

- [ ] **Step 1: Write metric-definition tests**

```python
def test_metrics_report_feasibility_gap_and_ratio(self):
    metrics = financial_quality_metrics(
        samples=(feasible_sample(value=8.0, count=60),
                 infeasible_sample(value=10.0, count=40)),
        objective_sense="maximize", reference_value=10.0,
    )
    self.assertEqual(metrics.feasibility_rate, 0.6)
    self.assertEqual(metrics.best_feasible_value, 8.0)
    self.assertEqual(metrics.objective_gap, 2.0)
    self.assertEqual(metrics.approximation_ratio, 0.8)

def test_circuit_metrics_count_all_two_qubit_operations(self):
    circuit = QuantumCircuit(3)
    circuit.cx(0, 1)
    circuit.rzz(0.2, 1, 2)
    metrics = circuit_metrics(circuit)
    self.assertEqual(metrics.two_qubit_gate_count, 2)
```

Add minimizing-objective, zero-reference ratio (`None`), no-feasible-sample, operation-count ordering, shot budget, runtime, and confidence-interval tests.

- [ ] **Step 2: Run metric tests to verify failure**

Run: `python -m unittest test.benchmarks.test_metrics -v`

Expected: FAIL because metrics are absent.

- [ ] **Step 3: Implement stable benchmark records**

```python
@dataclass(frozen=True)
class BenchmarkRecord:
    instance_id: str
    strategy: str
    source_sha256: str
    reference_value: float
    best_feasible_value: float | None
    feasibility_rate: float
    approximation_ratio: float | None
    objective_gap: float | None
    circuit_depth: int
    two_qubit_gate_count: int
    operation_counts: Mapping[str, int]
    runtime_seconds: float
    shots: int
    seed: int
    audit: tuple[Mapping[str, JSONValue], ...]
```

For maximize, gap is `reference-candidate`; for minimize, `candidate-reference`. Ratio is `candidate/reference` for nonnegative maximization and `reference/candidate` for positive minimization; otherwise return `None` and rely on gap. Compute feasibility rate from counts, not unique bitstrings.

- [ ] **Step 4: Implement the four configuration factory**

The factory returns these exact configurations:

```python
def truba_configuration(question_id: int) -> BenchmarkConfiguration:
    if question_id in (1, 2, 3):
        return BenchmarkConfiguration(
            policy=ConstraintPolicy(default=ConstraintHandling.PENALTY),
            mixer=TransverseFieldMixer(),
        )
    if question_id == 4:
        return BenchmarkConfiguration(
            policy=ConstraintPolicy(
                default=ConstraintHandling.PENALTY,
                overrides={"additional_conflicts":
                           ConstraintHandling.FEASIBLE_SUBSPACE},
            ),
            mixer=ComponentGroverMixer(max_component_qubits=8),
        )
    raise InvalidFinanceProblemError(f"Unsupported TRUBA question {question_id}")
```

Question 2 gains fixed-holding propagation automatically. Question 3 penalizes additional pairs. Question 4 preserves only `additional_conflicts` through component Grover diffusion while ordinary `graph_conflicts` remain in the cost model.

- [ ] **Step 5: Add serial-versus-scheduled paired comparison**

Build a serial schedule with one term per group and the compiler schedule from Task 15. Use identical parameter vectors. For small synthetic circuits, assert statevector equivalence. For supplied instances, run both circuits with 4096 shots for seeds 101-120 and compute the paired mean objective difference and standard error.

Pass when:

```python
scheduled_depth < serial_depth
abs(mean_scheduled - mean_serial) <= (
    3.0 * standard_error_of_paired_difference + 0.01 * objective_range
)
```

Report a failure per instance; do not average a failing instance into a suite-level success.

- [ ] **Step 6: Implement CLI output and reference manifest**

`validate` prints schema/optimum status. `benchmark` accepts `--input-dir`, `--output`, `--shots`, and `--seed`; writes sorted JSON atomically; and refuses to overwrite unless `--force` is passed. `truba_reference.json` contains the eight instance IDs, SHA-256 values, exact classical objective values, and no copied graph data.

Use this reference content, produced from SciPy MILP and independently rechecked through each structured problem:

```json
{
  "1:1": {"sha256": "1944309be1caa1b95ef7144989fb5c7ba4d5b449e073731736eb05b42bb6799e", "objective": 6.0},
  "1:2": {"sha256": "3a7713f438dc4e3a7018a5a798b7559ef9cdfb89eb99cfd3ba18da37f4f592cd", "objective": 8.0},
  "2:1": {"sha256": "9a55c2a2536b01e79dd7dedcdab1385d3a776fd90eac6010798ff3f0fa75fb5d", "objective": 5.0},
  "2:2": {"sha256": "30cc7e657e20133c7a019384b4e8c5f1dbb6e287e14c28a7aa6231110d7ce504", "objective": 8.0},
  "3:1": {"sha256": "a7bef5d61f201da1827267d241becf1c2dcb1d003290c4aab4b8d9b77a0b82a9", "objective": 5.0},
  "3:2": {"sha256": "97dcce3ea20ecd5a1857b1322da14fee402d2a84a0f9ae381a2367d5ca2d40da", "objective": 8.0},
  "4:1": {"sha256": "1fd39346a731e98fb29bb0c36d3b03d1f87f1b70a47bf90a0c3b6b3c94cdef83", "objective": 5.0},
  "4:2": {"sha256": "0d3a9a8994355bc360183778d9a27d6b3d0a5fb6ac8cc2aeb9b7ea9f5c921d7b", "objective": 7.0}
}
```

Run the local release benchmark:

```bash
python -m qiskit_finance.benchmarks.truba benchmark \
  --input-dir /Users/bilginkocak/hackathon/q-prehackathon/truba/ssb_exam/final \
  --output build/truba-benchmark.json --shots 4096 --seed 101
```

Expected: eight records, source hashes matching the manifest, feasible best samples, and passing per-instance scheduled-depth/equivalence criteria.

- [ ] **Step 7: Verify and commit**

Run:

```bash
python -m unittest discover -s test/benchmarks -p 'test_*.py' -v
python -m stestr run
```

Expected: all benchmark and existing tests pass.

```bash
git add qiskit_finance/benchmarks test/benchmarks benchmarks
git commit -m "feat: benchmark structured QAOA portfolios"
```

### Task 22: Complete dual-audience documentation and release validation

**Files:**

- Create: `docs/tutorials/12_structured_portfolio.ipynb`
- Create: `docs/tutorials/13_conflict_graph_portfolio.ipynb`
- Create: `docs/tutorials/14_constraint_strategies.ipynb`
- Create: `docs/tutorials/15_commuting_scheduling.ipynb`
- Create: `docs/tutorials/16_custom_finance_pass.ipynb`
- Modify: `docs/tutorials/00_amplitude_estimation.ipynb`
- Modify: `docs/tutorials/01_portfolio_optimization.ipynb`
- Modify: `docs/tutorials/02_portfolio_diversification.ipynb`
- Modify: `docs/tutorials/03_european_call_option_pricing.ipynb`
- Modify: `docs/tutorials/04_european_put_option_pricing.ipynb`
- Modify: `docs/tutorials/05_bull_spread_pricing.ipynb`
- Modify: `docs/tutorials/06_basket_option_pricing.ipynb`
- Modify: `docs/tutorials/07_asian_barrier_spread_pricing.ipynb`
- Modify: `docs/tutorials/08_fixed_income_pricing.ipynb`
- Modify: `docs/tutorials/09_credit_risk_analysis.ipynb`
- Modify: `docs/tutorials/10_qgan_option_pricing.ipynb`
- Modify: `docs/tutorials/index.rst`
- Modify: `docs/index.rst`
- Create: `docs/apidocs/qiskit_finance.qaoa.rst`
- Create: `docs/apidocs/qiskit_finance.results.rst`
- Create: `docs/apidocs/qiskit_finance.workflows.rst`
- Modify: `docs/apidocs/qiskit_finance.rst`
- Modify: `README.md`
- Modify: `.github/workflows/main.yml`
- Create: `releasenotes/notes/structured-quantum-finance-8f73c16a2d9450be.yaml`

**Interfaces:**

- Consumes: all stable 0.1-0.6 public APIs.
- Produces: finance-engineer and quantum-engineer learning paths, complete API reference, minimum/latest/prerelease CI, and final release evidence.

- [ ] **Step 1: Add documentation smoke tests**

Create `test/test_structured_readme_sample.py` containing the exact README example and assert:

```python
problem = ConflictGraphPortfolio(
    vertices=["trade-a", "trade-b", "trade-c"],
    edges=[("trade-a", "trade-b")],
    weights={"trade-a": 1.0, "trade-b": 2.0, "trade-c": 3.0},
).to_structured_problem()
artifact = FinanceCompiler().compile(problem, reps=1)
self.assertEqual(len(problem.assets), 3)
self.assertEqual(artifact.circuit.num_qubits, 3)
self.assertGreater(len(artifact.compiled_problem.trace.entries), 0)
self.assertIn("ConflictGraphPortfolio", Path("README.md").read_text(encoding="utf8"))
```

Add notebook execution to the existing tutorial CI for the five new notebooks using synthetic data and local primitives only.

Migrate every existing tutorial listed in this task from `Sampler` V1 to `StatevectorSampler` V2. Replace `Sampler(run_options={"shots": N, "seed": S})` with `StatevectorSampler(default_shots=N, seed=S)` and replace bare `Sampler()` with a seeded `StatevectorSampler` declared once in the notebook. Preserve numerical tolerances and output interpretation.

- [ ] **Step 2: Run the smoke test before docs are written**

Run: `python -m unittest test.test_structured_readme_sample -v`

Expected: API assertions pass after Tasks 1-21; README-text verification fails because the example is not present yet.

- [ ] **Step 3: Write the finance-engineer path**

Notebook 12 constructs a mean-variance problem and explains raw versus weighted objective values. Notebook 13 loads a synthetic conflict graph, compares the exact baseline with sampled output, and displays named violations. The README shows the Task 22 smoke-test example and links directly to both notebooks.

- [ ] **Step 4: Write the quantum-engineer path**

Notebook 14 compares penalty and feasible-subspace policies on the same source problem. Notebook 15 displays interaction groups and serial/scheduled depth. Notebook 16 defines this complete custom analysis pass and inserts it into a pass manager:

```python
@dataclass(frozen=True)
class CountDenseAssets:
    name: str = "count_dense_assets"
    requires: frozenset[str] = frozenset({"interaction_graph"})
    preserves: frozenset[str] = frozenset({"interaction_graph"})

    def run(self, problem, context):
        graph = context.analyses["interaction_graph"]
        count = sum(weighted_degree > 1.0 for weighted_degree in graph.weighted_degrees)
        return PassResult(problem, produced={"dense_asset_count": count},
                          metrics={"dense_asset_count": count},
                          message=f"Found {count} densely interacting assets")
```

- [ ] **Step 5: Finish API docs and release notes**

Autosummary every intentionally stable type from `problems`, `mappings`, `compilation`, `qaoa`, `results`, and `workflows`. Keep compiler internals out of top-level `qiskit_finance.__all__`. The release note describes additive APIs, version floors, optional execution dependencies, binary-holding limitation, and the external nature of TRUBA data.

- [ ] **Step 6: Verify every supported quality gate**

Run from a fresh Python 3.10 environment with minimum dependencies, then a fresh newest-stable environment:

```bash
python -m pip check
python -m stestr run
black --check qiskit_finance test tools docs
pylint -rn qiskit_finance test tools
mypy qiskit_finance test tools
python tools/check_copyright.py -check
python tools/verify_headers.py qiskit_finance test tools
python -m sphinx -W -T -b html docs docs/_build/html
```

Expected: every command exits zero in both environments. Run the prerelease CI job separately; record its result but do not block 0.6 on an upstream prerelease defect.

- [ ] **Step 7: Re-run the external acceptance benchmark**

```bash
python -m qiskit_finance.benchmarks.truba benchmark \
  --input-dir /Users/bilginkocak/hackathon/q-prehackathon/truba/ssb_exam/final \
  --output build/truba-benchmark.json --shots 4096 --seed 101 --force
```

Expected: all eight hashes match, all four configurations compile through one pipeline, every selected result is explicit about feasibility, and every scheduled circuit meets the per-instance depth/equivalence check.

- [ ] **Step 8: Commit and request the 0.6/stable-vertical-slice review**

```bash
git add README.md docs test/test_structured_readme_sample.py .github/workflows/main.yml releasenotes/notes
git commit -m "docs: publish structured quantum finance workflows"
```

## Stable Vertical-Slice Completion Checklist

- [ ] A finance engineer can model and validate a conflict portfolio without Hamiltonian or circuit code.
- [ ] A quantum engineer can inspect or replace mappings, passes, initial state, and mixer.
- [ ] Mapping and compilation traces are machine-readable and human-readable.
- [ ] Exhaustive small-instance tests prove source/mapped objective and constraint equivalence.
- [ ] Small-system statevector tests prove declared mixer invariants.
- [ ] One configuration factory expresses all four TRUBA variants.
- [ ] All eight external TRUBA inputs pass hash, feasibility, depth, and statistical-equivalence gates.
- [ ] Finance and quantum tutorials execute without network access.
- [ ] Minimum/latest CI passes; prerelease CI result is recorded.
- [ ] Existing public APIs remain present and any dependency behavior change is documented.

## Explicitly Deferred Follow-Up Designs

The approved specification deliberately excludes these from the 0.1-0.6 code path. Open separate design work after the stable vertical slice establishes performance and API evidence:

1. Integer, unary, and domain-wall holding encodings.
2. Low-rank factor-model lowering and covariance clustering.
3. Multi-period rebalancing, turnover limits, path-dependent transaction costs, tax-lot selection, and holding periods. The 0.1 binary `TransactionCost` objective remains the supported single-period linear case.
4. Scenario-based robust optimization, VaR/CVaR, credit-loss, and amplitude-estimation error reporting.
5. Accelerated native kernels only for profiles that identify a Python bottleneck.
