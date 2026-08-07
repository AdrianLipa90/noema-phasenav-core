"""Normalized phase primitives independent of radian convention."""
from __future__ import annotations

from dataclasses import dataclass
import cmath
import math


@dataclass(frozen=True)
class CycleCoordinate:
    """Point on R/Z represented by a normalized turn q in [0,1)."""

    q: float

    @property
    def wrapped(self) -> float:
        return float(self.q) % 1.0

    def advance(self, turns: float) -> "CycleCoordinate":
        return CycleCoordinate(self.wrapped + float(turns))


@dataclass(frozen=True)
class PhaseClosure:
    """Map normalized turns to an angular coordinate with period C."""

    period: float

    def __post_init__(self) -> None:
        if self.period <= 0.0:
            raise ValueError("period must be positive")

    def angle(self, q: float) -> float:
        return float(self.period) * float(q)

    def turns(self, angle: float) -> float:
        return float(angle) / float(self.period)


def winding_rate(delta_winding: float, delta_time: float) -> float:
    """Intrinsic frequency as cycle-count rate; no angular convention needed."""
    dt = float(delta_time)
    if dt <= 0.0:
        raise ValueError("delta_time must be positive")
    return float(delta_winding) / dt


def spinor_sheet(projective_winding: int) -> int:
    """Return +1/-1 sheet sign for the SU(2) double cover."""
    if not isinstance(projective_winding, int):
        raise TypeError("projective_winding must be an integer")
    return -1 if projective_winding % 2 else 1


def u1_holonomy(turns: float) -> complex:
    """U(1) holonomy from normalized turns; one turn closes to +1."""
    return cmath.exp(2j * math.pi * float(turns))


def spinor_holonomy(projective_winding: int) -> complex:
    """Holonomy of the lifted spinor after projective windings."""
    return complex(spinor_sheet(projective_winding), 0.0)
