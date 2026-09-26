"""Lorentz connection / holonomy kinematics with fail-closed pure-gauge controls.

This module stays at the group/link level. It does not identify nontrivial
holonomy with spacetime curvature until a continuum/small-loop limit and
connection field are separately established.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .gl4_coframe_bivector36 import (
    MINKOWSKI_ETA,
    bivector_metric6,
    determinant,
    frobenius_norm,
    identity4,
    inverse4,
    lambda2_gl4,
    lorentz_boost4,
    matmul,
    spatial_rotation4,
    sub,
    transpose,
    validate_lorentz4,
)


class HolonomyError(ValueError):
    pass


def identity6():
    return tuple(tuple(1.0 if i==j else 0.0 for j in range(6)) for i in range(6))


def _m(a,n):
    if len(a)!=n or any(len(r)!=n for r in a):
        raise HolonomyError(f"expected {n}x{n} matrix")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise HolonomyError("matrix entries must be finite")
    return m


def trace(a)->float:
    n=len(a);m=_m(a,n)
    return math.fsum(m[i][i] for i in range(n))


def link_from_vertex_frames(g_from,g_to):
    a=_m(g_from,4);b=_m(g_to,4)
    if not validate_lorentz4(a).admitted or not validate_lorentz4(b).admitted:
        raise HolonomyError("vertex frames must be proper orthochronous Lorentz matrices")
    return matmul(b,inverse4(a))


def path_holonomy4(links:Sequence[Sequence[Sequence[float]]]):
    h=identity4()
    for u in links:
        q=_m(u,4)
        if not validate_lorentz4(q).admitted:
            raise HolonomyError("all links must be proper orthochronous Lorentz matrices")
        h=matmul(q,h)
    return h


def path_holonomy6_from_links4(links):
    h=identity6()
    for u in links:
        h=matmul(lambda2_gl4(u),h)
    return h


def loop_residual4(links)->float:
    return frobenius_norm(sub(path_holonomy4(links),identity4()))


def loop_residual6(links)->float:
    return frobenius_norm(sub(path_holonomy6_from_links4(links),identity6()))


def gauge_transform_link4(link,h_from,h_to):
    u=_m(link,4);a=_m(h_from,4);b=_m(h_to,4)
    for q in (u,a,b):
        if not validate_lorentz4(q).admitted:
            raise HolonomyError("gauge/link matrices must be proper Lorentz")
    return matmul(b,matmul(u,inverse4(a)))


def conjugate4(h,x):
    q=_m(h,4);a=_m(x,4)
    return matmul(q,matmul(a,inverse4(q)))


def boost_generator4(axis:Sequence[float]):
    if len(axis)!=3:
        raise HolonomyError("axis must be a 3-vector")
    n=tuple(float(x) for x in axis)
    if not all(math.isfinite(x) for x in n):
        raise HolonomyError("axis entries must be finite")
    norm=math.sqrt(math.fsum(x*x for x in n))
    if norm==0.0:
        raise HolonomyError("axis must be nonzero")
    n=tuple(x/norm for x in n)
    return (
        (0.0,n[0],n[1],n[2]),
        (n[0],0.0,0.0,0.0),
        (n[1],0.0,0.0,0.0),
        (n[2],0.0,0.0,0.0),
    )


def rotation_generator4(axis:Sequence[float]):
    if len(axis)!=3:
        raise HolonomyError("axis must be a 3-vector")
    n=tuple(float(x) for x in axis)
    if not all(math.isfinite(x) for x in n):
        raise HolonomyError("axis entries must be finite")
    norm=math.sqrt(math.fsum(x*x for x in n))
    if norm==0.0:
        raise HolonomyError("axis must be nonzero")
    x,y,z=(v/norm for v in n)
    return (
        (0.0,0.0,0.0,0.0),
        (0.0,0.0,-z,y),
        (0.0,z,0.0,-x),
        (0.0,-y,x,0.0),
    )


def lorentz_lie_residual4(omega)->float:
    w=_m(omega,4)
    lhs=matmul(transpose(w),MINKOWSKI_ETA)
    rhs=matmul(MINKOWSKI_ETA,w)
    return frobenius_norm(tuple(tuple(lhs[i][j]+rhs[i][j] for j in range(4)) for i in range(4)))


def induced_generator6(omega):
    """Differential d(Lambda^2)_I(omega) in the declared oriented pair basis."""
    w=_m(omega,4)
    from .orbital_rotation36 import PAIR_BASIS
    out=[]
    for k,l in PAIR_BASIS:
        row=[]
        for i,j in PAIR_BASIS:
            val=(
                w[k][i]*(1.0 if l==j else 0.0)
                +(1.0 if k==i else 0.0)*w[l][j]
                -w[k][j]*(1.0 if l==i else 0.0)
                -(1.0 if k==j else 0.0)*w[l][i]
            )
            row.append(val)
        out.append(tuple(row))
    return tuple(out)


def bivector_lie_residual6(generator6)->float:
    j=_m(generator6,6);g=bivector_metric6()
    lhs=matmul(transpose(j),g)
    rhs=matmul(g,j)
    return frobenius_norm(tuple(tuple(lhs[i][k]+rhs[i][k] for k in range(6)) for i in range(6)))


@dataclass(frozen=True)
class HolonomyWitness:
    trace4: float
    trace6: float
    residual4: float
    residual6: float


def holonomy_witness(links)->HolonomyWitness:
    h4=path_holonomy4(links)
    h6=path_holonomy6_from_links4(links)
    return HolonomyWitness(trace(h4),trace(h6),frobenius_norm(sub(h4,identity4())),frobenius_norm(sub(h6,identity6())))


def pure_gauge_square_links(g0,g1,g2,g3):
    """Links 0->1->2->3->0 from vertex frame values."""
    return (
        link_from_vertex_frames(g0,g1),
        link_from_vertex_frames(g1,g2),
        link_from_vertex_frames(g2,g3),
        link_from_vertex_frames(g3,g0),
    )


def noncommuting_commutator_loop(u,v):
    """Closed algebraic loop U,V,U^{-1},V^{-1}; generally nontrivial if UV!=VU."""
    a=_m(u,4);b=_m(v,4)
    return (a,b,inverse4(a),inverse4(b))
