"""Typed T^36 log-phase adapter for the full spatial SO(3) bivector carrier."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .spatial_rotation36 import (
    SpatialRotation36Error,
    rotvec_generator36,
    rotation36_from_rotvec,
)

TAU=2.0*math.pi
DIM=36
GENERIC_T36_BASIS_ID="PNV_T36_PHASE_ANGLES_RADIANS_V1"
SPATIAL_LOG_PHASE36_BASIS_ID="PNV_SPATIAL_SO3_LOG_PHASE_MATRIX6_ROW_MAJOR_V1"
BIVECTOR36_BASIS_ID="PNV_BIVECTOR_OPERATOR36_LAMBDA2_R4_PAIRBASIS_V1"
ADAPTER_ID="PNV_TYPED_SPATIAL_LOG_PHASE36_TO_BIVECTOR36_SO3_V1"


class SpatialPhase36AdapterError(ValueError):
    pass


def _wrap(x:float)->float:
    if not math.isfinite(x): raise SpatialPhase36AdapterError("phase must be finite")
    return (x+math.pi)%TAU-math.pi


def _frob(m)->float:
    return math.sqrt(math.fsum(float(x)*float(x) for row in m for x in row))


@dataclass(frozen=True)
class SpatialLogPhase36Record:
    angles: tuple[float,...]
    basis_id: str
    derivation_id: str
    source_id: str

    def __post_init__(self):
        if len(self.angles)!=DIM: raise SpatialPhase36AdapterError("expected exactly 36 angles")
        vals=tuple(float(x) for x in self.angles)
        if not all(math.isfinite(x) and 0.0<=x<TAU for x in vals):
            raise SpatialPhase36AdapterError("angles must be finite and in [0,2pi)")
        if not self.basis_id or not self.derivation_id or not self.source_id:
            raise SpatialPhase36AdapterError("basis_id, derivation_id and source_id are required")
        object.__setattr__(self,"angles",vals)


@dataclass(frozen=True)
class SpatialBivector36Binding:
    rotation_vector: tuple[float,float,float]
    angle_radians: float
    axis: tuple[float,float,float] | None
    generator_fit_abs: float
    generator_fit_rel: float
    operator6: tuple[tuple[float,...],...]
    admitted: bool


def encode_spatial_rotvec_log_phase36(
    rotation_vector: Sequence[float],
    *,
    source_id: str,
    derivation_id: str="PNV_SPATIAL_SO3_FORWARD_LOG_PHASE_V1",
    branch_cut_margin: float=1e-9,
) -> SpatialLogPhase36Record:
    w=tuple(float(x) for x in rotation_vector)
    if len(w)!=3 or not all(math.isfinite(x) for x in w):
        raise SpatialPhase36AdapterError("rotation_vector must contain three finite values")
    theta=math.sqrt(math.fsum(x*x for x in w))
    if theta>=math.pi-branch_cut_margin:
        raise SpatialPhase36AdapterError("rotation vector is too close to the principal branch cut")
    x=rotvec_generator36(w)
    angles=tuple((x[r][c])%TAU for r in range(6) for c in range(6))
    return SpatialLogPhase36Record(angles,SPATIAL_LOG_PHASE36_BASIS_ID,derivation_id,source_id)


def _relative_matrix(a:SpatialLogPhase36Record,b:SpatialLogPhase36Record):
    for rec in (a,b):
        if rec.basis_id==GENERIC_T36_BASIS_ID:
            raise SpatialPhase36AdapterError("generic T36 basis cannot be retyped as spatial SO(3)")
        if rec.basis_id!=SPATIAL_LOG_PHASE36_BASIS_ID:
            raise SpatialPhase36AdapterError("unsupported source basis")
    d=tuple(_wrap(y-x) for x,y in zip(a.angles,b.angles))
    return tuple(tuple(d[6*r+c] for c in range(6)) for r in range(6))


def fit_spatial_rotvec_generator(matrix6):
    x=tuple(tuple(float(v) for v in row) for row in matrix6)
    basis=(
        rotvec_generator36((1.0,0.0,0.0)),
        rotvec_generator36((0.0,1.0,0.0)),
        rotvec_generator36((0.0,0.0,1.0)),
    )
    coeff=[]
    for j in basis:
        den=math.fsum(j[r][c]*j[r][c] for r in range(6) for c in range(6))
        coeff.append(math.fsum(x[r][c]*j[r][c] for r in range(6) for c in range(6))/den)
    recon=rotvec_generator36(coeff)
    diff=tuple(tuple(x[r][c]-recon[r][c] for c in range(6)) for r in range(6))
    ae=_frob(diff)
    scale=max(_frob(x),_frob(recon),1e-300)
    return (coeff[0],coeff[1],coeff[2]),ae,ae/scale


def adapt_spatial_log_phase36(
    reference: SpatialLogPhase36Record,
    target: SpatialLogPhase36Record,
    *,
    fit_tolerance: float=1e-10,
    branch_cut_margin: float=1e-9,
) -> SpatialBivector36Binding:
    x=_relative_matrix(reference,target)
    w,ae,re=fit_spatial_rotvec_generator(x)
    theta=math.sqrt(math.fsum(v*v for v in w))
    if theta>=math.pi-branch_cut_margin:
        raise SpatialPhase36AdapterError("recovered rotation is too close to the principal branch cut")
    if ae>fit_tolerance:
        raise SpatialPhase36AdapterError("typed log-phase matrix is off the calibrated so(3) generator subspace")
    axis=None if theta==0.0 else tuple(v/theta for v in w)
    op=rotation36_from_rotvec(w)
    return SpatialBivector36Binding(w,theta,axis,ae,re,op,True)
