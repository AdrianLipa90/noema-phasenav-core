"""Unified PhaseNav concept -> executable algorithm planning.

The planner reads the algorithm bindings already attached to concept cards.  It
returns a deterministic plan only; it never imports or invokes the referenced
callables.  Current-local/native and CANONICAL_V15 bindings are eligible by
default. Legacy executable sources and WRITE bindings require explicit opt-in.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .cards import card_by_id


CONCEPT_EXECUTION_PLAN_VERSION = "0.13.0"


@dataclass(frozen=True)
class PlannedAlgorithm:
    concept_id: str
    concept_name: str
    algorithm_id: str
    provenance_class: str
    side_effect: str
    priority: int
    binding: Mapping[str, object]

    @property
    def write_capable(self) -> bool:
        return self.side_effect == "WRITE"

    @property
    def legacy(self) -> bool:
        return self.provenance_class.startswith("LEGACY_")


_DEFAULT_PROVENANCE = {
    "LOCAL_PHASE_NAV_CURRENT",
    "PHASENAV_NATIVE_CURRENT",
    "CANONICAL_V15",
}


def _normalize_binding(concept_id: str, concept_name: str, row: Mapping[str, object]) -> PlannedAlgorithm:
    provenance = str(row.get("provenance_class") or "LOCAL_PHASE_NAV_CURRENT")
    side_effect = str(row.get("side_effect") or "PURE")
    return PlannedAlgorithm(
        concept_id=concept_id,
        concept_name=concept_name,
        algorithm_id=str(row["concept_algorithm_id"]),
        provenance_class=provenance,
        side_effect=side_effect,
        priority=int(row.get("priority") or 0),
        binding=dict(row),
    )


def execution_plan_for_concept(
    concept_id: str | int,
    *,
    include_legacy: bool = False,
    include_writes: bool = False,
) -> tuple[PlannedAlgorithm, ...]:
    """Build a deterministic, fail-closed execution plan for one concept.

    This function performs no algorithm execution.  Its default policy permits
    local PhaseNav algorithms, current native PhaseNav bindings and canonical V15
    CIEL bindings.  Legacy source bindings and WRITE-capable algorithms are
    excluded unless the corresponding flag is explicitly enabled.
    """
    key = str(concept_id).zfill(3)
    card = card_by_id(key)
    plan: list[PlannedAlgorithm] = []
    for row in card.get("algorithm_bindings", ()):
        item = _normalize_binding(key, str(card["canonical_name"]), row)
        if item.provenance_class not in _DEFAULT_PROVENANCE and not (
            include_legacy and item.legacy
        ):
            continue
        if item.write_capable and not include_writes:
            continue
        plan.append(item)
    plan.sort(key=lambda item: (
        0 if item.provenance_class == "LOCAL_PHASE_NAV_CURRENT" else
        1 if item.provenance_class == "PHASENAV_NATIVE_CURRENT" else
        2 if item.provenance_class == "CANONICAL_V15" else 3,
        item.priority,
        item.algorithm_id,
    ))
    return tuple(plan)


def concept_execution_summary(concept_id: str | int) -> dict[str, object]:
    key = str(concept_id).zfill(3)
    card = card_by_id(key)
    all_rows = tuple(
        _normalize_binding(key, str(card["canonical_name"]), row)
        for row in card.get("algorithm_bindings", ())
    )
    default = execution_plan_for_concept(key)
    return {
        "schema": "phasenav.concept-execution-plan/v0.13",
        "version": CONCEPT_EXECUTION_PLAN_VERSION,
        "concept_id": key,
        "concept_name": card["canonical_name"],
        "mapped_algorithm_count": len(all_rows),
        "default_plan_count": len(default),
        "write_binding_count": sum(item.write_capable for item in all_rows),
        "legacy_binding_count": sum(item.legacy for item in all_rows),
        "default_policy": {
            "local_current": True,
            "native_current": True,
            "canonical_v15": True,
            "legacy": False,
            "writes": False,
            "auto_execute": False,
        },
        "default_algorithm_ids": [item.algorithm_id for item in default],
    }
