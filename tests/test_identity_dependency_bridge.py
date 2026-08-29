from __future__ import annotations

from ciel_geometry.phasenav.canon.identity_dependency_bridge import (
    dependency_relation_graph,
    sigma_axis_vector,
)


def test_sigma_axis_vector_derives_sign_from_geometry() -> None:
    assert sigma_axis_vector(0.0, 0.25, 0.5, 0.75, 1.0) == (
        -0.5,
        -0.25,
        0.0,
        0.25,
        0.5,
    )


def test_declared_holonomies_are_normalized_turns() -> None:
    graph = dependency_relation_graph()
    half_turns = [
        edge.holonomy_turns
        for edge in graph.edges
        if edge.holonomy_turns is not None and edge.holonomy_turns != 0.0
    ]
    assert half_turns
    assert all(turn == 0.5 for turn in half_turns)


def test_generated_diagnostic_edges_have_no_canonical_holonomy() -> None:
    graph = dependency_relation_graph()
    diagnostic = [
        edge
        for edge in graph.edges
        if edge.provenance in {
            "identity_relations:complement",
            "identity_relations:binary-complement",
            "identity_relations:equatorial-phase-orbit",
        }
    ]
    assert diagnostic
    assert all(edge.holonomy_turns is None for edge in diagnostic)


def test_relation_graph_has_no_isolated_declared_endpoint() -> None:
    graph = dependency_relation_graph()
    degree = graph.degree()
    assert degree
    assert all(value >= 1 for value in degree.values())
