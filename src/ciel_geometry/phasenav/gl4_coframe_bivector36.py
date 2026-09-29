"""GL(4) coframe -> Bivector36 kinematics.

For A in GL(4), the exterior-square representation

    rho_36(A)=Lambda^2 A

is a 6x6 operator (36 real coefficients) on Lambda^2(R^4), using the project
pair basis

    (01,02,03,23,31,12).

Core identities:
    Lambda^2(AB)=Lambda^2(A)Lambda^2(B)
    det(Lambda^2 A)=det(A)^3
    Lambda^2(-A)=Lambda^2(A)

The last identity is an unavoidable Z2 reconstruction ambiguity.

For Minkowski eta=diag(-1,1,1,1), the induced bivector metric has signature
(3,3). Proper orthochronous Lorentz transformations preserve it.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .hyperelastic_field36 import HyperelasticFieldError
from .orbital_rotation36 import PAIR_BASIS, exterior_square6
from .spatial_deformation36 import deformation36
from .spatial_rotation36 import rotation3_axis_angle, rotation36_spatial


MINKOWSKI_ETA=(
    (-1.0,0.0,0.0,0.0),
    (0.0,1.0,0.0,0.0),
    (0.0,0.0,1.0,0.0),
    (0.0,0.0,0.0,1.0),
)


class Coframe36Error(ValueError):
    pass


def _matrix(a,n:int):
    if len(a)!=n or any(len(r)!=n for r in a):
        raise Coframe36Error(f"expected {n}x{n} matrix")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise Coframe36Error("matrix entries must be finite")
    return m


def matmul(a,b):
    n=len(a); x=_matrix(a,n); y=_matrix(b,n)
    return tuple(tuple(math.fsum(x[i][k]*y[k][j] for k in range(n)) for j in range(n)) for i in range(n))


def transpose(a):
    n=len(a); m=_matrix(a,n)
    return tuple(tuple(m[j][i] for j in range(n)) for i in range(n))


def frobenius_norm(a)->float:
    n=len(a); m=_matrix(a,n)
    return math.sqrt(math.fsum(x*x for r in m for x in r))


def sub(a,b):
    n=len(a);x=_matrix(a,n);y=_matrix(b,n)
    return tuple(tuple(x[i][j]-y[i][j] for j in range(n)) for i in range(n))


def determinant(a)->float:
    """Determinant by Gaussian elimination with partial pivoting."""
    n=len(a); m=[list(r) for r in _matrix(a,n)]
    sign=1.0
    det=1.0
    for col in range(n):
        pivot=max(range(col,n),key=lambda r:abs(m[r][col]))
        if abs(m[pivot][col])<1e-15:
            return 0.0
        if pivot!=col:
            m[col],m[pivot]=m[pivot],m[col]
            sign=-sign
        p=m[col][col]
        det*=p
        for r in range(col+1,n):
            q=m[r][col]/p
            for c in range(col+1,n):
                m[r][c]-=q*m[col][c]
    return sign*det


def inverse4(a):
    m=[list(r) for r in _matrix(a,4)]
    aug=[m[i]+[1.0 if i==j else 0.0 for j in range(4)] for i in range(4)]
    for col in range(4):
        pivot=max(range(col,4),key=lambda r:abs(aug[r][col]))
        if abs(aug[pivot][col])<1e-15:
            raise Coframe36Error("matrix must be invertible")
        if pivot!=col:
            aug[col],aug[pivot]=aug[pivot],aug[col]
        p=aug[col][col]
        aug[col]=[x/p for x in aug[col]]
        for r in range(4):
            if r==col: continue
            q=aug[r][col]
            aug[r]=[aug[r][c]-q*aug[col][c] for c in range(8)]
    return tuple(tuple(aug[i][j+4] for j in range(4)) for i in range(4))


def identity4():
    return tuple(tuple(1.0 if i==j else 0.0 for j in range(4)) for i in range(4))


def lambda2_gl4(a):
    m=_matrix(a,4)
    if abs(determinant(m))<1e-15:
        raise Coframe36Error("GL(4) carrier requires an invertible matrix")
    return exterior_square6(m)


def spatial_embedding4(f3):
    f=_matrix(f3,3)
    return (
        (1.0,0.0,0.0,0.0),
        (0.0,*f[0]),
        (0.0,*f[1]),
        (0.0,*f[2]),
    )


def coframe_metric4(e,eta=MINKOWSKI_ETA):
    """g=e^T eta e; local Lorentz acts from the left on e."""
    q=_matrix(e,4); h=_matrix(eta,4)
    return matmul(transpose(q),matmul(h,q))


def bivector_metric6(eta=MINKOWSKI_ETA):
    h=_matrix(eta,4)
    out=[]
    for i,j in PAIR_BASIS:
        row=[]
        for k,l in PAIR_BASIS:
            row.append(h[i][k]*h[j][l]-h[i][l]*h[j][k])
        out.append(tuple(row))
    return tuple(out)


def lorentz_boost4(axis:Sequence[float],rapidity:float):
    if len(axis)!=3:
        raise Coframe36Error("boost axis must be a 3-vector")
    n=tuple(float(x) for x in axis)
    if not all(math.isfinite(x) for x in n):
        raise Coframe36Error("boost axis must be finite")
    norm=math.sqrt(math.fsum(x*x for x in n))
    if norm==0.0:
        raise Coframe36Error("boost axis must be nonzero")
    n=tuple(x/norm for x in n)
    r=float(rapidity)
    if not math.isfinite(r):
        raise Coframe36Error("rapidity must be finite")
    c=math.cosh(r); s=math.sinh(r)
    out=[[0.0]*4 for _ in range(4)]
    out[0][0]=c
    for i in range(3):
        out[0][i+1]=s*n[i]
        out[i+1][0]=s*n[i]
    for i in range(3):
        for j in range(3):
            out[i+1][j+1]=(1.0 if i==j else 0.0)+(c-1.0)*n[i]*n[j]
    return tuple(tuple(row) for row in out)


def spatial_rotation4(axis:Sequence[float],theta:float):
    r=rotation3_axis_angle(axis,theta)
    return spatial_embedding4(r)


@dataclass(frozen=True)
class Lorentz4Validation:
    metric_residual: float
    determinant_residual: float
    orthochronous_margin: float
    admitted: bool


def validate_lorentz4(a, *, tolerance:float=1e-10)->Lorentz4Validation:
    q=_matrix(a,4)
    pull=matmul(transpose(q),matmul(MINKOWSKI_ETA,q))
    metric_res=frobenius_norm(sub(pull,MINKOWSKI_ETA))
    det_res=abs(determinant(q)-1.0)
    margin=q[0][0]-1.0
    return Lorentz4Validation(
        metric_res,
        det_res,
        margin,
        metric_res<=tolerance and det_res<=tolerance and margin>=-tolerance,
    )


@dataclass(frozen=True)
class BivectorLorentzValidation:
    metric_residual: float
    determinant_residual: float
    admitted: bool


def validate_bivector_lorentz6(b, *, tolerance:float=1e-10)->BivectorLorentzValidation:
    q=_matrix(b,6); g=bivector_metric6()
    pull=matmul(transpose(q),matmul(g,q))
    metric_res=frobenius_norm(sub(pull,g))
    det_res=abs(determinant(q)-1.0)
    return BivectorLorentzValidation(metric_res,det_res,metric_res<=tolerance and det_res<=tolerance)


def left_lorentz_action_on_coframe(lorentz,e):
    l=_matrix(lorentz,4); q=_matrix(e,4)
    if not validate_lorentz4(l).admitted:
        raise Coframe36Error("left action requires a proper orthochronous Lorentz matrix")
    return matmul(l,q)


def z2_partner(a):
    q=_matrix(a,4)
    return tuple(tuple(-x for x in row) for row in q)


def spatial_gl3_compatibility_residual(f3)->float:
    lhs=lambda2_gl4(spatial_embedding4(f3))
    rhs=deformation36(f3)
    return frobenius_norm(sub(lhs,rhs))


def spatial_so3_compatibility_residual(axis,theta:float)->float:
    lhs=lambda2_gl4(spatial_rotation4(axis,theta))
    rhs=rotation36_spatial(axis,theta)
    return frobenius_norm(sub(lhs,rhs))
