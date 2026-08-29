"""Bridge the declared 1/2 identity canon into geometry-first dependencies.

Semantic declarations remain in ``identity_relations``.  This module converts
those declarations to the low-level typed graph using normalized turns rather
than radians.  It never treats generated PhaseNav Berry geometry as semantic
proof.
"""
from __future__ import annotations

from ..dependencies import (
    EpistemicStatus,
    IdentityAxis,
    RelationEdge,
    RelationGraph,
    RelationKind,
    VectorizationOperator,
)
from .identity_relations import (
    HOLONOMY_BERRY_HALF_TURN_CONDITIONAL,
    HOLONOMY_GENERATOR_DIAGNOSTIC,
    HOLONOMY_NONE,
    HOLONOMY_SPINOR_DOUBLE_COVER,
    HOLONOMY_U1_FULL_CLOSURE,
    HOLONOMY_U1_HALF_TURN,
    IDENTITY_RELATIONS,
    IdentityRelation,
)


def _status(value: str) -> EpistemicStatus:
    upper = value.upper()
    if "OPEN" in upper:
        return EpistemicStatus.OPEN
    if "MODEL" in upper:
        return EpistemicStatus.MODEL
    if "STANDARD" in upper:
        return EpistemicStatus.STANDARD
    return EpistemicStatus.EXACT


def _kind(relation: IdentityRelation) -> RelationKind:
    name = relation.relation.lower()
    if "fixed" in name or "self-dual" in name:
        return RelationKind.FIXED_POINT
    if "complement" in name or "dual" in name or "factor-pair" in name:
        return RelationKind.DUAL
    if "projection" in name or "representation" in name or "realisation" in name:
        return RelationKind.REPRESENTS
    if relation.holonomy_policy not in {HOLONOMY_NONE, HOLONOMY_GENERATOR_DIAGNOSTIC}:
        return RelationKind.HOLONOMIC
    return RelationKind.IMPLIES


def _holonomy_turns(relation: IdentityRelation) -> float | None:
    policy = relation.holonomy_policy
    if policy in {HOLONOMY_NONE, HOLONOMY_GENERATOR_DIAGNOSTIC}:
        return None
    if policy in {
        HOLONOMY_SPINOR_DOUBLE_COVER,
        HOLONOMY_U1_HALF_TURN,
        HOLONOMY_BERRY_HALF_TURN_CONDITIONAL,
    }:
        return 0.5
    if policy == HOLONOMY_U1_FULL_CLOSURE:
        return 0.0
    raise ValueError(f"unsupported holonomy policy: {policy}")


def dependency_relation_graph() -> RelationGraph:
    graph = RelationGraph()
    for relation in IDENTITY_RELATIONS:
        graph.add(
            RelationEdge(
                source=relation.source_key,
                target=relation.target_key,
                kind=_kind(relation),
                status=_status(relation.status),
                reversible=relation.symmetric,
                holonomy_turns=_holonomy_turns(relation),
                provenance=f"identity_relations:{relation.relation}",
            )
        )
    return graph


def sigma_axis_vector(*values: float) -> tuple[float, ...]:
    """Vectorize binary coordinates by oriented displacement from Sigma=1/2."""
    vector = VectorizationOperator().centered_scalars(values, axis=IdentityAxis())
    return vector.components
