"""Candidate 36D moire hyperlayer primitives.

This module is deliberately outside canonical PhaseNav semantics. It supplies a
6x6 view of 36 phase coordinates and exact two-layer interference invariants.
It does not claim physical spacetime, gravity, or a unique 6x6 factorization.
"""
from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Sequence

TAU = 2.0 * math.pi
PHASE_DIM = 36
SLICE_N = 6


def _wrap(theta: float) -> float:
    if not math.isfinite(theta):
        raise ValueError("phase must be finite")
    return (float(theta) + math.pi) % TAU - math.pi


def _short_delta(left: float, right: float) -> float:
    return _wrap(left - right)


def so_generator_count(n: int) -> int:
    if n < 1:
        raise ValueError("n must be positive")
    return n * (n - 1) // 2


@dataclass(frozen=True)
class PhaseMatrix6:
    rows: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        if len(self.rows) != SLICE_N or any(len(r) != SLICE_N for r in self.rows):
            raise ValueError("expected a 6x6 phase matrix")
        flat = [x for row in self.rows for x in row]
        if not all(math.isfinite(float(x)) for x in flat):
            raise ValueError("all phase coordinates must be finite")
        object.__setattr__(self, "rows", tuple(tuple(float(x) % TAU for x in row) for row in self.rows))

    @classmethod
    def from_phase36(cls, components: Sequence[float]) -> "PhaseMatrix6":
        if len(components) != PHASE_DIM:
            raise ValueError("expected 36 phase coordinates")
        vals = tuple(float(x) for x in components)
        return cls(tuple(tuple(vals[6*r+c] for c in range(6)) for r in range(6)))

    def to_phase36(self) -> tuple[float, ...]:
        return tuple(x for row in self.rows for x in row)


@dataclass(frozen=True)
class MoireHyperlayerPair:
    mean_phase36: tuple[float, ...]
    half_delta36: tuple[float, ...]
    envelope36: tuple[float, ...]
    cancellation_mask36: tuple[bool, ...]

    @property
    def cancellation_fraction(self) -> float:
        return sum(self.cancellation_mask36) / PHASE_DIM


def pair_hyperlayers(left: PhaseMatrix6, right: PhaseMatrix6, *, tol: float = 1e-12) -> MoireHyperlayerPair:
    a = left.to_phase36()
    b = right.to_phase36()
    means=[]; half=[]; env=[]; mask=[]
    for x,y in zip(a,b):
        delta = _short_delta(x,y)
        h = 0.5 * delta
        mean = (y + h) % TAU
        e = 2.0 * math.cos(h)
        means.append(mean); half.append(h); env.append(e); mask.append(abs(e) <= tol)
    return MoireHyperlayerPair(tuple(means),tuple(half),tuple(env),tuple(mask))


def reconstruct_pair(mean_phase: float, half_delta: float) -> complex:
    return 2.0 * cmath.exp(1j * mean_phase) * math.cos(half_delta)


def direct_pair(left: float, right: float) -> complex:
    return cmath.exp(1j * left) + cmath.exp(1j * right)


def structured_rotation_counts() -> dict[str,int]:
    return {
        "so6_left": so_generator_count(6),
        "so6_right": so_generator_count(6),
        "so6xso6": 2 * so_generator_count(6),
        "so36_full": so_generator_count(36),
    }


def u1_holonomy_memory(edge_potentials: Sequence[float]) -> complex:
    """Candidate Abelian path-memory observable, matching exp(i sum A_e)."""
    vals=tuple(float(x) for x in edge_potentials)
    if not all(math.isfinite(x) for x in vals):
        raise ValueError("edge potentials must be finite")
    theta=math.fsum(vals)
    return complex(math.cos(theta),math.sin(theta))
