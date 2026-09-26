"""Thermodynamically admissible small-strain plastic-distortion reference.

Total displacement gradient:
    G = Grad u

Plastic distortion:
    beta_p

Elastic small strain:
    eps_e = sym(G-beta_p)

Free energy:
    psi = mu |eps_e|^2
          + lambda/2 [tr eps_e]^2
          + H/2 |beta_p|^2

Cauchy stress:
    sigma = 2 mu eps_e + lambda tr(eps_e) I

Thermodynamic force conjugate to beta_p:
    Y = sigma - H beta_p = - d psi / d beta_p

Onsager flow:
    beta_p_dot = M Y

Hence at fixed G:
    d psi / d tau = - M |Y|^2 <= 0.

Because the energy is quadratic, the local fixed-G flow is solved exactly by
decomposing beta_p into symmetric deviatoric, spherical and skew sectors.

This is a viscous plastic-distortion reference, not a complete dislocation law.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .hyperelastic_field36 import HyperelasticFieldError, curl_f_from_grad_f


def _m3(a:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    if len(a)!=3 or any(len(r)!=3 for r in a):
        raise HyperelasticFieldError("expected 3x3 matrix")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise HyperelasticFieldError("matrix entries must be finite")
    return m


def _add(a,b):
    return tuple(tuple(a[i][j]+b[i][j] for j in range(3)) for i in range(3))


def _sub(a,b):
    return tuple(tuple(a[i][j]-b[i][j] for j in range(3)) for i in range(3))


def _scale(s,a):
    return tuple(tuple(s*a[i][j] for j in range(3)) for i in range(3))


def _frob_sq(a)->float:
    return math.fsum(x*x for row in a for x in row)


def trace3(a)->float:
    return float(a[0][0]+a[1][1]+a[2][2])


def identity3():
    return ((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))


def sym(a:Sequence[Sequence[float]]):
    m=_m3(a)
    return tuple(tuple(0.5*(m[i][j]+m[j][i]) for j in range(3)) for i in range(3))


def skew(a:Sequence[Sequence[float]]):
    m=_m3(a)
    return tuple(tuple(0.5*(m[i][j]-m[j][i]) for j in range(3)) for i in range(3))


def spherical(a:Sequence[Sequence[float]]):
    m=_m3(a); b=trace3(m)/3.0
    return _scale(b,identity3())


def deviatoric(a:Sequence[Sequence[float]]):
    m=_m3(a)
    return _sub(m,spherical(m))


@dataclass(frozen=True)
class PlasticFlowParameters:
    mu: float
    lame_lambda: float
    hardening: float
    mobility: float

    def __post_init__(self):
        vals=tuple(float(x) for x in (self.mu,self.lame_lambda,self.hardening,self.mobility))
        if not all(math.isfinite(x) for x in vals):
            raise HyperelasticFieldError("plastic-flow parameters must be finite")
        mu,lam,h,m=vals
        if mu<=0.0:
            raise HyperelasticFieldError("mu must be positive")
        if lam+2.0*mu/3.0<=0.0:
            raise HyperelasticFieldError("lambda+2mu/3 must be positive")
        if h<0.0 or m<0.0:
            raise HyperelasticFieldError("hardening and mobility must be non-negative")
        object.__setattr__(self,"mu",mu)
        object.__setattr__(self,"lame_lambda",lam)
        object.__setattr__(self,"hardening",h)
        object.__setattr__(self,"mobility",m)


def elastic_small_strain(total_gradient,beta_p):
    return sym(_sub(_m3(total_gradient),_m3(beta_p)))


def small_strain_stress(total_gradient,beta_p,params:PlasticFlowParameters):
    e=elastic_small_strain(total_gradient,beta_p)
    tr=trace3(e)
    I=identity3()
    return tuple(tuple(
        2.0*params.mu*e[i][j]+params.lame_lambda*tr*I[i][j]
        for j in range(3)
    ) for i in range(3))


def plastic_free_energy_density(total_gradient,beta_p,params:PlasticFlowParameters)->float:
    e=elastic_small_strain(total_gradient,beta_p)
    tr=trace3(e)
    b=_m3(beta_p)
    return (
        params.mu*_frob_sq(e)
        +0.5*params.lame_lambda*tr*tr
        +0.5*params.hardening*_frob_sq(b)
    )


def plastic_driving_force(total_gradient,beta_p,params:PlasticFlowParameters):
    sigma=small_strain_stress(total_gradient,beta_p,params)
    b=_m3(beta_p)
    return _sub(sigma,_scale(params.hardening,b))


def dissipation_rate(total_gradient,beta_p,params:PlasticFlowParameters)->float:
    y=plastic_driving_force(total_gradient,beta_p,params)
    return params.mobility*_frob_sq(y)


def equilibrium_plastic_distortion(total_gradient,params:PlasticFlowParameters):
    """Unique energy minimizer if hardening>0; minimum-norm representative if H=0."""
    e=sym(total_gradient)
    edev=deviatoric(e)
    emean=trace3(e)/3.0
    h=params.hardening
    dev_eq=_scale((2.0*params.mu)/(2.0*params.mu+h),edev)
    a=2.0*params.mu+3.0*params.lame_lambda
    sphere_eq=_scale((a/(a+h))*emean,identity3())
    # Energy is independent of skew beta when H=0; choose zero skew equilibrium.
    return _add(dev_eq,sphere_eq)


def exact_plastic_relaxation_step(
    total_gradient,
    beta_p,
    dt:float,
    params:PlasticFlowParameters,
):
    """Exact local fixed-total-strain Onsager step."""
    t=float(dt)
    if not math.isfinite(t) or t<0.0:
        raise HyperelasticFieldError("dt must be finite and non-negative")
    g=sym(total_gradient)
    b=_m3(beta_p)
    bs=sym(b)
    ba=skew(b)
    bdev=deviatoric(bs)
    bmean=trace3(bs)/3.0

    edev=deviatoric(g)
    emean=trace3(g)/3.0

    h=params.hardening
    m=params.mobility

    rdev=2.0*params.mu+h
    dev_eq=_scale((2.0*params.mu/rdev),edev)
    dev1=_add(dev_eq,_scale(math.exp(-m*rdev*t),_sub(bdev,dev_eq)))

    a=2.0*params.mu+3.0*params.lame_lambda
    rsph=a+h
    mean_eq=(a/rsph)*emean
    mean1=mean_eq+(bmean-mean_eq)*math.exp(-m*rsph*t)
    sph1=_scale(mean1,identity3())

    skew1=_scale(math.exp(-m*h*t),ba) if h>0.0 else ba
    return _add(_add(dev1,sph1),skew1)


def curl_plastic_distortion_from_grad_beta(
    grad_beta:Sequence[Sequence[Sequence[float]]],
):
    """Project convention: alpha = Curl beta_p, row-wise."""
    return curl_f_from_grad_f(grad_beta)
