"""Deterministic, bounded phase-logic diagnostics across NOEMA formalisms.

This module makes the declared relations between CIELingo, PhaseNav, HTRI,
CQCL, metatime and CIEL Omega explicit.  It is a diagnostic contract only:
it does not train models, mutate memory, invoke daemons, or make physical
claims about the information-geometric vocabulary used by the project.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import math
from typing import Iterable


class RelationKind(StrEnum):
    """Typed relation used in the formalism dependency graph."""

    ENCODES = "encodes"
    CONSTRAINS = "constrains"
    PROPAGATES = "propagates"
    SCORES = "scores"
    STABILIZES = "stabilizes"
    RETRIEVES = "retrieves"


@dataclass(frozen=True)
class FormalismNode:
    """A named formalism and its implementation boundary."""

    identifier: str
    implementation: str
    boundary: str


@dataclass(frozen=True)
class FormalismEdge:
    """A documented dependency; it is not an execution route."""

    source: str
    target: str
    relation: RelationKind
    symbol: str
    provenance: str
    hypothesis_only: bool = True


@dataclass(frozen=True)
class FormalismGraph:
    """Small, hashable graph for a reviewable cross-formalism contract."""

    nodes: tuple[FormalismNode, ...]
    edges: tuple[FormalismEdge, ...]

    @classmethod
    def default(cls) -> "FormalismGraph":
        nodes = (
            FormalismNode("metatime", "runtime/ciel_omega/mathematics/metatime_intention.py", "bounded temporal scale"),
            FormalismNode("CIEL Omega", "runtime/ciel_omega", "CQCL and omega-local implementations"),
            FormalismNode("HTRI", "runtime/wrappers/vector_continuous_cqcl_lingophysics_htri", "hardware/vector bridge signal"),
            FormalismNode("CQCL", "runtime/ciel_omega/emotion/cqcl", "coherence signal only"),
            FormalismNode("PhaseNav", "src/ciel_geometry/phasenav", "diagnostic phase geometry"),
            FormalismNode("CIELingo", "src/cielingo_core", "language and context layer"),
        )
        edges = (
            FormalismEdge("metatime", "CIEL Omega", RelationKind.CONSTRAINS, "tau", "metatime_intention eigenvalues"),
            FormalismEdge("CIEL Omega", "CQCL", RelationKind.ENCODES, "H_CQCL", "CQCL resides in the Omega tree"),
            FormalismEdge("HTRI", "PhaseNav", RelationKind.PROPAGATES, "phi_36", "vector bridge provides bounded phase features"),
            FormalismEdge("CQCL", "PhaseNav", RelationKind.SCORES, "c_hm", "learning gate consumes heart-mind coherence"),
            FormalismEdge("PhaseNav", "CIELingo", RelationKind.STABILIZES, "R_phi", "bounded context diagnostics"),
            FormalismEdge("CIELingo", "PhaseNav", RelationKind.RETRIEVES, "q_ctx", "context layer supplies query-local observations"),
        )
        return cls(nodes=nodes, edges=edges)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "nodes": [node.__dict__ for node in sorted(self.nodes, key=lambda value: value.identifier)],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation.value,
                    "symbol": edge.symbol,
                    "provenance": edge.provenance,
                    "hypothesis_only": edge.hypothesis_only,
                }
                for edge in sorted(self.edges, key=lambda value: (value.source, value.target, value.relation.value))
            ],
        }

    @property
    def digest(self) -> str:
        payload = json.dumps(self.canonical_payload(), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _bounded(value: float, *, label: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{label} must be finite and within [0, 1]")
    return numeric


@dataclass(frozen=True)
class PhaseLogicState:
    """A validated, caller-owned snapshot of logic-relevant scalar signals."""

    phase_vector: tuple[float, ...]
    htri_coherence: float
    cqcl_coherence: float
    semantic_mass: float
    tau: float

    def __post_init__(self) -> None:
        phases = tuple(float(value) for value in self.phase_vector)
        if len(phases) != 36 or not all(math.isfinite(value) for value in phases):
            raise ValueError("phase_vector must contain 36 finite values")
        object.__setattr__(self, "phase_vector", phases)
        object.__setattr__(self, "htri_coherence", _bounded(self.htri_coherence, label="htri_coherence"))
        object.__setattr__(self, "cqcl_coherence", _bounded(self.cqcl_coherence, label="cqcl_coherence"))
        object.__setattr__(self, "semantic_mass", _bounded(self.semantic_mass, label="semantic_mass"))
        object.__setattr__(self, "tau", _bounded(self.tau, label="tau"))

    @classmethod
    def from_iterable(
        cls,
        phase_vector: Iterable[float],
        *,
        htri_coherence: float,
        cqcl_coherence: float,
        semantic_mass: float,
        tau: float,
    ) -> "PhaseLogicState":
        return cls(tuple(phase_vector), htri_coherence, cqcl_coherence, semantic_mass, tau)


@dataclass(frozen=True)
class PhaseLogicReport:
    """Pure diagnostic result.  ``recommendation`` cannot perform an action."""

    graph_digest: str
    phase_coherence: float
    tension: float
    temporal_step: float
    score: float
    recommendation: str
    hypothesis_only: bool = True


class PhaseLogicEngine:
    """Evaluate one or more snapshots deterministically and without writeback."""

    def __init__(self, graph: FormalismGraph | None = None) -> None:
        self.graph = graph or FormalismGraph.default()

    def observe(self, state: PhaseLogicState) -> PhaseLogicReport:
        phasor = sum(complex(math.cos(value), math.sin(value)) for value in state.phase_vector)
        phase_coherence = abs(phasor) / len(state.phase_vector)
        temporal_step = min(1.0, state.tau / 0.489)
        tension = min(
            1.0,
            0.55 * (1.0 - phase_coherence)
            + 0.25 * (1.0 - state.htri_coherence)
            + 0.20 * (1.0 - state.cqcl_coherence),
        )
        score = max(
            0.0,
            min(
                1.0,
                0.35 * phase_coherence
                + 0.20 * state.htri_coherence
                + 0.20 * state.cqcl_coherence
                + 0.15 * state.semantic_mass
                + 0.10 * temporal_step,
            ),
        )
        if tension > 0.65:
            recommendation = "hold"
        elif score < 0.35:
            recommendation = "reduce"
        else:
            recommendation = "continue"
        return PhaseLogicReport(
            graph_digest=self.graph.digest,
            phase_coherence=round(phase_coherence, 8),
            tension=round(tension, 8),
            temporal_step=round(temporal_step, 8),
            score=round(score, 8),
            recommendation=recommendation,
        )

    def replay(self, states: Iterable[PhaseLogicState]) -> tuple[PhaseLogicReport, ...]:
        """Return a deterministic report sequence; no state is retained between calls."""
        return tuple(self.observe(state) for state in states)
