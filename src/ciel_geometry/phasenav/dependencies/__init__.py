"""CIEL/PhaseNav geometry dependency layer.

Low-level primitives are intentionally separated from higher-level semantic
runtime code.  Geometry and recurrence create the coordinates; vectorization
consumes those coordinates.
"""
from .geometry import IdentityAxis, OrientedScalar, centered_sigma, complement_sigma
from .phase import CycleCoordinate, PhaseClosure, spinor_holonomy, spinor_sheet, winding_rate
from .crystal import (
    DEFAULT_CRYSTAL_DIMENSION,
    PhaseCrystal,
    shortest_turn_displacement,
    wrap_turn,
)
from .relation import EpistemicStatus, RelationEdge, RelationGraph, RelationKind
from .vectorization import GeometricVector, VectorizationOperator, lift_turn_vector

__all__ = [
    "IdentityAxis",
    "OrientedScalar",
    "centered_sigma",
    "complement_sigma",
    "CycleCoordinate",
    "PhaseClosure",
    "spinor_holonomy",
    "spinor_sheet",
    "winding_rate",
    "DEFAULT_CRYSTAL_DIMENSION",
    "PhaseCrystal",
    "shortest_turn_displacement",
    "wrap_turn",
    "EpistemicStatus",
    "RelationEdge",
    "RelationGraph",
    "RelationKind",
    "GeometricVector",
    "VectorizationOperator",
    "lift_turn_vector",
]
