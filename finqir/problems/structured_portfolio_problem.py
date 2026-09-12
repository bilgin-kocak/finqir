# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Immutable finance problem preserving source-level semantics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

from finqir._typing import JSONValue, freeze_json, require_exact_fields, thaw_json
from finqir.exceptions import InvalidFinanceProblemError

from .assets import Asset
from .constraints import (
    CapitalBudget,
    Cardinality,
    ExcludedHoldings,
    ExposureBounds,
    FinanceConstraint,
    MandatoryHoldings,
    MutualExclusions,
)
from .evaluation import FeasibilityReport, PortfolioEvaluation
from .objectives import ExpectedReturn, FinanceObjective, TransactionCost, VarianceRisk
from .variables import HoldingVariable


def _objective_from_dict(payload: Mapping[str, Any]) -> FinanceObjective:
    kind = payload.get("type")
    if kind == "expected_return":
        require_exact_fields(payload, {"type", "name", "weight", "expected_returns"}, kind)
        return ExpectedReturn(payload["expected_returns"], payload["weight"], payload["name"])
    if kind == "variance_risk":
        require_exact_fields(payload, {"type", "name", "weight", "covariance"}, kind)
        return VarianceRisk(payload["covariance"], payload["weight"], payload["name"])
    if kind == "transaction_cost":
        require_exact_fields(
            payload,
            {"type", "name", "weight", "current_holdings", "buy_costs", "sell_costs"},
            kind,
        )
        return TransactionCost(
            payload["current_holdings"],
            payload["buy_costs"],
            payload["sell_costs"],
            payload["weight"],
            payload["name"],
        )
    raise InvalidFinanceProblemError(f"Unknown objective type {kind!r}")


def _constraint_from_dict(payload: Mapping[str, Any]) -> FinanceConstraint:
    kind = payload.get("type")
    if kind == "cardinality":
        require_exact_fields(payload, {"type", "name", "exactly", "minimum", "maximum"}, kind)
        return Cardinality(
            payload["exactly"], payload["minimum"], payload["maximum"], payload["name"]
        )
    if kind == "capital_budget":
        require_exact_fields(payload, {"type", "name", "coefficients", "minimum", "maximum"}, kind)
        return CapitalBudget(
            payload["coefficients"], payload["minimum"], payload["maximum"], payload["name"]
        )
    if kind == "mandatory_holdings":
        require_exact_fields(payload, {"type", "name", "asset_ids"}, kind)
        return MandatoryHoldings(payload["asset_ids"], payload["name"])
    if kind == "excluded_holdings":
        require_exact_fields(payload, {"type", "name", "asset_ids"}, kind)
        return ExcludedHoldings(payload["asset_ids"], payload["name"])
    if kind == "mutual_exclusions":
        require_exact_fields(payload, {"type", "name", "pairs"}, kind)
        return MutualExclusions(payload["pairs"], payload["name"])
    if kind == "exposure_bounds":
        require_exact_fields(payload, {"type", "name", "coefficients", "minimum", "maximum"}, kind)
        return ExposureBounds(
            payload["coefficients"], payload["minimum"], payload["maximum"], payload["name"]
        )
    raise InvalidFinanceProblemError(f"Unknown constraint type {kind!r}")


