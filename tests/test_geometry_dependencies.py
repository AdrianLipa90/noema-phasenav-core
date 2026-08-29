from __future__ import annotations

import math

from ciel_geometry.phasenav.dependencies import (
    CycleCoordinate,
    EpistemicStatus,
    IdentityAxis,
    PhaseClosure,
    PhaseCrystal,
    RelationEdge,
    RelationGraph,
    RelationKind,
    VectorizationOperator,
    centered_sigma,
    complement_sigma,
    shortest_turn_displacement,
    spinor_sheet,
    winding_rate,
)


def test_identity_axis_generates_negative_zero_positive() -> None:
    axis = IdentityAxis()
    assert axis.orientation(0.25) == -1
    assert axis.orientation(0.5) == 0
    assert axis.orientation(0.75) == 1
    assert centered_sigma(0.25) == -0.25
    assert centered_sigma(0.5) == 0.0
    assert centered_sigma(0.75) == 0.25
    assert complement_sigma(0.2) == 0.8


def test_cycle_coordinate_is_prior_to_radian_closure() -> None:
    q = CycleCoordinate(1.25)
    assert q.wrapped == 0.25
    closure = PhaseClosure(math.tau)
    assert math.isclose(closure.angle(q.wrapped), math.pi / 2)
    assert math.isclose(closure.turns(math.pi), 0.5)


def test_frequency_is_winding_rate() -> None:
    assert winding_rate(12, 3) == 4


def test_spinor_sheet_is_double_cover() -> None:
    assert spinor_sheet(0) == 1
    assert spinor_sheet(1) == -1
    assert spinor_sheet(2) == 1


def test_phase_crystal_shortest_displacement_generates_sign() -> None:
    assert math.isclose(shortest_turn_displacement(0.9, 0.1), 0.2)
    assert math.isclose(shortest_turn_displacement(0.1, 0.9), -0.2)
    a = PhaseCrystal((0.9, 0.1, 0.5))
    b = PhaseCrystal((0.1, 0.9, 0.5))
    tangent = a.tangent_to(b)
    assert all(math.isclose(x, y) for x, y in zip(tangent, (0.2, -0.2, 0.0)))
    assert a.winding_signature_to(b) == (1, -1, 0)


def test_vectorization_consumes_geometry_not_identifiers() -> None:
    op = VectorizationOperator()
    a = PhaseCrystal((0.0, 0.25, 0.75))
    b = PhaseCrystal((0.25, 0.0, 0.75))
    vec = op.tangent(a, b)
    assert vec.components == (0.25, -0.25, 0.0)


def test_relation_closure_respects_epistemic_gate() -> None:
    graph = RelationGraph(
        [
            RelationEdge("half", "equator", RelationKind.IMPLIES, EpistemicStatus.EXACT),
            RelationEdge("equator", "phase_orbit", RelationKind.IMPLIES, EpistemicStatus.STANDARD),
            RelationEdge("phase_orbit", "zeta_zero_state", RelationKind.IMPLIES, EpistemicStatus.MODEL),
            RelationEdge("zeta_zero_state", "RH", RelationKind.IMPLIES, EpistemicStatus.OPEN),
        ]
    )
    assert graph.implication_closure(["half"]) == frozenset({"half", "equator", "phase_orbit"})
    assert graph.implication_closure(["half"], allow_model=True) == frozenset(
        {"half", "equator", "phase_orbit", "zeta_zero_state"}
    )
    assert "RH" not in graph.implication_closure(["half"], allow_model=True)


def test_holonomy_composes_in_normalized_turns() -> None:
    graph = RelationGraph(
        [
            RelationEdge(
                "a", "b", RelationKind.HOLONOMIC, EpistemicStatus.EXACT,
                reversible=True, holonomy_turns=0.25,
            ),
            RelationEdge(
                "b", "c", RelationKind.HOLONOMIC, EpistemicStatus.EXACT,
                reversible=True, holonomy_turns=0.25,
            ),
        ]
    )
    assert math.isclose(graph.holonomy_sum(["a", "b", "c"]), 0.5)
    assert math.isclose(graph.holonomy_sum(["c", "b", "a"]), -0.5)
