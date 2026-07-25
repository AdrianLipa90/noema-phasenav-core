"""Bounded information-geometric context dynamics.

This is a diagnostic state evolution for CIELingo context selection.  It is
not a simulator of physical quantum systems and it never performs writeback or
runtime actions on its own.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np


def _normalise(state: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(state))
    if norm <= 1e-12:
        raise ValueError("Bloch state must have non-zero norm")
    return state.astype(np.complex128) / norm


@dataclass(frozen=True)
class BlochState:
    amplitudes: np.ndarray

    def __post_init__(self) -> None:
        vector = np.asarray(self.amplitudes, dtype=np.complex128)
        if vector.shape != (2,):
            raise ValueError("BlochState requires exactly two amplitudes")
        object.__setattr__(self, "amplitudes", _normalise(vector))

    @classmethod
    def from_phase_vector(cls, phases: Iterable[float]) -> "BlochState":
        values = np.asarray(list(phases), dtype=np.float64)
        if values.size == 0:
            raise ValueError("phase vector cannot be empty")
        theta = float(np.mean(np.mod(values, 2 * math.pi)))
        phi = float(np.angle(np.mean(np.exp(1j * values))))
        return cls(np.array([math.cos(theta / 2), np.exp(1j * phi) * math.sin(theta / 2)]))

    def bloch_vector(self) -> np.ndarray:
        a, b = self.amplitudes
        return np.array([2 * np.real(np.conj(a) * b), 2 * np.imag(np.conj(a) * b), abs(a) ** 2 - abs(b) ** 2])


@dataclass(frozen=True)
class DynamicsReport:
    state: BlochState
    energy: float
    coherence: float
    step_norm: float
    hypothesis_only: bool = True


class SemanticHamiltonian:
    """A Hermitian two-level Hamiltonian derived from bounded semantic inputs."""

    def __init__(self, *, detuning: float = 0.0, coupling: float = 0.0, bias: float = 0.0) -> None:
        self.detuning = float(np.clip(detuning, -1.0, 1.0))
        self.coupling = float(np.clip(coupling, -1.0, 1.0))
        self.bias = float(np.clip(bias, -1.0, 1.0))

    @property
    def matrix(self) -> np.ndarray:
        return np.array(
            [[self.bias + self.detuning, self.coupling], [self.coupling, self.bias - self.detuning]],
            dtype=np.complex128,
        )

    def evolve(self, state: BlochState, *, dt: float, damping: float = 0.0) -> DynamicsReport:
        if not 0.0 < dt <= 1.0:
            raise ValueError("dt must be in (0, 1]")
        if not 0.0 <= damping < 1.0:
            raise ValueError("damping must be in [0, 1)")
        eigenvalues, eigenvectors = np.linalg.eigh(self.matrix)
        unitary = eigenvectors @ np.diag(np.exp(-1j * eigenvalues * dt)) @ eigenvectors.conj().T
        evolved = unitary @ state.amplitudes
        if damping:
            evolved = (1.0 - damping) * evolved + damping * np.array([1.0 + 0j, 0j])
        next_state = BlochState(evolved)
        energy = float(np.real(np.vdot(next_state.amplitudes, self.matrix @ next_state.amplitudes)))
        coherence = float(np.linalg.norm(next_state.bloch_vector()[:2]))
        step_norm = float(np.linalg.norm(next_state.amplitudes - state.amplitudes))
        return DynamicsReport(next_state, energy, coherence, step_norm)


class StableReductionGate:
    """Hysteretic diagnostic gate; it emits a state only and cannot commit work."""

    def __init__(self, *, commit_after: int = 3, release_after: int = 2, threshold: float = 0.45) -> None:
        self.commit_after = commit_after
        self.release_after = release_after
        self.threshold = threshold
        self._above = 0
        self._below = 0
        self._stable = False

    def observe(self, score: float, coherence: float, mean_coherence: float) -> str:
        accepted = score > self.threshold and coherence > mean_coherence
        if accepted:
            self._above += 1
            self._below = 0
            if not self._stable and self._above >= self.commit_after:
                self._stable = True
                return "hold"
        else:
            self._below += 1
            self._above = 0
            if self._stable and self._below >= self.release_after:
                self._stable = False
                return "release"
        return "stable" if self._stable else "continue"


class TrajectoryMemory:
    """Bounded in-memory trajectories indexed by a caller-provided entity id."""

    def __init__(self, window: int = 32) -> None:
        if window < 1:
            raise ValueError("window must be positive")
        self.window = window
        self._records: dict[str, deque[DynamicsReport]] = {}

    def append(self, entity_id: str, report: DynamicsReport) -> None:
        self._records.setdefault(entity_id, deque(maxlen=self.window)).append(report)

    def window_for(self, entity_id: str) -> tuple[DynamicsReport, ...]:
        return tuple(self._records.get(entity_id, ()))
