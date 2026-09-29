"""36D Moire calibration observables.

Representation-level only. This module deliberately separates the raw
channelwise relation from the global-U(1)-blind projective shape quotient.
No physical axis semantics are assigned here.
"""
from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Sequence

TAU = 2.0 * math.pi
DIM = 36


def _wrap(theta: float) -> float:
    if not math.isfinite(theta):
        raise ValueError("phase must be finite")
    return (float(theta) + math.pi) % TAU - math.pi


def relative_deltas36(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    if len(left) != DIM or len(right) != DIM:
        raise ValueError("expected exactly 36 coordinates")
    vals = tuple(float(v) for v in (*left, *right))
    if not all(math.isfinite(v) for v in vals):
        raise ValueError("all coordinates must be finite")
    return tuple(_wrap(b-a) for a,b in zip(left,right))


@dataclass(frozen=True)
class MoireResidual36:
    coherence: complex
    coherence_abs: float
    coherence_phase: float
    raw: float
    shape: float
    coherent: float


def residual36(left: Sequence[float], right: Sequence[float]) -> MoireResidual36:
    delta = relative_deltas36(left,right)
    c = sum(cmath.exp(1j*d) for d in delta) / DIM
    raw = math.fsum(4.0 * math.sin(0.5*d)**2 for d in delta) / DIM
    shape = 2.0 * (1.0 - abs(c))
    coherent = 2.0 * (abs(c) - c.real)
    if coherent < 0.0 and abs(coherent) < 1e-15:
        coherent = 0.0
    return MoireResidual36(
        coherence=c,
        coherence_abs=abs(c),
        coherence_phase=cmath.phase(c),
        raw=raw,
        shape=shape,
        coherent=coherent,
    )
