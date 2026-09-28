"""Candidate four-packet coframe -> bivector36 bridge.

The module uses the existing TIR x IDT packet coordinates
    x = ell/2 * (1, r_x, r_y, r_z)
and requires four independent packets before a coframe exists.

Legacy anonymous Phase36 coordinates are not accepted as coframe input.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .bivector36 import BivectorField36, exterior_square

def _det4(a: Sequence[Sequence[float]]) -> float:
    m=[list(map(float,row)) for row in a]
    det=1.0
    for c in range(4):
        p=max(range(c,4),key=lambda r:abs(m[r][c]))
        if abs(m[p][c])<1e-15:
            return 0.0
        if p!=c:
            m[c],m[p]=m[p],m[c]
            det=-det
        pivot=m[c][c]
        det*=pivot
        for j in range(c,4):
            m[c][j]/=pivot
        for r in range(c+1,4):
            factor=m[r][c]
            for j in range(c,4):
                m[r][j]-=factor*m[c][j]
    return det

def _inv4(a: Sequence[Sequence[float]]) -> tuple[tuple[float,...],...]:
    m=[
        list(map(float,row))
        + [1.0 if i==j else 0.0 for j in range(4)]
        for i,row in enumerate(a)
    ]
    for c in range(4):
        p=max(range(c,4),key=lambda r:abs(m[r][c]))
        if abs(m[p][c])<1e-15:
            raise ValueError("singular frame")
        m[c],m[p]=m[p],m[c]
        pivot=m[c][c]
        m[c]=[x/pivot for x in m[c]]
        for r in range(4):
            if r==c:
                continue
            factor=m[r][c]
            m[r]=[x-factor*y for x,y in zip(m[r],m[c])]
    return tuple(tuple(row[4:]) for row in m)

def _matmul(a,b):
    return tuple(
        tuple(
            math.fsum(a[i][k]*b[k][j] for k in range(len(b)))
            for j in range(len(b[0]))
        )
        for i in range(len(a))
    )

@dataclass(frozen=True)
class ElapsedBlochPacket:
    ell: float
    bloch3: tuple[float,float,float]

    def __post_init__(self):
        if not math.isfinite(self.ell) or self.ell<=0.0:
            raise ValueError("ell must be positive finite")
        if len(self.bloch3)!=3 or not all(math.isfinite(float(x)) for x in self.bloch3):
            raise ValueError("invalid Bloch vector")
        norm2=math.fsum(float(x)**2 for x in self.bloch3)
        if norm2>1.0+1e-12:
            raise ValueError("Bloch vector lies outside the unit ball")

    @property
    def vector4(self) -> tuple[float,float,float,float]:
        s=0.5*self.ell
        return (
            s,
            s*self.bloch3[0],
            s*self.bloch3[1],
            s*self.bloch3[2],
        )

    @property
    def minkowski_norm2(self) -> float:
        x=self.vector4
        return x[0]**2-x[1]**2-x[2]**2-x[3]**2

@dataclass(frozen=True)
class PacketFrame4:
    packets: tuple[
        ElapsedBlochPacket,
        ElapsedBlochPacket,
        ElapsedBlochPacket,
        ElapsedBlochPacket,
    ]

    def __post_init__(self):
        if len(self.packets)!=4:
            raise ValueError("expected exactly four packets")
        if abs(self.determinant)<=1e-14:
            raise ValueError("packets do not form an invertible frame")

    @property
    def matrix4(self) -> tuple[tuple[float,...],...]:
        columns=[packet.vector4 for packet in self.packets]
        return tuple(
            tuple(columns[col][row] for col in range(4))
            for row in range(4)
        )

    @property
    def determinant(self) -> float:
        return _det4(self.matrix4)

    def relative_to(
        self,
        source: "PacketFrame4",
    ) -> tuple[tuple[float,...],...]:
        """Return target * source^{-1}."""
        return _matmul(self.matrix4,_inv4(source.matrix4))

    def bivector_relative_to(
        self,
        source: "PacketFrame4",
    ) -> BivectorField36:
        return BivectorField36(exterior_square(self.relative_to(source)))

def canonical_tetra_frame(
    ell: float=2.0,
    *,
    antipodal: bool=False,
) -> PacketFrame4:
    s=1.0/math.sqrt(3.0)
    raw=((1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1))
    sign=-1.0 if antipodal else 1.0
    return PacketFrame4(
        tuple(
            ElapsedBlochPacket(
                ell,
                tuple(sign*s*x for x in vertex),
            )
            for vertex in raw
        )
    )

def spatial_parity4() -> tuple[tuple[float,...],...]:
    return (
        (1.0,0.0,0.0,0.0),
        (0.0,-1.0,0.0,0.0),
        (0.0,0.0,-1.0,0.0),
        (0.0,0.0,0.0,-1.0),
    )
