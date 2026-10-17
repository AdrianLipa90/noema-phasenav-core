"""Hard canonical PhaseNav state model.

The canonical state is a normalized vector in C^2048. The operational
PhaseNav surface is the coordinate phase projection T^36. The first 36
Hilbert coordinates reproduce the existing PhaseNav 36D runtime exactly;
the remaining coordinates extend the same Metatime/Collatz phase law to the
complete 11-bit Hilbert basis.
"""
from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Iterable, Sequence

from ..pnv_runtime import (
    ALPHA_M,
    KAPPA,
    L3,
    L4,
    L5,
    L_RATIO,
    TAU,
    M_36d_angular_distance,
    M_36d_berry_connection,
    M_36d_mean_phase,
    M_36d_order_parameter,
    M_collatz_hash,
    _phase36_from_id,
    _phase_precise,
    _ternary_phase_offset,
)

HILBERT_DIM = 2048
HILBERT_BITS = 11
PHASE_DIM = 36
COMPLEMENT_MASK = HILBERT_DIM - 1
ETA_M_36D = PHASE_DIM * KAPPA
CANON_VERSION = "1.0.0"

_Q_PRIMES = (3, 5, 7, 11, 13, 17)


def _numeric_eid(eid: object) -> int | None:
    try:
        value = int(str(eid).lstrip("Ff"))
    except (TypeError, ValueError):
        return None
    if value < 1:
        raise ValueError("numeric canonical phase ID must be positive")
    return value


