"""Load PhaseNav data — concept cards, phases, orbits, edges.

Supports both JSONL files and direct in-memory loading.
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


def load_phasenav(base_path: Path | None = None) -> PhaseNavData:
    base = base_path or _default_path()
    data = PhaseNavData()

    data.name_mass = _load_jsonl_map(base / "CIELINGO_PHASENAV_NAME_MASS.noema.jsonl", "normalized")
    for nm in data.name_mass.values():
        cid = nm.get("card_id", "")
        if cid:
            data.name_mass_by_card_id[cid] = nm

    data.concept_phases = _load_jsonl_map(base / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl", "concept_card_id")
    op_path = base / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
    data.operator_vectors = _load_orbit_map(op_path)
    if not data.operator_vectors:
        from .operator_algebra import generate_operator_map
        gen = generate_operator_map()
        data.operator_vectors = {k: [round(float(x), 6) for x in v] for k, v in gen.items()}

    edges_raw = _lines(base / "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl")
    data.edges = [json.loads(line) for line in edges_raw]

    orbits_raw = _lines(base / "CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl")
    data.orbits = {o["card_id"]: [float(x) for x in o.get("orbit_vector", [])] for o in (json.loads(l) for l in orbits_raw)}

    for e in data.edges:
        cid = e.get("concept_id", "")
        if cid:
            data.edges_by_concept.setdefault(cid, []).append(e)

    return data


def _default_path() -> Path:
    return Path("/dev/shm/ciel_noema/phasenav")


def _lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _load_jsonl_map(path: Path, key_field: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for line in _lines(path):
        obj = json.loads(line)
        out[str(obj.get(key_field, ""))] = obj
    return out


def _load_orbit_map(path: Path) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for line in _lines(path):
        obj = json.loads(line)
        vec = obj.get("orbit_vector") or obj.get("vector")
        if vec:
            out[obj["card_id"]] = [float(x) for x in vec]
    return out
