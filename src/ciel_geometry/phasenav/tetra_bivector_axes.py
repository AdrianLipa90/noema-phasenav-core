"""Exact tetrahedral edge-pair axis carrier for candidate bivector PhaseNav work.

This module does not reinterpret the legacy phi_0..phi_35 coordinates as
physical bivectors. It supplies a separate six-edge x six-edge carrier whose
axis labels come from the exact tetrahedral pair-index combinatorics.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

EDGE_BASIS=((0,1),(0,2),(0,3),(2,3),(3,1),(1,2))
EDGE_LABELS=("01","02","03","23","31","12")
OPPOSITE_INDEX=((0,3),(1,4),(2,5))
EDGE_PAIR_CHANNELS=tuple((row,col) for row in range(6) for col in range(6))

def opposite_edge_pairing():
    j=[[0.0]*6 for _ in range(6)]
    for a,b in OPPOSITE_INDEX:
        j[a][b]=1.0
        j[b][a]=1.0
    return tuple(tuple(row) for row in j)

def _pair_index_sign(i:int,j:int):
    if i==j:
        raise ValueError("edge requires distinct vertices")
    for index,(a,b) in enumerate(EDGE_BASIS):
        if (i,j)==(a,b): return index,1.0
        if (i,j)==(b,a): return index,-1.0
    raise ValueError((i,j))

def induced_edge_matrix(vertex_permutation):
    p=tuple(int(x) for x in vertex_permutation)
    if sorted(p)!=[0,1,2,3]:
        raise ValueError("expected permutation of 0,1,2,3")
    matrix=[[0.0]*6 for _ in range(6)]
    for col,(i,j) in enumerate(EDGE_BASIS):
        row,sign=_pair_index_sign(p[i],p[j])
        matrix[row][col]=sign
    return tuple(tuple(row) for row in matrix)

@dataclass(frozen=True)
class TetraEdgePairField36:
    """Explicit 6x6 relation field between two six-edge tetrahedral sheets."""

    matrix6: tuple[tuple[float,...],...]
    source_receipt: str
    binding_status: str="EXPLICIT_TETRA_EDGE_PAIR_RELATIONS"

    def __post_init__(self):
        if len(self.matrix6)!=6 or any(len(row)!=6 for row in self.matrix6):
            raise ValueError("expected 6x6 relation matrix")
        if not all(math.isfinite(float(x)) for row in self.matrix6 for x in row):
            raise ValueError("relation values must be finite")
        if not self.source_receipt:
            raise ValueError("source_receipt is required")
        object.__setattr__(
            self,
            "matrix6",
            tuple(tuple(float(x) for x in row) for row in self.matrix6),
        )

    @classmethod
    def from_mapping(
        cls,
        relations: Mapping[tuple[str,str],float],
        *,
        source_receipt: str,
    ) -> "TetraEdgePairField36":
        expected={(a,b) for a in EDGE_LABELS for b in EDGE_LABELS}
        supplied=set(relations)
        if supplied!=expected:
            missing=sorted(expected-supplied)
            extra=sorted(supplied-expected)
            raise ValueError(f"relation map must contain exactly 36 edge pairs; missing={missing[:4]}, extra={extra[:4]}")
        matrix=tuple(
            tuple(float(relations[(a,b)]) for b in EDGE_LABELS)
            for a in EDGE_LABELS
        )
        return cls(matrix,source_receipt=source_receipt)

    def to_flat36(self):
        return tuple(x for row in self.matrix6 for x in row)

def legacy_phase36_row_major_view(values):
    """Computational-only reshape. It deliberately does not return a bound field."""
    vals=tuple(float(x) for x in values)
    if len(vals)!=36:
        raise ValueError("expected 36 values")
    if not all(math.isfinite(x) for x in vals):
        raise ValueError("values must be finite")
    return {
        "matrix6":tuple(tuple(vals[6*r+c] for c in range(6)) for r in range(6)),
        "binding_status":"LEGACY_ROW_MAJOR_RESHAPE_NOT_DERIVED",
        "physical_binding":False,
    }


@dataclass(frozen=True)
class TetraEdgePairPhaseReceipt:
    field: TetraEdgePairField36
    overlap_abs6: tuple[tuple[float,...],...]
    observable: str="ARG_CANONICAL_PHASE36_OVERLAP"
    candidate_only: bool=True


def phase_overlap_edge_pair_field(
    plus_edges: Mapping[str, tuple[float,...] | list[float]],
    minus_edges: Mapping[str, tuple[float,...] | list[float]],
    *,
    source_receipt: str,
) -> TetraEdgePairPhaseReceipt:
    """Build the 6x6 edge-pair field from canonical PhaseNav overlap phases.

    Z_ab = (1/36) sum_k exp(i(phi^-_{b,k} - phi^+_{a,k}))
    X_ab = arg Z_ab
    R_ab = |Z_ab|

    No fitted coefficient is used. Exact zero overlap fails closed because its
    argument is undefined.
    """
    from .pnv_runtime import M_36d_inner_product

    if set(plus_edges) != set(EDGE_LABELS) or set(minus_edges) != set(EDGE_LABELS):
        raise ValueError("both sheets must provide exactly the six canonical edge labels")

    matrix=[]
    strength=[]
    for a in EDGE_LABELS:
        phase_row=[]
        strength_row=[]
        va=tuple(float(x) for x in plus_edges[a])
        if len(va)!=36 or not all(math.isfinite(x) for x in va):
            raise ValueError(f"invalid plus edge vector {a}")
        for b in EDGE_LABELS:
            vb=tuple(float(x) for x in minus_edges[b])
            if len(vb)!=36 or not all(math.isfinite(x) for x in vb):
                raise ValueError(f"invalid minus edge vector {b}")
            re,im=M_36d_inner_product(va,vb)
            mag=math.hypot(re,im)
            if mag <= 1e-15:
                raise ValueError(f"undefined overlap phase for edge pair {(a,b)}")
            phase_row.append(math.atan2(im,re))
            strength_row.append(mag)
        matrix.append(tuple(phase_row))
        strength.append(tuple(strength_row))

    field=TetraEdgePairField36(
        tuple(matrix),
        source_receipt=source_receipt,
        binding_status="EXPLICIT_TETRA_EDGE_PAIR_PHASE_OVERLAP",
    )
    return TetraEdgePairPhaseReceipt(field,tuple(strength))
