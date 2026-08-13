"""NOEMA cognition surfaces for PhaseNav.

All modules are non-actuating and preserve the repository authority boundary.
"""
from . import memory_orchestrator
from .affective_salience import AffectiveSalienceError, seal_affect_state, validate_affect_state

__all__ = [
    "memory_orchestrator",
    "AffectiveSalienceError",
    "seal_affect_state",
    "validate_affect_state",
]
