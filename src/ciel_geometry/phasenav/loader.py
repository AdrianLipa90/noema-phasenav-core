"""Load PhaseNav cards, phases, operators, orbits and target-aware edges.

v0.14 integrity behavior:
- legacy runtime JSONL is still accepted;
- missing or empty required runtime tables fall back to the canonical card registry;
- every operator/orbit vector is validated as finite 36D;
- malformed JSONL raises instead of being silently ignored;
- canonical cards are always available in-memory even when sidecars are absent.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .artifact_registry import (
    ArtifactIntegrityError,
    build_canonical_runtime_bundle,
)
from .runtime_integrity import install_runtime_compat

VECTOR_DIM = 36
_RUNTIME_COMPAT_RECEIPT = install_runtime_compat(materialize_active_host=False)


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
    artifact_source: str = "runtime"

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


def _default_path() -> Path:
    return Path("/dev/shm/ciel_noema/phasenav")


def _validate_vector36(value: Any, *, label: str) -> list[float]:
    try:
        vector = [float(x) for x in value]
    except (TypeError, ValueError) as exc:
        raise ArtifactIntegrityError(f"{label}: vector is not numeric") from exc
    if len(vector) != VECTOR_DIM:
        raise ArtifactIntegrityError(
            f"{label}: expected {VECTOR_DIM} coordinates, got {len(vector)}"
        )
    if not all(math.isfinite(x) for x in vector):
        raise ArtifactIntegrityError(f"{label}: non-finite coordinate")
    return vector


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
            raise ArtifactIntegrityError(
                f"invalid JSONL at {path}:{line_number}: {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise ArtifactIntegrityError(f"expected object at {path}:{line_number}")
        out.append(obj)
    return out


def _runtime_or_fallback(
    path: Path,
    fallback: list[dict[str, Any]],
    *,
    label: str,
    warnings: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    rows = _load_jsonl(path)
    if rows:
        return rows, False
    warnings.append(
        f"{label}: runtime file missing/empty at {path}; using canonical registry fallback"
    )
    if not fallback:
        raise ArtifactIntegrityError(f"{label}: runtime and canonical fallback are both empty")
    return list(fallback), True


def _load_jsonl_map(rows: list[dict[str, Any]], key_field: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for obj in rows:
        key = str(obj.get(key_field, ""))
        if key:
            out[key] = obj
    return out


def _load_vector_map(
    rows: list[dict[str, Any]],
    *,
    id_fields: tuple[str, ...],
    vector_fields: tuple[str, ...],
    label: str,
) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for index, obj in enumerate(rows):
        card_id = ""
        for field_name in id_fields:
            if obj.get(field_name):
                card_id = str(obj[field_name])
                break
        raw = None
        for field_name in vector_fields:
            if obj.get(field_name) is not None:
                raw = obj[field_name]
                break
        if not card_id or raw is None:
            continue
        out[card_id] = _validate_vector36(raw, label=f"{label}[{index}]/{card_id}")
    if not out:
        raise ArtifactIntegrityError(f"{label}: zero usable 36D vectors")
    return out


def load_phasenav(base_path: Path | None = None) -> PhaseNavData:
    install_runtime_compat(materialize_active_host=False)
    base = Path(base_path) if base_path is not None else _default_path()
    bundle = build_canonical_runtime_bundle()
    data = PhaseNavData()
    used_fallback = False

    name_rows, fell_back = _runtime_or_fallback(
        base / "CIELINGO_PHASENAV_NAME_MASS.noema.jsonl",
        bundle.records["name_mass"],
        label="name_mass",
        warnings=data.load_warnings,
    )
    used_fallback |= fell_back
    data.name_mass = _load_jsonl_map(name_rows, "normalized")
    if not data.name_mass:
        raise ArtifactIntegrityError("name_mass resolved to zero records")

    for nm in data.name_mass.values():
        cid = str(nm.get("card_id", ""))
        if cid:
            canonical_id = cid if ":" in cid else f"concept:{cid}"
            data.name_mass_by_card_id[cid] = nm
            data.name_mass_by_card_id.setdefault(canonical_id, nm)
            data.card_aliases[cid] = canonical_id
            data.card_aliases[canonical_id] = canonical_id

    concept_rows, fell_back = _runtime_or_fallback(
        base / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl",
        bundle.records["concept_phases"],
        label="concept_phases",
        warnings=data.load_warnings,
    )
    used_fallback |= fell_back
    data.concept_phases = _load_jsonl_map(concept_rows, "concept_card_id")
    for key, value in list(data.concept_phases.items()):
        state_id = str(value.get("state_id", ""))
        if state_id:
            data.concept_phases.setdefault(state_id, value)
            data.card_aliases.setdefault(state_id, f"concept:{state_id}")
            data.card_aliases.setdefault(f"concept:{state_id}", f"concept:{state_id}")

    operator_rows, fell_back = _runtime_or_fallback(
        base / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl",
        bundle.records["operator_vectors"],
        label="operator_vectors",
        warnings=data.load_warnings,
    )
    used_fallback |= fell_back
    data.operator_vectors = _load_vector_map(
        operator_rows,
        id_fields=("operator_id", "operator_name", "card_id"),
        vector_fields=("vector_36d", "phase_vector_36d", "orbit_vector", "vector"),
        label="operator_vectors",
    )

    edge_rows, fell_back = _runtime_or_fallback(
        base / "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl",
        bundle.records["holonomic_edges"],
        label="holonomic_edges",
        warnings=data.load_warnings,
    )
    used_fallback |= fell_back
    emergent_rows = _load_jsonl(base / "PHASENAV_EMERGENT_GLOSSARY_36D.noema.jsonl")
    data.edges = edge_rows + emergent_rows

    orbit_rows, fell_back = _runtime_or_fallback(
        base / "CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl",
        bundle.records["orbit_vectors"],
        label="orbit_vectors",
        warnings=data.load_warnings,
    )
    used_fallback |= fell_back
    data.orbits = _load_vector_map(
        orbit_rows,
        id_fields=("card_id", "state_id"),
        vector_fields=("phase_vector_36d", "vector_36d", "orbit_vector"),
        label="orbit_vectors",
    )

    from .canon.cards import load_canonical_cards

    for card in load_canonical_cards():
        gid = str(card["glossary_id"])
        card_id = str(card["card_id"])
        data.canonical_cards[card_id] = card
        data.card_aliases[gid] = f"concept:{gid}"
        data.card_aliases[f"concept:{gid}"] = f"concept:{gid}"
        data.card_aliases[card_id] = card_id

    canonical_path = base / "PHASENAV_CANONICAL_CARDS_36D.noema.jsonl"
    for card in _load_jsonl(canonical_path):
        card_id = str(card.get("card_id", ""))
        if card_id:
            data.canonical_cards.setdefault(card_id, card)
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

    data.artifact_source = (
        "CANONICAL_FALLBACK+RUNTIME" if used_fallback else "RUNTIME_VALIDATED"
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


__all__ = ["ArtifactIntegrityError", "PhaseNavData", "load_phasenav"]
