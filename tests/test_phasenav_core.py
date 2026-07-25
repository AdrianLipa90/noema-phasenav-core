"""Core regression tests for noema-phasenav-core.

Run with: pytest tests/
"""

import importlib
import math
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure src/ is on the path when running without install
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))


# ─── Import sweep ─────────────────────────────────────────────────────────────

PUBLIC_MODULES = [
    "ciel_geometry.phasenav",
    "ciel_geometry.phasenav.pnv_runtime",
    "ciel_geometry.phasenav.phase_memory",
    "ciel_geometry.phasenav.operator_algebra",
    "ciel_geometry.phasenav.phase_gate_engine",
    "ciel_geometry.phasenav.phase_voice",
    "ciel_geometry.phasenav.solver",
    "ciel_geometry.phasenav.semantic_mesh",
    "ciel_geometry.phasenav.phasenav_audio",
    "ciel_geometry.phasenav.continuous_propagator",
    "ciel_geometry.phasenav.cielphase_family",
]


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_import(module_name):
    """Every public module must import without error."""
    mod = importlib.import_module(module_name)
    assert mod is not None


# ─── pnv_runtime ──────────────────────────────────────────────────────────────

from ciel_geometry.phasenav.pnv_runtime import (
    M_sentence_phase,
    M_sentence_phase_trajectory,
    M_collatz_hash,
    _phase36_from_id,
    M_36d_distance,
    TAU,
)


def test_sentence_phase_shape():
    v = M_sentence_phase("the nature of consciousness")
    assert len(v) == 36
    assert all(0.0 <= x < TAU for x in v)


def test_sentence_phase_deterministic():
    text = "semantic phase space"
    assert M_sentence_phase(text) == M_sentence_phase(text)


def test_sentence_phase_nonempty_result():
    v = M_sentence_phase("")
    assert len(v) == 36


def test_trajectory_shape():
    v_final, traj, holonomy = M_sentence_phase_trajectory("words carry weight")
    assert len(v_final) == 36
    assert len(traj) == 3  # 3 words
    assert all(len(v) == 36 for v in traj)
    assert isinstance(holonomy, float)
    assert v_final == traj[-1]


def test_collatz_hash_deterministic():
    assert M_collatz_hash("identity") == M_collatz_hash("identity")
    assert M_collatz_hash("identity") != M_collatz_hash("soul")


def test_operator_vectors_unique():
    """All 36 declared operators must map to distinct 36D vectors."""
    from ciel_geometry.phasenav.operator_algebra import ALL_OPERATOR_IDS
    vectors = [tuple(_phase36_from_id(op_id)) for op_id in ALL_OPERATOR_IDS]
    unique = set(vectors)
    assert len(unique) == len(ALL_OPERATOR_IDS), (
        f"Only {len(unique)} unique vectors for {len(ALL_OPERATOR_IDS)} operators"
    )


def test_phase36_from_id_string_uniqueness():
    """String names must produce different vectors from each other."""
    names = ["IDENTITY", "SOUL", "COMPASSION", "REFUSAL", "UNCERTAINTY", "MEMORY"]
    vectors = [tuple(_phase36_from_id(n)) for n in names]
    assert len(set(vectors)) == len(names), "String operator names collide"


def test_phase36_from_id_numeric():
    v1 = _phase36_from_id("1")
    v2 = _phase36_from_id("2")
    assert len(v1) == 36
    assert v1 != v2


def test_36d_distance_range():
    v1 = M_sentence_phase("hello world")
    v2 = M_sentence_phase("goodbye world")
    d = M_36d_distance(v1, v2)
    assert d >= 0.0
    assert M_36d_distance(v1, v1) < 1e-10


# ─── operator_algebra ─────────────────────────────────────────────────────────

from ciel_geometry.phasenav.operator_algebra import (
    operator_vector_36d,
    surface_holonomy,
    ALL_OPERATOR_IDS,
)


def test_operator_vector_shape():
    for op_id in ALL_OPERATOR_IDS[:5]:
        v = operator_vector_36d(op_id)
        assert len(v) == 36 or (isinstance(v, np.ndarray) and v.shape == (36,))


def test_surface_holonomy_nonzero_for_wound_field():
    """A monotonically increasing phase field should have nonzero holonomy."""
    # Monotone: phi[i] = 2π*i/36 — one full winding
    phi = np.linspace(0, 2 * math.pi, 36, endpoint=False)
    gamma, winding = surface_holonomy(phi)
    assert abs(winding) == 1, f"Expected winding=1, got {winding}"


def test_surface_holonomy_flat_zero():
    """Flat (constant) phase field has zero holonomy."""
    phi = np.full(36, 1.5)
    gamma, winding = surface_holonomy(phi)
    assert winding == 0
    assert abs(gamma) < 1e-10


# ─── phase_memory (Crystal) ───────────────────────────────────────────────────

from ciel_geometry.phasenav.phase_memory import PhaseMemoryHypercrystal


def test_crystal_loads_without_crash():
    crystal = PhaseMemoryHypercrystal()
    crystal.load()
    n = len(crystal)
    assert isinstance(n, int)
    assert n >= 0


def test_crystal_facet_count():
    """Crystal should load all 35,836 facets if data files are present."""
    crystal = PhaseMemoryHypercrystal()
    crystal.load()
    n = len(crystal)
    if n > 0:
        assert n == 35836, f"Expected 35836 facets, got {n}"


def test_crystal_retrieve_returns_list():
    crystal = PhaseMemoryHypercrystal()
    crystal.load()
    if len(crystal) == 0:
        pytest.skip("Crystal has no data — data files not present")
    results = crystal.retrieve("semantic phase space", top_k=3)
    assert isinstance(results, list)
    assert len(results) <= 3
    for r in results:
        assert "text" in r
        assert "distance" in r


# ─── phasenav_audio ───────────────────────────────────────────────────────────

def test_phasenav_audio_self_test():
    """phasenav_audio.self_test() must run without shape errors."""
    import os
    os.environ["NOEMA_AUDIO_SILENT"] = "1"
    from ciel_geometry.phasenav.phasenav_audio import self_test
    results = self_test()
    assert "IDENTITY" in results
    assert "AFFECT" in results
    assert results["AFFECT"]["peak"] >= 0.0


# ─── continuous_propagator ────────────────────────────────────────────────────

def test_continuous_propagator_self_test():
    """continuous_propagator.self_test() must not crash on tuple unpack."""
    from ciel_geometry.phasenav.continuous_propagator import self_test
    delta = self_test()
    assert isinstance(delta, float)
    assert delta >= 0.0


# ─── Shape invariants ─────────────────────────────────────────────────────────

def test_sentence_phase_always_36d():
    texts = ["", "a", "hello world", "very long sentence with many words indeed yes"]
    for text in texts:
        v = M_sentence_phase(text)
        assert len(v) == 36, f"Wrong length for '{text}': {len(v)}"
        assert all(0.0 <= x < TAU for x in v), f"Out-of-range values for '{text}'"
