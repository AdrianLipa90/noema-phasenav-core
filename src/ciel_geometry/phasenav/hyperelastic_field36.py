"""Objective hyperelastic dynamics on the calibrated GL(3) deformation carrier.

Reference model:
    F = I + Grad u
    J = det F > 0
    C = F^T F

Compressible neo-Hookean stored energy:
    W = mu/2 * (tr(C)-3-2 ln J) + lambda/2 * (ln J)^2

First Piola stress:
    P = mu (F-F^{-T}) + lambda ln(J) F^{-T}

Second-gradient regularization:
    W_grad = eta/2 * |Grad F|^2

For u as the primary field, the Euler-Lagrange equation is
    rho0 u_tt = Div P - Div Div H
with
    H_{iAB} = eta * partial_B F_{iA}.

In a homogeneous linearized medium this gives
    omega_L^2 = ((lambda+2mu)/rho0) k^2 + (eta/rho0) k^4
    omega_T^2 = (mu/rho0) k^2 + (eta/rho0) k^4.

This module is a continuum-mechanics reference layer. It makes no gravity claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .spatial_deformation36 import (
    Deformation36Error,
    det3,
    inverse3,
    recover_deformation3,
)


class HyperelasticFieldError(ValueError):
    pass


def _m3(a: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    if len(a) != 3 or any(len(row) != 3 for row in a):
        raise HyperelasticFieldError("expected a 3x3 matrix")
    m = tuple(tuple(float(x) for x in row) for row in a)
    if not all(math.isfinite(x) for row in m for x in row):
        raise HyperelasticFieldError("matrix entries must be finite")
    return m


def _v3(v: Sequence[float]) -> tuple[float, float, float]:
    if len(v) != 3:
        raise HyperelasticFieldError("expected a 3-vector")
    x = tuple(float(a) for a in v)
    if not all(math.isfinite(a) for a in x):
        raise HyperelasticFieldError("vector entries must be finite")
    return x  # type: ignore[return-value]


def _transpose(a):
    return tuple(tuple(a[j][i] for j in range(len(a))) for i in range(len(a[0])))


def _matmul(a, b):
    return tuple(
        tuple(math.fsum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0])))
        for i in range(len(a))
    )


def _frob_sq(a) -> float:
    return math.fsum(float(x) * float(x) for row in a for x in row)


def _trace3(a) -> float:
    return float(a[0][0] + a[1][1] + a[2][2])


@dataclass(frozen=True)
class HyperelasticParameters:
    rho0: float
    mu: float
    lame_lambda: float
    eta: float = 0.0

    def __post_init__(self) -> None:
        vals = tuple(float(x) for x in (self.rho0, self.mu, self.lame_lambda, self.eta))
        if not all(math.isfinite(x) for x in vals):
            raise HyperelasticFieldError("material parameters must be finite")
        rho0, mu, lam, eta = vals
        if rho0 <= 0.0:
            raise HyperelasticFieldError("rho0 must be positive")
        if mu <= 0.0:
            raise HyperelasticFieldError("mu must be positive")
        if eta < 0.0:
            raise HyperelasticFieldError("eta must be non-negative")
        # Positive infinitesimal bulk modulus K=lambda+2mu/3.
        if lam + 2.0 * mu / 3.0 <= 0.0:
            raise HyperelasticFieldError("lambda+2mu/3 must be positive")
        object.__setattr__(self, "rho0", rho0)
        object.__setattr__(self, "mu", mu)
        object.__setattr__(self, "lame_lambda", lam)
        object.__setattr__(self, "eta", eta)


def deformation_gradient(displacement_gradient: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    g = _m3(displacement_gradient)
    return tuple(
        tuple((1.0 if i == j else 0.0) + g[i][j] for j in range(3))
        for i in range(3)
    )


def right_cauchy_green(f: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    m = _m3(f)
    return _matmul(_transpose(m), m)


def neo_hookean_energy_density(
    f: Sequence[Sequence[float]],
    params: HyperelasticParameters,
) -> float:
    m = _m3(f)
    j = det3(m)
    if j <= 0.0:
        raise HyperelasticFieldError("orientation-preserving deformation requires det(F)>0")
    c = right_cauchy_green(m)
    ln_j = math.log(j)
    return (
        0.5 * params.mu * (_trace3(c) - 3.0 - 2.0 * ln_j)
        + 0.5 * params.lame_lambda * ln_j * ln_j
    )


def first_piola_stress(
    f: Sequence[Sequence[float]],
    params: HyperelasticParameters,
) -> tuple[tuple[float, ...], ...]:
    m = _m3(f)
    j = det3(m)
    if j <= 0.0:
        raise HyperelasticFieldError("orientation-preserving deformation requires det(F)>0")
    finv_t = _transpose(inverse3(m))
    ln_j = math.log(j)
    return tuple(
        tuple(
            params.mu * (m[i][a] - finv_t[i][a])
            + params.lame_lambda * ln_j * finv_t[i][a]
            for a in range(3)
        )
        for i in range(3)
    )


def linear_strain(displacement_gradient: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    g = _m3(displacement_gradient)
    return tuple(
        tuple(0.5 * (g[i][j] + g[j][i]) for j in range(3))
        for i in range(3)
    )


def linear_elastic_energy_density(
    displacement_gradient: Sequence[Sequence[float]],
    params: HyperelasticParameters,
) -> float:
    eps = linear_strain(displacement_gradient)
    tr = _trace3(eps)
    return params.mu * _frob_sq(eps) + 0.5 * params.lame_lambda * tr * tr


def gradient_energy_density(
    grad_f: Sequence[Sequence[Sequence[float]]],
    params: HyperelasticParameters,
) -> float:
    if len(grad_f) != 3:
        raise HyperelasticFieldError("Grad F must have shape 3x3x3")
    vals = []
    for i in range(3):
        if len(grad_f[i]) != 3:
            raise HyperelasticFieldError("Grad F must have shape 3x3x3")
        for a in range(3):
            if len(grad_f[i][a]) != 3:
                raise HyperelasticFieldError("Grad F must have shape 3x3x3")
            for b in range(3):
                x = float(grad_f[i][a][b])
                if not math.isfinite(x):
                    raise HyperelasticFieldError("Grad F entries must be finite")
                vals.append(x)
    return 0.5 * params.eta * math.fsum(x * x for x in vals)


def kinetic_energy_density(
    velocity: Sequence[float],
    params: HyperelasticParameters,
) -> float:
    v = _v3(velocity)
    return 0.5 * params.rho0 * math.fsum(x * x for x in v)


def lagrangian_density(
    velocity: Sequence[float],
    f: Sequence[Sequence[float]],
    grad_f: Sequence[Sequence[Sequence[float]]],
    params: HyperelasticParameters,
) -> float:
    return (
        kinetic_energy_density(velocity, params)
        - neo_hookean_energy_density(f, params)
        - gradient_energy_density(grad_f, params)
    )


def carrier_energy_density(
    bivector_operator36: Sequence[Sequence[float]],
    params: HyperelasticParameters,
    *,
    tolerance: float = 1e-10,
) -> float:
    try:
        f = recover_deformation3(bivector_operator36, tolerance=tolerance)
    except Deformation36Error as exc:
        raise HyperelasticFieldError(str(exc)) from exc
    return neo_hookean_energy_density(f, params)


def linear_wave_speeds(params: HyperelasticParameters) -> tuple[float, float]:
    c_l = math.sqrt((params.lame_lambda + 2.0 * params.mu) / params.rho0)
    c_t = math.sqrt(params.mu / params.rho0)
    return c_l, c_t


def linear_dispersion_omega_sq(
    wavenumber: float,
    mode: str,
    params: HyperelasticParameters,
) -> float:
    k = float(wavenumber)
    if not math.isfinite(k):
        raise HyperelasticFieldError("wavenumber must be finite")
    c_l, c_t = linear_wave_speeds(params)
    key = mode.strip().lower()
    if key in {"l", "longitudinal"}:
        c = c_l
    elif key in {"t", "transverse"}:
        c = c_t
    else:
        raise HyperelasticFieldError("mode must be longitudinal/L or transverse/T")
    return c * c * k * k + (params.eta / params.rho0) * k ** 4


def periodic_linear_acceleration_1d(
    displacement: Sequence[float],
    dx: float,
    mode: str,
    params: HyperelasticParameters,
) -> tuple[float, ...]:
    """Reference periodic 1D linearized field operator.

    u_tt = c_mode^2 u_xx - (eta/rho0) u_xxxx.
    """
    u = tuple(float(x) for x in displacement)
    if len(u) < 5:
        raise HyperelasticFieldError("need at least five periodic samples")
    if not all(math.isfinite(x) for x in u):
        raise HyperelasticFieldError("displacement samples must be finite")
    h = float(dx)
    if not math.isfinite(h) or h <= 0.0:
        raise HyperelasticFieldError("dx must be finite and positive")
    c_l, c_t = linear_wave_speeds(params)
    key = mode.strip().lower()
    if key in {"l", "longitudinal"}:
        c2 = c_l * c_l
    elif key in {"t", "transverse"}:
        c2 = c_t * c_t
    else:
        raise HyperelasticFieldError("mode must be longitudinal/L or transverse/T")
    q = params.eta / params.rho0
    n = len(u)
    out = []
    for i in range(n):
        im2, im1 = u[(i - 2) % n], u[(i - 1) % n]
        ui, ip1, ip2 = u[i], u[(i + 1) % n], u[(i + 2) % n]
        uxx = (ip1 - 2.0 * ui + im1) / (h * h)
        uxxxx = (ip2 - 4.0 * ip1 + 6.0 * ui - 4.0 * im1 + im2) / (h ** 4)
        out.append(c2 * uxx - q * uxxxx)
    return tuple(out)


def curl_f_from_grad_f(
    grad_f: Sequence[Sequence[Sequence[float]]],
) -> tuple[tuple[float, ...], ...]:
    """Row-wise Curl F: alpha_{iJ}=epsilon_{JKL} partial_K F_{iL}.

    This is a compatibility / defect-density diagnostic. For a smooth
    compatible deformation F=Grad y, Curl F vanishes identically.
    """
    # grad_f[i][L][K] = partial_K F_{iL}
    if len(grad_f) != 3 or any(len(grad_f[i]) != 3 for i in range(3)):
        raise HyperelasticFieldError("Grad F must have shape 3x3x3")
    g = []
    for i in range(3):
        rows = []
        for l in range(3):
            if len(grad_f[i][l]) != 3:
                raise HyperelasticFieldError("Grad F must have shape 3x3x3")
            row = tuple(float(x) for x in grad_f[i][l])
            if not all(math.isfinite(x) for x in row):
                raise HyperelasticFieldError("Grad F entries must be finite")
            rows.append(row)
        g.append(tuple(rows))
    return tuple(
        (
            g[i][2][1] - g[i][1][2],
            g[i][0][2] - g[i][2][0],
            g[i][1][0] - g[i][0][1],
        )
        for i in range(3)
    )


def defect_energy_density(
    grad_f: Sequence[Sequence[Sequence[float]]],
    defect_modulus: float,
) -> float:
    gamma = float(defect_modulus)
    if not math.isfinite(gamma) or gamma < 0.0:
        raise HyperelasticFieldError("defect_modulus must be finite and non-negative")
    alpha = curl_f_from_grad_f(grad_f)
    return 0.5 * gamma * _frob_sq(alpha)
