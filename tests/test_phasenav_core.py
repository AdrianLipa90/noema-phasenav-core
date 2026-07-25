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
    """Crystal should have at least 34,770 facets after deduplication."""
    crystal = PhaseMemoryHypercrystal()
    crystal.load()
    n = len(crystal)
    if n > 0:
        assert n >= 34770, f"Expected >= 34770 facets (po deduplikacji), got {n}"


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

# ─── HTRI Poincare time hypercrystal ─────────────────────────────────────────

from ciel_geometry.phasenav.htri_hypercrystal import (
    HypercrystalConfig,
    build_htri_hypercrystal,
    build_intention_operator,
    build_magnetic_poincare_laplacian,
    embed_poincare_disk,
    evolve_state,
    hermiticity_error,
    load_crystal_arrays,
    localized_state,
    poincare_distance,
    schrodinger_lagrangian,
    schrodinger_velocity,
)


def _synthetic_hypercrystal_data(n: int = 24):
    x = np.arange(n, dtype=float)[:, None]
    dims = np.arange(36, dtype=float)[None, :]
    phases = (0.17 * x + 0.031 * x * dims + 0.11 * np.sin((dims + 1) * (x + 1))) % TAU
    metadata = [
        {
            "kappa_i": 0.2 + 0.01 * i,
            "t_score": 0.1 + 0.02 * np.sin(i),
            "memory_density": 0.05 + 0.001 * i,
            "text": f"facet {i}",
        }
        for i in range(n)
    ]
    return phases, metadata


def test_poincare_embedding_stays_in_open_disk():
    phases, _ = _synthetic_hypercrystal_data()
    embedding = embed_poincare_disk(phases)
    assert embedding.coordinates.shape == (len(phases),)
    assert np.all(np.abs(embedding.coordinates) < 1.0)
    assert embedding.basis.shape == (72, 2)


def test_poincare_distance_metric_basics():
    u = 0.12 + 0.08j
    v = -0.21 + 0.17j
    assert float(poincare_distance(u, u)) < 1e-12
    assert float(poincare_distance(u, v)) > 0.0
    assert np.isclose(poincare_distance(u, v), poincare_distance(v, u))


def test_magnetic_poincare_laplacian_is_hermitian():
    phases, _ = _synthetic_hypercrystal_data()
    embedding = embed_poincare_disk(phases)
    laplacian = build_magnetic_poincare_laplacian(
        phases, embedding.coordinates, neighbours=4
    )
    assert laplacian.shape == (len(phases), len(phases))
    assert hermiticity_error(laplacian) < 1e-12


def test_intention_fluctuation_operator_is_hermitian_and_centered():
    phases, _ = _synthetic_hypercrystal_data()
    intention, fluctuation, resonance, centred = build_intention_operator(
        phases, "protect life and free will"
    )
    assert hermiticity_error(intention) < 1e-12
    assert hermiticity_error(fluctuation) < 1e-12
    assert abs(float(centred.mean())) < 1e-12
    assert np.all((0.0 <= resonance) & (resonance <= 1.0))


def test_htri_hypercrystal_hamiltonian_is_hermitian():
    phases, metadata = _synthetic_hypercrystal_data()
    config = HypercrystalConfig(neighbours=4, time_slices=3)
    _, operators = build_htri_hypercrystal(
        phases, metadata, "coherent intention", config
    )
    assert operators.hamiltonian.shape == (len(phases) * 3, len(phases) * 3)
    assert hermiticity_error(operators.spatial_hamiltonian) < 1e-12
    assert hermiticity_error(operators.temporal_momentum) < 1e-12
    assert hermiticity_error(operators.temporal_hamiltonian) < 1e-12
    assert hermiticity_error(operators.hamiltonian) < 1e-12
    assert np.all(np.isfinite(operators.base_potential))


def test_hypercrystal_unitary_evolution_preserves_norm():
    phases, metadata = _synthetic_hypercrystal_data(18)
    config = HypercrystalConfig(neighbours=3, time_slices=3)
    _, operators = build_htri_hypercrystal(phases, metadata, "memory", config)
    psi = localized_state(len(phases), config.time_slices, facet_index=2)
    evolved = evolve_state(psi, operators.hamiltonian, 0.02, hbar=config.hbar)
    assert abs(np.linalg.norm(evolved) - 1.0) < 1e-10


