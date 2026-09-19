"""Typed U(1) nonlocal semantic holonomy for canonical PhaseNav states.

W_sem[gamma] is derived from a declared local semantic connection/potential A_sem.
It is a computational phase transporter. It is not, by itself, a physical gauge
field, a signalling channel, hypercharge, or a weak-interaction W boson.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .context_dynamics import PhaseVector36
from .u1_transport import finite_edge_potentials, u1_phase, u1_transport

SEMANTIC_HOLONOMY_VERSION = "0.1.0"
SEMANTIC_HOLONOMY_EPISTEMIC = "CHYBA"


def _finite_edges(edge_potentials: Sequence[float]) -> tuple[float, ...]:
    try:
        return finite_edge_potentials(edge_potentials)
    except ValueError as exc:
        raise ValueError("semantic connection edge potentials must be finite") from exc


def u1_semantic_transport(edge_potentials: Sequence[float]) -> complex:
    """Return W_sem[gamma] = exp(i * sum_e A_sem,e)."""
    return u1_transport(_finite_edges(edge_potentials))


def u1_semantic_holonomy_phase(edge_potentials: Sequence[float]) -> float:
    """Return wrapped arg(W_sem) in [-pi, pi]."""
    return u1_phase(_finite_edges(edge_potentials))


def phase_overlap(left: PhaseVector36, right: PhaseVector36) -> complex:
    """Equal-amplitude 36-mode projective overlap <psi(left)|psi(right)>."""
    if len(left.components) != len(right.components):
        raise ValueError("phase-vector dimension mismatch")
    n = len(left.components)
    re = math.fsum(
        math.cos(b - a) for a, b in zip(left.components, right.components)
    ) / n
    im = math.fsum(
        math.sin(b - a) for a, b in zip(left.components, right.components)
    ) / n
    return complex(re, im)


def semantic_holonomy_coupling(
    left: PhaseVector36,
    right: PhaseVector36,
    edge_potentials: Sequence[float],
) -> complex:
    """C_ij[gamma] = W_sem[gamma] * <psi_i|psi_j>."""
    return u1_semantic_transport(edge_potentials) * phase_overlap(left, right)


@dataclass(frozen=True)
class SemanticHolonomyReceipt:
    """Read-only receipt for one declared semantic path transport."""

    path_id: str
    edge_potentials: tuple[float, ...]
    transport: complex
    phase: float
    strength: float
    coupling: complex
    epistemic: str = SEMANTIC_HOLONOMY_EPISTEMIC
    canon_allowed: bool = False

    @classmethod
    def build(
        cls,
        path_id: str,
        left: PhaseVector36,
        right: PhaseVector36,
        edge_potentials: Sequence[float],
    ) -> "SemanticHolonomyReceipt":
        if not isinstance(path_id, str) or not path_id.strip():
            raise ValueError("path_id must be non-empty")
        edges = _finite_edges(edge_potentials)
        w = u1_semantic_transport(edges)
        coupling = w * phase_overlap(left, right)
        return cls(
            path_id=path_id.strip(),
            edge_potentials=edges,
            transport=w,
            phase=math.atan2(w.imag, w.real),
            strength=abs(coupling),
            coupling=coupling,
        )
