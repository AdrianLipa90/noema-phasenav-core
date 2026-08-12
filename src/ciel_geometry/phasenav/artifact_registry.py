"""Fail-closed PhaseNav runtime artifact registry.

This module materializes the canonical card registry into the legacy JSONL surface
without depending on historical glossary.pnv files. Every phase/orbit/operator
vector is validated as finite 36D before it is exposed or written.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Iterable

VECTOR_DIM = 36

RUNTIME_FILENAMES = {
    "name_mass": "CIELINGO_PHASENAV_NAME_MASS.noema.jsonl",
    "concept_phases": "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl",
    "operator_vectors": "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl",
    "holonomic_edges": "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl",
    "orbit_vectors": "CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl",
}
MANIFEST_FILENAME = "PHASENAV_RUNTIME_ARTIFACT_MANIFEST.json"


class ArtifactIntegrityError(RuntimeError):
    """Raised when a required PhaseNav artifact is empty, malformed or non-36D."""


@dataclass(frozen=True)
class ArtifactBundle:
    records: dict[str, list[dict[str, Any]]]
    source: str = "CANONICAL_CARD_REGISTRY"

    def count(self, key: str) -> int:
        return len(self.records[key])

    def manifest(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": "phasenav.runtime-artifacts/v2",
            "vector_dim": VECTOR_DIM,
            "source": self.source,
            "files": {},
        }
        for key, filename in RUNTIME_FILENAMES.items():
            lines = [
                json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                for record in self.records[key]
            ]
            data = ("\n".join(lines) + "\n").encode("utf-8")
            payload["files"][filename] = {
                "records": len(lines),
                "sha256": sha256(data).hexdigest(),
                "nonempty": bool(lines),
            }
        return payload


def _finite_vector36(value: Iterable[Any], *, label: str) -> list[float]:
    vector = [float(x) for x in value]
    if len(vector) != VECTOR_DIM:
        raise ArtifactIntegrityError(
            f"{label}: expected {VECTOR_DIM} coordinates, got {len(vector)}"
        )
    if not all(math.isfinite(x) for x in vector):
        raise ArtifactIntegrityError(f"{label}: non-finite coordinate")
    return vector


def canonical_glossary() -> dict[str, dict[str, Any]]:
    """Return a glossary-compatible mapping backed by the current canonical cards."""
    from .canon.cards import load_canonical_cards

    cards = load_canonical_cards()
    if not cards:
        raise ArtifactIntegrityError("canonical card registry is empty")

    glossary: dict[str, dict[str, Any]] = {}
    for card in cards:
        gid = str(card["glossary_id"])
        marker = card.get("phase_marker_36d", {})
        vector = _finite_vector36(marker.get("vector", ()), label=f"card {gid}")
        glossary[gid] = {
            "name": str(card.get("canonical_name", gid)),
            "operator": str(card.get("operator", "ORBIT")),
            "type": str(card.get("type", "operator")),
            "epistemic": dict(card.get("epistemic", {})),
            "v36": vector,
            "v2": [],
            "semantic_mass": float(card["semantic_mass_canon"]),
        }
    return glossary


def _edge_records(card: dict[str, Any]) -> list[dict[str, Any]]:
    gid = str(card["glossary_id"])
    operator = str(card.get("operator", "ORBIT"))
    op_cards = {
        "DIFFERENTIAL": "op_diff",
        "AFFECT": "op_affect",
        "ORBIT": "op_orbit",
        "IDENTITY": "op_identity",
    }
    lanes = {
        "DIFFERENTIAL": "frequency",
        "AFFECT": "phase",
        "ORBIT": "mass",
        "IDENTITY": "identity",
    }
    rows: list[dict[str, Any]] = []
    for edge in card.get("emergent_paths_canon", []):
        angular = float(edge.get("angular_distance_36d", 0.0))
        berry = float(edge.get("berry_connection", 0.0))
        edge_weight = float(edge.get("edge_weight", angular * (1.0 + abs(berry))))
        viscosity = max(0.0, angular * 0.1 + abs(berry) * 0.05)
        affordance = 1.0 / (max(edge_weight, 0.0) + 0.01)
        rows.append(
            {
                "schema": "PHASENAV_HOLONOMIC_EDGE_V2",
                "src": gid,
                "dst": str(edge["to"]),
                "concept_id": gid,
                "source_card_id": gid,
                "target_card_id": str(edge["to"]),
                "operator_card_id": op_cards.get(operator, "op_orbit"),
                "operator_hook": operator.lower(),
                "holonomic_viscosity": round(viscosity, 12),
                "phasenav_affordance": round(affordance, 12),
                "transition_lane": lanes.get(operator, "mass"),
                "path_integral": round(edge_weight, 12),
                "epistemic_status": str(edge.get("epistemic_operator", "chyba")),
                "canon_allowed": False,
            }
        )
    return rows


def build_canonical_runtime_bundle() -> ArtifactBundle:
    """Build all legacy-compatible runtime tables from canonical 36D cards."""
    from .canon.cards import load_canonical_cards
    from .operator_algebra import generate_operator_map

    cards = load_canonical_cards()
    if not cards:
        raise ArtifactIntegrityError("cannot build runtime artifacts from zero cards")

    name_mass: list[dict[str, Any]] = []
    concept_phases: list[dict[str, Any]] = []
    orbit_vectors: list[dict[str, Any]] = []
    holonomic_edges: list[dict[str, Any]] = []

    for card in cards:
        gid = str(card["glossary_id"])
        marker = card["phase_marker_36d"]
        vector = _finite_vector36(marker["vector"], label=f"orbit {gid}")
        name = str(card.get("canonical_name", gid))
        mass = float(card["semantic_mass_canon"])
        mean_phase = float(marker["mean_phase"])
        coherence = float(marker["order_parameter_R"])

        name_mass.append(
            {
                "schema": "PHASENAV_NAME_MASS_V2",
                "card_id": gid,
                "normalized": name,
                "semantic_mass": mass,
                "geometric_phase_rad": mean_phase,
                "coherence_R": coherence,
                "vector_dim": VECTOR_DIM,
                "vector_36d": vector,
            }
        )
        concept_phases.append(
            {
                "schema": "PHASENAV_CONCEPT_PHASE_V2",
                "concept_card_id": f"concept:{gid}",
                "state_id": gid,
                "name": name,
                "geometric_phase_rad": mean_phase,
                "coherence_R": coherence,
                "semantic_mass": mass,
                "vector_dim": VECTOR_DIM,
                "phase_vector_36d": vector,
            }
        )
        orbit_vectors.append(
            {
                "schema": "PHASENAV_PHASE_ORBIT_V2",
                "card_id": gid,
                "state_id": gid,
                "vector_dim": VECTOR_DIM,
                "vector_semantics": "phase_angles_radians",
                "orbit_vector": vector,
                "phase_vector_36d": vector,
            }
        )
        holonomic_edges.extend(_edge_records(card))

    operator_vectors: list[dict[str, Any]] = []
    for op_id, vector_raw in sorted(generate_operator_map().items()):
        vector = _finite_vector36(vector_raw, label=f"operator {op_id}")
        operator_vectors.append(
            {
                "schema": "PHASENAV_OPERATOR_VECTOR_V2",
                "card_id": op_id,
                "operator_id": op_id,
                "operator_name": op_id,
                "vector_dim": VECTOR_DIM,
                "vector_semantics": "phase_angles_radians",
                "vector_36d": vector,
                "orbit_vector": vector,
            }
        )

    records = {
        "name_mass": name_mass,
        "concept_phases": concept_phases,
        "operator_vectors": operator_vectors,
        "holonomic_edges": holonomic_edges,
        "orbit_vectors": orbit_vectors,
    }
    for key in ("name_mass", "concept_phases", "operator_vectors", "orbit_vectors"):
        if not records[key]:
            raise ArtifactIntegrityError(f"required runtime table {key} is empty")
    return ArtifactBundle(records=records)


def _jsonl(records: list[dict[str, Any]]) -> str:
    if not records:
        raise ArtifactIntegrityError("refusing to serialize an empty required artifact")
    return "\n".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ) + "\n"


def write_runtime_artifacts(base_path: str | Path) -> dict[str, Path]:
    """Atomically materialize a complete, validated runtime surface."""
    base = Path(base_path)
    base.mkdir(parents=True, exist_ok=True)
    bundle = build_canonical_runtime_bundle()
    written: dict[str, Path] = {}

    for key, filename in RUNTIME_FILENAMES.items():
        path = base / filename
        content = _jsonl(bundle.records[key])
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
        written[key] = path

    manifest_path = base / MANIFEST_FILENAME
    manifest = bundle.manifest()
    tmp_manifest = manifest_path.with_suffix(".tmp")
    tmp_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_manifest.replace(manifest_path)
    written["manifest"] = manifest_path
    return written


def validate_runtime_directory(base_path: str | Path) -> dict[str, Any]:
    """Validate required runtime JSONLs without silently accepting zero records."""
    base = Path(base_path)
    report: dict[str, Any] = {
        "schema": "phasenav.runtime-integrity-report/v2",
        "vector_dim": VECTOR_DIM,
        "base_path": str(base),
        "ok": True,
        "files": {},
    }
    for key, filename in RUNTIME_FILENAMES.items():
        path = base / filename
        entry = {"exists": path.exists(), "records": 0, "errors": []}
        if not path.exists():
            entry["errors"].append("missing")
        else:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                entry["records"] += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    entry["errors"].append(f"line {line_number}: {exc}")
                    continue
                if key in {"orbit_vectors", "operator_vectors"}:
                    raw = (
                        record.get("phase_vector_36d")
                        or record.get("vector_36d")
                        or record.get("orbit_vector")
                        or []
                    )
                    try:
                        _finite_vector36(raw, label=f"{filename}:{line_number}")
                    except ArtifactIntegrityError as exc:
                        entry["errors"].append(str(exc))
        if key != "holonomic_edges" and entry["records"] == 0:
            entry["errors"].append("zero_records")
        if entry["errors"]:
            report["ok"] = False
        report["files"][filename] = entry
    return report


__all__ = [
    "ArtifactBundle",
    "ArtifactIntegrityError",
    "MANIFEST_FILENAME",
    "RUNTIME_FILENAMES",
    "VECTOR_DIM",
    "build_canonical_runtime_bundle",
    "canonical_glossary",
    "validate_runtime_directory",
    "write_runtime_artifacts",
]