@dataclass(frozen=True)
class StructuredPortfolioProblem:
    """A backend-independent portfolio problem with auditable finance semantics."""

    assets: tuple[Asset, ...]
    objectives: tuple[FinanceObjective, ...]
    constraints: tuple[FinanceConstraint, ...] = ()
    holding_variables: tuple[HoldingVariable, ...] = ()
    objective_sense: Literal["minimize", "maximize"] = "minimize"
    name: str = "portfolio"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        assets: Sequence[Asset],
        objectives: Sequence[FinanceObjective],
        constraints: Sequence[FinanceConstraint] = (),
        holding_variables: Sequence[HoldingVariable] | None = None,
        objective_sense: Literal["minimize", "maximize"] = "minimize",
        name: str = "portfolio",
        metadata: Mapping[str, Any] | None = None,
    ):
        asset_values = tuple(assets)
        objective_values = tuple(objectives)
        constraint_values = tuple(constraints)
        if holding_variables is None:
            variable_values = tuple(HoldingVariable(asset.id) for asset in asset_values)
        else:
            variable_values = tuple(holding_variables)
        object.__setattr__(self, "assets", asset_values)
        object.__setattr__(self, "objectives", objective_values)
        object.__setattr__(self, "constraints", constraint_values)
        object.__setattr__(self, "holding_variables", variable_values)
        object.__setattr__(self, "objective_sense", objective_sense)
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self, "metadata", freeze_json({} if metadata is None else dict(metadata))
        )
        self._validate()

    @property
    def asset_ids(self) -> tuple[str, ...]:
        """Stable source asset order."""
        return tuple(asset.id for asset in self.assets)

    def _validate(self) -> None:
        if not self.assets:
            raise InvalidFinanceProblemError("A portfolio problem requires at least one asset")
        if any(not isinstance(asset, Asset) for asset in self.assets):
            raise InvalidFinanceProblemError("assets must contain Asset values")
        if len(set(self.asset_ids)) != len(self.asset_ids):
            raise InvalidFinanceProblemError("Asset IDs must be unique")
        if self.objective_sense not in ("minimize", "maximize"):
            raise InvalidFinanceProblemError("objective_sense must be 'minimize' or 'maximize'")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidFinanceProblemError("Problem name must be non-empty")
        if not self.objectives:
            raise InvalidFinanceProblemError("A portfolio problem requires at least one objective")
        if any(not isinstance(item, FinanceObjective) for item in self.objectives):
            raise InvalidFinanceProblemError("All objectives must implement FinanceObjective")
        if any(item.dimension != len(self.assets) for item in self.objectives):
            raise InvalidFinanceProblemError("Objective dimensions must match the asset count")
        objective_names = [item.name for item in self.objectives]
        if len(set(objective_names)) != len(objective_names):
            raise InvalidFinanceProblemError("Objective names must be unique")
        if any(not isinstance(item, HoldingVariable) for item in self.holding_variables):
            raise InvalidFinanceProblemError(
                "holding_variables must contain HoldingVariable values"
            )
        if (
            len(self.holding_variables) != len(self.assets)
            or tuple(item.asset_id for item in self.holding_variables) != self.asset_ids
        ):
            raise InvalidFinanceProblemError(
                "Holding variables must align exactly with asset order"
            )
        if any(not isinstance(item, FinanceConstraint) for item in self.constraints):
            raise InvalidFinanceProblemError("All constraints must implement FinanceConstraint")
        constraint_names = [item.name for item in self.constraints]
        if len(set(constraint_names)) != len(constraint_names):
            raise InvalidFinanceProblemError("Constraint names must be unique")
        for constraint in self.constraints:
            constraint.validate(self.asset_ids)
        self._validate_direct_contradictions()

    def _validate_direct_contradictions(self) -> None:
        mandatory = {
            asset_id
            for constraint in self.constraints
            if isinstance(constraint, MandatoryHoldings)
            for asset_id in constraint.asset_ids
        }
        excluded = {
            asset_id
            for constraint in self.constraints
            if isinstance(constraint, ExcludedHoldings)
            for asset_id in constraint.asset_ids
        }
        overlap = mandatory & excluded
        if overlap:
            raise InvalidFinanceProblemError(
                f"Assets cannot be mandatory and excluded: {sorted(overlap)!r}"
            )
        for constraint in self.constraints:
            if isinstance(constraint, MutualExclusions):
                for left, right in constraint.pairs:
                    if left in mandatory and right in mandatory:
                        raise InvalidFinanceProblemError(
                            "Mandatory holdings contain a mutually exclusive pair"
                        )
        lower = len(mandatory)
        upper = len(self.assets) - len(excluded)
        for constraint in self.constraints:
            if isinstance(constraint, Cardinality):
                if constraint.effective_minimum is not None:
                    lower = max(lower, constraint.effective_minimum)
                if constraint.effective_maximum is not None:
                    upper = min(upper, constraint.effective_maximum)
        if lower > upper:
            raise InvalidFinanceProblemError(
                "Cardinality conflicts with mandatory or excluded holdings"
            )

    def _validate_holdings(self, holdings: Sequence[int]) -> tuple[int, ...]:
        vector = tuple(holdings)
        if len(vector) != len(self.assets) or any(value not in (0, 1) for value in vector):
            raise InvalidFinanceProblemError(f"Expected {len(self.assets)} binary holdings")
        return vector

    def evaluate(self, holdings: Sequence[int]) -> PortfolioEvaluation:
        """Evaluate every objective and return its weighted decomposition."""
        vector = self._validate_holdings(holdings)
        components = tuple(item.evaluate(vector) for item in self.objectives)
        return PortfolioEvaluation(
            self.objective_sense,
            sum(item.contribution for item in components),
            components,
        )

    def check_feasibility(self, holdings: Sequence[int]) -> FeasibilityReport:
        """Evaluate every named source constraint."""
        vector = self._validate_holdings(holdings)
        return FeasibilityReport(
            tuple(item.evaluate(vector, self.asset_ids) for item in self.constraints)
        )

    def to_dict(self) -> dict[str, JSONValue]:
        """Serialize to deterministic schema version 1 data."""
        return {
            "schema_version": 1,
            "name": self.name,
            "assets": [asset.to_dict() for asset in self.assets],
            "holding_variables": [item.to_dict() for item in self.holding_variables],
            "objective_sense": self.objective_sense,
            "objectives": [item.to_dict() for item in self.objectives],
            "constraints": [item.to_dict() for item in self.constraints],
            "metadata": thaw_json(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "StructuredPortfolioProblem":
        """Deserialize strict schema version 1 data."""
        if not isinstance(payload, Mapping):
            raise InvalidFinanceProblemError("Structured problem payload must be an object")
        expected = {
            "schema_version",
            "name",
            "assets",
            "holding_variables",
            "objective_sense",
            "objectives",
            "constraints",
            "metadata",
        }
        require_exact_fields(payload, expected, "structured portfolio problem")
        if payload["schema_version"] != 1:
            raise InvalidFinanceProblemError(
                f"Unknown schema version {payload['schema_version']!r}"
            )
        try:
            assets = [Asset.from_dict(item) for item in payload["assets"]]
            variables = [HoldingVariable.from_dict(item) for item in payload["holding_variables"]]
            objectives = [_objective_from_dict(item) for item in payload["objectives"]]
            constraints = [_constraint_from_dict(item) for item in payload["constraints"]]
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise InvalidFinanceProblemError("Malformed structured portfolio payload") from exc
        metadata = payload["metadata"]
        if not isinstance(metadata, Mapping):
            raise InvalidFinanceProblemError("Problem metadata must be an object")
        return cls(
            assets=assets,
            objectives=objectives,
            constraints=constraints,
            holding_variables=variables,
            objective_sense=payload["objective_sense"],
            name=payload["name"],
            metadata=metadata,
        )
