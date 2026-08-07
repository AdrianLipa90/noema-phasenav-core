"""Semantic relation graph for the PhaseNav 1/2 identity canon.

The graph separates four things that must not be conflated:

- semantic relation: declared TIR/PhaseNav meaning,
- generator geometry: deterministic C^2048 -> T^36 coordinates from PhaseNav,
- analytic phase law: e.g. the spin-1/2 double-cover sign,
- Berry holonomy: path-dependent geometric phase.

PhaseNav's native generator is used to provide deterministic diagnostic paths,
but geometry generated from stable semantic IDs is *not* treated as evidence
for the semantic relation itself. Generated Berry values therefore remain
``chyba`` and ``canon_allowed=False``.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from ..canonical_cards import CanonicalCard, Phase36Marker
from ..emergent_glossary import EmergentGlossary, GlossaryPath
from .identity_cycle import spinor_rotation_phase
from .model import CanonicalConceptState

IDENTITY_RELATIONS_VERSION = "2.0.0"
IDENTITY_NAMESPACE = "half"

HOLONOMY_NONE = "none"
HOLONOMY_SPINOR_DOUBLE_COVER = "spinor-double-cover"
HOLONOMY_U1_HALF_TURN = "u1-half-turn"
HOLONOMY_U1_FULL_CLOSURE = "u1-full-closure"
HOLONOMY_BERRY_HALF_TURN_CONDITIONAL = "berry-half-turn-conditional"
HOLONOMY_GENERATOR_DIAGNOSTIC = "generator-diagnostic"
HOLONOMY_POLICIES = frozenset({
    HOLONOMY_NONE,
    HOLONOMY_SPINOR_DOUBLE_COVER,
    HOLONOMY_U1_HALF_TURN,
    HOLONOMY_U1_FULL_CLOSURE,
    HOLONOMY_BERRY_HALF_TURN_CONDITIONAL,
    HOLONOMY_GENERATOR_DIAGNOSTIC,
})


@dataclass(frozen=True)
class IdentityNode:
    key: str
    label: str
    status: str
    note: str = ""

    @property
    def card_id(self) -> str:
        return f"{IDENTITY_NAMESPACE}:{self.key}"


@dataclass(frozen=True)
class IdentityRelation:
    source_key: str
    target_key: str
    relation: str
    status: str
    holonomy_policy: str = HOLONOMY_NONE
    symmetric: bool = True
    note: str = ""

    @property
    def source_card_id(self) -> str:
        return f"{IDENTITY_NAMESPACE}:{self.source_key}"

    @property
    def target_card_id(self) -> str:
        return f"{IDENTITY_NAMESPACE}:{self.target_key}"


@dataclass(frozen=True)
class RelationPathReceipt:
    source_card_id: str
    target_card_id: str
    relation: str
    declared_status: str
    holonomy_policy: str
    generator_path_found: bool
    generator_path_integral: float | None
    generator_berry_rad: float | None
    generator_sequence: tuple[str, ...]
    generator_epistemic_status: str
    generator_semantic_evidence: bool
    analytic_holonomy_rad: float | None
    analytic_holonomy_status: str
    trivial_generator_path: bool
    canon_allowed: bool


# Compatibility name retained for callers of v1.
PairPathReceipt = RelationPathReceipt


IDENTITY_NODES: tuple[IdentityNode, ...] = (
    IdentityNode("sigma_axis", "Sigma identity axis = 1/2", "MODEL+EXACT", "identity interpretation is model; fixed point is exact"),
    IdentityNode("sigma", "sigma", "EXACT"),
    IdentityNode("sigma_complement", "1-sigma", "EXACT"),
    IdentityNode("binary_0", "binary 0", "EXACT"),
    IdentityNode("binary_1", "binary 1", "EXACT"),
    IdentityNode("equal_partition", "equal partition 1/2 : 1/2", "EXACT"),
    IdentityNode("binary_entropy_ln2", "binary entropy maximum ln(2)", "EXACT"),
    IdentityNode("bloch_equator", "Bloch/Poincare equator n_z=0", "STANDARD"),
    IdentityNode("phase_freedom", "equatorial relative phase freedom", "STANDARD"),
    IdentityNode("cycle_q", "normalized cycle q in R/Z", "EXACT"),
    IdentityNode("phase_phi", "angular phase phi=C*q", "EXACT_CONDITIONAL"),
    IdentityNode("projective_cycle", "projective 2*pi recurrence", "STANDARD"),
    IdentityNode("spinor_cycle", "spinor 4*pi recurrence", "STANDARD"),
    IdentityNode("projective_cycle_12", "12 projective recurrences", "MODEL"),
    IdentityNode("spinor_cycle_6", "6 spinor recurrences", "MODEL+STANDARD"),
    IdentityNode("mix_count_8", "8 mixes", "MODEL"),
    IdentityNode("flavour_count_3", "3 flavours", "MODEL"),
    IdentityNode("count_24", "24 half-turn units", "MODEL+EXACT"),
    IdentityNode("phase_pi", "U(1) half-turn phase pi", "STANDARD"),
    IdentityNode("euler_minus_one", "Euler phase factor exp(i*pi)=-1", "EXACT"),
    IdentityNode("berry_minus_one", "Berry holonomy -1 when geometric phase is pi mod 2*pi", "STANDARD_CONDITIONAL"),
    IdentityNode("destructive_interference", "equal-amplitude destructive interference", "STANDARD_CONDITIONAL"),
    IdentityNode("information_ln2", "information quantum ln(2)", "MODEL+EXACT"),
    IdentityNode("phase_span_24pi", "information phase span 24*pi", "MODEL"),
    IdentityNode("arithmetic_information", "information arithmetic sector", "MODEL"),
    IdentityNode("phase_geometry", "phase geometry sector", "MODEL"),
    IdentityNode("energy_matter", "energy / matter projection", "MODEL_BRIDGE"),
    IdentityNode("time_space", "time / space projection", "MODEL_BRIDGE"),
    IdentityNode("winding_frequency", "frequency as winding rate", "EXACT_DEFINITION"),
    IdentityNode("return_time", "inverse recurrence / return time", "EXACT_DEFINITION"),
)


IDENTITY_RELATIONS: tuple[IdentityRelation, ...] = (
    IdentityRelation("sigma_axis", "sigma_axis", "fixed-point/self-dual", "EXACT", note="unique fixed locus of sigma -> 1-sigma"),
    IdentityRelation("sigma", "sigma_complement", "complement", "EXACT", HOLONOMY_GENERATOR_DIAGNOSTIC),
    IdentityRelation("binary_0", "binary_1", "binary-complement", "EXACT", HOLONOMY_GENERATOR_DIAGNOSTIC),
    IdentityRelation("sigma_axis", "equal_partition", "axis-realisation", "EXACT"),
    IdentityRelation("equal_partition", "binary_entropy_ln2", "entropy-maximum", "EXACT", note="H_2(1/2)=ln(2)"),
    IdentityRelation("equal_partition", "bloch_equator", "equal-population-equator", "STANDARD", note="n_z=2*sigma-1=0"),
    IdentityRelation("bloch_equator", "phase_freedom", "equatorial-phase-orbit", "STANDARD", HOLONOMY_GENERATOR_DIAGNOSTIC),
    IdentityRelation("cycle_q", "phase_phi", "representation", "EXACT_CONDITIONAL", note="phi=C*q after choosing geometric closure C"),
    IdentityRelation("cycle_q", "winding_frequency", "cycle-rate", "EXACT_DEFINITION"),
    IdentityRelation("winding_frequency", "return_time", "reciprocal-period", "EXACT_DEFINITION", note="for a periodic unit winding, f=1/T"),
    IdentityRelation("projective_cycle", "spinor_cycle", "double-cover", "STANDARD", HOLONOMY_SPINOR_DOUBLE_COVER),
    IdentityRelation("projective_cycle_12", "spinor_cycle_6", "equivalent-cycle-count", "MODEL+STANDARD", note="12 projective recurrences = 6 spinor recurrences"),
    IdentityRelation("mix_count_8", "flavour_count_3", "factor-pair", "MODEL", note="independence/completeness remains an obligation"),
    IdentityRelation("mix_count_8", "count_24", "factorisation", "MODEL+EXACT", note="8*3=24 only together with flavour_count_3"),
    IdentityRelation("flavour_count_3", "count_24", "factorisation", "MODEL+EXACT", note="8*3=24 only together with mix_count_8"),
    IdentityRelation("projective_cycle_12", "count_24", "half-turn-factorisation", "MODEL+EXACT", note="12*2=24"),
    IdentityRelation("spinor_cycle_6", "count_24", "half-turn-factorisation", "MODEL+STANDARD", note="6*4=24"),
    IdentityRelation("phase_pi", "euler_minus_one", "u1-half-turn", "EXACT", HOLONOMY_U1_HALF_TURN, note="exp(i*pi)=-1"),
    IdentityRelation("phase_pi", "berry_minus_one", "berry-holonomy-condition", "STANDARD_CONDITIONAL", HOLONOMY_BERRY_HALF_TURN_CONDITIONAL, note="only loops whose Berry phase is pi mod 2*pi"),
    IdentityRelation("phase_pi", "destructive_interference", "relative-phase-cancellation", "STANDARD_CONDITIONAL", HOLONOMY_U1_HALF_TURN, note="equal amplitudes and relative phase pi"),
    IdentityRelation("information_ln2", "phase_span_24pi", "arithmetic-geometry-coupling", "MODEL", HOLONOMY_U1_FULL_CLOSURE, note="kappa=ln(2)/(24*pi) in the current PhaseNav normalization"),
    IdentityRelation("count_24", "phase_span_24pi", "half-turn-to-radian-map", "MODEL+STANDARD", HOLONOMY_U1_FULL_CLOSURE, note="24 half-turn units times pi"),
    IdentityRelation("arithmetic_information", "phase_geometry", "sector-dual", "MODEL", note="distinct but coupled sectors"),
    IdentityRelation("arithmetic_information", "energy_matter", "model-projection", "MODEL_BRIDGE", note="physical bridge obligation; not established physics"),
    IdentityRelation("phase_geometry", "time_space", "model-projection", "MODEL_BRIDGE", note="physical bridge obligation; t from tau deferred"),
)

# v1 compatibility: expose a seed-like node tuple under the old name.
IDENTITY_RELATION_SEEDS = IDENTITY_NODES


def _node_map(nodes: Iterable[IdentityNode] = IDENTITY_NODES) -> dict[str, IdentityNode]:
    return {node.key: node for node in nodes}


def audit_relation_graph(
    nodes: Iterable[IdentityNode] = IDENTITY_NODES,
    relations: Iterable[IdentityRelation] = IDENTITY_RELATIONS,
) -> tuple[str, ...]:
    """Return graph violations; empty tuple means structurally complete."""
    node_items = tuple(nodes)
    relation_items = tuple(relations)
    by_key = {node.key: node for node in node_items}
    issues: list[str] = []
    if len(by_key) != len(node_items):
        issues.append("duplicate node key")

    degree = {key: 0 for key in by_key}
    signatures: set[tuple[str, str, str]] = set()
    for relation in relation_items:
        if relation.source_key not in by_key:
            issues.append(f"missing source node: {relation.source_key}")
            continue
        if relation.target_key not in by_key:
            issues.append(f"missing target node: {relation.target_key}")
            continue
        if relation.holonomy_policy not in HOLONOMY_POLICIES:
            issues.append(
                f"invalid holonomy policy for {relation.source_key}->{relation.target_key}: "
                f"{relation.holonomy_policy}"
            )
        left, right = (
            sorted((relation.source_key, relation.target_key))
            if relation.symmetric
            else (relation.source_key, relation.target_key)
        )
        signature = (left, right, relation.relation)
        if signature in signatures:
            issues.append(f"duplicate relation: {signature!r}")
        signatures.add(signature)
        degree[relation.source_key] += 1
        if relation.target_key != relation.source_key:
            degree[relation.target_key] += 1

    for key, value in degree.items():
        if value < 1:
            issues.append(f"unpaired node: {key}")
    return tuple(issues)


def audit_declared_pairs(*_args, **_kwargs) -> tuple[str, ...]:
    """Compatibility wrapper: in v2 a 'pair' is any semantic graph edge."""
    return audit_relation_graph()


def identity_relation_cards() -> tuple[CanonicalCard, ...]:
    """Generate PhaseNav cards while preserving the generator/evidence boundary.

    Stable IDs drive the existing PhaseNav H2048->T36 generator. The resulting
    coordinates are deterministic model coordinates, not semantic evidence.
    """
    issues = audit_relation_graph()
    if issues:
        raise ValueError("invalid identity relation graph: " + "; ".join(issues))

    cards: list[CanonicalCard] = []
    for node in IDENTITY_NODES:
        state = CanonicalConceptState.from_id(node.card_id)
        marker = Phase36Marker.from_vector(
            state.phase36,
            encoding="tir_metatime_collatz_h2048_v1",
        )
        cards.append(
            CanonicalCard(
                card_id=node.card_id,
                card_type="identity-relation",
                label=node.label,
                marker_36d=marker,
                operator_bindings=["identity_cycle", "emergent_36d"],
                semantic_mass=state.semantic_mass,
                epistemic_status="candidate",
                confidence=0.65,
                canon_allowed=False,
                provenance=[{
                    "source_namespace": "phasenav-canon/identity-relations",
                    "source_binding": "MODEL_SPEC",
                    "generator": state.hilbert.generator,
                    "geometry_binding": "STABLE_ID_GENERATED",
                }],
                attributes={
                    "declared_status": node.status,
                    "note": node.note,
                    "sigma_half_scope": True,
                    "generator_geometry_semantic_evidence": False,
                },
            )
        )
    return tuple(cards)


def build_identity_relation_glossary(
    *,
    neighbours: int = 6,
    max_distance: float | None = None,
) -> EmergentGlossary:
    """Run the native PhaseNav emergent-edge generator over the 1/2 graph."""
    glossary = EmergentGlossary(identity_relation_cards())
    glossary.build(
        neighbours=neighbours,
        max_distance=max_distance,
        symmetric=True,
    )
    return glossary


def _analytic_holonomy(relation: IdentityRelation) -> tuple[float | None, str]:
    policy = relation.holonomy_policy
    if policy in {HOLONOMY_NONE, HOLONOMY_GENERATOR_DIAGNOSTIC}:
        return None, "NOT_APPLICABLE"
    if policy == HOLONOMY_SPINOR_DOUBLE_COVER:
        return spinor_rotation_phase(1), "STANDARD_DOUBLE_COVER"
    if policy == HOLONOMY_U1_HALF_TURN:
        return math.pi, "EXACT_OR_STANDARD_CONDITIONAL"
    if policy == HOLONOMY_U1_FULL_CLOSURE:
        return 0.0, "MODEL_SPAN_WITH_EXACT_U1_CLOSURE"
    if policy == HOLONOMY_BERRY_HALF_TURN_CONDITIONAL:
        return math.pi, "STANDARD_CONDITIONAL_ON_BERRY_PHASE_PI"
    raise ValueError(f"unsupported holonomy policy: {policy}")


def generated_relation_paths(
    glossary: EmergentGlossary | None = None,
) -> tuple[RelationPathReceipt, ...]:
    """Resolve declared semantic edges through native PhaseNav generator paths.

    ``generator_berry_rad`` is diagnostic only. It is never promoted to
    semantic evidence because the current coordinates are generated from stable
    IDs rather than independently measured/derived semantic phase coordinates.
    """
    graph = glossary or build_identity_relation_glossary()
    receipts: list[RelationPathReceipt] = []

    for relation in IDENTITY_RELATIONS:
        path: GlossaryPath | None = graph.trace(
            relation.source_card_id,
            relation.target_card_id,
        )
        analytic, analytic_status = _analytic_holonomy(relation)
        if path is None:
            receipts.append(
                RelationPathReceipt(
                    source_card_id=relation.source_card_id,
                    target_card_id=relation.target_card_id,
                    relation=relation.relation,
                    declared_status=relation.status,
                    holonomy_policy=relation.holonomy_policy,
                    generator_path_found=False,
                    generator_path_integral=None,
                    generator_berry_rad=None,
                    generator_sequence=(),
                    generator_epistemic_status="OPEN",
                    generator_semantic_evidence=False,
                    analytic_holonomy_rad=analytic,
                    analytic_holonomy_status=analytic_status,
                    trivial_generator_path=False,
                    canon_allowed=False,
                )
            )
            continue

        trivial = len(path.card_sequence) <= 1
        receipts.append(
            RelationPathReceipt(
                source_card_id=relation.source_card_id,
                target_card_id=relation.target_card_id,
                relation=relation.relation,
                declared_status=relation.status,
                holonomy_policy=relation.holonomy_policy,
                generator_path_found=True,
                generator_path_integral=path.total_path_integral,
                generator_berry_rad=path.berry_holonomy_rad,
                generator_sequence=path.card_sequence,
                generator_epistemic_status=path.epistemic_status,
                generator_semantic_evidence=False,
                analytic_holonomy_rad=analytic,
                analytic_holonomy_status=analytic_status,
                trivial_generator_path=trivial,
                canon_allowed=False,
            )
        )
    return tuple(receipts)


def generated_pair_paths(
    glossary: EmergentGlossary | None = None,
) -> tuple[RelationPathReceipt, ...]:
    """Compatibility alias for v1 callers."""
    return generated_relation_paths(glossary)


def standard_spinor_projective_holonomy(projective_cycles: int = 1) -> float:
    """Compatibility alias; this is a spinor rotation phase, not generic Berry."""
    return spinor_rotation_phase(projective_cycles)


def holonomy_eligible_relations() -> tuple[IdentityRelation, ...]:
    """Relations with an analytic/conditional phase law beyond diagnostics."""
    return tuple(
        relation
        for relation in IDENTITY_RELATIONS
        if relation.holonomy_policy not in {
            HOLONOMY_NONE,
            HOLONOMY_GENERATOR_DIAGNOSTIC,
        }
    )


__all__ = [
    "IDENTITY_RELATIONS_VERSION",
    "IDENTITY_NAMESPACE",
    "HOLONOMY_NONE",
    "HOLONOMY_SPINOR_DOUBLE_COVER",
    "HOLONOMY_U1_HALF_TURN",
    "HOLONOMY_U1_FULL_CLOSURE",
    "HOLONOMY_BERRY_HALF_TURN_CONDITIONAL",
    "HOLONOMY_GENERATOR_DIAGNOSTIC",
    "HOLONOMY_POLICIES",
    "IdentityNode",
    "IdentityRelation",
    "RelationPathReceipt",
    "PairPathReceipt",
    "IDENTITY_NODES",
    "IDENTITY_RELATIONS",
    "IDENTITY_RELATION_SEEDS",
    "audit_relation_graph",
    "audit_declared_pairs",
    "identity_relation_cards",
    "build_identity_relation_glossary",
    "generated_relation_paths",
    "generated_pair_paths",
    "standard_spinor_projective_holonomy",
    "holonomy_eligible_relations",
]
