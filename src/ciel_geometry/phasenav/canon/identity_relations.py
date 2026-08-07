"""Generated semantic-pair layer for the PhaseNav 1/2 identity canon.

Only semantic obligations are declared here. Geometry is not hand-authored:
canonical PhaseNav states are generated from stable IDs, projected to T^36, and
all candidate semantic/Berry paths are produced by :mod:`emergent_glossary`.

This keeps three layers separate:
- declared pair: a TIR/PhaseNav semantic requirement;
- generated path: native PhaseNav geometry and winding;
- promoted holonomy: never automatic; generated paths remain ``chyba`` until
  independently justified.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from ..canonical_cards import CanonicalCard, Phase36Marker
from ..emergent_glossary import EmergentGlossary, GlossaryPath
from .model import CanonicalConceptState

IDENTITY_RELATIONS_VERSION = "1.0.0"
IDENTITY_NAMESPACE = "half"


@dataclass(frozen=True)
class IdentityRelationSeed:
    key: str
    label: str
    pair_key: str
    relation: str
    status: str
    self_dual: bool = False
    note: str = ""

    @property
    def card_id(self) -> str:
        return f"{IDENTITY_NAMESPACE}:{self.key}"

    @property
    def pair_card_id(self) -> str:
        return f"{IDENTITY_NAMESPACE}:{self.pair_key}"


@dataclass(frozen=True)
class PairPathReceipt:
    source_card_id: str
    target_card_id: str
    relation: str
    declared_status: str
    generated: bool
    total_path_integral: float | None
    berry_holonomy_rad: float | None
    card_sequence: tuple[str, ...]
    epistemic_status: str
    canon_allowed: bool


# Pairing is deliberately semantic rather than numeric.  A fixed axis is the
# only self-dual object in this 1/2 slice.  All non-self pairs are reciprocal.
IDENTITY_RELATION_SEEDS: tuple[IdentityRelationSeed, ...] = (
    IdentityRelationSeed(
        "sigma_axis",
        "Sigma identity axis = 1/2",
        "sigma_axis",
        "fixed-point/self-dual",
        "EXACT",
        self_dual=True,
        note="fixed locus of sigma -> 1-sigma",
    ),
    IdentityRelationSeed(
        "sigma",
        "sigma",
        "sigma_complement",
        "complement",
        "EXACT",
    ),
    IdentityRelationSeed(
        "sigma_complement",
        "1-sigma",
        "sigma",
        "complement",
        "EXACT",
    ),
    IdentityRelationSeed(
        "binary_0",
        "binary 0",
        "binary_1",
        "binary-complement",
        "EXACT",
    ),
    IdentityRelationSeed(
        "binary_1",
        "binary 1",
        "binary_0",
        "binary-complement",
        "EXACT",
    ),
    IdentityRelationSeed(
        "cycle_q",
        "normalized cycle q in R/Z",
        "phase_phi",
        "representation",
        "EXACT",
        note="phi=C*q only after a geometric closure convention is selected",
    ),
    IdentityRelationSeed(
        "phase_phi",
        "angular phase phi",
        "cycle_q",
        "representation",
        "EXACT",
    ),
    IdentityRelationSeed(
        "projective_cycle_12",
        "12 projective cycles",
        "spinor_cycle_6",
        "equivalent-cycle-count",
        "EXACT+STANDARD",
        note="12*2 half-turns = 6*4 half-turns = 24",
    ),
    IdentityRelationSeed(
        "spinor_cycle_6",
        "6 spinor cycles",
        "projective_cycle_12",
        "equivalent-cycle-count",
        "EXACT+STANDARD",
    ),
    IdentityRelationSeed(
        "mix_count_8",
        "8 mixes",
        "flavour_count_3",
        "factor-pair",
        "MODEL_POSTULATE",
        note="8*3=24; completeness/independence is a model obligation",
    ),
    IdentityRelationSeed(
        "flavour_count_3",
        "3 flavours",
        "mix_count_8",
        "factor-pair",
        "MODEL_POSTULATE",
    ),
    IdentityRelationSeed(
        "information_ln2",
        "information quantum ln(2)",
        "phase_closure_24pi",
        "arithmetic-geometry-coupling",
        "MODEL_POSTULATE",
        note="coupled by kappa=ln(2)/(24*pi)",
    ),
    IdentityRelationSeed(
        "phase_closure_24pi",
        "phase closure 24*pi",
        "information_ln2",
        "arithmetic-geometry-coupling",
        "MODEL_POSTULATE",
    ),
    IdentityRelationSeed(
        "arithmetic_information",
        "information arithmetic",
        "phase_geometry",
        "sector-dual",
        "MODEL_POSTULATE",
        note="arithmetic and phase geometry are kept distinct at the interface",
    ),
    IdentityRelationSeed(
        "phase_geometry",
        "phase geometry",
        "arithmetic_information",
        "sector-dual",
        "MODEL_POSTULATE",
    ),
)


def _seed_map() -> dict[str, IdentityRelationSeed]:
    return {seed.key: seed for seed in IDENTITY_RELATION_SEEDS}


def audit_declared_pairs(
    seeds: Iterable[IdentityRelationSeed] = IDENTITY_RELATION_SEEDS,
) -> tuple[str, ...]:
    """Return pair-registry violations; empty tuple means reciprocal/complete."""
    items = tuple(seeds)
    by_key = {seed.key: seed for seed in items}
    issues: list[str] = []
    if len(by_key) != len(items):
        issues.append("duplicate seed key")
    for seed in items:
        pair = by_key.get(seed.pair_key)
        if pair is None:
            issues.append(f"missing pair for {seed.key}: {seed.pair_key}")
            continue
        if seed.self_dual:
            if seed.pair_key != seed.key:
                issues.append(f"self-dual {seed.key} must pair with itself")
        elif pair.pair_key != seed.key:
            issues.append(
                f"non-reciprocal pair: {seed.key}->{pair.key}->{pair.pair_key}"
            )
    return tuple(issues)


def identity_relation_cards() -> tuple[CanonicalCard, ...]:
    """Generate canonical PhaseNav cards from stable semantic IDs.

    The 2048D source state and its T^36 projection are generated by the existing
    PhaseNav canonical generator; no phase coordinates are authored here.
    """
    issues = audit_declared_pairs()
    if issues:
        raise ValueError("invalid identity relation registry: " + "; ".join(issues))

    cards: list[CanonicalCard] = []
    for seed in IDENTITY_RELATION_SEEDS:
        state = CanonicalConceptState.from_id(seed.card_id)
        marker = Phase36Marker.from_vector(
            state.phase36,
            encoding="tir_metatime_collatz_h2048_v1",
        )
        cards.append(
            CanonicalCard(
                card_id=seed.card_id,
                card_type="identity-relation",
                label=seed.label,
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
                }],
                attributes={
                    "pair_id": seed.pair_card_id,
                    "relation": seed.relation,
                    "declared_status": seed.status,
                    "self_dual": seed.self_dual,
                    "note": seed.note,
                    "sigma_half_scope": True,
                },
            )
        )
    return tuple(cards)


def build_identity_relation_glossary(
    *,
    neighbours: int = 6,
    max_distance: float | None = None,
) -> EmergentGlossary:
    """Run the native PhaseNav emergent-edge generator over the 1/2 seed set."""
    glossary = EmergentGlossary(identity_relation_cards())
    glossary.build(
        neighbours=neighbours,
        max_distance=max_distance,
        symmetric=True,
    )
    return glossary


def generated_pair_paths(
    glossary: EmergentGlossary | None = None,
) -> tuple[PairPathReceipt, ...]:
    """Resolve each declared pair through generated PhaseNav paths.

    Holonomy reported here is generated Berry holonomy and therefore remains
    epistemically ``chyba``.  It is never promoted merely because the semantic
    pair was declared.
    """
    graph = glossary or build_identity_relation_glossary()
    seeds = _seed_map()
    receipts: list[PairPathReceipt] = []
    seen: set[tuple[str, str]] = set()

    for seed in IDENTITY_RELATION_SEEDS:
        pair = seeds[seed.pair_key]
        unordered = tuple(sorted((seed.card_id, pair.card_id)))
        if unordered in seen:
            continue
        seen.add(unordered)
        path: GlossaryPath | None = graph.trace(seed.card_id, pair.card_id)
        if path is None:
            receipts.append(
                PairPathReceipt(
                    source_card_id=seed.card_id,
                    target_card_id=pair.card_id,
                    relation=seed.relation,
                    declared_status=seed.status,
                    generated=False,
                    total_path_integral=None,
                    berry_holonomy_rad=None,
                    card_sequence=(),
                    epistemic_status="OPEN",
                    canon_allowed=False,
                )
            )
            continue
        receipts.append(
            PairPathReceipt(
                source_card_id=seed.card_id,
                target_card_id=pair.card_id,
                relation=seed.relation,
                declared_status=seed.status,
                generated=True,
                total_path_integral=path.total_path_integral,
                berry_holonomy_rad=path.berry_holonomy_rad,
                card_sequence=path.card_sequence,
                epistemic_status=path.epistemic_status,
                canon_allowed=False,
            )
        )
    return tuple(receipts)


def standard_spinor_projective_holonomy(projective_cycles: int = 1) -> float:
    """Standard spin-1/2 sign holonomy for integer projective loops.

    One projective 2*pi loop contributes pi to the representative's U(1) phase
    (a sign flip); two loops close to zero modulo 2*pi.  This is intentionally
    separate from generated semantic Berry paths.
    """
    if isinstance(projective_cycles, bool) or not isinstance(projective_cycles, int):
        raise TypeError("projective_cycles must be an integer")
    return (projective_cycles * math.pi) % (2.0 * math.pi)


__all__ = [
    "IDENTITY_RELATIONS_VERSION",
    "IDENTITY_NAMESPACE",
    "IdentityRelationSeed",
    "PairPathReceipt",
    "IDENTITY_RELATION_SEEDS",
    "audit_declared_pairs",
    "identity_relation_cards",
    "build_identity_relation_glossary",
    "generated_pair_paths",
    "standard_spinor_projective_holonomy",
]
