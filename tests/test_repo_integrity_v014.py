from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from ciel_geometry.phasenav.artifact_registry import (
    build_canonical_runtime_bundle,
    validate_runtime_directory,
    write_runtime_artifacts,
)
from ciel_geometry.phasenav.canon.cards import load_canonical_cards
from ciel_geometry.phasenav.loader import load_phasenav
from ciel_geometry.phasenav.runtime_integrity import runtime_integrity_receipt
from ciel_geometry.phasenav.solver import ORBIT_DIMS, PhaseNavSolver


def test_canonical_runtime_bundle_is_full_and_36d():
    cards = load_canonical_cards()
    bundle = build_canonical_runtime_bundle()
    assert len(cards) >= 120
    assert bundle.count("concept_phases") == len(cards)
    assert bundle.count("orbit_vectors") == len(cards)
    assert bundle.count("operator_vectors") > 0
    assert bundle.count("holonomic_edges") > 0
    for row in bundle.records["orbit_vectors"]:
        assert len(row["orbit_vector"]) == 36
        assert all(math.isfinite(float(x)) for x in row["orbit_vector"])
    for row in bundle.records["operator_vectors"]:
        assert len(row["vector_36d"]) == 36
        assert all(math.isfinite(float(x)) for x in row["vector_36d"])


def test_runtime_materialization_never_writes_empty_tables(tmp_path: Path):
    paths = write_runtime_artifacts(tmp_path)
    assert paths
    report = validate_runtime_directory(tmp_path)
    assert report["ok"], report
    for filename, entry in report["files"].items():
        if "HOLONOMIC_EDGES" not in filename:
            assert entry["records"] > 0


def test_empty_runtime_directory_falls_back_to_canonical_registry(tmp_path: Path):
    data = load_phasenav(tmp_path)
    cards = load_canonical_cards()
    assert len(data.orbits) == len(cards)
    assert len(data.operator_vectors) > 0
    assert data.artifact_source.startswith("CANONICAL_FALLBACK")
    assert data.load_warnings


def test_solver_orbit_contract_is_36d_not_legacy_11d(tmp_path: Path):
    solver = PhaseNavSolver.load(tmp_path)
    orbit = solver.get_orbit("001")
    assert len(ORBIT_DIMS) == 36
    assert len(orbit) == 36
    assert np.all(np.isfinite(np.asarray(orbit, dtype=float)))


def test_runtime_compatibility_populates_pnv_glossary():
    from ciel_geometry.phasenav import pnv_runtime

    receipt = runtime_integrity_receipt()
    glossary = pnv_runtime._load_glossary()
    assert receipt["status"] == "ACTIVE"
    assert receipt["silent_empty_fallback"] is False
    assert len(glossary) >= 120
    assert pnv_runtime.ALL_STATE_IDS
    assert all(len(entry["v36"]) == 36 for entry in glossary.values())


def test_crystal_data_is_present_and_dimensionally_consistent():
    from ciel_geometry.phasenav.phase_memory import CRYSTAL_META_PATH, CRYSTAL_VEC_PATH

    arr = np.load(CRYSTAL_VEC_PATH, mmap_mode="r")
    metadata_count = sum(1 for line in Path(CRYSTAL_META_PATH).open(encoding="utf-8") if line.strip())
    assert arr.ndim == 2
    assert arr.shape[1] == 36
    assert arr.shape[0] >= 34770
    assert metadata_count == arr.shape[0]


def test_placeholder_top_level_directories_are_executable_surfaces():
    root = Path(__file__).resolve().parents[1]
    expected = {
        "concept_phases": {"README.md", "__init__.py", "catalog.py", "export.py"},
        "orbit_vectors": {"README.md", "__init__.py", "catalog.py", "export.py"},
        "kuramoto": {"README.md", "__init__.py", "synchronizer.py", "diagnostics.py"},
        "solver": {"README.md", "__init__.py", "runtime.py", "cli.py"},
        "encryption": {"README.md", "__init__.py", "runtime.py", "validation.py"},
    }
    for dirname, files in expected.items():
        present = {p.name for p in (root / dirname).iterdir()}
        assert files <= present, (dirname, files - present)
