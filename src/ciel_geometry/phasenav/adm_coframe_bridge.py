"""Typed 3+1 coframe adapter from the calibrated spatial GL+(3) carrier.

Time-gauge coframe:
    e^0 = N dt
    e^a = E^a_i (dx^i + beta^i dt)

Matrix form (internal rows, coordinate columns):
    e = [[N, 0],
         [E beta, E]]

with N>0, E in GL+(3), beta in R^3.

Metric:
    h = E^T E
    g_tt = -N^2 + beta^T h beta
    g_ti = (h beta)_i
    g_ij = h_ij

This is a typed ADM/coframe kinematic adapter. It does not infer N or beta from
generic PhaseNav T36 state.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .gl4_coframe_bivector36 import (
    Coframe36Error,
    coframe_metric4,
    frobenius_norm,
    lambda2_gl4,
    spatial_embedding4,
    sub,
)
from .spatial_deformation36 import det3, inverse3, deformation36


class ADMCoframeError(ValueError):
    pass


def _m3(a:Sequence[Sequence[float]])->tuple[tuple[float,...],...]:
    if len(a)!=3 or any(len(r)!=3 for r in a):
        raise ADMCoframeError("expected a 3x3 triad")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise ADMCoframeError("triad entries must be finite")
    if det3(m)<=0.0:
        raise ADMCoframeError("triad must lie in GL+(3)")
    return m


def _v3(v:Sequence[float])->tuple[float,float,float]:
    if len(v)!=3:
        raise ADMCoframeError("shift must have three components")
    q=tuple(float(x) for x in v)
    if not all(math.isfinite(x) for x in q):
        raise ADMCoframeError("shift components must be finite")
    return q  # type: ignore[return-value]


def _matmul3(a,b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _transpose3(a):
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))


def _matvec3(a,v):
    return tuple(sum(a[i][j]*v[j] for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class ADMFrame:
    lapse: float
    triad: tuple[tuple[float,...],...]
    shift: tuple[float,float,float]

    def __post_init__(self):
        n=float(self.lapse)
        if not math.isfinite(n) or n<=0.0:
            raise ADMCoframeError("lapse must be finite and positive")
        object.__setattr__(self,"lapse",n)
        object.__setattr__(self,"triad",_m3(self.triad))
        object.__setattr__(self,"shift",_v3(self.shift))


def coframe4_from_adm(frame:ADMFrame):
    e=frame.triad
    eb=_matvec3(e,frame.shift)
    return (
        (frame.lapse,0.0,0.0,0.0),
        (eb[0],e[0][0],e[0][1],e[0][2]),
        (eb[1],e[1][0],e[1][1],e[1][2]),
        (eb[2],e[2][0],e[2][1],e[2][2]),
    )


def spatial_metric3(frame:ADMFrame):
    e=frame.triad
    return _matmul3(_transpose3(e),e)


def metric4_from_adm(frame:ADMFrame):
    return coframe_metric4(coframe4_from_adm(frame))


def expected_metric4_from_adm(frame:ADMFrame):
    h=spatial_metric3(frame)
    hb=_matvec3(h,frame.shift)
    b_h_b=sum(frame.shift[i]*hb[i] for i in range(3))
    return (
        (-frame.lapse**2+b_h_b,hb[0],hb[1],hb[2]),
        (hb[0],h[0][0],h[0][1],h[0][2]),
        (hb[1],h[1][0],h[1][1],h[1][2]),
        (hb[2],h[2][0],h[2][1],h[2][2]),
    )


def bivector36_from_adm(frame:ADMFrame):
    return lambda2_gl4(coframe4_from_adm(frame))


def recover_adm_from_time_gauge_coframe(coframe, *, tolerance:float=1e-10)->ADMFrame:
    if len(coframe)!=4 or any(len(r)!=4 for r in coframe):
        raise ADMCoframeError("expected 4x4 coframe")
    e=tuple(tuple(float(x) for x in r) for r in coframe)
    if not all(math.isfinite(x) for r in e for x in r):
        raise ADMCoframeError("coframe entries must be finite")
    if max(abs(e[0][i]) for i in range(1,4))>tolerance:
        raise ADMCoframeError("coframe is outside the declared time gauge")
    lapse=e[0][0]
    triad=tuple(tuple(e[i+1][j+1] for j in range(3)) for i in range(3))
    if lapse<=0.0:
        raise ADMCoframeError("time-gauge lapse must be positive")
    triad=_m3(triad)
    eb=tuple(e[i+1][0] for i in range(3))
    shift=_matvec3(inverse3(triad),eb)
    return ADMFrame(lapse,triad,shift)


def zero_shift_unit_lapse_gl3_residual(triad)->float:
    e=_m3(triad)
    frame=ADMFrame(1.0,e,(0.0,0.0,0.0))
    lhs=bivector36_from_adm(frame)
    rhs=deformation36(e)
    return frobenius_norm(sub(lhs,rhs))


def conformal_reference_adm(a:float,x:float,y:float)->ADMFrame:
    aa=float(a);xx=float(x);yy=float(y)
    if not all(math.isfinite(v) for v in (aa,xx,yy)):
        raise ADMCoframeError("reference parameters must be finite")
    s=math.exp(aa*(xx*xx+yy*yy))
    return ADMFrame(
        1.0,
        ((s,0.0,0.0),(0.0,s,0.0),(0.0,0.0,1.0)),
        (0.0,0.0,0.0),
    )
