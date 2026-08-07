"""PhaseNav Sigma identity-axis and normalized-cycle canon.

The module keeps three layers deliberately separate:

1. exact arithmetic / topology (complement fixed point, R/Z cycle coordinate,
   integer factorisations, spinor double-cover parity),
2. PhaseNav model identifications (8 mixes, 3 flavours, one ln(2) information
   cycle per twelve projective recurrences),
3. angular convention (phi = C q, with C = 2*pi for radians).

A crucial claim boundary is enforced in the API: the sign acquired by a
spin-1/2 representative after a 2*pi spatial rotation is a double-cover phase,
not the Berry phase of an arbitrary closed path. Berry holonomy remains
path-dependent and belongs to the geometric/path layer.
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
IDENTITY_CYCLE_VERSION = "1.1.0"

# This is a consistency/cross-factorisation status, not an independence proof.
CROSS_DERIVATION_STATUS = "MODEL_DEPENDENT_CROSS_CONSISTENCY"


@dataclass(frozen=True)
class IdentityAxis:
    """Fixed axis of the binary complement sigma -> 1-sigma.

    The canonical axis is not configurable: for the stated complement the
    unique fixed point is exactly 1/2. A state coordinate sigma may evolve on
    either side of the axis; the axis itself remains the reference locus.
    """

    center: float = SIGMA_AXIS

    def __post_init__(self) -> None:
        if not math.isclose(self.center, SIGMA_AXIS, rel_tol=0.0, abs_tol=0.0):
            raise ValueError("the complement sigma -> 1-sigma has fixed axis 1/2")

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
    """Unwrapped normalized projective cycle coordinate q.

    q lives on the universal cover R while ``projective`` is its class in R/Z.
    The spinor representative uses the double cover R/(2Z).
    """

    q: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.q):
            raise ValueError("q must be finite")

    @property
    def projective(self) -> float:
        return self.q % 1.0

    @property
    def spinor(self) -> float:
        return self.q % 2.0

    @property
    def projective_cell(self) -> int:
        """Lower integer cell containing q (floor convention)."""
        return math.floor(self.q)

    @property
    def signed_completed_projective_cycles(self) -> int:
        """Whole traversals from q=0, symmetric under reversal near the origin."""
        return math.trunc(self.q)

    @property
    def completed_projective_cycles(self) -> int:
        """Compatibility alias for signed_completed_projective_cycles."""
        return self.signed_completed_projective_cycles

    def phase(self, *, closure: float = TAU) -> float:
        if closure <= 0.0 or not math.isfinite(closure):
            raise ValueError("closure must be finite and positive")
        return self.q * closure


@dataclass(frozen=True)
class CrossDerivation24:
    """Cross-consistency certificate for 24 half-turn units.

    The equalities are exact once the counts are supplied. They do *not* prove
    that 8 mixes / 3 flavours or 12 projective recurrences are independently
    fundamental. Those counts remain PhaseNav model obligations.
    """

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
            raise ValueError(f"inconsistent cycle factorisation: {values!r}")
        return values[0]

    @property
    def status(self) -> str:
        return CROSS_DERIVATION_STATUS

    @property
    def information_phase_span_rad(self) -> float:
        """Model phase span after selecting the radian half-turn pi."""
        return self.common_units * math.pi

    @property
    def phase_closure(self) -> float:
        """Compatibility alias; prefer information_phase_span_rad."""
        return self.information_phase_span_rad

    @property
    def kappa_candidate(self) -> float:
        return INFORMATION_QUANTUM / self.information_phase_span_rad

    @property
    def kappa(self) -> float:
        """Compatibility alias for the model-dependent kappa candidate."""
        return self.kappa_candidate


def winding_frequency(delta_cycles: float, delta_time: float) -> float:
    """Frequency as signed winding-count rate; no angular unit is required."""
    if delta_time <= 0.0 or not math.isfinite(delta_time):
        raise ValueError("delta_time must be finite and positive")
    if not math.isfinite(delta_cycles):
        raise ValueError("delta_cycles must be finite")
    return float(delta_cycles) / float(delta_time)


def cycle_from_phase(phase: float, *, closure: float = TAU) -> float:
    """Convert angular phase to normalized cycles after choosing closure C."""
    if closure <= 0.0 or not math.isfinite(closure):
        raise ValueError("closure must be finite and positive")
    if not math.isfinite(phase):
        raise ValueError("phase must be finite")
    return float(phase) / float(closure)


def phase_from_cycle(cycle: float, *, closure: float = TAU) -> float:
    """Project normalized cycles into an angular convention phi=C*q."""
    if closure <= 0.0 or not math.isfinite(closure):
        raise ValueError("closure must be finite and positive")
    if not math.isfinite(cycle):
        raise ValueError("cycle must be finite")
    return float(cycle) * float(closure)


def information_from_projective_cycles(cycles: float) -> float:
    """PhaseNav model accumulation: dI/dq = ln(2)/12."""
    if not math.isfinite(cycles):
        raise ValueError("cycles must be finite")
    return float(cycles) * INFORMATION_PER_PROJECTIVE_CYCLE


def projective_cycles_from_information(information: float) -> float:
    if not math.isfinite(information):
        raise ValueError("information must be finite")
    return float(information) / INFORMATION_PER_PROJECTIVE_CYCLE


def information_rate(frequency_hz: float) -> float:
    """PhaseNav model rate dI/dt = (ln 2 / 12) f_q."""
    if not math.isfinite(frequency_hz):
        raise ValueError("frequency_hz must be finite")
    return INFORMATION_PER_PROJECTIVE_CYCLE * float(frequency_hz)


def phase_information_density(*, closure: float = TAU) -> float:
    """dI/dphi after selecting geometric closure C for one q-cycle."""
    if closure <= 0.0 or not math.isfinite(closure):
        raise ValueError("closure must be finite and positive")
    return INFORMATION_PER_PROJECTIVE_CYCLE / float(closure)


def spinor_parity(projective_cycles: int) -> int:
    """Return representative sign (+1/-1) after integer projective rotations."""
    if isinstance(projective_cycles, bool) or not isinstance(projective_cycles, int):
        raise TypeError("projective_cycles must be an integer")
    return 1 if projective_cycles % 2 == 0 else -1


def spinor_rotation_phase(projective_cycles: int = 1) -> float:
    """U(1) representative phase induced by the spin-1/2 double cover.

    This is *not* a generic Berry phase. A Berry phase depends on the actual
    closed path in projective state space; this function encodes only the
    standard sign change under successive 2*pi spatial rotations.
    """
    if isinstance(projective_cycles, bool) or not isinstance(projective_cycles, int):
        raise TypeError("projective_cycles must be an integer")
    return (projective_cycles * math.pi) % TAU


def verify_runtime_identity(*, atol: float = 1e-15) -> bool:
    """Check that the selected PhaseNav model normalization reproduces KAPPA."""
    return math.isclose(
        phase_information_density(closure=TAU),
        KAPPA,
        rel_tol=0.0,
        abs_tol=atol,
    )


def identity_cycle_claims() -> dict[str, tuple[str, ...]]:
    """Machine-readable claim ledger used by tests and documentation."""
    return {
        "exact": (
            "sigma=1/2 is the unique fixed point of sigma->1-sigma",
            "q projective class is R/Z",
            "spinor class uses the double cover R/(2Z)",
            "8*3=12*2=6*4=24 for the configured counts",
            "KAPPA*TAU=ln(2)/12 for the current runtime constants",
        ),
        "standard": (
            "spin-1/2 representatives change sign under one 2*pi spatial rotation",
            "two such rotations restore the representative",
        ),
        "model": (
            "Sigma is interpreted as an evolving axis of system identity",
            "the complete branch uses 8 mixes and 3 flavours",
            "one ln(2) information cycle contains 12 projective recurrences",
            "the configured cross-factorisation is physically fundamental",
        ),
        "open": (
            "independent derivation of the integer 12",
            "independent completeness proof for 8 mixes and 3 flavours",
            "physical derivation of time t from tau",
        ),
    }


__all__ = [
    "SIGMA_AXIS",
    "MIX_COUNT",
    "FLAVOUR_COUNT",
    "PROJECTIVE_CYCLES_PER_INFORMATION_CYCLE",
    "SPINOR_CYCLES_PER_INFORMATION_CYCLE",
    "PROJECTIVE_HALF_TURNS",
    "SPINOR_HALF_TURNS",
    "INFORMATION_QUANTUM",
    "INFORMATION_PER_PROJECTIVE_CYCLE",
    "IDENTITY_CYCLE_VERSION",
    "CROSS_DERIVATION_STATUS",
    "IdentityAxis",
    "CycleCoordinate",
    "CrossDerivation24",
    "winding_frequency",
    "cycle_from_phase",
    "phase_from_cycle",
    "information_from_projective_cycles",
    "projective_cycles_from_information",
    "information_rate",
    "phase_information_density",
    "spinor_parity",
    "spinor_rotation_phase",
    "verify_runtime_identity",
    "identity_cycle_claims",
]
