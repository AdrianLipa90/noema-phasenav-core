"""Numerical guards for finite PhaseNav projections and trajectory observables."""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from ..pnv_runtime import TAU
from .context_dynamics import PhaseVector36
from .model import PHASE_DIM

_EPS = 1.0e-12


def project_oscillator_banks_36(
    cpu_phases: np.ndarray,
    gpu_phases: np.ndarray,
) -> PhaseVector36:
    """Project any non-empty finite oscillator population onto all 36 axes.

    For populations smaller than 36, dimensions without a native strided member
    reuse the oscillator at ``dimension mod population``. This preserves finite,
    deterministic output instead of taking the mean of an empty slice.
    """

    phases = np.concatenate(
        (
            np.asarray(cpu_phases, dtype=np.float64).reshape(-1),
            np.asarray(gpu_phases, dtype=np.float64).reshape(-1),
        )
    )
    if phases.size == 0:
        raise ValueError("at least one oscillator phase is required")
    if not np.all(np.isfinite(phases)):
        raise ValueError("oscillator phases must be finite")

    projected: list[float] = []
    for dimension in range(PHASE_DIM):
        selected = phases[dimension::PHASE_DIM]
        if selected.size == 0:
            selected = phases[[dimension % phases.size]]
        resultant = np.mean(np.exp(1j * selected))
        projected.append(float(np.angle(resultant) % TAU))
    return PhaseVector36(tuple(projected))


def stable_trajectory_curvature(
    trajectory: Sequence[PhaseVector36],
) -> float:
    """RMS turning angle with exact-zero stabilization for collinear tangents."""

    if len(trajectory) < 3:
        return 0.0
    tangents = [
        (
            np.asarray(trajectory[index + 1].components)
            - np.asarray(trajectory[index].components)
            + math.pi
        )
        % TAU
        - math.pi
        for index in range(len(trajectory) - 1)
    ]
    turns: list[float] = []
    for left, right in zip(tangents, tangents[1:]):
        left_norm = float(np.linalg.norm(left))
        right_norm = float(np.linalg.norm(right))
        if left_norm <= _EPS or right_norm <= _EPS:
            continue
        cosine = float(np.dot(left, right) / (left_norm * right_norm))
        if cosine >= 1.0 - _EPS:
            turns.append(0.0)
        elif cosine <= -1.0 + _EPS:
            turns.append(math.pi)
        else:
            turns.append(math.acos(cosine))
    if not turns:
        return 0.0
    curvature = float(np.sqrt(np.mean(np.square(turns))))
    return 0.0 if curvature <= _EPS else curvature
