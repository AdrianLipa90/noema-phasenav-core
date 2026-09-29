"""Independent straight-string-dust source reference for Einstein admission.

For a static congruence of straight strings aligned with z, with density rho,
signature (-,+,+,+):

    T^{mu nu} = rho (u^mu u^nu - s^mu s^nu)

with
    u^mu=(1,0,0,0),
    s^mu=(0,0,0,1)

for the validated static product metric.

Thus
    T_cov = diag(rho,0,0,-rho)
    T^mu_nu = diag(-rho,0,0,-rho).

This is an independently typed source model. Matching it to a geometry is a
separate equation and is not used to define the source semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .einstein_geometric_reference import EinsteinConformalReference
from .gl4_coframe_bivector36 import frobenius_norm, sub


class StringDustSourceError(ValueError):
    pass


def string_dust_cov(rho:float):
    r=float(rho)
    if not math.isfinite(r):
        raise StringDustSourceError("rho must be finite")
    return (
        (r,0.0,0.0,0.0),
        (0.0,0.0,0.0,0.0),
        (0.0,0.0,0.0,0.0),
        (0.0,0.0,0.0,-r),
    )


def string_dust_mixed(rho:float):
    r=float(rho)
    if not math.isfinite(r):
        raise StringDustSourceError("rho must be finite")
    return (
        (-r,0.0,0.0,0.0),
        (0.0,0.0,0.0,0.0),
        (0.0,0.0,0.0,0.0),
        (0.0,0.0,0.0,-r),
    )


def required_density_for_reference(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    *,
    coupling:float,
)->float:
    k=float(coupling)
    if not math.isfinite(k) or k<=0.0:
        raise StringDustSourceError("coupling must be finite and positive")
    q=ref._q(x,y)
    return -q/k


def source_equation_residual(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    rho:float,
    *,
    coupling:float,
)->float:
    k=float(coupling)
    if not math.isfinite(k) or k<=0.0:
        raise StringDustSourceError("coupling must be finite and positive")
    rhs=tuple(tuple(k*v for v in row) for row in string_dust_cov(rho))
    return frobenius_norm(sub(ref.einstein_cov4(x,y),rhs))


def mixed_covariant_divergence_reference(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    rho:float,
    *,
    rho_t:float=0.0,
    rho_z:float=0.0,
):
    """Divergence for the aligned-string mixed tensor on this static product geometry.

    For rho=rho(x,y), the result is identically zero. Time/z dependence appears
    through the t and z conservation channels.
    """
    rt=float(rho_t);rz=float(rho_z)
    if not math.isfinite(rt) or not math.isfinite(rz):
        raise StringDustSourceError("density derivatives must be finite")
    # T^t_t=-rho and T^z_z=-rho; all relevant Gamma couplings vanish for the
    # reference product metric. Therefore only t and z derivatives remain.
    return (-rt,0.0,0.0,-rz)


def weak_energy_condition_holds(rho:float)->bool:
    r=float(rho)
    return math.isfinite(r) and r>=0.0


def dominant_energy_condition_holds(rho:float)->bool:
    # Principal pressures: p_x=p_y=0, p_z=-rho. DEC requires rho>=|p_i|.
    r=float(rho)
    return math.isfinite(r) and r>=0.0


def proper_energy_per_coordinate_area(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    rho:float,
)->float:
    """rho * sqrt(det h_xy) = rho * exp(2 sigma)."""
    r=float(rho)
    return r*math.exp(2.0*ref.sigma(x,y))


def matched_proper_energy_per_coordinate_area(
    ref:EinsteinConformalReference,
    *,
    coupling:float,
)->float:
    """For rho_required=-4a e^-2sigma/kappa, proper areal density is constant."""
    k=float(coupling)
    if not math.isfinite(k) or k<=0.0:
        raise StringDustSourceError("coupling must be finite and positive")
    return -4.0*ref.a/k
