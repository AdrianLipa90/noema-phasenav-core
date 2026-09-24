"""Frame/curvature interpretation of the existing 36D bivector split.

This module corrects the earlier provisional interpretation of the 20D
J-self-adjoint traceless complement as a generic "simplicity defect".

For an oriented four-dimensional carrier with wedge pairing J,

    Mat(6) = co(3,3) + K(V)

where the 16D co(3,3) sector is the exterior-square image of gl(4), while the
20D complement maps to algebraic curvature tensors through S = J Q.

This is pointwise representation theory. It does not assert that Q is the
Levi-Civita curvature of the frame sector without differential compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .bivector36 import BivectorField36, wedge_pairing
from .moire_bivector_decoder import (
    Co33Decomposition,
    decompose_co33,
    inverse_lie_exterior_square,
)

J=wedge_pairing()


def _matmul(a,b):
    return tuple(
        tuple(
            math.fsum(a[i][k]*b[k][j] for k in range(len(b)))
            for j in range(len(b[0]))
        )
        for i in range(len(a))
    )


def _transpose(a):
    return tuple(
        tuple(a[j][i] for j in range(len(a)))
        for i in range(len(a[0]))
    )


def _frob(a):
    return math.sqrt(math.fsum(x*x for row in a for x in row))


@dataclass(frozen=True)
class FrameCurvatureSplit36:
    raw: BivectorField36
    frame_sector: BivectorField36
    algebraic_curvature_sector: BivectorField36
    algebraic_curvature_bilinear6: tuple[tuple[float,...],...]
    frame_generator4: tuple[tuple[float,...],...]
    frame_dimension: int
    curvature_dimension: int
    bianchi_residual: float
    curvature_symmetry_residual: float
    frame_fraction_frob2: float
    curvature_fraction_frob2: float
    candidate_only: bool=True
    physical_curvature_claim: bool=False

    @property
    def reconstruction_fraction(self) -> float:
        return self.frame_fraction_frob2 + self.curvature_fraction_frob2


def split_frame_curvature(field: BivectorField36) -> FrameCurvatureSplit36:
    d: Co33Decomposition=decompose_co33(field)
    q=d.defect.matrix6
    s=_matmul(J,q)
    sym=_transpose(s)

    symmetry_residual=_frob(
        tuple(
            tuple(s[i][j]-sym[i][j] for j in range(6))
            for i in range(6)
        )
    )
    bianchi=abs(s[0][3]+s[1][4]+s[2][5])

    total2=math.fsum(x*x for row in field.matrix6 for x in row)
    frame2=math.fsum(x*x for row in d.geometric.matrix6 for x in row)
    curvature2=math.fsum(x*x for row in q for x in row)
    denom=max(total2,1e-300)

    return FrameCurvatureSplit36(
        raw=field,
        frame_sector=d.geometric,
        algebraic_curvature_sector=d.defect,
        algebraic_curvature_bilinear6=s,
        frame_generator4=inverse_lie_exterior_square(d.geometric),
        frame_dimension=16,
        curvature_dimension=20,
        bianchi_residual=bianchi,
        curvature_symmetry_residual=symmetry_residual,
        frame_fraction_frob2=frame2/denom,
        curvature_fraction_frob2=curvature2/denom,
    )
