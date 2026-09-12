# This file is part of FinQIR.
#
# (C) Copyright FinQIR Contributors 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.

"""Strict adapter for the TRUBA SSB graph inputs used by the hackathon."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from finqir.applications.optimization import ConflictGraphPortfolio
from finqir.exceptions import InvalidFinanceProblemError
from finqir.mappings import ConstraintHandling, ConstraintPolicy

from .baselines import solve_conflict_graph_classically


@dataclass(frozen=True)
class TrubaInstance:
    """Validated contest identifiers, finance application, policy, and provenance."""

    question_id: int
    case_id: int
    application: ConflictGraphPortfolio
    constraint_policy: ConstraintPolicy
    source_sha256: str
    source_path: str


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidFinanceProblemError(f"{label} must be an integer")
    return value


def _indices(value: Any, count: int, label: str) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise InvalidFinanceProblemError(f"{label} must be a list")
    result = tuple(_integer(item, label) for item in value)
    if len(set(result)) != len(result) or any(item < 0 or item >= count for item in result):
        raise InvalidFinanceProblemError(f"{label} contains duplicate or out-of-range indices")
    return result


def _pairs(value: Any, count: int, label: str) -> tuple[tuple[int, int], ...]:
    if not isinstance(value, list):
        raise InvalidFinanceProblemError(f"{label} must be a list")
    pairs: list[tuple[int, int]] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise InvalidFinanceProblemError(f"{label} entries must be two-index lists")
        left, right = (_integer(part, label) for part in item)
        if left < 0 or right < 0 or left >= count or right >= count or left == right:
            raise InvalidFinanceProblemError(f"{label} contains an invalid pair")
        pairs.append((min(left, right), max(left, right)))
    if len(set(pairs)) != len(pairs):
        raise InvalidFinanceProblemError(f"{label} contains duplicate pairs")
    return tuple(pairs)


def load_truba_instance(path: str | Path) -> TrubaInstance:
    """Load one official-shape JSON input into ``ConflictGraphPortfolio``."""
    source_path = Path(path)
    try:
        raw = source_path.read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidFinanceProblemError(f"Could not load TRUBA input {source_path}") from exc
    if not isinstance(payload, Mapping):
        raise InvalidFinanceProblemError("TRUBA input must be a JSON object")
    question_id = _integer(payload.get("question_id"), "question_id")
    case_id = _integer(payload.get("case_id"), "case_id")
    if question_id not in (1, 2, 3, 4):
        raise InvalidFinanceProblemError("question_id must be between 1 and 4")
    required_fields = {"question_id", "case_id", "cizge"}
    if question_id == 2:
        required_fields.add("zorunlu_dugumler")
    if question_id in (3, 4):
        required_fields.add("yasak_ikililer")
    if set(payload) != required_fields:
        raise InvalidFinanceProblemError(
            f"Question {question_id} requires exactly fields {sorted(required_fields)!r}"
        )

    matrix = payload["cizge"]
    if not isinstance(matrix, list) or not matrix:
        raise InvalidFinanceProblemError("cizge must be a non-empty adjacency matrix")
    count = len(matrix)
    for row_index, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != count:
            raise InvalidFinanceProblemError("cizge must be square")
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or value not in (0, 1):
                raise InvalidFinanceProblemError("cizge values must be zero or one")
            if row_index == column_index and value != 0:
                raise InvalidFinanceProblemError("cizge diagonal must be zero")
            if not isinstance(matrix[column_index], list) or len(matrix[column_index]) != count:
                raise InvalidFinanceProblemError("cizge must be square")
            if matrix[column_index][row_index] != value:
                raise InvalidFinanceProblemError("cizge must be symmetric")

    vertices = tuple(str(index) for index in range(count))
    edges = tuple(
        (str(row), str(column))
        for row in range(count)
        for column in range(row + 1, count)
        if matrix[row][column] == 1
    )
    mandatory_indices = (
        _indices(payload["zorunlu_dugumler"], count, "zorunlu_dugumler") if question_id == 2 else ()
    )
    forbidden_indices = (
        _pairs(payload["yasak_ikililer"], count, "yasak_ikililer") if question_id in (3, 4) else ()
    )
    application = ConflictGraphPortfolio(
        vertices,
        edges,
        mandatory=[str(index) for index in mandatory_indices],
        additional_conflicts=[(str(left), str(right)) for left, right in forbidden_indices],
        name=f"truba_q{question_id}_case{case_id}",
    )
    overrides = (
        {"additional_conflicts": ConstraintHandling.FEASIBLE_SUBSPACE} if question_id == 4 else {}
    )
    return TrubaInstance(
        question_id=question_id,
        case_id=case_id,
        application=application,
        constraint_policy=ConstraintPolicy(overrides=overrides),
        source_sha256=hashlib.sha256(raw).hexdigest(),
        source_path=str(source_path.resolve()),
    )


def _validate_directory(input_directory: Path) -> int:
    paths = sorted(input_directory.glob("soru[1-4]_girdi*.json"))
    if not paths:
        raise InvalidFinanceProblemError(f"No TRUBA input files found in {input_directory}")
    for path in paths:
        instance = load_truba_instance(path)
        result = solve_conflict_graph_classically(instance.application)
        print(
            json.dumps(
                {
                    "file": path.name,
                    "question_id": instance.question_id,
                    "case_id": instance.case_id,
                    "vertices": len(instance.application.vertices),
                    "graph_edges": len(instance.application.edges),
                    "additional_conflicts": len(instance.application.additional_conflicts),
                    "optimum": result.objective_value,
                    "selected": list(result.selected_assets),
                    "source_sha256": instance.source_sha256,
                },
                sort_keys=True,
            )
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the TRUBA validation command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate and solve an input directory")
    validate.add_argument("--input-dir", required=True, type=Path)
    arguments = parser.parse_args(argv)
    if arguments.command == "validate":
        return _validate_directory(arguments.input_dir)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
