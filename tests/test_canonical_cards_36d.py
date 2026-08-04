from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ciel_geometry.phasenav.canonical_cards import (
    MARKER_SCHEMA,
    CanonicalCard,
    Phase36Marker,
    canonicalize_record,
    merge_card_views,
)
from ciel_geometry.phasenav.emergent_glossary import (
    PATH_MARKER_SCHEMA,
    EmergentEdge,
    EmergentGlossary,
    weighted_torus_distance,
)
from ciel_geometry.phasenav.loader import load_phasenav
from ciel_geometry.phasenav.solver import PhaseNavSolver


def vector(offset: float) -> list[float]:
    return [float((offset + i * 0.071) % (2.0 * np.pi)) for i in range(36)]


def card(card_id: str, offset: float, label: str | None = None) -> CanonicalCard:
    return canonicalize_record(
        {
            "concept_card_id": card_id,
            "name": label or card_id,
            "type": "concept",
            "epistemic_status": "candidate",
            "canon_allowed": False,
            "v36": vector(offset),
        },
        source_kind="concept",
        source_namespace="test",
        source_index=0,
        encoding="test-v36",
    )


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def test_phase36_marker_has_exact_dimension_and_fingerprint():
    marker = Phase36Marker.from_vector(vector(0.1), encoding="test")
    assert marker.schema == MARKER_SCHEMA
    assert marker.dimension == 36
    assert len(marker.vector) == 36
    assert marker.fingerprint.startswith("p36:")
    assert marker.validate() == []


def test_missing_card_id_is_deterministic_and_not_canonized():
    record = {"name": "Recovered concept", "v36": vector(0.2)}
    first = canonicalize_record(record, source_namespace="recovery", source_index=7)
    second = canonicalize_record(record, source_namespace="recovery", source_index=7)
    assert first.card_id == second.card_id
    assert first.epistemic_status == "chyba"
    assert first.canon_allowed is False


def test_explicit_concept_id_is_preserved():
    result = card("concept:031", 0.3, "Consciousness")
    assert result.card_id == "concept:031"
    assert result.source_ids == ["concept:031"]


def test_merge_never_averages_conflicting_phase_vectors():
    first = card("concept:001", 0.1, "Resonance")
    second = card("concept:001", 1.1, "Resonance")
    merged = merge_card_views([first, second])
    assert len(merged) == 1
    assert merged[0].marker_36d.fingerprint == first.marker_36d.fingerprint
    assert merged[0].conflicts[0]["kind"] == "phase36_conflict"
    assert merged[0].epistemic_status == "chyba"
    assert merged[0].canon_allowed is False


def test_emergent_edge_is_always_chyba():
    source = card("concept:001", 0.1)
    target = card("concept:002", 0.2)
    edge = EmergentEdge.between(source, target, rank=1)
    assert edge.epistemic_status == "chyba"
    assert edge.canon_allowed is False
    assert edge.marker_36d.schema == PATH_MARKER_SCHEMA
    assert len(edge.marker_36d.delta_36d) == 36
    assert edge.to_dict()["src"] == "concept:001"
    assert edge.to_dict()["dst"] == "concept:002"


def test_weighted_distance_is_symmetric_and_zero_on_identity():
    a = vector(0.1)
    b = vector(0.7)
    assert weighted_torus_distance(a, a) < 1e-12
    assert np.isclose(weighted_torus_distance(a, b), weighted_torus_distance(b, a))


def test_emergent_glossary_build_and_trace_are_deterministic():
    cards = [
        card("concept:001", 0.0),
        card("concept:002", 0.1),
        card("concept:003", 0.2),
        card("concept:004", 0.3),
    ]
    first = EmergentGlossary(cards)
    second = EmergentGlossary(reversed(cards))
    first.build(neighbours=2)
    second.build(neighbours=2)
    assert [edge.to_dict() for edge in first.edges] == [edge.to_dict() for edge in second.edges]
    path = first.trace("concept:001", "concept:004")
    assert path is not None
    assert path.card_sequence[0] == "concept:001"
    assert path.card_sequence[-1] == "concept:004"
    assert path.epistemic_status == "chyba"
    assert path.canon_allowed is False


def test_loader_indexes_only_target_aware_pairs(tmp_path: Path):
    write_jsonl(
        tmp_path / "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl",
        [
            {"concept_id": "concept:001", "phasenav_affordance": 9.0},
            {"src": "concept:001", "dst": "concept:002", "phasenav_affordance": 0.5},
        ],
    )
    data = load_phasenav(tmp_path)
    assert len(data.edges_by_concept["concept:001"]) == 2
    assert data.edge_between("concept:001", "concept:002") is not None
    assert data.edge_between("concept:001", "concept:999") is None
    assert data.load_warnings


def test_solver_does_not_apply_targetless_edge_to_arbitrary_target(tmp_path: Path):
    write_jsonl(
        tmp_path / "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl",
        [{"concept_id": "concept:001", "phasenav_affordance": 999.0}],
    )
    solver = PhaseNavSolver.load(tmp_path)
    assert solver.trace(["concept:001", "concept:002"]).steps == []


def test_solver_uses_exact_emergent_target_and_propagates_marker(tmp_path: Path):
    source = card("concept:001", 0.1)
    target = card("concept:002", 0.2)
    glossary = EmergentGlossary([source, target])
    glossary.build(neighbours=1)
    solver = PhaseNavSolver.load(tmp_path, glossary=glossary)
    trace = solver.trace(["concept:001", "concept:002"])
    assert len(trace.steps) == 1
    step = trace.steps[0]
    assert step.target_card_id == "concept:002"
    assert step.epistemic_status == "chyba"
    assert step.canon_allowed is False
    assert step.phase36_path_marker["schema"] == PATH_MARKER_SCHEMA
    assert step.edge_source == "emergent_36d"
