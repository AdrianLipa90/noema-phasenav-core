"""Spectroscopic holonomy bridge for PhaseNav graph models.

The layer is intentionally substrate-neutral. It reuses the exact finite U(1)
path algebra but does not identify a computational graph connection with a
measured electromagnetic/gauge field, molecular flux, hypercharge, or any
specific physical substrate.

For a graph G=(V,E) with C connected components, the independent cycle count is
beta_1 = E - V + C. Only beta_1 closed-loop U(1) phases are retained as
gauge-invariant graph coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Sequence

from .u1_transport import (
    finite_edge_potentials,
    relative_path_holonomy,
    u1_phase,
    u1_transport,
)

SPECTROSCOPIC_HOLONOMY_VERSION = "0.1.0"
SPECTROSCOPIC_HOLONOMY_EPISTEMIC = "CHYBA"


def _strict_int(value: int, field: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return value


def _finite_scalar(value: float, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field} must be finite")
    return out


def _finite_vector(values: Sequence[float], field: str) -> tuple[float, ...]:
    out = tuple(float(x) for x in values)
    if not all(math.isfinite(x) for x in out):
        raise ValueError(f"{field} must contain only finite values")
    return out


def wrap_phase(phase: float) -> float:
    value = _finite_scalar(phase, "phase")
    return math.atan2(math.sin(value), math.cos(value))


def cycle_rank(vertex_count: int, edge_count: int, component_count: int = 1) -> int:
    """Return the first Betti number beta_1 = E - V + C for a finite graph."""
    vertices = _strict_int(vertex_count, "vertex_count", 1)
    edges = _strict_int(edge_count, "edge_count", 0)
    components = _strict_int(component_count, "component_count", 1)
    if components > vertices:
        raise ValueError("component_count cannot exceed vertex_count")
    beta = edges - vertices + components
    if beta < 0:
        raise ValueError("graph counts are inconsistent with a finite graph")
    return beta


@dataclass(frozen=True)
class SpectroscopicHolonomyState:
    """Gauge-reduced U(1) cycle coordinates for a spectroscopic graph model."""

    vertex_count: int
    edge_count: int
    component_count: int
    beta_1: int
    cycle_edge_potentials: tuple[tuple[float, ...], ...]
    cycle_phases: tuple[float, ...]
    cycle_holonomies: tuple[complex, ...]
    epistemic: str = SPECTROSCOPIC_HOLONOMY_EPISTEMIC
    canon_allowed: bool = False
    physical_gauge_field_claimed: bool = False
    physical_substrate_claimed: bool = False

    @classmethod
    def build(
        cls,
        *,
        vertex_count: int,
        edge_count: int,
        component_count: int = 1,
        cycle_edge_potentials: Sequence[Sequence[float]] = (),
    ) -> "SpectroscopicHolonomyState":
        beta = cycle_rank(vertex_count, edge_count, component_count)
        cycles = tuple(finite_edge_potentials(path) for path in cycle_edge_potentials)
        if len(cycles) != beta:
            raise ValueError(
                "cycle_edge_potentials must contain exactly beta_1 independent cycles"
            )
        holonomies = tuple(u1_transport(path) for path in cycles)
        phases = tuple(math.atan2(w.imag, w.real) for w in holonomies)
        return cls(
            vertex_count=vertex_count,
            edge_count=edge_count,
            component_count=component_count,
            beta_1=beta,
            cycle_edge_potentials=cycles,
            cycle_phases=phases,
            cycle_holonomies=holonomies,
        )


@dataclass(frozen=True)
class RingTransitionCandidate:
    """Kinematic ring-level energy difference; no dipole selection rule implied."""

    lower_index: int
    upper_index: int
    delta_energy: float


def ring_energy_levels(
    n_sites: int,
    *,
    onsite_energy: float = 0.0,
    hopping: float = 1.0,
    holonomy_phase: float = 0.0,
) -> tuple[float, ...]:
    """Exact N-site nearest-neighbour ring spectrum with total U(1) holonomy Phi.

    E_m(Phi) = epsilon + 2 t cos((2 pi m + Phi)/N).

    The function is a graph-model identity. Mapping epsilon, t, or Phi to a
    particular molecule requires an independent physical binding.
    """
    n = _strict_int(n_sites, "n_sites", 3)
    epsilon = _finite_scalar(onsite_energy, "onsite_energy")
    t = _finite_scalar(hopping, "hopping")
    phi = _finite_scalar(holonomy_phase, "holonomy_phase")
    return tuple(
        epsilon + 2.0 * t * math.cos((2.0 * math.pi * m + phi) / n)
        for m in range(n)
    )


def ring_transition_candidates(
    n_sites: int,
    *,
    onsite_energy: float = 0.0,
    hopping: float = 1.0,
    holonomy_phase: float = 0.0,
) -> tuple[RingTransitionCandidate, ...]:
    """Return all pairwise positive ring energy gaps, without selection rules."""
    levels = ring_energy_levels(
        n_sites,
        onsite_energy=onsite_energy,
        hopping=hopping,
        holonomy_phase=holonomy_phase,
    )
    ordered = sorted(enumerate(levels), key=lambda item: (item[1], item[0]))
    out: list[RingTransitionCandidate] = []
    for lower_pos, (lower_index, lower_energy) in enumerate(ordered):
        for upper_index, upper_energy in ordered[lower_pos + 1 :]:
            out.append(
                RingTransitionCandidate(
                    lower_index=lower_index,
                    upper_index=upper_index,
                    delta_energy=upper_energy - lower_energy,
                )
            )
    return tuple(sorted(out, key=lambda item: (item.delta_energy, item.lower_index, item.upper_index)))


def phase_vibronic_linearization(
    phase_at_equilibrium: float,
    gradient: Sequence[float],
    normal_coordinates: Sequence[float],
) -> float:
    """First-order Phi(Q) = Phi_0 + grad(Phi) dot Q."""
    phi0 = _finite_scalar(phase_at_equilibrium, "phase_at_equilibrium")
    grad = _finite_vector(gradient, "gradient")
    coords = _finite_vector(normal_coordinates, "normal_coordinates")
    if len(grad) != len(coords):
        raise ValueError("gradient and normal_coordinates dimensions must match")
    return phi0 + math.fsum(g * q for g, q in zip(grad, coords))


def central_difference_jacobian(
    observable: Callable[[tuple[float, ...]], Sequence[float]],
    phases: Sequence[float],
    *,
    step: float = 1.0e-6,
) -> tuple[tuple[float, ...], ...]:
    """Numerically evaluate J_{alpha k}=d O_alpha / d Phi_k."""
    params = _finite_vector(phases, "phases")
    h = _finite_scalar(step, "step")
    if h <= 0.0:
        raise ValueError("step must be positive")

    if not params:
        base = _finite_vector(observable(tuple()), "observable")
        return tuple(tuple() for _ in base)

    columns: list[tuple[float, ...]] = []
    output_dim: int | None = None
    for index in range(len(params)):
        plus = list(params)
        minus = list(params)
        plus[index] += h
        minus[index] -= h
        f_plus = _finite_vector(observable(tuple(plus)), "observable")
        f_minus = _finite_vector(observable(tuple(minus)), "observable")
        if len(f_plus) != len(f_minus):
            raise ValueError("observable output dimension changed under perturbation")
        if output_dim is None:
            output_dim = len(f_plus)
        elif len(f_plus) != output_dim:
            raise ValueError("observable output dimension changed between parameters")
        columns.append(
            tuple((a - b) / (2.0 * h) for a, b in zip(f_plus, f_minus))
        )

    assert output_dim is not None
    return tuple(
        tuple(columns[column][row] for column in range(len(columns)))
        for row in range(output_dim)
    )


def fisher_information_diagonal_noise(
    jacobian: Sequence[Sequence[float]],
    variances: Sequence[float],
) -> tuple[tuple[float, ...], ...]:
    """Return F = J^T Sigma^-1 J for diagonal observable-noise covariance."""
    rows = tuple(_finite_vector(row, "jacobian row") for row in jacobian)
    noise = _finite_vector(variances, "variances")
    if len(rows) != len(noise):
        raise ValueError("variances length must match jacobian row count")
    if any(v <= 0.0 for v in noise):
        raise ValueError("variances must be strictly positive")
    if not rows:
        return tuple()
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("jacobian must be rectangular")
    return tuple(
        tuple(
            math.fsum(
                rows[alpha][i] * rows[alpha][j] / noise[alpha]
                for alpha in range(len(rows))
            )
            for j in range(width)
        )
        for i in range(width)
    )


__all__ = [
    "SPECTROSCOPIC_HOLONOMY_EPISTEMIC",
    "SPECTROSCOPIC_HOLONOMY_VERSION",
    "RingTransitionCandidate",
    "SpectroscopicHolonomyState",
    "central_difference_jacobian",
    "cycle_rank",
    "fisher_information_diagonal_noise",
    "phase_vibronic_linearization",
    "relative_path_holonomy",
    "ring_energy_levels",
    "ring_transition_candidates",
    "u1_phase",
    "u1_transport",
    "wrap_phase",
]
