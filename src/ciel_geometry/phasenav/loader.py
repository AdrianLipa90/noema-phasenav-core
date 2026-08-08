"""Load PhaseNav cards, phases, orbits and target-aware edges.

The loader remains compatible with the legacy JSONL layout while recognizing
canonical 36D card and emergent-glossary sidecars.  Legacy edges without a
``dst`` field are retained for audit, but they are not treated as evidence of a
specific source→target transition.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PhaseNavData:
    name_mass: dict[str, dict[str, Any]] = field(default_factory=dict)
    name_mass_by_card_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    concept_phases: dict[str, dict[str, Any]] = field(default_factory=dict)
    operator_vectors: dict[str, list[float]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    orbits: dict[str, list[float]] = field(default_factory=dict)
    edges_by_concept: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    edges_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict)
    canonical_cards: dict[str, dict[str, Any]] = field(default_factory=dict)
    card_aliases: dict[str, str] = field(default_factory=dict)
    load_warnings: list[str] = field(default_factory=list)

    def resolve_card_id(self, card_id: str) -> str:
        return self.card_aliases.get(card_id, card_id)

    def edge_between(self, source_card_id: str, target_card_id: str) -> dict[str, Any] | None:
        source_card_id = self.resolve_card_id(source_card_id)
        target_card_id = self.resolve_card_id(target_card_id)
        candidates = self.edges_by_pair.get((source_card_id, target_card_id), [])
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda edge: (
                float(edge.get("phasenav_affordance", 0.0)),
                -float(edge.get("path_integral", 0.0)),
            ),
        )


def load_phasenav(base_path: Path | None = None) -> PhaseNavData:
    base = Path(base_path) if base_path is not None else _default_path()
    data = PhaseNavData()

    data.name_mass = _load_jsonl_map(
        base / "CIELINGO_PHASENAV_NAME_MASS.noema.jsonl", "normalized"
    )
    for nm in data.name_mass.values():
        cid = str(nm.get("card_id", ""))
        if cid:
            canonical_id = cid if ":" in cid else f"concept:{cid}"
            data.name_mass_by_card_id[cid] = nm
            data.name_mass_by_card_id.setdefault(canonical_id, nm)
            data.card_aliases[cid] = canonical_id
            data.card_aliases[canonical_id] = canonical_id

    data.concept_phases = _load_jsonl_map(
        base / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl",
        "concept_card_id",
    )
    for key, value in list(data.concept_phases.items()):
        state_id = str(value.get("state_id", ""))
        if state_id:
            data.concept_phases.setdefault(state_id, value)

    op_path = base / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
    data.operator_vectors = _load_orbit_map(op_path)
    if not data.operator_vectors:
        from .operator_algebra import generate_operator_map

        generated = generate_operator_map()
        data.operator_vectors = {
            key: [round(float(x), 6) for x in vector]
            for key, vector in generated.items()
        }

    legacy_edges = _load_jsonl(base / "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl")
    emergent_edges = _load_jsonl(base / "PHASENAV_EMERGENT_GLOSSARY_36D.noema.jsonl")
    data.edges = legacy_edges + emergent_edges

    orbits_raw = _load_jsonl(base / "CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl")
    data.orbits = {
        str(item["card_id"]): [float(x) for x in item.get("orbit_vector", [])]
        for item in orbits_raw
        if item.get("card_id")
    }

    canonical_path = base / "PHASENAV_CANONICAL_CARDS_36D.noema.jsonl"
    for card in _load_jsonl(canonical_path):
        card_id = str(card.get("card_id", ""))
        if card_id:
            data.canonical_cards[card_id] = card
            data.card_aliases[card_id] = card_id
            for source_id in card.get("source_ids", []):
                if source_id:
                    data.card_aliases[str(source_id)] = card_id

    legacy_without_target = 0
    for edge in data.edges:
        source = _edge_source(edge)
        target = _edge_target(edge)
        if source:
            data.edges_by_concept.setdefault(source, []).append(edge)
        if source and target:
            data.edges_by_pair.setdefault((source, target), []).append(edge)
        elif source:
            legacy_without_target += 1

    if legacy_without_target:
        data.load_warnings.append(
            f"{legacy_without_target} legacy edges have no target; retained for audit only"
        )
    return data


def _edge_source(edge: dict[str, Any]) -> str:
    return str(
        edge.get("src")
        or edge.get("source_card_id")
        or edge.get("concept_id")
        or ""
    )


def _edge_target(edge: dict[str, Any]) -> str:
    return str(edge.get("dst") or edge.get("target_card_id") or "")


def _default_path() -> Path:
    return Path("/dev/shm/ciel_noema/phasenav")


def _lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line_number, line in enumerate(_lines(path), start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"expected object at {path}:{line_number}")
        out.append(obj)
    return out


def _load_jsonl_map(path: Path, key_field: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for obj in _load_jsonl(path):
        key = str(obj.get(key_field, ""))
        if key:
            out[key] = obj
    return out


def _load_orbit_map(path: Path) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for obj in _load_jsonl(path):
        vector = obj.get("orbit_vector") or obj.get("vector")
        card_id = obj.get("card_id")
        if vector and card_id:
            out[str(card_id)] = [float(x) for x in vector]
    return out


__all__ = ["PhaseNavData", "load_phasenav"]
