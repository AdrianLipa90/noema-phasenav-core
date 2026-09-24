"""Candidate PhaseNav 36D <-> four-dimensional bivector lift gates.

A 36-component real field is organized as a 6x6 coefficient matrix on Lambda^2(R^4).
No physical gravity claim is made unless an upstream decoder and downstream
simplicity/metric gates are satisfied.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

PAIR_BASIS = ((0,1),(0,2),(0,3),(2,3),(3,1),(1,2))

def _matmul(a,b):
    return tuple(tuple(math.fsum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))) for i in range(len(a)))

def _transpose(a):
    return tuple(tuple(a[j][i] for j in range(len(a))) for i in range(len(a[0])))

def wedge_pairing() -> tuple[tuple[float,...],...]:
    j=[[0.0]*6 for _ in range(6)]
    for i in range(3):
        j[i][i+3]=1.0
        j[i+3][i]=1.0
    return tuple(tuple(r) for r in j)

def exterior_square(coframe4: Sequence[Sequence[float]]) -> tuple[tuple[float,...],...]:
    if len(coframe4)!=4 or any(len(row)!=4 for row in coframe4):
        raise ValueError("expected 4x4 coframe")
    e=tuple(tuple(float(x) for x in row) for row in coframe4)
    if not all(math.isfinite(x) for row in e for x in row):
        raise ValueError("coframe entries must be finite")
    out=[]
    for i,j in PAIR_BASIS:
        row=[]
        for mu,nu in PAIR_BASIS:
            row.append(e[i][mu]*e[j][nu]-e[i][nu]*e[j][mu])
        out.append(tuple(row))
    return tuple(out)

@dataclass(frozen=True)
class BivectorField36:
    matrix6: tuple[tuple[float,...],...]

    def __post_init__(self):
        if len(self.matrix6)!=6 or any(len(r)!=6 for r in self.matrix6):
            raise ValueError("expected 6x6 matrix")
        if not all(math.isfinite(float(x)) for r in self.matrix6 for x in r):
            raise ValueError("all coefficients must be finite")
        object.__setattr__(self,"matrix6",tuple(tuple(float(x) for x in r) for r in self.matrix6))

    @classmethod
    def from_flat36(cls, values: Sequence[float]) -> "BivectorField36":
        if len(values)!=36:
            raise ValueError("expected 36 coefficients")
        vals=tuple(float(x) for x in values)
        return cls(tuple(tuple(vals[6*r+c] for c in range(6)) for r in range(6)))

    def to_flat36(self) -> tuple[float,...]:
        return tuple(x for r in self.matrix6 for x in r)

    def wedge_conformal_residual(self) -> tuple[float,float]:
        """Return (lambda, normalized residual) for M^T J M approx lambda J.

        This is a necessary coframe-lift gate, not a global sufficiency proof.
        """
        m=self.matrix6
        j=wedge_pairing()
        k=_matmul(_matmul(_transpose(m),j),m)
        lam=(k[0][3]+k[1][4]+k[2][5]+k[3][0]+k[4][1]+k[5][2])/6.0
        num=math.sqrt(math.fsum((k[i][q]-lam*j[i][q])**2 for i in range(6) for q in range(6)))
        den=max(1e-300,abs(lam)*math.sqrt(6.0))
        return lam,num/den

    def passes_necessary_lift_gate(self, tolerance: float=1e-10) -> bool:
        lam,res=self.wedge_conformal_residual()
        return abs(lam)>tolerance and res<=tolerance

def euclidean_half_projectors():
    """Return numerical matrices (I +/- *)/2 for the chosen Euclidean basis."""
    h=wedge_pairing()  # same numeric matrix here; conceptually Hodge star requires metric
    pp=[];pm=[]
    for i in range(6):
        rp=[];rm=[]
        for j in range(6):
            ident=1.0 if i==j else 0.0
            rp.append(0.5*(ident+h[i][j]))
            rm.append(0.5*(ident-h[i][j]))
        pp.append(tuple(rp));pm.append(tuple(rm))
    return tuple(pp),tuple(pm)
