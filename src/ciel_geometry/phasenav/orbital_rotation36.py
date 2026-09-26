"""Calibrated SO(2) -> 36-coefficient bivector operator representation.

This module defines a typed physical orbital carrier:
    R_4(theta) in the spatial x-y plane,
    rho_36(theta) = Lambda^2 R_4(theta).

The 36 numbers are the flattened coefficients of a 6x6 operator on Lambda^2 R^4.
They are NOT generic PhaseNav phase coordinates.
"""
from __future__ import annotations

import math
from typing import Sequence

PAIR_BASIS = ((0,1),(0,2),(0,3),(2,3),(3,1),(1,2))


def _validate_theta(theta: float) -> float:
    x=float(theta)
    if not math.isfinite(x):
        raise ValueError("theta must be finite")
    return x


def rotation4_xy(theta: float) -> tuple[tuple[float,...],...]:
    """4D embedding of an ordinary spatial x-y rotation."""
    t=_validate_theta(theta)
    c,s=math.cos(t),math.sin(t)
    return (
        (1.0,0.0,0.0,0.0),
        (0.0,c,-s,0.0),
        (0.0,s,c,0.0),
        (0.0,0.0,0.0,1.0),
    )


def exterior_square6(matrix4: Sequence[Sequence[float]]) -> tuple[tuple[float,...],...]:
    """Exterior-square representation Lambda^2 of a 4x4 linear map."""
    if len(matrix4)!=4 or any(len(row)!=4 for row in matrix4):
        raise ValueError("expected 4x4 matrix")
    a=tuple(tuple(float(x) for x in row) for row in matrix4)
    if not all(math.isfinite(x) for row in a for x in row):
        raise ValueError("matrix entries must be finite")
    out=[[0.0]*6 for _ in range(6)]
    for col,(i,j) in enumerate(PAIR_BASIS):
        for row,(k,l) in enumerate(PAIR_BASIS):
            out[row][col]=a[k][i]*a[l][j]-a[k][j]*a[l][i]
    return tuple(tuple(row) for row in out)


def rotation36_xy(theta: float) -> tuple[tuple[float,...],...]:
    """rho_36(theta)=Lambda^2 R_xy(theta), represented as 6x6 / 36 coefficients."""
    return exterior_square6(rotation4_xy(theta))


def flatten36(matrix6: Sequence[Sequence[float]]) -> tuple[float,...]:
    if len(matrix6)!=6 or any(len(row)!=6 for row in matrix6):
        raise ValueError("expected 6x6 matrix")
    vals=tuple(float(x) for row in matrix6 for x in row)
    if not all(math.isfinite(x) for x in vals):
        raise ValueError("matrix entries must be finite")
    return vals


def generator36_xy() -> tuple[tuple[float,...],...]:
    """J_36=d/dtheta rho_36(theta)|_0 in PAIR_BASIS ordering."""
    return (
        (0.0,-1.0,0.0,0.0,0.0,0.0),
        (1.0, 0.0,0.0,0.0,0.0,0.0),
        (0.0, 0.0,0.0,0.0,0.0,0.0),
        (0.0, 0.0,0.0,0.0,-1.0,0.0),
        (0.0, 0.0,0.0,1.0, 0.0,0.0),
        (0.0, 0.0,0.0,0.0, 0.0,0.0),
    )


def trace6(matrix6: Sequence[Sequence[float]]) -> float:
    if len(matrix6)!=6 or any(len(row)!=6 for row in matrix6):
        raise ValueError("expected 6x6 matrix")
    return math.fsum(float(matrix6[i][i]) for i in range(6))


def calibrated_twist_residual36(matrix6: Sequence[Sequence[float]]) -> float:
    """Typed bivector-36 twist residual.

    For matrix6=rho_36(theta):
        (6-tr(matrix6))/2 = 4 sin^2(theta/2).
    """
    d=(6.0-trace6(matrix6))/2.0
    if d<0.0 and abs(d)<1e-14:
        d=0.0
    return d


def twist_from_rotation36_trace(matrix6: Sequence[Sequence[float]]) -> float:
    """Recover principal |theta| in [0,pi] from a calibrated rho_36 carrier."""
    tr=trace6(matrix6)
    c=(tr-2.0)/4.0
    if c>1.0 and c-1.0<1e-14: c=1.0
    if c<-1.0 and -1.0-c<1e-14: c=-1.0
    if not -1.0<=c<=1.0:
        raise ValueError("matrix trace is outside calibrated SO(2) bivector range")
    return math.acos(c)


def moire_period_from_rotation36(lattice_constant: float, matrix6: Sequence[Sequence[float]]) -> float:
    """Map calibrated typed bivector rotation to identical-lattice Moire period."""
    a=float(lattice_constant)
    if not math.isfinite(a) or a<=0.0:
        raise ValueError("lattice_constant must be finite and positive")
    d=calibrated_twist_residual36(matrix6)
    if d==0.0:
        return math.inf
    if d<0.0:
        raise ValueError("negative calibrated residual")
    return a/math.sqrt(d)
