import math

import pytest

from ciel_geometry.phasenav.canon.identity_relations import (
    IDENTITY_RELATION_SEEDS,
    audit_declared_pairs,
    build_identity_relation_glossary,
    generated_pair_paths,
    identity_relation_cards,
    standard_spinor_projective_holonomy,
)


def test_declared_pair_registry_is_complete_and_reciprocal():
    assert audit_declared_pairs() == ()


def test_every_seed_has_exactly_one_declared_pair():
    by_key = {seed.key: seed for seed in IDENTITY_RELATION_SEEDS}
    for seed in IDENTITY_RELATION_SEEDS:
        assert seed.pair_key in by_key
        pair = by_key[seed.pair_key]
        if seed.self_dual:
            assert seed.pair_key == seed.key
        else:
            assert pair.pair_key == seed.key


def test_cards_use_native_phasenav_generator_and_remain_candidates():
    cards = identity_relation_cards()
    assert len(cards) == len(IDENTITY_RELATION_SEEDS)
    assert all(card.marker_36d.dimension == 36 for card in cards)
    assert all(card.epistemic_status == "candidate" for card in cards)
    assert all(not card.canon_allowed for card in cards)
    assert all(card.attributes["sigma_half_scope"] is True for card in cards)


def test_native_emergent_generator_connects_pair_graph():
    glossary = build_identity_relation_glossary(neighbours=6)
    assert len(glossary.cards) == len(IDENTITY_RELATION_SEEDS)
    assert len(glossary.edges) > 0
    receipts = generated_pair_paths(glossary)
    assert receipts
    assert all(receipt.generated for receipt in receipts)
    assert all(receipt.berry_holonomy_rad is not None for receipt in receipts)
    assert all(receipt.canon_allowed is False for receipt in receipts)


def test_generated_holonomy_is_not_silently_promoted():
    receipts = generated_pair_paths()
    assert all(receipt.epistemic_status == "chyba" for receipt in receipts)
    assert all(receipt.canon_allowed is False for receipt in receipts)


def test_standard_spinor_holonomy_is_separate_from_generated_semantics():
    assert standard_spinor_projective_holonomy(0) == pytest.approx(0.0)
    assert standard_spinor_projective_holonomy(1) == pytest.approx(math.pi)
    assert standard_spinor_projective_holonomy(2) == pytest.approx(0.0)
    assert standard_spinor_projective_holonomy(3) == pytest.approx(math.pi)
    with pytest.raises(TypeError):
        standard_spinor_projective_holonomy(1.5)
