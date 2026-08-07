"""Normalized phase-crystal geometry on the torus (R/Z)^N.

Coordinates are stored in turns rather than radians.  Signed components arise
from the orientation of the shortest tangent displacement on the torus.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


def wrap_turn(q: float) -> float:
    return float(q) % 1.0


def shortest_turn_displacement(source: float, target: float) -> float:
    """Oriented shortest displacement on R/Z in [-1/2, 1/2)."""
    return (float(target) - float(source) + 0.5) % 1.0 - 0.5


@dataclass(frozen=True)
class PhaseCrystal:
    turns: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.turns:
            raise ValueError("phase crystal must have at least one dimension")
        object.__setattr__(self, "turns", tuple(wrap_turn(q) for q in self.turns))

    @property
    def dimension(self) -> int:
        return len(self.turns)

    @classmethod
    def from_iterable(cls, turns: Iterable[float]) -> "PhaseCrystal":
        return cls(tuple(float(q) for q in turns))

    def tangent_to(self, other: "PhaseCrystal") -> tuple[float, ...]:
        if self.dimension != other.dimension:
            raise ValueError("phase crystals must have the same dimension")
        return tuple(
            shortest_turn_displacement(a, b)
            for a, b in zip(self.turns, other.turns)
        )

    def distance(self, other: "PhaseCrystal") -> float:
        tangent = self.tangent_to(other)
        return math.sqrt(sum(x * x for x in tangent))

    def winding_signature_to(self, other: "PhaseCrystal") -> tuple[int, ...]:
        """Return orientation signatures of shortest tangent components."""
        out: list[int] = []
        for x in self.tangent_to(other):
            if x == 0.0:
                out.append(0)
            else:
                out.append(1 if x > 0.0 else -1)
        return tuple(out)


DEFAULT_CRYSTAL_DIMENSION = 36
