"""Canonical orbital audit and atomic-orbital adapter for PhaseNav.

The generic semantic orbital audit and the atomic adapter intentionally remain
separate.  In particular:

* an atomic principal shell ``n`` is not a generic semantic shell;
* magnetic winding ``m`` is a phase/winding label, not a semantic-mass index;
* ``semantic_mass`` is never relabelled as physical inertial/gravitational mass;
* the Cayley/Poincare radial adapter is a coordinate bridge, not a physical
  promotion of the research model.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Literal, Mapping

from .model import CanonicalConceptState, ETA_M_36D
from ..pnv_runtime import TAU


ATOMIC_ORBITAL_ADAPTER_VERSION = "0.8.0"
ATOMIC_ORBITAL_ADAPTER_STATUS = (
    "CANDIDATE_VALIDATED_MATH_NOT_PHYSICAL_PROMOTION"
)
AtomicAddressMode = Literal["coulomb", "central", "full"]


@dataclass(frozen=True)
class OrbitalRecord:
    concept: str
    current_path: str
    architectural_role: str
    semantic_mass: float
    order_parameter: float
    p_plus: float
    p_minus: float
    q_ratio: float
    log_radius: float
    half_deficit: float
    self_dual_shell: int
    distance_from_mass_attractor: float
    geometric_shell: int
    berry_from_mass_attractor: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AtomicOrbitalState:
    """Symmetry-aware atomic view over a canonical numeric PhaseNav state.

    ``phase_address`` selects the existing numeric PhaseNav state.  The mapping
    depends on which degeneracies the declared Hamiltonian actually resolves:

    * ``coulomb``: only principal shell ``n`` enters the address;
    * ``central``: ``(n, l)`` enters the address, preserving ``m``/spin;
    * ``full``: every spin-orbital receives a unique address.

    The physical radial ratios are dimensionless hydrogenic baseline ratios for
    a fixed-Z family.  They are deliberately not folded into ``semantic_mass``.
    """

    n: int
    l: int
    m: int
    spin: float
    address_mode: AtomicAddressMode
    phase_address: int
    rho_atomic: float
    u_dual: float
    azimuth: float
    orbital_phase: float
    winding: int
    radial_ratio: float
    energy_ratio: float
    period_ratio: float
    semantic_mass: float
    order_parameter: float
    phase36: tuple[float, ...]
    epistemic_status: str = ATOMIC_ORBITAL_ADAPTER_STATUS

    @classmethod
    def from_quantum_numbers(
        cls,
        n: int,
        l: int,
        m: int,
        spin: float,
        *,
        azimuth: float = 0.0,
        address_mode: AtomicAddressMode = "coulomb",
    ) -> "AtomicOrbitalState":
        _validate_quantum_numbers(n, l, m, spin)
        address = atomic_quantum_address(n, l, m, spin, mode=address_mode)
        canonical = CanonicalConceptState.from_id(address)
        rho = atomic_poincare_radius(n)
        phi = float(azimuth) % TAU
        return cls(
            n=n,
            l=l,
            m=m,
            spin=float(spin),
            address_mode=address_mode,
            phase_address=address,
            rho_atomic=rho,
            u_dual=centered_dual_coordinate(rho),
            azimuth=phi,
            orbital_phase=(m * phi) % TAU,
            winding=m,
            radial_ratio=radial_ratio_from_poincare(rho),
            energy_ratio=energy_ratio_from_poincare(rho),
            period_ratio=period_ratio_from_poincare(rho),
            semantic_mass=canonical.semantic_mass,
            order_parameter=canonical.order_parameter,
            phase36=canonical.phase36,
        )

    def inverted_coordinate(self) -> tuple[float, float]:
        """Return the orbital reciprocal view without mutating canonical state.

        The 36D PhaseNav state, semantic mass and winding label are not changed.
        Only the focus-relative radial/azimuthal coordinate is dualized.
        """

        return orbital_inversion(self.rho_atomic, self.azimuth)

    def to_dict(self) -> dict:
        return asdict(self)


def _require_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def _spin_bit(spin: float) -> int:
    value = float(spin)
    if math.isclose(value, -0.5, rel_tol=0.0, abs_tol=1e-12):
        return 0
    if math.isclose(value, 0.5, rel_tol=0.0, abs_tol=1e-12):
        return 1
    raise ValueError("spin must be -1/2 or +1/2")


def _validate_quantum_numbers(n: int, l: int, m: int, spin: float) -> None:
    n = _require_int("n", n)
    l = _require_int("l", l)
    m = _require_int("m", m)
    if n < 1:
        raise ValueError("n must be >= 1")
    if l < 0 or l >= n:
        raise ValueError("l must satisfy 0 <= l < n")
    if m < -l or m > l:
        raise ValueError("m must satisfy -l <= m <= l")
    _spin_bit(spin)


def coulomb_phase_address(n: int) -> int:
    """Symmetry-preserving numeric address for an ideal Coulomb baseline."""

    n = _require_int("n", n)
    if n < 1:
        raise ValueError("n must be >= 1")
    return n


def central_phase_address(n: int, l: int) -> int:
    """Unique ``(n,l)`` address preserving magnetic and spin degeneracy."""

    n = _require_int("n", n)
    l = _require_int("l", l)
    if n < 1:
        raise ValueError("n must be >= 1")
    if l < 0 or l >= n:
        raise ValueError("l must satisfy 0 <= l < n")
    return n * (n - 1) // 2 + l + 1


def full_spin_orbital_address(n: int, l: int, m: int, spin: float) -> int:
    """Contiguous unique address for a fully resolved spin-orbital.

    The address is only appropriate when the declared dynamics really breaks
    the Coulomb/central degeneracies.  It must not be used merely to make every
    atomic label numerically distinct.
    """

    _validate_quantum_numbers(n, l, m, spin)
    prior_shell_orbitals = (n - 1) * n * (2 * n - 1) // 6
    orbital_index = prior_shell_orbitals + l * l + (m + l) + 1
    return 2 * (orbital_index - 1) + _spin_bit(spin) + 1


def atomic_quantum_address(
    n: int,
    l: int,
    m: int,
    spin: float,
    *,
    mode: AtomicAddressMode = "coulomb",
) -> int:
    """Map quantum labels to the numeric PhaseNav address at declared resolution."""

    _validate_quantum_numbers(n, l, m, spin)
    if mode == "coulomb":
        return coulomb_phase_address(n)
    if mode == "central":
        return central_phase_address(n, l)
    if mode == "full":
        return full_spin_orbital_address(n, l, m, spin)
    raise ValueError("mode must be 'coulomb', 'central', or 'full'")


def cayley_radius_from_ratio(x: float) -> float:
    """Compactify a positive focus-relative radial ratio into ``[0,1)``.

    ``rho = x / (1 + x)`` is the real Mobius map fixed by the anchors
    ``0 -> 0``, ``1 -> 1/2`` and ``infinity -> 1``.
    """

    value = float(x)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("radial ratio x must be finite and >= 0")
    return value / (1.0 + value)


def radial_ratio_from_poincare(rho: float) -> float:
    """Inverse Cayley map ``x = rho / (1-rho)``."""

    value = float(rho)
    if not math.isfinite(value) or value < 0.0 or value >= 1.0:
        raise ValueError("rho must satisfy 0 <= rho < 1")
    return value / (1.0 - value)


def centered_dual_coordinate(rho: float) -> float:
    """Centered interior/exterior coordinate ``u = 2 rho - 1``."""

    value = float(rho)
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError("rho must satisfy 0 <= rho <= 1")
    return 2.0 * value - 1.0


def atomic_poincare_radius(n: int) -> float:
    """Hydrogenic fixed-Z principal-shell radius in Cayley/Poincare form.

    With ``r_n/r_1 = n^2`` and ``r_ref = r_1``:
    ``rho_n = n^2 / (n^2 + 1)``.
    """

    n = _require_int("n", n)
    if n < 1:
        raise ValueError("n must be >= 1")
    n2 = n * n
    return n2 / (n2 + 1.0)


def principal_coordinate_from_poincare(rho: float) -> float:
    """Continuous principal coordinate ``sqrt(rho/(1-rho))``."""

    return math.sqrt(radial_ratio_from_poincare(rho))


def quantized_principal_shell(rho: float, *, atol: float = 1e-9) -> int | None:
    """Return integer principal shell when ``rho`` lies on the atomic radial lattice."""

    coordinate = principal_coordinate_from_poincare(rho)
    nearest = int(round(coordinate))
    if nearest < 1 or not math.isclose(
        coordinate, float(nearest), rel_tol=0.0, abs_tol=float(atol)
    ):
        return None
    return nearest


def energy_ratio_from_poincare(rho: float) -> float:
    """Hydrogenic ``|E|/|E_1|`` for the fixed-Z baseline."""

    ratio = radial_ratio_from_poincare(rho)
    if ratio <= 0.0:
        raise ValueError("rho must be > 0 for an inverse-distance energy ratio")
    return 1.0 / ratio


def period_ratio_from_poincare(rho: float) -> float:
    """Kepler/Bohr baseline ``T/T_1 = (r/r_1)^(3/2)``."""

    return radial_ratio_from_poincare(rho) ** 1.5


def orbital_inversion(rho: float, azimuth: float) -> tuple[float, float]:
    """Focus-relative reciprocal dualization in compact orbital coordinates.

    ``r -> r_ref^2/r`` becomes ``rho -> 1-rho`` and the complex reciprocal
    reverses azimuth.  This is an orbital involution, not a claim that ``1/z``
    is a holomorphic automorphism of the open Poincare disk.
    """

    radius = float(rho)
    if not math.isfinite(radius) or radius < 0.0 or radius > 1.0:
        raise ValueError("rho must satisfy 0 <= rho <= 1")
    phase = float(azimuth)
    if not math.isfinite(phase):
        raise ValueError("azimuth must be finite")
    return 1.0 - radius, (-phase) % TAU


def architectural_role(path: str, concept: str) -> str:
    p = path.strip("/")
    if p == "mmap" or concept.endswith("_mmap") or concept in {
        "phi", "aux_phi", "flavor", "g", "omega", "gravity", "holonomy",
        "psi_geom", "R_geom", "Z_geom", "sensor_raw", "tau", "tick", "registry",
    }:
        return "mmap"
    if p.startswith("scripts"):
        return "script"
    if p.startswith("integration"):
        return "registry"
    return "library"


def audit_orbits(corpus: Mapping[str, str]) -> dict:
    if not corpus:
        raise ValueError("corpus must not be empty")

    states = {name: CanonicalConceptState.from_id(name) for name in corpus}
    mass_attractor = max(
        states,
        key=lambda name: (states[name].semantic_mass, name),
    )
    coherence_peak = max(
        states,
        key=lambda name: (states[name].order_parameter, name),
    )
    self_dual_nearest = min(
        states,
        key=lambda name: (states[name].log_radius, name),
    )
    anchor = states[mass_attractor]

    records: list[OrbitalRecord] = []
    for name in sorted(corpus):
        state = states[name]
        distance = state.angular_distance(anchor)
        records.append(
            OrbitalRecord(
                concept=name,
                current_path=corpus[name],
                architectural_role=architectural_role(corpus[name], name),
                semantic_mass=state.semantic_mass,
                order_parameter=state.order_parameter,
                p_plus=state.p_plus,
                p_minus=state.p_minus,
                q_ratio=state.q_ratio,
                log_radius=state.log_radius,
                half_deficit=state.half_deficit,
                self_dual_shell=state.orbital_shell,
                distance_from_mass_attractor=distance,
                geometric_shell=int(distance // ETA_M_36D),
                berry_from_mass_attractor=anchor.berry_connection(state),
            )
        )

    return {
        "canon_version": "1.0.0",
        "atomic_orbital_adapter_version": ATOMIC_ORBITAL_ADAPTER_VERSION,
        "atomic_orbital_adapter_status": ATOMIC_ORBITAL_ADAPTER_STATUS,
        "mass_attractor": mass_attractor,
        "coherence_peak": coherence_peak,
        "self_dual_nearest": self_dual_nearest,
        "eta_m_36d": ETA_M_36D,
        "mutation_policy": "READ_ONLY",
        "directory_policy": "architectural role is independent of orbital shell",
        "atomic_policy": (
            "atomic principal shell, phase winding, semantic mass and physical radial ratios "
            "remain distinct unless separately derived"
        ),
        "records": [record.to_dict() for record in records],
    }
