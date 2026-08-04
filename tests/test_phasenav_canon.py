import math

from ciel_geometry.phasenav.canon import (
    CORPUS,
    HILBERT_DIM,
    CanonicalConceptState,
    Hilbert2048State,
    audit_orbits,
)
from ciel_geometry.phasenav.pnv_runtime import _phase36_from_id


def test_h2048_normalized_and_projected_numeric():
    state = Hilbert2048State.from_id("17")
    assert len(state.amplitudes) == HILBERT_DIM
    assert math.isclose(state.norm2, 1.0, rel_tol=0.0, abs_tol=2e-12)
    assert state.project_t36() == tuple(_phase36_from_id("17"))


def test_h2048_normalized_and_projected_collatz():
    state = Hilbert2048State.from_id("holonomy")
    assert state.project_t36() == tuple(_phase36_from_id("holonomy"))


def test_complement_is_involution_and_swaps_channels():
    state = Hilbert2048State.from_id("orbital_mmap_promotion")
    p0, p1 = state.channel_weights()
    complement = state.complement()
    q0, q1 = complement.channel_weights()
    restored = complement.complement()
    assert math.isclose(p0, q1, abs_tol=2e-12)
    assert math.isclose(p1, q0, abs_tol=2e-12)
    assert all(
        abs(a - b) < 2e-12
        for a, b in zip(state.amplitudes, restored.amplitudes)
    )


def test_canonical_mass_modes_are_distinct():
    numeric = CanonicalConceptState.from_id("17")
    fallback = CanonicalConceptState.from_id("holonomy")
    assert numeric.semantic_mass > 0.0
    assert fallback.semantic_mass > 0.0
    assert numeric.canonical_id == "17"


def test_orbital_audit_has_separate_axes_and_no_move_policy():
    report = audit_orbits(CORPUS)
    assert report["mutation_policy"] == "READ_ONLY"
    assert report["directory_policy"].startswith("architectural role")
    assert report["mass_attractor"] in CORPUS
    assert report["coherence_peak"] in CORPUS
    assert report["self_dual_nearest"] in CORPUS
    assert len(report["records"]) == len(CORPUS)


def test_packaged_card_canon_is_complete_and_non_destructive():
    from ciel_geometry.phasenav.canon import load_canonical_cards

    cards = load_canonical_cards()
    assert len(cards) == 115
    assert sum(c["epistemic"]["operator"] == "canonical" for c in cards) == 2
    assert sum(c["epistemic"]["operator"] == "chyba" for c in cards) == 113
    assert all(c["hilbert_state"]["space"] == "C^2048" for c in cards)
    assert all(len(c["emergent_paths_canon"]) == 5 for c in cards)
    assert all(
        all(edge["edge_weight"] > 0 for edge in card["emergent_paths_canon"])
        for card in cards
    )


def test_card_registry_is_deterministic():
    from ciel_geometry.phasenav.canon import card_by_id

    first = card_by_id("001")
    second = card_by_id("1")
    assert first["content_digest_sha256"] == second["content_digest_sha256"]
    assert first["phase_marker_36d"]["marker"] == "⟦H2048→T36⟧"
