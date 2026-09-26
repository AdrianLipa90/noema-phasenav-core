"""Finite-strain multiplicative plasticity on GL+(3).

Kinematics:
    F = F_e F_p
    F_e = F F_p^{-1}

Elastic free energy (compressible neo-Hookean):
    psi(F_e)
      = mu/2 [tr(C_e)-3-2 ln J_e]
        + lambda/2 (ln J_e)^2

Elastic first Piola stress:
    P_e
      = mu(F_e-F_e^{-T})
        + lambda ln(J_e) F_e^{-T}

Mandel stress:
    M = F_e^T P_e

Plastic velocity gradient:
    L_p
      = m_dev dev(sym M)
        + m_vol mean(M) I

At fixed total F:
    psi_dot = - M:L_p <= 0.

The plastic state is updated multiplicatively:
    F_p^{n+1}=exp(dt L_p) F_p^n.

Because det(exp A)=exp(tr A)>0 and det(F_p)>0, the update stays in GL+(3).
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .hyperelastic_field36 import HyperelasticFieldError
from .spatial_deformation36 import det3, inverse3
from .spatial_rotation36 import rotation3_axis_angle


def _m3(a:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    if len(a)!=3 or any(len(r)!=3 for r in a):
        raise HyperelasticFieldError("expected 3x3 matrix")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise HyperelasticFieldError("matrix entries must be finite")
    return m


def identity3():
    return ((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))


def transpose3(a):
    m=_m3(a)
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def matmul3(a,b):
    x=_m3(a); y=_m3(b)
    return tuple(tuple(math.fsum(x[i][k]*y[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def add3(a,b):
    x=_m3(a);y=_m3(b)
    return tuple(tuple(x[i][j]+y[i][j] for j in range(3)) for i in range(3))


def sub3(a,b):
    x=_m3(a);y=_m3(b)
    return tuple(tuple(x[i][j]-y[i][j] for j in range(3)) for i in range(3))


def scale3(s,a):
    q=float(s);m=_m3(a)
    if not math.isfinite(q): raise HyperelasticFieldError("scale must be finite")
    return tuple(tuple(q*m[i][j] for j in range(3)) for i in range(3))


def trace3(a)->float:
    m=_m3(a)
    return float(m[0][0]+m[1][1]+m[2][2])


def frobenius_inner3(a,b)->float:
    x=_m3(a);y=_m3(b)
    return math.fsum(x[i][j]*y[i][j] for i in range(3) for j in range(3))


def frobenius_norm3(a)->float:
    return math.sqrt(frobenius_inner3(a,a))


def sym3(a):
    m=_m3(a)
    return tuple(tuple(0.5*(m[i][j]+m[j][i]) for j in range(3)) for i in range(3))


def mean3(a)->float:
    return trace3(a)/3.0


def dev3(a):
    m=_m3(a); q=mean3(m); I=identity3()
    return tuple(tuple(m[i][j]-q*I[i][j] for j in range(3)) for i in range(3))


def _matrix_inf_norm(a)->float:
    m=_m3(a)
    return max(math.fsum(abs(x) for x in row) for row in m)


def matrix_exponential3(a, *, tolerance:float=1e-16, max_terms:int=80):
    """Pure-Python scaling-and-squaring Taylor expm for a 3x3 matrix."""
    m=_m3(a)
    norm=_matrix_inf_norm(m)
    if norm==0.0:
        return identity3()
    scale_power=max(0,int(math.ceil(math.log(norm/0.5,2.0)))) if norm>0.5 else 0
    scaled=scale3(2.0**(-scale_power),m)
    term=identity3()
    result=identity3()
    converged=False
    for k in range(1,max_terms+1):
        term=scale3(1.0/k,matmul3(term,scaled))
        result=add3(result,term)
        if _matrix_inf_norm(term)<=tolerance*max(1.0,_matrix_inf_norm(result)):
            converged=True
            break
    if not converged:
        raise HyperelasticFieldError("matrix exponential failed to converge")
    for _ in range(scale_power):
        result=matmul3(result,result)
    return result


@dataclass(frozen=True)
class FinitePlasticParameters:
    mu: float
    lame_lambda: float
    dev_mobility: float
    volumetric_mobility: float = 0.0

    def __post_init__(self):
        vals=tuple(float(x) for x in (
            self.mu,self.lame_lambda,self.dev_mobility,self.volumetric_mobility
        ))
        if not all(math.isfinite(x) for x in vals):
            raise HyperelasticFieldError("finite-plastic parameters must be finite")
        mu,lam,md,mv=vals
        if mu<=0.0:
            raise HyperelasticFieldError("mu must be positive")
        if lam+2.0*mu/3.0<=0.0:
            raise HyperelasticFieldError("lambda+2mu/3 must be positive")
        if md<0.0 or mv<0.0:
            raise HyperelasticFieldError("mobilities must be non-negative")
        object.__setattr__(self,"mu",mu)
        object.__setattr__(self,"lame_lambda",lam)
        object.__setattr__(self,"dev_mobility",md)
        object.__setattr__(self,"volumetric_mobility",mv)


@dataclass(frozen=True)
class MultiplicativePlasticState:
    total_f: tuple[tuple[float,...],...]
    plastic_f: tuple[tuple[float,...],...]
    tau: float = 0.0

    def __post_init__(self):
        f=_m3(self.total_f); fp=_m3(self.plastic_f); t=float(self.tau)
        if det3(f)<=0.0:
            raise HyperelasticFieldError("total F must lie in GL+(3)")
        if det3(fp)<=0.0:
            raise HyperelasticFieldError("plastic F_p must lie in GL+(3)")
        if not math.isfinite(t):
            raise HyperelasticFieldError("tau must be finite")
        object.__setattr__(self,"total_f",f)
        object.__setattr__(self,"plastic_f",fp)
        object.__setattr__(self,"tau",t)


def elastic_f(total_f,plastic_f):
    f=_m3(total_f);fp=_m3(plastic_f)
    if det3(f)<=0.0 or det3(fp)<=0.0:
        raise HyperelasticFieldError("F and F_p must lie in GL+(3)")
    return matmul3(f,inverse3(fp))


def elastic_energy_density(fe,params:FinitePlasticParameters)->float:
    e=_m3(fe); j=det3(e)
    if j<=0.0:
        raise HyperelasticFieldError("elastic F_e must lie in GL+(3)")
    c=matmul3(transpose3(e),e)
    ln_j=math.log(j)
    return (
        0.5*params.mu*(trace3(c)-3.0-2.0*ln_j)
        +0.5*params.lame_lambda*ln_j*ln_j
    )


def elastic_first_piola(fe,params:FinitePlasticParameters):
    e=_m3(fe);j=det3(e)
    if j<=0.0:
        raise HyperelasticFieldError("elastic F_e must lie in GL+(3)")
    eit=transpose3(inverse3(e))
    ln_j=math.log(j)
    return tuple(tuple(
        params.mu*(e[i][j]-eit[i][j])
        +params.lame_lambda*ln_j*eit[i][j]
        for j in range(3)
    ) for i in range(3))


def total_first_piola(total_f,plastic_f,params:FinitePlasticParameters):
    fe=elastic_f(total_f,plastic_f)
    pe=elastic_first_piola(fe,params)
    fpit=transpose3(inverse3(plastic_f))
    return matmul3(pe,fpit)


def mandel_stress(total_f,plastic_f,params:FinitePlasticParameters):
    fe=elastic_f(total_f,plastic_f)
    pe=elastic_first_piola(fe,params)
    return matmul3(transpose3(fe),pe)


def plastic_velocity_gradient(total_f,plastic_f,params:FinitePlasticParameters):
    m=sym3(mandel_stress(total_f,plastic_f,params))
    dev=dev3(m)
    q=mean3(m)
    I=identity3()
    return add3(
        scale3(params.dev_mobility,dev),
        scale3(params.volumetric_mobility*q,I),
    )


def plastic_dissipation_rate(total_f,plastic_f,params:FinitePlasticParameters)->float:
    m=sym3(mandel_stress(total_f,plastic_f,params))
    lp=plastic_velocity_gradient(total_f,plastic_f,params)
    d=frobenius_inner3(m,lp)
    if d<0.0 and abs(d)<1e-13:
        d=0.0
    return d


def plastic_step(
    state:MultiplicativePlasticState,
    dt:float,
    params:FinitePlasticParameters,
)->MultiplicativePlasticState:
    h=float(dt)
    if not math.isfinite(h) or h<0.0:
        raise HyperelasticFieldError("dt must be finite and non-negative")
    lp=plastic_velocity_gradient(state.total_f,state.plastic_f,params)
    inc=matrix_exponential3(scale3(h,lp))
    fp1=matmul3(inc,state.plastic_f)
    if det3(fp1)<=0.0:
        raise HyperelasticFieldError("multiplicative update left GL+(3)")
    return MultiplicativePlasticState(state.total_f,fp1,state.tau+h)


def fixed_total_energy(state:MultiplicativePlasticState,params:FinitePlasticParameters)->float:
    return elastic_energy_density(elastic_f(state.total_f,state.plastic_f),params)


def rotated_total_state(state:MultiplicativePlasticState,axis,theta:float):
    q=rotation3_axis_angle(axis,theta)
    return MultiplicativePlasticState(matmul3(q,state.total_f),state.plastic_f,state.tau)
