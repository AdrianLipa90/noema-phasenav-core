"""Full spatial SO(3) orbital representation on the 36-coefficient bivector carrier.

For R in SO(3), embed it in 4D as diag(1,R). In the ordered bivector basis
(01,02,03,23,31,12), the exterior-square representation is exactly

    Lambda^2 diag(1,R) = diag(R,R).

The flattened 6x6 operator therefore has exactly 36 real coefficients.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .orbital_rotation36 import exterior_square6, rotation36_xy

PAIR_BASIS = ((0,1),(0,2),(0,3),(2,3),(3,1),(1,2))


class SpatialRotation36Error(ValueError):
    pass


def _norm3(v: Sequence[float]) -> float:
    if len(v) != 3:
        raise SpatialRotation36Error("expected a 3-vector")
    vals=tuple(float(x) for x in v)
    if not all(math.isfinite(x) for x in vals):
        raise SpatialRotation36Error("vector entries must be finite")
    return math.sqrt(math.fsum(x*x for x in vals))


def _normalize3(v: Sequence[float]) -> tuple[float,float,float]:
    vals=tuple(float(x) for x in v)
    n=_norm3(vals)
    if n == 0.0:
        raise SpatialRotation36Error("axis must be nonzero")
    return tuple(x/n for x in vals)  # type: ignore[return-value]


def cross_generator3(v: Sequence[float]) -> tuple[tuple[float,...],...]:
    """Skew generator [v]_x with [v]_x w = v x w."""
    x,y,z=(float(a) for a in v)
    if not all(math.isfinite(a) for a in (x,y,z)):
        raise SpatialRotation36Error("generator entries must be finite")
    return (
        (0.0,-z, y),
        (z, 0.0,-x),
        (-y,x, 0.0),
    )


def rotation3_axis_angle(axis: Sequence[float], theta: float) -> tuple[tuple[float,...],...]:
    x,y,z=_normalize3(axis)
    t=float(theta)
    if not math.isfinite(t):
        raise SpatialRotation36Error("theta must be finite")
    c,s=math.cos(t),math.sin(t)
    v=1.0-c
    return (
        (c+x*x*v, x*y*v-z*s, x*z*v+y*s),
        (y*x*v+z*s, c+y*y*v, y*z*v-x*s),
        (z*x*v-y*s, z*y*v+x*s, c+z*z*v),
    )


def rotation4_spatial(axis: Sequence[float], theta: float) -> tuple[tuple[float,...],...]:
    r=rotation3_axis_angle(axis,theta)
    return (
        (1.0,0.0,0.0,0.0),
        (0.0,*r[0]),
        (0.0,*r[1]),
        (0.0,*r[2]),
    )


def rotation36_spatial(axis: Sequence[float], theta: float) -> tuple[tuple[float,...],...]:
    return exterior_square6(rotation4_spatial(axis,theta))


def generator36_spatial(axis: Sequence[float]) -> tuple[tuple[float,...],...]:
    k=cross_generator3(_normalize3(axis))
    z=(0.0,0.0,0.0)
    return (
        (k[0][0],k[0][1],k[0][2],0.0,0.0,0.0),
        (k[1][0],k[1][1],k[1][2],0.0,0.0,0.0),
        (k[2][0],k[2][1],k[2][2],0.0,0.0,0.0),
        (0.0,0.0,0.0,k[0][0],k[0][1],k[0][2]),
        (0.0,0.0,0.0,k[1][0],k[1][1],k[1][2]),
        (0.0,0.0,0.0,k[2][0],k[2][1],k[2][2]),
    )


def rotvec_generator36(rotation_vector: Sequence[float]) -> tuple[tuple[float,...],...]:
    """Lie-algebra element diag([omega]_x,[omega]_x)."""
    k=cross_generator3(rotation_vector)
    return (
        (k[0][0],k[0][1],k[0][2],0.0,0.0,0.0),
        (k[1][0],k[1][1],k[1][2],0.0,0.0,0.0),
        (k[2][0],k[2][1],k[2][2],0.0,0.0,0.0),
        (0.0,0.0,0.0,k[0][0],k[0][1],k[0][2]),
        (0.0,0.0,0.0,k[1][0],k[1][1],k[1][2]),
        (0.0,0.0,0.0,k[2][0],k[2][1],k[2][2]),
    )


def rotation36_from_rotvec(rotation_vector: Sequence[float]) -> tuple[tuple[float,...],...]:
    w=tuple(float(x) for x in rotation_vector)
    theta=_norm3(w)
    if theta == 0.0:
        return tuple(tuple(1.0 if i==j else 0.0 for j in range(6)) for i in range(6))
    axis=tuple(x/theta for x in w)
    return rotation36_spatial(axis,theta)


def trace6(matrix6: Sequence[Sequence[float]]) -> float:
    if len(matrix6)!=6 or any(len(row)!=6 for row in matrix6):
        raise SpatialRotation36Error("expected 6x6 matrix")
    return math.fsum(float(matrix6[i][i]) for i in range(6))


def _matmul(a,b):
    return tuple(tuple(math.fsum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))) for i in range(len(a)))


def _transpose(a):
    return tuple(tuple(a[j][i] for j in range(len(a))) for i in range(len(a[0])))


def _frob(a) -> float:
    return math.sqrt(math.fsum(float(x)*float(x) for row in a for x in row))


def _det3(r) -> float:
    return (
        r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])
        -r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])
        +r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0])
    )


@dataclass(frozen=True)
class SpatialRotation36Validation:
    block_residual: float
    orthogonality_residual: float
    determinant_residual: float
    admitted: bool


def validate_spatial_rotation36(
    matrix6: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-10,
) -> SpatialRotation36Validation:
    if len(matrix6)!=6 or any(len(row)!=6 for row in matrix6):
        raise SpatialRotation36Error("expected 6x6 matrix")
    m=tuple(tuple(float(x) for x in row) for row in matrix6)
    if not all(math.isfinite(x) for row in m for x in row):
        raise SpatialRotation36Error("matrix entries must be finite")
    if tolerance < 0.0 or not math.isfinite(tolerance):
        raise SpatialRotation36Error("tolerance must be finite and non-negative")

    a=tuple(tuple(m[i][j] for j in range(3)) for i in range(3))
    b=tuple(tuple(m[i+3][j+3] for j in range(3)) for i in range(3))
    off=math.sqrt(math.fsum(
        m[i][j]*m[i][j]
        for i in range(6) for j in range(6)
        if (i<3) != (j<3)
    ))
    block_diff=_frob(tuple(tuple(a[i][j]-b[i][j] for j in range(3)) for i in range(3)))
    block_res=math.hypot(off,block_diff)

    ata=_matmul(_transpose(a),a)
    ident=tuple(tuple(1.0 if i==j else 0.0 for j in range(3)) for i in range(3))
    ortho=_frob(tuple(tuple(ata[i][j]-ident[i][j] for j in range(3)) for i in range(3)))
    det_res=abs(_det3(a)-1.0)
    admitted=block_res<=tolerance and ortho<=tolerance and det_res<=tolerance
    return SpatialRotation36Validation(block_res,ortho,det_res,admitted)


def axis_angle_from_rotation36(
    matrix6: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-10,
    singular_margin: float = 1e-8,
) -> tuple[tuple[float,float,float],float]:
    check=validate_spatial_rotation36(matrix6,tolerance=tolerance)
    if not check.admitted:
        raise SpatialRotation36Error("matrix is not in the calibrated spatial SO(3) image")
    r=tuple(tuple(float(matrix6[i][j]) for j in range(3)) for i in range(3))
    c=(r[0][0]+r[1][1]+r[2][2]-1.0)/2.0
    c=max(-1.0,min(1.0,c))
    theta=math.acos(c)
    if theta < singular_margin:
        raise SpatialRotation36Error("rotation axis is undefined near theta=0")
    if math.pi-theta < singular_margin:
        raise SpatialRotation36Error("axis extraction near theta=pi requires a separate branch")
    s=2.0*math.sin(theta)
    axis=((r[2][1]-r[1][2])/s,(r[0][2]-r[2][0])/s,(r[1][0]-r[0][1])/s)
    return _normalize3(axis),theta


def calibrated_spatial_residual36(matrix6: Sequence[Sequence[float]]) -> float:
    """For rho_36(R_axis(theta)): (6-tr)/2 = 4 sin^2(theta/2)."""
    return (6.0-trace6(matrix6))/2.0


def z_axis_compatibility_residual(theta: float) -> float:
    a=rotation36_spatial((0.0,0.0,1.0),theta)
    b=rotation36_xy(theta)
    return _frob(tuple(tuple(a[i][j]-b[i][j] for j in range(6)) for i in range(6)))