def _full_phase_vector(eid: object) -> tuple[float, ...]:
    """Generate all 2048 canonical coordinate phases."""
    numeric = _numeric_eid(eid)
    if numeric is None:
        h = M_collatz_hash(str(eid).casefold())
        return tuple(round(_phase_precise(h, i), 10) for i in range(HILBERT_DIM))

    qk = _Q_PRIMES[(numeric - 1) % len(_Q_PRIMES)]
    phases: list[float] = []
    for i in range(HILBERT_DIM):
        phi = (
            KAPPA * TAU
            + ALPHA_M * TAU * (i % L3)
            + L_RATIO * TAU * (i // L3)
            + (qk % L5) * TAU / L3
            + _ternary_phase_offset(numeric, i)
        ) % TAU
        phases.append(round(phi, 10))
    return tuple(phases)


def _channel_weight(phases: Sequence[float]) -> float:
    """Derive the complementary channel weight from the full phase field."""
    z = sum(cmath.exp(1j * p) for p in phases) / len(phases)
    return min(1.0, max(0.0, 0.5 * (1.0 + float(z.real))))


def _normalise(amplitudes: Iterable[complex]) -> tuple[complex, ...]:
    values = tuple(complex(v) for v in amplitudes)
    norm2 = math.fsum(abs(v) ** 2 for v in values)
    if norm2 <= 0.0:
        raise ValueError("Hilbert state has zero norm")
    scale = norm2 ** -0.5
    return tuple(v * scale for v in values)


@dataclass(frozen=True)
class Hilbert2048State:
    """Normalized PhaseNav source state in C^2048."""

    amplitudes: tuple[complex, ...]
    source_id: str
    generator: str = "tir_metatime_collatz_h2048_v2_ternary_candidate"

    def __post_init__(self) -> None:
        if len(self.amplitudes) != HILBERT_DIM:
            raise ValueError(f"expected {HILBERT_DIM} amplitudes")
        norm2 = math.fsum(abs(v) ** 2 for v in self.amplitudes)
        if not math.isclose(norm2, 1.0, rel_tol=0.0, abs_tol=2e-12):
            raise ValueError(f"state is not normalized: {norm2!r}")

    @classmethod
    def from_id(cls, eid: object) -> "Hilbert2048State":
        phases = _full_phase_vector(eid)
        sigma = _channel_weight(phases)
        n_channel = HILBERT_DIM // 2
        a_plus = math.sqrt(sigma / n_channel)
        a_minus = math.sqrt((1.0 - sigma) / n_channel)
        amplitudes = [
            (a_plus if i < n_channel else a_minus) * cmath.exp(1j * phases[i])
            for i in range(HILBERT_DIM)
        ]
        return cls(_normalise(amplitudes), source_id=str(eid))

    @property
    def norm2(self) -> float:
        return math.fsum(abs(v) ** 2 for v in self.amplitudes)

    def complement(self) -> "Hilbert2048State":
        """11-bit anti-linear complement J, with J^2 = I."""
        out = tuple(
            self.amplitudes[i ^ COMPLEMENT_MASK].conjugate()
            for i in range(HILBERT_DIM)
        )
        return Hilbert2048State(
            out,
            source_id=f"J({self.source_id})",
            generator=self.generator,
        )

    def channel_weights(self) -> tuple[float, float]:
        half = HILBERT_DIM // 2
        p_plus = math.fsum(abs(v) ** 2 for v in self.amplitudes[:half])
        p_minus = math.fsum(abs(v) ** 2 for v in self.amplitudes[half:])
        total = p_plus + p_minus
        return p_plus / total, p_minus / total

    def project_t36(self) -> tuple[float, ...]:
        phases = tuple(cmath.phase(v) % TAU for v in self.amplitudes[:PHASE_DIM])
        return tuple(round(p, 10) for p in phases)


@dataclass(frozen=True)
class CanonicalConceptState:
    canonical_id: str
    hilbert: Hilbert2048State
    phase36: tuple[float, ...]
    p_plus: float
    p_minus: float
    q_ratio: float
    log_radius: float
    half_deficit: float
    order_parameter: float
    mean_phase: float
    semantic_mass: float
    orbital_shell: int
    fixed_point_residual: float

    @classmethod
    def from_id(cls, eid: object) -> "CanonicalConceptState":
        hilbert = Hilbert2048State.from_id(eid)
        phase36 = hilbert.project_t36()
        expected = tuple(_phase36_from_id(eid))
        if phase36 != expected:
            raise AssertionError(
                "H2048→T36 projection violates candidate ternary36 phase contract"
            )

        p_plus, p_minus = hilbert.channel_weights()
        if p_plus == 0.0:
            q = 0.0
            radius = math.inf
        elif p_minus == 0.0:
            q = math.inf
            radius = math.inf
        else:
            q = p_plus / p_minus
            radius = abs(math.log(q))

        half_deficit = _binary_half_deficit(p_plus)
        order = M_36d_order_parameter(phase36)
        mean_phase = M_36d_mean_phase(phase36) % TAU
        mass = semantic_mass(eid, phase36)
        shell = 0 if not math.isfinite(radius) else int(
            math.floor(radius / ETA_M_36D)
        )
        complemented = hilbert.complement()
        fixed_residual = math.sqrt(
            math.fsum(
                abs(a - b) ** 2
                for a, b in zip(hilbert.amplitudes, complemented.amplitudes)
            )
        )
        return cls(
            canonical_id=str(eid),
            hilbert=hilbert,
            phase36=phase36,
            p_plus=p_plus,
            p_minus=p_minus,
            q_ratio=q,
            log_radius=radius,
            half_deficit=half_deficit,
            order_parameter=order,
            mean_phase=mean_phase,
            semantic_mass=mass,
            orbital_shell=shell,
            fixed_point_residual=fixed_residual,
        )

    def angular_distance(self, other: "CanonicalConceptState") -> float:
        return M_36d_angular_distance(self.phase36, other.phase36)

    def berry_connection(self, other: "CanonicalConceptState") -> float:
        return M_36d_berry_connection(self.phase36, other.phase36)


def _binary_half_deficit(sigma: float) -> float:
    if sigma <= 0.0 or sigma >= 1.0:
        entropy = 0.0
    else:
        entropy = (
            -sigma * math.log(sigma)
            - (1.0 - sigma) * math.log(1.0 - sigma)
        )
    return math.log(2.0) - entropy


def semantic_mass(eid: object, phase36: Sequence[float]) -> float:
    """Canonical two-mode semantic mass."""
    R = M_36d_order_parameter(phase36)
    numeric = _numeric_eid(eid)
    if numeric is None:
        return KAPPA * (1.0 + R)
    return KAPPA * (1.0 + ALPHA_M * numeric) + (L4 / L3) * R
