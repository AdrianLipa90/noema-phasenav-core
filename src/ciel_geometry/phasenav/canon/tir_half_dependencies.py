"""Canonical TIR × Secret-of-a-Half dependency firewall for PhaseNav.

This module vectorizes provenance-bearing dependency states into the existing
PhaseNav T^36 routing envelope.  It deliberately keeps the intrinsic scientific
state separate from its 36D routing representation and never promotes OPEN,
retrospective, or failed scientific claims by virtue of vectorization.

The module is a dependency/epistemic layer over the existing PhaseNav canon;
it is not a second phase engine and it does not use measured masses or Yukawa
couplings as derivation inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Iterable, Mapping

from .model import CanonicalConceptState, PHASE_DIM

TIR_HALF_DEPENDENCY_VERSION = "0.7.0"
INTRINSIC_COEFFICIENT_DIM = 4


class EpistemicStatus(str, Enum):
    EXACT = "EXACT"
    STANDARD = "STANDARD"
    PROJECT_DERIVED_EXACT_ALGEBRA = "PROJECT_DERIVED_EXACT_ALGEBRA"
    STRUCTURAL_ROLE_ROUTING_PASS = "STRUCTURAL_ROLE_ROUTING_PASS"
    IMPLEMENTED_PROJECT_ORBITAL_RULE = "IMPLEMENTED_PROJECT_ORBITAL_RULE"
    IMPLEMENTED_SOURCE_OPERATOR_CANDIDATE_TIR_BINDING = (
        "IMPLEMENTED_SOURCE_OPERATOR_CANDIDATE_TIR_BINDING"
    )
    OPEN = "OPEN"
    PHYSICAL_FAIL = "PHYSICAL_FAIL"
    RETROSPECTIVE_CANDIDATE_NEEDS_PROSPECTIVE_TEST = (
        "RETROSPECTIVE_CANDIDATE_NEEDS_PROSPECTIVE_TEST"
    )


# Only classical/exact anchors may be consumed as proof-strength edges.
# Project-derived and structural states are executable dependencies but retain
# their weaker epistemic class and cannot prove an external mathematical or
# physical claim.
_PROOF_CONSUMABLE = {EpistemicStatus.EXACT, EpistemicStatus.STANDARD}
_CANON_BLOCKED = {
    EpistemicStatus.OPEN,
    EpistemicStatus.PHYSICAL_FAIL,
    EpistemicStatus.RETROSPECTIVE_CANDIDATE_NEEDS_PROSPECTIVE_TEST,
}


@dataclass(frozen=True)
class DependencyNode:
    node_id: str
    status: EpistemicStatus
    provenance: tuple[str, ...]
    relation: str
    intrinsic_dimension: int | None
    vector36: tuple[float, ...]
    falsification_or_open_condition: str | None = None

    def __post_init__(self) -> None:
        if len(self.vector36) != PHASE_DIM:
            raise ValueError(f"{self.node_id}: expected {PHASE_DIM}D routing vector")
        if not all(math.isfinite(value) for value in self.vector36):
            raise ValueError(f"{self.node_id}: routing vector must be finite")
        if self.intrinsic_dimension is not None and self.intrinsic_dimension < 1:
            raise ValueError("intrinsic_dimension must be positive when supplied")
        if not self.provenance:
            raise ValueError(f"{self.node_id}: provenance must not be empty")

    @property
    def proof_consumable(self) -> bool:
        return self.status in _PROOF_CONSUMABLE

    @property
    def canon_blocked(self) -> bool:
        return self.status in _CANON_BLOCKED

    @property
    def vector_sha256(self) -> str:
        payload = json.dumps(
            [round(float(v), 15) for v in self.vector36],
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    relation: str
    status: str


@dataclass(frozen=True)
class DependencyGraph:
    nodes: Mapping[str, DependencyNode]
    edges: tuple[DependencyEdge, ...]

    def node(self, node_id: str) -> DependencyNode:
        return self.nodes[node_id]

    def proof_path_allowed(self, node_ids: Iterable[str]) -> bool:
        """Return True only when every node is proof-strength consumable."""
        return all(self.node(node_id).proof_consumable for node_id in node_ids)

    def blocked_nodes(self) -> tuple[str, ...]:
        return tuple(sorted(node.node_id for node in self.nodes.values() if node.canon_blocked))

    def receipt(self) -> dict[str, object]:
        node_rows = {
            key: {
                "status": node.status.value,
                "provenance": list(node.provenance),
                "relation": node.relation,
                "intrinsic_dimension": node.intrinsic_dimension,
                "routing_dimension": PHASE_DIM,
                "vector_sha256": node.vector_sha256,
                "proof_consumable": node.proof_consumable,
                "canon_blocked": node.canon_blocked,
                "open_condition": node.falsification_or_open_condition,
            }
            for key, node in sorted(self.nodes.items())
        }
        edge_rows = [
            {
                "source": edge.source,
                "target": edge.target,
                "relation": edge.relation,
                "status": edge.status,
            }
            for edge in self.edges
        ]
        payload: dict[str, object] = {
            "schema": "phasenav.tir-half-dependencies/v0.7",
            "version": TIR_HALF_DEPENDENCY_VERSION,
            "routing_dimension": PHASE_DIM,
            "intrinsic_coefficient_dimension": INTRINSIC_COEFFICIENT_DIM,
            "nodes": node_rows,
            "edges": edge_rows,
            "blocked_nodes": list(self.blocked_nodes()),
            "firewall": {
                "mass_as_derivation_input": "FORBIDDEN",
                "yukawa_as_derivation_input": "FORBIDDEN",
                "coefficient_enriched_vector_as_parent": "FORBIDDEN",
                "retrospective_promotion_without_prospective_test": "FORBIDDEN",
                "vectorization_implies_scientific_promotion": False,
                "intrinsic_state_equals_routing_envelope": False,
            },
        }
        digest_source = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        payload["receipt_sha256"] = hashlib.sha256(digest_source).hexdigest()
        return payload

    def noema_projection(self) -> dict[str, object]:
        """Project status/provenance for NOEMA without mutating memory.

        NOEMA receives dependency state and receipt identity.  It does not gain
        authority to promote scientific claims and this function performs no IO.
        """
        receipt = self.receipt()
        return {
            "schema": "noema.phasenav-dependency-projection/v0.7",
            "source_schema": receipt["schema"],
            "source_receipt_sha256": receipt["receipt_sha256"],
            "routing_dimension": PHASE_DIM,
            "intrinsic_coefficient_dimension": INTRINSIC_COEFFICIENT_DIM,
            "scientific_promotion": "NOT_PERFORMED",
            "memory_mutation": "NOT_PERFORMED",
            "blocked_nodes": receipt["blocked_nodes"],
            "statuses": {
                node_id: node.status.value for node_id, node in sorted(self.nodes.items())
            },
        }


def _routing_vector(node_id: str) -> tuple[float, ...]:
    """Use the existing hard-canon PhaseNav generator for the T^36 envelope."""
    return tuple(CanonicalConceptState.from_id(f"TIR_HALF_V07::{node_id}").phase36)


def _node(
    node_id: str,
    status: EpistemicStatus,
    provenance: tuple[str, ...],
    relation: str,
    *,
    intrinsic_dimension: int | None = None,
    open_condition: str | None = None,
) -> DependencyNode:
    return DependencyNode(
        node_id=node_id,
        status=status,
        provenance=provenance,
        relation=relation,
        intrinsic_dimension=intrinsic_dimension,
        vector36=_routing_vector(node_id),
        falsification_or_open_condition=open_condition,
    )


def build_tir_half_dependency_graph() -> DependencyGraph:
    """Build the v0.7 dependency graph from recovered, typed project anchors."""
    nodes = {
        "HALF": _node(
            "HALF",
            EpistemicStatus.EXACT,
            ("Secret-of-a-Half exact half-axis anchors",),
            "foundation",
            intrinsic_dimension=1,
        ),
        "KAPPA": _node(
            "KAPPA",
            EpistemicStatus.PROJECT_DERIVED_EXACT_ALGEBRA,
            ("Secret-of-a-Half v0.7 Eq.23.16", "project ln2/12 phase chain"),
            "information_phase_scale",
            intrinsic_dimension=1,
        ),
        "ROLE_ROUTER_HABC": _node(
            "ROLE_ROUTER_HABC",
            EpistemicStatus.STRUCTURAL_ROLE_ROUTING_PASS,
            ("TIR/Metatime source-role grammar", "TIR×1/2 foundation v0.6"),
            "coefficient_role_router",
            intrinsic_dimension=INTRINSIC_COEFFICIENT_DIM,
        ),
        "ORBIT_DIRECTION": _node(
            "ORBIT_DIRECTION",
            EpistemicStatus.IMPLEMENTED_PROJECT_ORBITAL_RULE,
            ("ciel_geometry:orbital_model.py",),
            "orientation_source",
        ),
        "RELATIONAL_GRADIENT": _node(
            "RELATIONAL_GRADIENT",
            EpistemicStatus.IMPLEMENTED_SOURCE_OPERATOR_CANDIDATE_TIR_BINDING,
            ("CIEL_OMEGA_COMPLETE_SYSTEM:ciel_omega/orbital/dynamics.py",),
            "orientation_source",
            open_condition="prospective binding to each TIR coefficient slot",
        ),
        "TIR_SLOT_BINDING": _node(
            "TIR_SLOT_BINDING",
            EpistemicStatus.OPEN,
            ("TIR×1/2 REVIEW_FINAL_V0.6",),
            "physical_binding",
            intrinsic_dimension=INTRINSIC_COEFFICIENT_DIM,
            open_condition=(
                "prospective atomic/orbital state -> sign/orientation -> recovered tuple "
                "without coefficient or mass inputs"
            ),
        ),
        "COLLATZ_STOPPING_ORIENTATION": _node(
            "COLLATZ_STOPPING_ORIENTATION",
            EpistemicStatus.RETROSPECTIVE_CANDIDATE_NEEDS_PROSPECTIVE_TEST,
            ("TIR recovered charged-lepton gates", "structural seed assignment"),
            "retrospective_candidate",
            open_condition="independent prospective test before any canon promotion",
        ),
        "SOH_C004": _node(
            "SOH_C004",
            EpistemicStatus.OPEN,
            ("secret-of-a-half claims/CLAIM_LEDGER.md",),
            "rh_firewall",
            open_condition="prove xi-zero -> canonical self-dual/native PhaseNav closure",
        ),
        "SOH_C005": _node(
            "SOH_C005",
            EpistemicStatus.OPEN,
            ("secret-of-a-half claims/CLAIM_LEDGER.md",),
            "weil_positivity_firewall",
            open_condition=(
                "dense-family arithmetic Weil positivity, regularization, and null -> closure"
            ),
        ),
        "TIR_COMMON_LIKELIHOOD": _node(
            "TIR_COMMON_LIKELIHOOD",
            EpistemicStatus.OPEN,
            ("TIR/monograph/chapters/ch31_open_problems.tex",),
            "methodological_debt",
            open_condition="common likelihood with uncertainties and covariance",
        ),
        "TIR_NEUTRON_EDM": _node(
            "TIR_NEUTRON_EDM",
            EpistemicStatus.PHYSICAL_FAIL,
            ("TIR/monograph/chapters/ch31_open_problems.tex",),
            "failed_physical_claim",
            open_condition="retain failure unless prospectively motivated replacement exists",
        ),
    }
    edges = (
        DependencyEdge("HALF", "KAPPA", "information_phase_chain", "PROJECT_DERIVED"),
        DependencyEdge("KAPPA", "ROLE_ROUTER_HABC", "generator_scale", "PROJECT_DERIVED"),
        DependencyEdge("ROLE_ROUTER_HABC", "TIR_SLOT_BINDING", "role_constraint", "OPEN_BINDING"),
        DependencyEdge("ORBIT_DIRECTION", "TIR_SLOT_BINDING", "orientation_constraint", "OPEN_BINDING"),
        DependencyEdge("RELATIONAL_GRADIENT", "TIR_SLOT_BINDING", "sign_constraint", "OPEN_BINDING"),
        DependencyEdge("TIR_SLOT_BINDING", "COLLATZ_STOPPING_ORIENTATION", "prospective_test", "BLOCKED"),
        DependencyEdge("SOH_C005", "SOH_C004", "positivity_to_native_closure", "OPEN"),
    )
    return DependencyGraph(nodes=nodes, edges=edges)


TIR_HALF_DEPENDENCY_GRAPH = build_tir_half_dependency_graph()
