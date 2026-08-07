"""Geometry-first scalar primitives for CIEL/PhaseNav.

The purpose of this layer is to keep algebraic sign/zero semantics downstream of
geometry.  A signed scalar is represented as an oriented displacement from an
axis.  Zero is the fixed axis itself; negative and positive values are the two
orientations of the same one-dimensional tangent coordinate.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class IdentityAxis:
    """Distinguished origin for an oriented one-dimensional chart."""

    value: float = 0.5
    name: str = "Sigma"

    def displacement(self, value: float) -> float:
        """Return the oriented displacement x=value-axis."""
        return float(value) - float(self.value)

    def orientation(self, value: float, *, atol: float = 0.0) -> int:
        """Return -1, 0 or +1 from orientation relative to the axis."""
        x = self.displacement(value)
        if math.isclose(x, 0.0, abs_tol=float(atol), rel_tol=0.0):
            return 0
        return 1 if x > 0.0 else -1

    def reflect(self, value: float) -> float:
        """Reflect a point through the axis."""
        return 2.0 * float(self.value) - float(value)


@dataclass(frozen=True)
class OrientedScalar:
    """Real scalar reconstructed from orientation and non-negative magnitude."""

    orientation: int
    magnitude: float

    def __post_init__(self) -> None:
        if self.orientation not in (-1, 0, 1):
            raise ValueError("orientation must be -1, 0, or +1")
        if self.magnitude < 0.0:
            raise ValueError("magnitude must be non-negative")
        if self.orientation == 0 and self.magnitude != 0.0:
            raise ValueError("zero orientation requires zero magnitude")

    @property
    def value(self) -> float:
        return float(self.orientation) * float(self.magnitude)

    @classmethod
    def from_axis(cls, value: float, axis: IdentityAxis = IdentityAxis()) -> "OrientedScalar":
        x = axis.displacement(value)
        if x == 0.0:
            return cls(0, 0.0)
        return cls(1 if x > 0.0 else -1, abs(x))


def centered_sigma(sigma: float) -> float:
    """Canonical binary identity coordinate u=sigma-1/2."""
    return IdentityAxis().displacement(sigma)


def complement_sigma(sigma: float) -> float:
    """Binary complement, equivalent to reflection through Sigma=1/2."""
    return IdentityAxis().reflect(sigma)
