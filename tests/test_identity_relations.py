import math

import pytest

from ciel_geometry.phasenav.canon.identity_relations import (
    HOLONOMY_BERRY_HALF_TURN_CONDITIONAL,
    HOLONOMY_SPINOR_DOUBLE_COVER,
    HOLONOMY_U1_FULL_CLOSURE,
    HOLONOMY_U1_HALF_TURN,
    IDENTITY_NODES,
    IDENTITY_RELATIONS,
    audit_declared_pairs,
    audit_relation_graph,
    build_identity_relation_glossary,
    generated_relation_paths,
    holonomy_eligible_relations,
    identity_relation_cards,
    standard_spinor_projective_holonomy,
)


def test_semantic_relation_graph_is_structurally_complete():
    assert audit_relation_graph() == ()
    assert audit_declared_pairs() == ()


def test_every_node_has_at_least_one_semantic_partner():
    degree = {node.key: 0 for node in IDENTITY_NODES}
    for relation in IDENTITY_RELATIONS:
        degree[relation.source_key] += 1
        if relation.target_key != relation.source_key:
            degree[relation.target_key] += 1
    assert all(value >= 1 for value in degree.values())


def test_sigma_axis_can_be_self_dual_while_other_nodes_have_multiple_edges():
    sigma_self = [
        relation
        for relation in IDENTITY_RELATIONS
        if relation.source_key == relation.target_key == "sigma_axis"
    ]
    assert len(sigma_self) == 1
    equal_partition_edges = [
        relation
        for relation in IDENTITY_RELATIONS
        if "equal_partition" in {relation.source_key, relation.target_key}
    ]
    assert len(equal_partition_edges) >= 2


def test_cards_use_native_generator_but_do_not_treat_hash_geometry_as_evidence():
    cards = identity_relation_cards()
    assert len(cards) == len(IDENTITY_NODES)
    assert all(card.marker_36d.dimension == 36 for card in cards)
    assert all(card.epistemic_status == "candidate" for card in cards)
    assert all(not card.canon_allowed for card in cards)
    assert all(card.attributes["sigma_half_scope"] is True for card in cards)
    assert all(
        card.attributes["generator_geometry_semantic_evidence"] is False
        for card in cards
    )


def test_native_generator_paths_remain_diagnostic_even_when_connected():
    glossary = build_identity_relation_glossary(neighbours=len(IDENTITY_NODES) - 1)
    receipts = generated_relation_paths(glossary)
    assert len(receipts) == len(IDENTITY_RELATIONS)
    assert all(receipt.generator_path_found for receipt in receipts)
    assert all(receipt.generator_semantic_evidence is False for receipt in receipts)
    assert all(receipt.canon_allowed is False for receipt in receipts)
    assert all(receipt.generator_epistemic_status == "chyba" for receipt in receipts)


def test_holonomy_policy_distinguishes_spinor_u1_and_conditional_berry():
    eligible = holonomy_eligible_relations()
    policies = {relation.holonomy_policy for relation in eligible}
    assert HOLONOMY_SPINOR_DOUBLE_COVER in policies
    assert HOLONOMY_U1_HALF_TURN in policies
    assert HOLONOMY_U1_FULL_CLOSURE in policies
    assert HOLONOMY_BERRY_HALF_TURN_CONDITIONAL in policies

    glossary = build_identity_relation_glossary(neighbours=len(IDENTITY_NODES) - 1)
    receipts = generated_relation_paths(glossary)
    by_relation = {(r.source_card_id, r.target_card_id): r for r in receipts}

    spinor = by_relation[("half:projective_cycle", "half:spinor_cycle")]
    assert spinor.analytic_holonomy_rad == pytest.approx(math.pi)
    assert spinor.analytic_holonomy_status == "STANDARD_DOUBLE_COVER"

    euler = by_relation[("half:phase_pi", "half:euler_minus_one")]
    assert euler.analytic_holonomy_rad == pytest.approx(math.pi)

    closure = by_relation[("half:information_ln2", "half:phase_span_24pi")]
    assert closure.analytic_holonomy_rad == pytest.approx(0.0)

    berry = by_relation[("half:phase_pi", "half:berry_minus_one")]
    assert berry.analytic_holonomy_rad == pytest.approx(math.pi)
    assert "CONDITIONAL" in berry.analytic_holonomy_status


def test_standard_spinor_compatibility_function_is_not_generic_berry():
    assert standard_spinor_projective_holonomy(0) == pytest.approx(0.0)
    assert standard_spinor_projective_holonomy(1) == pytest.approx(math.pi)
    assert standard_spinor_projective_holonomy(2) == pytest.approx(0.0)
    assert standard_spinor_projective_holonomy(3) == pytest.approx(math.pi)
    with pytest.raises(TypeError):
        standard_spinor_projective_holonomy(1.5)
