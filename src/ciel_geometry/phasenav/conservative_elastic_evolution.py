"""Conservative periodic reference evolution for the linearized hyperelastic field.

This is deliberately a verification integrator, not a production PDE solver.

For one longitudinal or transverse displacement component u(x,tau):

    u_tt = c^2 u_xx - (eta/rho0) u_xxxx

with periodic boundary conditions.

The discrete Hamiltonian is

    E = dx sum_i [
        rho0/2 v_i^2
        + rho0 c^2/2 (D_+ u_i)^2
        + eta/2 (D_2 u_i)^2
    ]

and the update is velocity-Verlet / Störmer-Verlet.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .hyperelastic_field36 import (
    HyperelasticFieldError,
    HyperelasticParameters,
    linear_wave_speeds,
)


@dataclass(frozen=True)
class EnergyLedger1D:
    kinetic: float
    elastic: float
    gradient: float
    total: float
    momentum: float


@dataclass(frozen=True)
class PeriodicElasticState1D:
    displacement: tuple[float, ...]
    velocity: tuple[float, ...]
    tau: float

    def __post_init__(self) -> None:
        if len(self.displacement) != len(self.velocity):
            raise HyperelasticFieldError("displacement and velocity lengths must match")
        if len(self.displacement) < 5:
            raise HyperelasticFieldError("need at least five periodic samples")
        u = tuple(float(x) for x in self.displacement)
        v = tuple(float(x) for x in self.velocity)
        if not all(math.isfinite(x) for x in (*u, *v)):
            raise HyperelasticFieldError("state values must be finite")
        t = float(self.tau)
        if not math.isfinite(t):
            raise HyperelasticFieldError("tau must be finite")
        object.__setattr__(self, "displacement", u)
        object.__setattr__(self, "velocity", v)
        object.__setattr__(self, "tau", t)


def _mode_c2(mode: str, params: HyperelasticParameters) -> float:
    c_l, c_t = linear_wave_speeds(params)
    key = mode.strip().lower()
    if key in {"l", "longitudinal"}:
        return c_l * c_l
    if key in {"t", "transverse"}:
        return c_t * c_t
    raise HyperelasticFieldError("mode must be longitudinal/L or transverse/T")


def periodic_acceleration(
    displacement: Sequence[float],
    dx: float,
    mode: str,
    params: HyperelasticParameters,
) -> tuple[float, ...]:
    u = tuple(float(x) for x in displacement)
    if len(u) < 5:
        raise HyperelasticFieldError("need at least five periodic samples")
    if not all(math.isfinite(x) for x in u):
        raise HyperelasticFieldError("displacement values must be finite")
    h = float(dx)
    if not math.isfinite(h) or h <= 0.0:
        raise HyperelasticFieldError("dx must be finite and positive")
    c2 = _mode_c2(mode, params)
    q = params.eta / params.rho0
    n = len(u)
    out = []
    for i in range(n):
        im2, im1 = u[(i - 2) % n], u[(i - 1) % n]
        ui, ip1, ip2 = u[i], u[(i + 1) % n], u[(i + 2) % n]
        d2 = (ip1 - 2.0 * ui + im1) / (h * h)
        d4 = (ip2 - 4.0 * ip1 + 6.0 * ui - 4.0 * im1 + im2) / (h ** 4)
        out.append(c2 * d2 - q * d4)
    return tuple(out)


def energy_ledger(
    state: PeriodicElasticState1D,
    dx: float,
    mode: str,
    params: HyperelasticParameters,
) -> EnergyLedger1D:
    h = float(dx)
    if not math.isfinite(h) or h <= 0.0:
        raise HyperelasticFieldError("dx must be finite and positive")
    u, v = state.displacement, state.velocity
    c2 = _mode_c2(mode, params)
    n = len(u)
    kinetic = 0.5 * params.rho0 * h * math.fsum(x * x for x in v)
    elastic = (
        0.5 * params.rho0 * c2 * h
        * math.fsum(((u[(i + 1) % n] - u[i]) / h) ** 2 for i in range(n))
    )
    gradient = (
        0.5 * params.eta * h
        * math.fsum(
            ((u[(i + 1) % n] - 2.0 * u[i] + u[(i - 1) % n]) / (h * h)) ** 2
            for i in range(n)
        )
    )
    momentum = params.rho0 * h * math.fsum(v)
    total = kinetic + elastic + gradient
    return EnergyLedger1D(kinetic, elastic, gradient, total, momentum)


def verlet_stability_limit(
    dx: float,
    mode: str,
    params: HyperelasticParameters,
) -> float:
    """Sufficient exact spectral limit for the periodic finite-difference operator.

    The largest discrete -D2 eigenvalue is 4/dx^2 and D4 is its square.
    Velocity-Verlet is linearly stable for dt * omega_max < 2.
    """
    h = float(dx)
    if not math.isfinite(h) or h <= 0.0:
        raise HyperelasticFieldError("dx must be finite and positive")
    c2 = _mode_c2(mode, params)
    omega2_max = c2 * (4.0 / h ** 2) + (params.eta / params.rho0) * (16.0 / h ** 4)
    return 2.0 / math.sqrt(omega2_max)


def verlet_step(
    state: PeriodicElasticState1D,
    dt: float,
    dx: float,
    mode: str,
    params: HyperelasticParameters,
    *,
    enforce_stability_limit: bool = True,
) -> PeriodicElasticState1D:
    hdt = float(dt)
    if not math.isfinite(hdt) or hdt <= 0.0:
        raise HyperelasticFieldError("dt must be finite and positive")
    if enforce_stability_limit and hdt >= verlet_stability_limit(dx, mode, params):
        raise HyperelasticFieldError("dt violates the velocity-Verlet spectral stability limit")

    u, v = state.displacement, state.velocity
    a0 = periodic_acceleration(u, dx, mode, params)
    v_half = tuple(v[i] + 0.5 * hdt * a0[i] for i in range(len(u)))
    u1 = tuple(u[i] + hdt * v_half[i] for i in range(len(u)))
    a1 = periodic_acceleration(u1, dx, mode, params)
    v1 = tuple(v_half[i] + 0.5 * hdt * a1[i] for i in range(len(u)))
    return PeriodicElasticState1D(u1, v1, state.tau + hdt)


def evolve_verlet(
    state: PeriodicElasticState1D,
    steps: int,
    dt: float,
    dx: float,
    mode: str,
    params: HyperelasticParameters,
) -> tuple[PeriodicElasticState1D, tuple[EnergyLedger1D, ...]]:
    count = int(steps)
    if count < 0:
        raise HyperelasticFieldError("steps must be non-negative")
    current = state
    ledger = [energy_ledger(current, dx, mode, params)]
    for _ in range(count):
        current = verlet_step(current, dt, dx, mode, params)
        ledger.append(energy_ledger(current, dx, mode, params))
    return current, tuple(ledger)
