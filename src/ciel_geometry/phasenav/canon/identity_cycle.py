"""PhaseNav Sigma identity-axis and normalized cycle canon.

This module separates cycle arithmetic from angular convention.

Exact algebra already present in PhaseNav:
    KAPPA * TAU = ln(2) / 12

The normalized cycle coordinate q lives in R/Z.  Frequency can therefore be
defined as completed windings per unit time without inserting 2*pi.  Angular
phase is a later geometric projection phi = closure * q.

Epistemic boundary:
- integer factorisations and conversions are exact;
- spin-1/2 double-cover periodicity is standard mathematics/physics;
- Sigma-as-identity-axis, the 8-mix/3-flavour count, and the interpretation of
  ln(2) as one complete PhaseNav information cycle are canonical TIR/PhaseNav
  model statements, not claims of established fundamental physics.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from ..pnv_runtime import KAPPA, TAU

SIGMA_AXIS = 0.5
MIX_COUNT = 8
FLAVOUR_COUNT = 3
PROJECTIVE_CYCLES_PER_INFORMATION_CYCLE = 12
SPINOR_CYCLES_PER_INFORMATION_CYCLE = 6
PROJECTIVE_HALF_TURNS = 2
SPINOR_HALF_TURNS = 4
INFORMATION_QUANTUM = math.log(2.0)
INFORMATION_PER_PROJECTIVE_CYCLE = (
    INFORMATION_QUANTUM / PROJECTIVE_CYCLES_PER_INFORMATION_CYCLE
)
IDENTITY_CYCLE_VERSION = "1.0.0"


@dataclass(frozen=True)
class IdentityAxis:
    """Binary identity axis.

    ``sigma`` may evolve as a state coordinate.  The axis is the fixed locus of
    the complement sigma -> 1-sigma and therefore sits at 1/2.
    """

    center: float = SIGMA_AXIS

    def centered(self, sigma: float) -> float:
        return float(sigma) - self.center

    @staticmethod
    def complement(sigma: float) -> float:
        return 1.0 - float(sigma)

    def fixed_residual(self, sigma: float) -> float:
        value = float(sigma)
        return abs(self.complement(value) - value)

    def is_on_axis(self, sigma: float, *, atol: float = 1e-12) -> bool:
        return self.fixed_residual(sigma) <= atol


@dataclass(frozen=True)
class CycleCoordinate:
    """Unwrapped normalized cycle coordinate q.

    One projective cycle is q -> q+1.  A spin-1/2 representative requires two
    projective cycles to return to the same vector rather than merely the same
    projective ray.
    """

    q: float

    @property
    def projective(self) -> float:
        return self.q % 1.0

    @property
    def spinor(self) -> float:
        return self.q % 2.0

    @property
    def completed_projective_cycles(self) -> int:
        return math.floor(self.q)

    def phase(self, *, closure: float = TAU) -> float:
        if closure <= 0.0 or not math.isfinite(closure):
            raise ValueError("closure must be finite and positive")
        return self.q * closure


@dataclass(frozen=True)
class CrossDerivation24:
    """Arithmetic certificate for the common 24 half-turn units."""

    mixes: int = MIX_COUNT
    flavours: int = FLAVOUR_COUNT
    projective_cycles: int = PROJECTIVE_CYCLES_PER_INFORMATION_CYCLE
    spinor_cycles: int = SPINOR_CYCLES_PER_INFORMATION_CYCLE

    @property
    def mix_flavour_units(self) -> int:
        return self.mixes * self.flavours

    @property
    def projective_units(self) -> int:
        return self.projective_cycles * PROJECTIVE_HALF_TURNS

    @property
    def spinor_units(self) -> int:
        return self.spinor_cycles * SPINOR_HALF_TURNS

    @property
    def common_units(self) -> int:
        values = (
            self.mix_flavour_units,
            self.projective_units,
            self.spinor_units,
        )
        if len(set(values)) != 1:
            raise ValueError(f"inconsistent cycle derivation: {values!r}")
        return values[0]

    @property
    def phase_closure(self) -> float:
        """Angular image after selecting the radian half-turn pi."""
        return self.common_units * math.pi

    @property
    def kappa(self) -> float:
        return INFORMATION_QUANTUM / self.phase_closure


def winding_frequency(delta_cycles: float, delta_time: float) -> float:
    """Frequency as winding-count rate, with no angular convention required."""
    if delta_time <= 0.0 or not math.isfinite(delta_time):
        raise ValueError("delta_time must be finite and positive")
    if not math.isfinite(delta_cycles):
        raise ValueError("delta_cycles must be finite")
    return float(delta_cycles) / float(delta_time)


def cycle_from_phase(phase: float, *, closure: float = TAU) -> float:
    """Convert angular phase to normalized cycle coordinate."""
    if closure <= 0.0 or not math.isfinite(closure):
        raise ValueError("closure must be finite and positive")
    return float(phase) / float(closure)


def phase_from_cycle(cycle: float, *, closure: float = TAU) -> float:
    """Project normalized cycles into an angular convention."""
    if closure <= 0.0 or not math.isfinite(closure):
        raise ValueError("closure must be finite and positive")
    return float(cycle) * float(closure)


def information_from_projective_cycles(cycles: float) -> float:
    """Accumulate the canonical ln(2) information cycle in q-space."""
    return float(cycles) * INFORMATION_PER_PROJECTIVE_CYCLE


def projective_cycles_from_information(information: float) -> float:
    return float(information) / INFORMATION_PER_PROJECTIVE_CYCLE


def information_rate(frequency_hz: float) -> float:
    """dI/dt = (ln 2 / 12) f for projective winding frequency f."""
    if not math.isfinite(frequency_hz):
        raise ValueError("frequency_hz must be finite")
    return INFORMATION_PER_PROJECTIVE_CYCLE * float(frequency_hz)


def phase_information_density(*, closure: float = TAU) -> float:
    """dI/dphi obtained only after choosing a geometric cycle closure."""
    if closure <= 0.0 or not math.isfinite(closure):
        raise ValueError("closure must be finite and positive")
    return INFORMATION_PER_PROJECTIVE_CYCLE / float(closure)


def spinor_parity(projective_cycles: int) -> int:
    """Return +1/-1 after an integer number of projective 2*pi cycles."""
    if isinstance(projective_cycles, bool) or not isinstance(projective_cycles, int):
        raise TypeError("projective_cycles must be an integer")
    return 1 if projective_cycles % 2 == 0 else -1


def verify_runtime_identity(*, atol: float = 1e-15) -> bool:
    """Check that the normalized-cycle derivation reproduces runtime KAPPA."""
    return math.isclose(
        phase_information_density(closure=TAU),
        KAPPA,
        rel_tol=0.0,
        abs_tol=atol,
    )
