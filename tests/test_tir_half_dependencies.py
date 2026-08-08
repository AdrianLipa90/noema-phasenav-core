from __future__ import annotations

from ciel_geometry.phasenav.canon.model import PHASE_DIM
from ciel_geometry.phasenav.canon.tir_half_dependencies import (
    INTRINSIC_COEFFICIENT_DIM,
    EpistemicStatus,
    build_tir_half_dependency_graph,
)


def graph():
    return build_tir_half_dependency_graph()


def test_every_dependency_has_finite_36d_routing_envelope() -> None:
    g = graph()
    assert PHASE_DIM == 36
    assert all(len(node.vector36) == 36 for node in g.nodes.values())
    assert all(node.vector_sha256 for node in g.nodes.values())


def test_intrinsic_coefficient_state_is_not_identified_with_routing_space() -> None:
    g = graph()
    assert INTRINSIC_COEFFICIENT_DIM == 4
    assert g.node("ROLE_ROUTER_HABC").intrinsic_dimension == 4
    assert len(g.node("ROLE_ROUTER_HABC").vector36) == 36
    assert INTRINSIC_COEFFICIENT_DIM != PHASE_DIM


def test_v06_structural_progress_is_preserved_without_physical_promotion() -> None:
    g = graph()
    assert g.node("ROLE_ROUTER_HABC").status is EpistemicStatus.STRUCTURAL_ROLE_ROUTING_PASS
    assert g.node("ORBIT_DIRECTION").status is EpistemicStatus.IMPLEMENTED_PROJECT_ORBITAL_RULE
    assert (
        g.node("RELATIONAL_GRADIENT").status
        is EpistemicStatus.IMPLEMENTED_SOURCE_OPERATOR_CANDIDATE_TIR_BINDING
    )
    assert g.node("TIR_SLOT_BINDING").status is EpistemicStatus.OPEN
    assert g.node("TIR_SLOT_BINDING").canon_blocked


def test_rh_firewall_remains_closed_to_unproved_edges() -> None:
    g = graph()
    assert g.node("SOH_C004").status is EpistemicStatus.OPEN
    assert g.node("SOH_C005").status is EpistemicStatus.OPEN
    assert not g.proof_path_allowed(("SOH_C005", "SOH_C004"))
    assert {"SOH_C004", "SOH_C005"}.issubset(set(g.blocked_nodes()))


def test_retrospective_collatz_orientation_cannot_be_canonized() -> None:
    g = graph()
    node = g.node("COLLATZ_STOPPING_ORIENTATION")
    assert node.status is EpistemicStatus.RETROSPECTIVE_CANDIDATE_NEEDS_PROSPECTIVE_TEST
    assert node.canon_blocked
    assert not node.proof_consumable


def test_project_derived_kappa_keeps_its_epistemic_label() -> None:
    g = graph()
    assert g.node("KAPPA").status is EpistemicStatus.PROJECT_DERIVED_EXACT_ALGEBRA
    assert not g.node("KAPPA").proof_consumable
    assert g.node("HALF").proof_consumable


def test_current_tir_physical_failure_is_preserved() -> None:
    g = graph()
    edm = g.node("TIR_NEUTRON_EDM")
    assert edm.status is EpistemicStatus.PHYSICAL_FAIL
    assert edm.canon_blocked


def test_receipt_is_deterministic_and_declares_input_firewall() -> None:
    left = graph().receipt()
    right = graph().receipt()
    assert left["receipt_sha256"] == right["receipt_sha256"]
    assert left["routing_dimension"] == 36
    assert left["intrinsic_coefficient_dimension"] == 4
    assert left["firewall"]["mass_as_derivation_input"] == "FORBIDDEN"
    assert left["firewall"]["yukawa_as_derivation_input"] == "FORBIDDEN"
    assert left["firewall"]["vectorization_implies_scientific_promotion"] is False


def test_noema_projection_is_status_and_provenance_only() -> None:
    projection = graph().noema_projection()
    assert projection["routing_dimension"] == 36
    assert projection["intrinsic_coefficient_dimension"] == 4
    assert projection["scientific_promotion"] == "NOT_PERFORMED"
    assert projection["memory_mutation"] == "NOT_PERFORMED"
    assert projection["statuses"]["TIR_SLOT_BINDING"] == "OPEN"
    assert projection["statuses"]["TIR_NEUTRON_EDM"] == "PHYSICAL_FAIL"
