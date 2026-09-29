"""GL(3) spatial deformation lifted to the 36-coefficient bivector carrier.

For invertible F in GL(3), embed E=diag(1,F). In the ordered bivector basis
(01,02,03,23,31,12),

    Lambda^2 E = diag(F, cof(F)),

where cof(F)=det(F) F^{-T}.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .orbital_rotation36 import exterior_square6

PAIR_BASIS=((0,1),(0,2),(0,3),(2,3),(3,1),(1,2))
TAU=2.0*math.pi


class Deformation36Error(ValueError):
    pass


def _matrix3(a:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    if len(a)!=3 or any(len(r)!=3 for r in a):
        raise Deformation36Error("expected 3x3 matrix")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise Deformation36Error("matrix entries must be finite")
    return m


def det3(a:Sequence[Sequence[float]])->float:
    m=_matrix3(a)
    return (
        m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
        -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
        +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0])
    )


def inverse3(a:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    m=_matrix3(a); d=det3(m)
    if abs(d)<1e-15:
        raise Deformation36Error("matrix must be invertible")
    cof=[]
    for i in range(3):
        row=[]
        for j in range(3):
            rows=[r for r in range(3) if r!=i]
            cols=[c for c in range(3) if c!=j]
            minor=m[rows[0]][cols[0]]*m[rows[1]][cols[1]]-m[rows[0]][cols[1]]*m[rows[1]][cols[0]]
            row.append(((-1.0)**(i+j))*minor)
        cof.append(tuple(row))
    return tuple(tuple(cof[j][i]/d for j in range(3)) for i in range(3))


def transpose3(a:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    m=_matrix3(a)
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def cofactor3(a:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    m=_matrix3(a); d=det3(m); inv=inverse3(m)
    return tuple(tuple(d*inv[j][i] for j in range(3)) for i in range(3))


def embed4_spatial_deformation(f:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    m=_matrix3(f)
    return (
        (1.0,0.0,0.0,0.0),
        (0.0,*m[0]),
        (0.0,*m[1]),
        (0.0,*m[2]),
    )


def deformation36(f:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    if abs(det3(f))<1e-15:
        raise Deformation36Error("deformation must be invertible")
    return exterior_square6(embed4_spatial_deformation(f))


def expected_block_deformation36(f:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    m=_matrix3(f); c=cofactor3(m)
    return tuple(tuple(
        m[i][j] if i<3 and j<3
        else c[i-3][j-3] if i>=3 and j>=3
        else 0.0
        for j in range(6)
    ) for i in range(6))


def _frob(a)->float:
    return math.sqrt(math.fsum(float(x)*float(x) for row in a for x in row))


@dataclass(frozen=True)
class Deformation36Validation:
    determinant3: float
    off_block_residual: float
    cofactor_residual: float
    admitted: bool


def validate_deformation36(
    matrix6:Sequence[Sequence[float]],
    *,
    tolerance:float=1e-10,
)->Deformation36Validation:
    if len(matrix6)!=6 or any(len(r)!=6 for r in matrix6):
        raise Deformation36Error("expected 6x6 matrix")
    m=tuple(tuple(float(x) for x in r) for r in matrix6)
    if not all(math.isfinite(x) for r in m for x in r):
        raise Deformation36Error("matrix entries must be finite")
    f=tuple(tuple(m[i][j] for j in range(3)) for i in range(3))
    d=det3(f)
    if abs(d)<1e-15:
        return Deformation36Validation(d,math.inf,math.inf,False)
    c=cofactor3(f)
    off=math.sqrt(math.fsum(
        m[i][j]*m[i][j]
        for i in range(6) for j in range(6)
        if (i<3)!=(j<3)
    ))
    cr=_frob(tuple(tuple(m[i+3][j+3]-c[i][j] for j in range(3)) for i in range(3)))
    return Deformation36Validation(d,off,cr,off<=tolerance and cr<=tolerance)


def recover_deformation3(
    matrix6:Sequence[Sequence[float]],
    *,
    tolerance:float=1e-10,
)->tuple[tuple[float,...],...]:
    v=validate_deformation36(matrix6,tolerance=tolerance)
    if not v.admitted:
        raise Deformation36Error("matrix is not in the calibrated GL(3) deformation image")
    return tuple(tuple(float(matrix6[i][j]) for j in range(3)) for i in range(3))


def _matrix2(a):
    if len(a)!=2 or any(len(r)!=2 for r in a): raise Deformation36Error("expected 2x2 matrix")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r): raise Deformation36Error("2x2 entries must be finite")
    return m


def det2(a)->float:
    m=_matrix2(a); return m[0][0]*m[1][1]-m[0][1]*m[1][0]


def inverse2(a):
    m=_matrix2(a); d=det2(m)
    if abs(d)<1e-15: raise Deformation36Error("2x2 matrix must be invertible")
    return ((m[1][1]/d,-m[0][1]/d),(-m[1][0]/d,m[0][0]/d))


def transpose2(a):
    m=_matrix2(a); return ((m[0][0],m[1][0]),(m[0][1],m[1][1]))


def matmul2(a,b):
    x=_matrix2(a);y=_matrix2(b)
    return tuple(tuple(math.fsum(x[i][k]*y[k][j] for k in range(2)) for j in range(2)) for i in range(2))


def reciprocal_basis2(direct_basis):
    """Return B=2pi A^{-T}; columns of A are direct primitive vectors."""
    return tuple(tuple(TAU*x for x in row) for row in transpose2(inverse2(direct_basis)))


def moire_reciprocal_delta2(direct_basis,deformation2):
    """Delta B=(F^{-T}-I)B for layer2=F layer1."""
    b=reciprocal_basis2(direct_basis)
    fit=transpose2(inverse2(deformation2))
    b2=matmul2(fit,b)
    return tuple(tuple(b2[i][j]-b[i][j] for j in range(2)) for i in range(2))


def moire_direct_basis2(direct_basis,deformation2):
    """Real-space Moire primitive matrix A_M=2pi (Delta B)^(-T)."""
    db=moire_reciprocal_delta2(direct_basis,deformation2)
    if abs(det2(db))<1e-15:
        raise Deformation36Error("Moire reciprocal mismatch is singular")
    return tuple(tuple(TAU*x for x in row) for row in transpose2(inverse2(db)))


def hex_direct_basis2(lattice_constant:float):
    a=float(lattice_constant)
    if not math.isfinite(a) or a<=0.0: raise Deformation36Error("lattice_constant must be finite and positive")
    return ((a,0.5*a),(0.0,0.5*math.sqrt(3.0)*a))


def rotation2(theta:float):
    t=float(theta)
    if not math.isfinite(t): raise Deformation36Error("theta must be finite")
    c,s=math.cos(t),math.sin(t)
    return ((c,-s),(s,c))


def isotropic_scale2(scale:float):
    s=float(scale)
    if not math.isfinite(s) or s==0.0: raise Deformation36Error("scale must be finite and nonzero")
    return ((s,0.0),(0.0,s))


def column_lengths2(a):
    m=_matrix2(a)
    return (
        math.hypot(m[0][0],m[1][0]),
        math.hypot(m[0][1],m[1][1]),
    )
