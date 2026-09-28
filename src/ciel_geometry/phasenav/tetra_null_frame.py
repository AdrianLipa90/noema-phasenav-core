"""Typed tetrahedral null-frame, null-event lift, and bivector-36 parity carrier.

This module preserves both established interfaces:
- the typed BivectorField36 carrier built from canonical tetrahedral frames;
- the normalized TIR/IDT null-event lift x=(ell/2)(1,n), its Minkowski
  invariants, conformal/parity receipt, and generic GL(4) frame-pair route.

The legacy anonymous phi_0..phi_35 ordering is not reinterpreted here.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .bivector36 import BivectorField36, exterior_square

TETRA_SIGN_VECTORS=(
    (1.0,1.0,1.0),
    (1.0,-1.0,-1.0),
    (-1.0,1.0,-1.0),
    (-1.0,-1.0,1.0),
)
PAIR_BASIS=((0,1),(0,2),(0,3),(2,3),(3,1),(1,2))
E_PLUS=(
    (1.0,1.0,1.0,1.0),
    (1.0,1.0,-1.0,-1.0),
    (1.0,-1.0,1.0,-1.0),
    (1.0,-1.0,-1.0,1.0),
)
PARITY=(
    (1.0,0.0,0.0,0.0),
    (0.0,-1.0,0.0,0.0),
    (0.0,0.0,-1.0,0.0),
    (0.0,0.0,0.0,-1.0),
)
ETA=PARITY


def _matmul(a,b):
    return tuple(
        tuple(
            math.fsum(a[i][k]*b[k][j] for k in range(len(b)))
            for j in range(len(b[0]))
        )
        for i in range(len(a))
    )


def _transpose(a):
    return tuple(tuple(a[j][i] for j in range(len(a))) for i in range(len(a[0])))


def _max_abs_diff(a,b):
    return max(abs(x-y) for ra,rb in zip(a,b) for x,y in zip(ra,rb))


def _inverse4(a):
    if len(a)!=4 or any(len(row)!=4 for row in a):
        raise ValueError("expected 4x4 matrix")
    m=[
        [float(x) for x in row]
        + [1.0 if i==j else 0.0 for j in range(4)]
        for i,row in enumerate(a)
    ]
    for col in range(4):
        pivot=max(range(col,4),key=lambda r:abs(m[r][col]))
        if abs(m[pivot][col])<1e-15:
            raise ValueError("singular 4x4 frame")
        m[col],m[pivot]=m[pivot],m[col]
        s=m[col][col]
        m[col]=[x/s for x in m[col]]
        for r in range(4):
            if r==col:
                continue
            f=m[r][col]
            m[r]=[x-f*y for x,y in zip(m[r],m[col])]
    return tuple(tuple(row[4:]) for row in m)


def determinant4(a):
    if len(a)!=4 or any(len(row)!=4 for row in a):
        raise ValueError("expected 4x4 matrix")
    m=[list(map(float,row)) for row in a]
    det=1.0
    sign=1.0
    for col in range(4):
        pivot=max(range(col,4),key=lambda r:abs(m[r][col]))
        if abs(m[pivot][col])<=1e-14:
            return 0.0
        if pivot!=col:
            m[col],m[pivot]=m[pivot],m[col]
            sign*=-1.0
        piv=m[col][col]
        det*=piv
        for row in range(col+1,4):
            factor=m[row][col]/piv
            for j in range(col+1,4):
                m[row][j]-=factor*m[col][j]
    return sign*det


def minkowski_inner(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x)!=4 or len(y)!=4:
        raise ValueError("expected 4-vectors")
    return float(x[0]*y[0]-x[1]*y[1]-x[2]*y[2]-x[3]*y[3])


def tetra_null_frame(elapsed_scale: float=2.0, *, antipodal: bool=False):
    """Return the normalized tetrahedral TIR/IDT null-event frame as columns."""
    ell=float(elapsed_scale)
    if not math.isfinite(ell) or ell<=0:
        raise ValueError("elapsed_scale must be finite and positive")
    s=ell/2.0
    root3=math.sqrt(3.0)
    columns=[]
    for raw in TETRA_SIGN_VECTORS:
        direction=tuple(((-v if antipodal else v)/root3) for v in raw)
        columns.append((s,s*direction[0],s*direction[1],s*direction[2]))
    return tuple(tuple(columns[col][row] for col in range(4)) for row in range(4))


def frame_columns(frame4):
    return tuple(tuple(frame4[row][col] for row in range(4)) for col in range(4))


def canonical_plus_frame4():
    return E_PLUS


def canonical_minus_frame4():
    return _matmul(PARITY,E_PLUS)


def relative_frame(reference4, target4):
    """Return target * inverse(reference)."""
    return _matmul(target4,_inverse4(reference4))


def exterior_square4(e4):
    if len(e4)!=4 or any(len(row)!=4 for row in e4):
        raise ValueError("expected 4x4 matrix")
    return exterior_square(e4)


def canonical_bivector_frames():
    return (
        BivectorField36(exterior_square(canonical_plus_frame4())),
        BivectorField36(exterior_square(canonical_minus_frame4())),
    )


def canonical_bivector_parity():
    return BivectorField36(exterior_square(PARITY))


def relative_bivector_operator(
    left_frame4: Sequence[Sequence[float]],
    right_frame4: Sequence[Sequence[float]],
) -> BivectorField36:
    left=tuple(tuple(float(x) for x in row) for row in left_frame4)
    right=tuple(tuple(float(x) for x in row) for row in right_frame4)
    if len(left)!=4 or len(right)!=4 or any(len(r)!=4 for r in left+right):
        raise ValueError("expected two 4x4 frames")
    return BivectorField36(exterior_square(relative_frame(left,right)))


@dataclass(frozen=True)
class AntipodalOverlay36:
    half_sum: BivectorField36
    half_difference: BivectorField36
    parity_operator: BivectorField36
    legacy_phase36_required: bool=False
    physical_gravity_claim: bool=False


def canonical_antipodal_overlay() -> AntipodalOverlay36:
    plus,minus=canonical_bivector_frames()
    hs=tuple(
        tuple(0.5*(a+b) for a,b in zip(ra,rb))
        for ra,rb in zip(plus.matrix6,minus.matrix6)
    )
    hd=tuple(
        tuple(0.5*(a-b) for a,b in zip(ra,rb))
        for ra,rb in zip(plus.matrix6,minus.matrix6)
    )
    return AntipodalOverlay36(
        BivectorField36(hs),
        BivectorField36(hd),
        canonical_bivector_parity(),
    )


@dataclass(frozen=True)
class AntipodalSplit4:
    common_rank1: tuple[tuple[float,...],...]
    differential_rank3: tuple[tuple[float,...],...]
    physical_time_space_binding: str="CONDITIONAL"
    gravity_claim: bool=False


def canonical_antipodal_split4() -> AntipodalSplit4:
    plus=canonical_plus_frame4()
    minus=canonical_minus_frame4()
    common=tuple(
        tuple(0.5*(a+b) for a,b in zip(ra,rb))
        for ra,rb in zip(plus,minus)
    )
    differential=tuple(
        tuple(0.5*(a-b) for a,b in zip(ra,rb))
        for ra,rb in zip(plus,minus)
    )
    return AntipodalSplit4(common,differential)


@dataclass(frozen=True)
class StellaParityReceipt:
    reference_frame4: tuple[tuple[float,...],...]
    antipodal_frame4: tuple[tuple[float,...],...]
    relative_frame4: tuple[tuple[float,...],...]
    bivector6: tuple[tuple[float,...],...]
    scale_ratio: float
    expected_parity_residual: float
    metric_conformal_residual: float
    candidate_only: bool=True
    physical_gravity_claim: bool=False


def stella_parity_receipt(
    elapsed_scale_plus: float=2.0,
    elapsed_scale_minus: float=2.0,
) -> StellaParityReceipt:
    plus=tetra_null_frame(elapsed_scale_plus,antipodal=False)
    minus=tetra_null_frame(elapsed_scale_minus,antipodal=True)
    rel=relative_frame(plus,minus)
    q=float(elapsed_scale_minus)/float(elapsed_scale_plus)
    expected=tuple(
        tuple(q*PARITY[i][j] for j in range(4))
        for i in range(4)
    )
    metric=_matmul(_matmul(_transpose(rel),ETA),rel)
    metric_target=tuple(
        tuple(q*q*ETA[i][j] for j in range(4))
        for i in range(4)
    )
    return StellaParityReceipt(
        reference_frame4=plus,
        antipodal_frame4=minus,
        relative_frame4=rel,
        bivector6=exterior_square4(rel),
        scale_ratio=q,
        expected_parity_residual=_max_abs_diff(rel,expected),
        metric_conformal_residual=_max_abs_diff(metric,metric_target),
    )


def generic_frame_pair(reference4, target4):
    """General algebraic route for a deformed pair of independent 4D frames."""
    rel=relative_frame(reference4,target4)
    return {
        "relative_frame4":rel,
        "bivector6":exterior_square4(rel),
        "det_relative":determinant4(rel),
        "candidate_only":True,
        "physical_gravity_claim":False,
    }
