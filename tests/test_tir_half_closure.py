from __future__ import annotations

import math

from ciel_geometry.phasenav.canon.model import PHASE_DIM
from ciel_geometry.phasenav.canon.tir_half_closure import (
    NOEMA_PARENT,
    PHASENAV_RUNTIME_PARENT,
    SECRET_HALF_PARENT,
    TIR_HALF_CLOSURE_SCHEMA,
    TIR_HALF_CLOSURE_VERSION,
    TIR_PARENT,
    build_tir_half_closure,
)


def closure():
    return build_tir_half_closure()


def test_exact_merged_source_commits_are_pinned() -> None:
    c = closure()
    assert c.sources["PHASENAV_RUNTIME"].commit_sha == PHASENAV_RUNTIME_PARENT
    assert c.sources["NOEMA"].commit_sha == NOEMA_PARENT
    assert c.sources["TIR"].commit_sha == TIR_PARENT
    assert c.sources["SECRET_OF_A_HALF"].commit_sha == SECRET_HALF_PARENT
    assert TIR_PARENT == "df8a6e1321ecf2e2c8819f4e9d5ec7d4f997d170"
    assert SECRET_HALF_PARENT == "a1b0aeba192766163893fab1468b8f9cd9b8853b"


def test_source_anchor_vectors_are_native_finite_36d() -> None:
    c = closure()
    assert PHASE_DIM == 36
    assert len(c.sources) == 4
    assert all(len(source.vector36) == 36 for source in c.sources.values())
    assert all(all(math.isfinite(v) for v in source.vector36) for source in c.sources.values())
    assert len({source.vector_sha256 for source in c.sources.values()}) == 4


def test_dependency_node_vectors_are_preserved_not_reinvented() -> None:
    left = closure()
    right = closure()
    assert left.graph.receipt()["receipt_sha256"] == right.graph.receipt()["receipt_sha256"]
    for node_id, node in left.graph.nodes.items():
        assert node.vector36 == right.graph.node(node_id).vector36
        assert len(node.vector36) == 36


def test_every_dependency_edge_has_routing_identity_not_truth_semantics() -> None:
    c = closure()
    assert len(c.paths) == len(c.graph.edges)
    for edge, path in zip(c.graph.edges, c.paths, strict=True):
        assert (path.source, path.target, path.relation, path.status) == (
            edge.source,
            edge.target,
            edge.relation,
            edge.status,
        )
        assert len(path.vector36) == 36
        assert all(math.isfinite(v) for v in path.vector36)
        assert c.source_state_sha256 in path.routing_identity


def test_open_and_failed_scientific_nodes_remain_blocked_after_vectorization() -> None:
    c = closure()
    blocked = set(c.graph.blocked_nodes())
    assert {"SOH_C004", "SOH_C005", "TIR_SLOT_BINDING", "TIR_NEUTRON_EDM"}.issubset(blocked)
    assert not c.graph.proof_path_allowed(("SOH_C005", "SOH_C004"))


def test_closure_receipt_is_deterministic_and_fully_vectorized() -> None:
    left = closure().receipt()
    right = closure().receipt()
    assert left["schema"] == TIR_HALF_CLOSURE_SCHEMA
    assert left["version"] == TIR_HALF_CLOSURE_VERSION == "0.8.0"
    assert left["closure_sha256"] == right["closure_sha256"]
    assert left["source_state_sha256"] == right["source_state_sha256"]
    assert left["routing_dimension"] == 36
    assert left["intrinsic_coefficient_dimension"] == 4
    assert left["intrinsic_state_equals_routing_envelope"] is False
    assert all(len(row["vector_36d"]) == 36 for row in left["sources"].values())
    assert all(len(row["vector_36d"]) == 36 for row in left["nodes"].values())
    assert all(len(row["vector_36d"]) == 36 for row in left["paths"])
    assert all(row["scientific_meaning"] == "EDGE_METADATA_ONLY" for row in left["paths"])
    assert left["scientific_promotion"] == "NOT_PERFORMED"


def test_noema_projection_is_append_only_input_without_promotion_authority() -> None:
    projection = closure().noema_projection()
    assert projection["routing_dimension"] == 36
    assert projection["intrinsic_coefficient_dimension"] == 4
    assert projection["scientific_promotion"] == "NOT_PERFORMED"
    assert projection["memory_mutation"] == "NOT_PERFORMED"
    assert projection["source_commits"]["TIR"] == TIR_PARENT
    assert projection["source_commits"]["SECRET_OF_A_HALF"] == SECRET_HALF_PARENT
    assert {"SOH_C004", "SOH_C005"}.issubset(set(projection["blocked_nodes"]))
