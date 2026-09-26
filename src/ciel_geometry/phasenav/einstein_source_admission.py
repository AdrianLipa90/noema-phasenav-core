"""Einstein-source admission helpers for the validated geometric reference.

This module does not invent a physical source. It provides fail-closed tests
that any proposed T_{mu nu} must pass before coupling claims are made.
"""
from __future__ import annotations

import math
from typing import Sequence

from .einstein_geometric_reference import EinsteinConformalReference
from .gl4_coframe_bivector36 import frobenius_norm, sub


class SourceAdmissionError(ValueError):
    pass


def _m4(a):
    if len(a)!=4 or any(len(r)!=4 for r in a):
        raise SourceAdmissionError("expected 4x4 tensor")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise SourceAdmissionError("tensor entries must be finite")
    return m


def add_scaled(a,b,scale:float):
    x=_m4(a);y=_m4(b);q=float(scale)
    if not math.isfinite(q):
        raise SourceAdmissionError("scale must be finite")
    return tuple(tuple(x[i][j]+q*y[i][j] for j in range(4)) for i in range(4))


def tensor_symmetry_residual(a)->float:
    x=_m4(a)
    xt=tuple(tuple(x[j][i] for j in range(4)) for i in range(4))
    return frobenius_norm(sub(x,xt))


def einstein_equation_residual(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    source_cov,
    *,
    coupling:float,
    cosmological_constant:float=0.0,
)->float:
    k=float(coupling);lam=float(cosmological_constant)
    if not math.isfinite(k) or k==0.0:
        raise SourceAdmissionError("coupling must be finite and nonzero")
    if not math.isfinite(lam):
        raise SourceAdmissionError("cosmological_constant must be finite")
    t=_m4(source_cov)
    if tensor_symmetry_residual(t)>1e-10:
        raise SourceAdmissionError("source tensor must be symmetric")
    lhs=add_scaled(ref.einstein_cov4(x,y),ref.metric4(x,y),lam)
    rhs=tuple(tuple(k*t[i][j] for j in range(4)) for i in range(4))
    return frobenius_norm(sub(lhs,rhs))


def vacuum_lambda_residual(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    cosmological_constant:float,
)->float:
    lam=float(cosmological_constant)
    return frobenius_norm(add_scaled(ref.einstein_cov4(x,y),ref.metric4(x,y),lam))


def best_fit_vacuum_lambda(ref:EinsteinConformalReference,x:float,y:float):
    """Least-squares Lambda minimizing ||G+Lambda g||_F at one point."""
    G=ref.einstein_cov4(x,y)
    g=ref.metric4(x,y)
    dot=sum(G[i][j]*g[i][j] for i in range(4) for j in range(4))
    gg=sum(g[i][j]*g[i][j] for i in range(4) for j in range(4))
    lam=-dot/gg
    return lam,vacuum_lambda_residual(ref,x,y,lam)


def covariant_divergence_mixed(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    tensor_mixed,
    partials,
):
    """Compute nabla_mu T^mu_nu.

    partials[coord][rho][nu] = partial_coord T^rho_nu.
    """
    T=_m4(tensor_mixed)
    if len(partials)!=4:
        raise SourceAdmissionError("partials must have shape 4x4x4")
    d=[]
    for c in range(4):
        if len(partials[c])!=4 or any(len(r)!=4 for r in partials[c]):
            raise SourceAdmissionError("partials must have shape 4x4x4")
        block=tuple(tuple(float(v) for v in r) for r in partials[c])
        if not all(math.isfinite(v) for r in block for v in r):
            raise SourceAdmissionError("partial entries must be finite")
        d.append(block)
    Gamma=ref.christoffel4(x,y)
    out=[]
    for nu in range(4):
        val=0.0
        for mu in range(4):
            val+=d[mu][mu][nu]
            for lam in range(4):
                val+=Gamma[mu][mu][lam]*T[lam][nu]
                val-=Gamma[lam][mu][nu]*T[mu][lam]
        out.append(val)
    return tuple(out)


def geometric_placeholder_source_cov(
    ref:EinsteinConformalReference,
    x:float,
    y:float,
    *,
    coupling:float,
    cosmological_constant:float=0.0,
):
    """Algebraic placeholder only: (G+Lambda g)/kappa.

    Returning this tensor does NOT establish a physical source mechanism.
    """
    k=float(coupling)
    if not math.isfinite(k) or k==0.0:
        raise SourceAdmissionError("coupling must be finite and nonzero")
    lhs=add_scaled(ref.einstein_cov4(x,y),ref.metric4(x,y),cosmological_constant)
    return tuple(tuple(lhs[i][j]/k for j in range(4)) for i in range(4))
