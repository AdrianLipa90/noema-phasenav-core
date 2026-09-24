"""Generic finite U(1) path transport primitives for PhaseNav.

This module contains only mathematical/software transport identities. Domain-specific
meaning belongs in typed adapters such as semantic_holonomy or
spectroscopic_holonomy.
"""
from __future__ import annotations

import math
from typing import Sequence

U1_TRANSPORT_VERSION = "0.1.0"


def finite_edge_potentials(edge_potentials: Sequence[float]) -> tuple[float, ...]:
    values = tuple(float(x) for x in edge_potentials)
    if not all(math.isfinite(x) for x in values):
        raise ValueError("U(1) edge potentials must be finite")
    return values


def u1_transport(edge_potentials: Sequence[float]) -> complex:
    """Return exp(i * sum_e A_e) for a finite discrete path."""
    theta = math.fsum(finite_edge_potentials(edge_potentials))
    return complex(math.cos(theta), math.sin(theta))


def u1_phase(edge_potentials: Sequence[float]) -> float:
    """Return wrapped arg(U(1) transport) in [-pi, pi]."""
    w = u1_transport(edge_potentials)
    return math.atan2(w.imag, w.real)


def reversed_edge_potentials(edge_potentials: Sequence[float]) -> tuple[float, ...]:
    """Reverse path orientation and connection sign."""
    values = finite_edge_potentials(edge_potentials)
    return tuple(-x for x in reversed(values))


def relative_path_holonomy(
    first_path: Sequence[float],
    second_path: Sequence[float],
) -> complex:
    """Return W[first] * W[second]^* for two same-endpoint path candidates.

    If the supplied paths share endpoints, the product is the holonomy of the
    closed loop first_path followed by the reversed second_path.
    """
    return u1_transport(first_path) * u1_transport(second_path).conjugate()
