"""Typed tetrahedral null-frame -> bivector-36 carrier.

This is a separate candidate carrier. It does not reinterpret legacy
phi_0..phi_35 as bivector coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .bivector36 import BivectorField36, exterior_square

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

def _matmul(a,b):
    return tuple(tuple(math.fsum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))) for i in range(len(a)))

def _transpose(a):
    return tuple(tuple(a[j][i] for j in range(len(a))) for i in range(len(a[0])))

def _inverse4(a):
    m=[list(map(float,row))+[1.0 if i==j else 0.0 for j in range(4)] for i,row in enumerate(a)]
    for col in range(4):
        pivot=max(range(col,4),key=lambda r:abs(m[r][col]))
        if abs(m[pivot][col])<1e-15: raise ValueError("singular 4x4 frame")
        m[col],m[pivot]=m[pivot],m[col]
        s=m[col][col]
        m[col]=[x/s for x in m[col]]
        for r in range(4):
            if r==col: continue
            f=m[r][col]
            m[r]=[x-f*y for x,y in zip(m[r],m[col])]
    return tuple(tuple(row[4:]) for row in m)

def canonical_plus_frame4():
    return E_PLUS

def canonical_minus_frame4():
    return _matmul(PARITY,E_PLUS)

def canonical_bivector_frames():
    return (
        BivectorField36(exterior_square(canonical_plus_frame4())),
        BivectorField36(exterior_square(canonical_minus_frame4())),
    )

def canonical_bivector_parity():
    return BivectorField36(exterior_square(PARITY))

def relative_bivector_operator(left_frame4: Sequence[Sequence[float]], right_frame4: Sequence[Sequence[float]]) -> BivectorField36:
    left=tuple(tuple(float(x) for x in row) for row in left_frame4)
    right=tuple(tuple(float(x) for x in row) for row in right_frame4)
    if len(left)!=4 or len(right)!=4 or any(len(r)!=4 for r in left+right):
        raise ValueError("expected two 4x4 frames")
    e=_matmul(right,_inverse4(left))
    return BivectorField36(exterior_square(e))

@dataclass(frozen=True)
class AntipodalOverlay36:
    half_sum: BivectorField36
    half_difference: BivectorField36
    parity_operator: BivectorField36
    legacy_phase36_required: bool=False
    physical_gravity_claim: bool=False

def canonical_antipodal_overlay() -> AntipodalOverlay36:
    plus,minus=canonical_bivector_frames()
    hs=tuple(tuple(0.5*(a+b) for a,b in zip(ra,rb)) for ra,rb in zip(plus.matrix6,minus.matrix6))
    hd=tuple(tuple(0.5*(a-b) for a,b in zip(ra,rb)) for ra,rb in zip(plus.matrix6,minus.matrix6))
    return AntipodalOverlay36(BivectorField36(hs),BivectorField36(hd),canonical_bivector_parity())


@dataclass(frozen=True)
class AntipodalSplit4:
    common_rank1: tuple[tuple[float,...],...]
    differential_rank3: tuple[tuple[float,...],...]
    physical_time_space_binding: str="CONDITIONAL"
    gravity_claim: bool=False

def canonical_antipodal_split4() -> AntipodalSplit4:
    plus=canonical_plus_frame4()
    minus=canonical_minus_frame4()
    common=tuple(tuple(0.5*(a+b) for a,b in zip(ra,rb)) for ra,rb in zip(plus,minus))
    differential=tuple(tuple(0.5*(a-b) for a,b in zip(ra,rb)) for ra,rb in zip(plus,minus))
    return AntipodalSplit4(common,differential)
