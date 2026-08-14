from __future__ import annotations

import json
from pathlib import Path

from ciel_geometry.phasenav.pnv_platform import PNVPlatform


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SOT_POLICY = REPO_ROOT / "provenance" / "PNV_PLATFORM_REPO_SOT_V1.json"


def _canon() -> dict:
    z = [0.0] * 36
    q = [0.0] * 36
    q[0] = 3.141592653589793
    gate_ids = [
        "PNV.GATE.VECTOR36_SHAPE",
        "PNV.GATE.HALF_STATUS",
        "PNV.GATE.RH_FIREWALL",
        "PNV.GATE.M8_ROOT_AUTHORITY",
        "PNV.GATE.M10_RECEIPT_ONLY",
        "PNV.GATE.NO_COORDINATE_TO_M",
        "PNV.GATE.NOEMA_ONLY",
        "PNV.GATE.AUX_FRESHNESS",
    ]
    operator_ids = [
        "pnv.torus.normalize",
        "pnv.torus.delta",
        "pnv.torus.geodesic",
        "pnv.path.length_l2",
        "pnv.vector.project",
        "pnv.vector.orthogonalize",
        "pnv.path.compose",
        "pnv.path.closure_residual",
        "pnv.holonomy.eligibility",
    ]
    return {
        "status": "TEST_FIXTURE_NOT_CANON",
        "dimension": 36,
        "concepts": [
            {"id": "A", "label": "alpha"},
            {"id": "B", "label": "beta"},
        ],
        "words": [
            {"word": "alpha", "concept_id": "A"},
            {"word": "beta", "concept_id": "B"},
        ],
        "vectors": {
            "A": {"phase36": z},
            "B": {"phase36": q},
        },
        "relations": [{"from": "A", "to": "B", "kind": "TEST_TYPED"}],
        "paths": [{
            "path_id": "PATH_A_TO_B",
            "from": "A",
            "to": "B",
            "tangent36_turns": [0.5] + [0.0] * 35,
        }],
        "gates": [{"id": x} for x in gate_ids],
        "operators": [{"id": x} for x in operator_ids],
    }


def _platform(tmp_path: Path) -> PNVPlatform:
    canon = tmp_path / "canon.json"
    canon.write_text(json.dumps(_canon()), encoding="utf-8")
    return PNVPlatform(
        canon,
        tmp_path / "overlay.jsonl",
        tmp_path / "receipts.jsonl",
    )


def test_repository_is_declared_source_of_truth():
    policy = json.loads(REPO_SOT_POLICY.read_text(encoding="utf-8"))
    assert policy["source_of_truth"] == "GITHUB_REPOSITORY"
    assert policy["repository"] == "AdrianLipa90/noema-phasenav-core"
    assert policy["library_role"] == "MIRROR_RECOVERY_INDEX_PROVENANCE"
    assert policy["sync_direction"]["authoritative"] == "REPO_TO_LIBRARY"
    assert policy["subscription_independence_required"] is True


def test_terminal_surface_resolve_route_path_and_gate(tmp_path):
    db = _platform(tmp_path)
    assert db.status()["dimension"] == 36
    assert db.resolve("alpha")[0]["id"] == "A"
    assert db.route("A", "B")["status"] == "FOUND"
    assert db.path("A", "B")["path_id"] == "PATH_A_TO_B"
    assert db.gate_check(
        "PNV.GATE.NOEMA_ONLY", {"promotion_source": "NOEMA_LIBRARY"}
    )["allow"] is True
    assert db.gate_check(
        "PNV.GATE.NOEMA_ONLY", {"promotion_source": "OTHER"}
    )["allow"] is False


def test_overlay_commit_is_append_only_and_hash_chained(tmp_path):
    db = _platform(tmp_path)
    dry = db.mutate(
        "ADD_ALIAS",
        {"word": "aleph", "concept_id": "A"},
        commit=False,
    )
    assert dry["mode"] == "DRY_RUN"
    assert dry["allow"] is True
    assert not db.overlay_path.exists()

    first = db.mutate(
        "ADD_ALIAS",
        {"word": "aleph", "concept_id": "A"},
        commit=True,
    )
    second = db.mutate(
        "ADD_ALIAS",
        {"word": "first", "concept_id": "A"},
        commit=True,
    )
    assert first["result"] == "COMMITTED"
    assert second["result"] == "COMMITTED"
    assert second["event"]["prev_event_sha256"] == first["event"]["event_sha256"]
    assert second["receipt"]["prev_receipt_sha256"] == first["receipt"]["receipt_sha256"]
    assert db.verify_journal() == {"status": "PASS", "issues": []}
    assert db.resolve("aleph")[0]["id"] == "A"


def test_deep_doctor_and_36d_shape_fail_closed(tmp_path):
    db = _platform(tmp_path)
    assert db.doctor(deep=True)["status"] == "PASS"
    bad = db.gate_check("PNV.GATE.VECTOR36_SHAPE", {"vector": [0.0] * 35})
    assert bad["allow"] is False
    assert bad["reason"] == "VECTOR_SHAPE_OR_FINITE_FAIL"