def test_schrodinger_lagrangian_is_real_and_on_shell_zero():
    phases, metadata = _synthetic_hypercrystal_data(16)
    config = HypercrystalConfig(neighbours=3, time_slices=3)
    _, operators = build_htri_hypercrystal(phases, metadata, "return", config)
    psi = localized_state(len(phases), config.time_slices, facet_index=1)
    psi_dot = schrodinger_velocity(psi, operators.hamiltonian, hbar=config.hbar)
    value = schrodinger_lagrangian(
        psi, psi_dot, operators.hamiltonian, hbar=config.hbar
    )
    assert isinstance(value.lagrangian, float)
    assert abs(value.lagrangian) < 1e-10
    assert np.isclose(value.symplectic_term, value.energy_expectation)


def test_real_crystal_hypercrystal_smoke():
    phases, metadata = load_crystal_arrays(sample=64, seed=11)
    config = HypercrystalConfig(neighbours=3, time_slices=2)
    embedding, operators = build_htri_hypercrystal(
        phases, metadata, "HTRI time hypercrystal", config
    )
    assert phases.shape == (64, 36)
    assert np.all(np.abs(embedding.coordinates) < 1.0)
    assert operators.hamiltonian.shape == (128, 128)
    assert hermiticity_error(operators.hamiltonian) < 1e-12


# ─── CrystalTextEngine ────────────────────────────────────────────────────────

from ciel_geometry.phasenav.crystal_text_engine import (
    CrystalTextEngine,
    ConsciousnessPulse,
    ConsciousnessStream,
)


def test_crystal_text_engine_loads():
    """Engine musi załadować kryształ bez błędu."""
    engine = CrystalTextEngine(sample=32, seed=7)
    engine.load()
    assert engine._phases is not None
    assert engine._phases.shape == (32, 36)
    assert len(engine._metadata) == 32


def test_crystal_text_engine_generate_returns_stream():
    """generate() musi zwrócić ConsciousnessStream z poprawnymi impulsami."""
    from ciel_geometry.phasenav.htri_hypercrystal import HypercrystalConfig
    config = HypercrystalConfig(neighbours=3, time_slices=3)
    engine = CrystalTextEngine(config=config, sample=32, seed=3)
    engine.load()

    stream = engine.generate("awareness and time", steps=4, dt=0.3, substeps=4)

    assert isinstance(stream, ConsciousnessStream)
    assert stream.intention == "awareness and time"
    assert len(stream.pulses) == 4
    for p in stream.pulses:
        assert isinstance(p, ConsciousnessPulse)
        assert isinstance(p.text, str)
        assert isinstance(p.voice, str) and len(p.voice) > 0
        assert isinstance(p.emotion, str)
        assert isinstance(p.gate_state, dict)
        assert p.resonance >= 0.0
        assert abs(p.psi_norm - 1.0) < 1e-6
        assert len(p.phase_vector) == 36


def test_crystal_text_engine_no_repeated_facets():
    """Strumień NIE może powtarzać tego samego facetu — collapse gwarantuje różnorodność."""
    from ciel_geometry.phasenav.htri_hypercrystal import HypercrystalConfig
    config = HypercrystalConfig(neighbours=3, time_slices=3)
    engine = CrystalTextEngine(config=config, sample=40, seed=5)
    engine.load()
    stream = engine.generate("consciousness", steps=6, dt=0.3, substeps=4)
    facet_indices = [p.facet_index for p in stream.pulses]
    assert len(set(facet_indices)) == len(facet_indices), (
        f"Powtórzone facety: {facet_indices}"
    )


def test_crystal_text_engine_time_increases():
    """Czas zewnętrzny musi rosnąć monotonicznie między impulsami."""
    from ciel_geometry.phasenav.htri_hypercrystal import HypercrystalConfig
    config = HypercrystalConfig(neighbours=3, time_slices=3)
    engine = CrystalTextEngine(config=config, sample=24, seed=9)
    engine.load()
    pulses = list(engine.stream_pulses("identity", steps=4, dt=0.3, substeps=4))
    assert len(pulses) == 4
    times = [p.internal_time for p in pulses]
    assert times == sorted(times), f"Czas nie rośnie: {times}"
    assert times[0] < times[-1], "Czas stoi w miejscu"


def test_crystal_text_engine_psi_norm_preserved():
    """Norma stanu kwantowego musi być zachowana przez ewolucję + collapse (≈ 1.0)."""
    from ciel_geometry.phasenav.htri_hypercrystal import HypercrystalConfig
    config = HypercrystalConfig(neighbours=3, time_slices=3)
    engine = CrystalTextEngine(config=config, sample=20, seed=1)
    engine.load()
    stream = engine.generate("time crystal", steps=5, dt=0.3, substeps=4)
    for p in stream.pulses:
        assert abs(p.psi_norm - 1.0) < 1e-6, (
            f"Norma stanu niestabilna w kroku {p.step}: {p.psi_norm}"
        )
