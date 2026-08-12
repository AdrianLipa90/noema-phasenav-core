"""Minimal production Kuramoto synchronizer for PhaseNav oscillator populations."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

TAU = 2.0 * math.pi
BASE_FREQUENCY_HZ = 7.83
BASE_ANGULAR_FREQUENCY = TAU * BASE_FREQUENCY_HZ
MIN_OSCILLATORS = 3


def _finite(values: Iterable[float], *, label: str) -> list[float]:
    out = [float(x) for x in values]
    if len(out) < MIN_OSCILLATORS:
        raise ValueError(f"{label}: need at least {MIN_OSCILLATORS} oscillators")
    if not all(math.isfinite(x) for x in out):
        raise ValueError(f"{label}: non-finite value")
    return out


def order_parameter(phases: Iterable[float]) -> tuple[float, float]:
    phi = _finite(phases, label="phases")
    s = sum(math.sin(x) for x in phi)
    c = sum(math.cos(x) for x in phi)
    n = len(phi)
    return math.hypot(s, c) / n, math.atan2(s, c) % TAU


def step(
    phases: Iterable[float],
    natural_angular_frequencies: Iterable[float] | None = None,
    *,
    coupling: float = 1.0,
    dt: float = 1e-3,
) -> list[float]:
    phi = _finite(phases, label="phases")
    if natural_angular_frequencies is None:
        omega = [BASE_ANGULAR_FREQUENCY] * len(phi)
    else:
        omega = _finite(natural_angular_frequencies, label="frequencies")
        if len(omega) != len(phi):
            raise ValueError("frequencies must match phase population")
    coupling = float(coupling)
    dt = float(dt)
    if not math.isfinite(coupling) or not math.isfinite(dt) or dt <= 0.0:
        raise ValueError("coupling and dt must be finite; dt must be positive")
    n = len(phi)
    out: list[float] = []
    for i, phase_i in enumerate(phi):
        interaction = sum(math.sin(phase_j - phase_i) for phase_j in phi) / n
        out.append((phase_i + dt * (omega[i] + coupling * interaction)) % TAU)
    return out


@dataclass(frozen=True)
class KuramotoTrace:
    phases: tuple[tuple[float, ...], ...]
    coherence: tuple[float, ...]
    mean_phase: tuple[float, ...]


def simulate(
    phases: Iterable[float],
    *,
    steps: int,
    coupling: float = 1.0,
    dt: float = 1e-3,
    natural_angular_frequencies: Iterable[float] | None = None,
) -> KuramotoTrace:
    current = _finite(phases, label="phases")
    if int(steps) < 0:
        raise ValueError("steps must be non-negative")
    phase_rows = [tuple(current)]
    R0, psi0 = order_parameter(current)
    coherence = [R0]
    mean_phase = [psi0]
    omega = None if natural_angular_frequencies is None else list(natural_angular_frequencies)
    for _ in range(int(steps)):
        current = step(current, omega, coupling=coupling, dt=dt)
        phase_rows.append(tuple(current))
        R, psi = order_parameter(current)
        coherence.append(R)
        mean_phase.append(psi)
    return KuramotoTrace(
        phases=tuple(phase_rows),
        coherence=tuple(coherence),
        mean_phase=tuple(mean_phase),
    )


__all__ = [
    "BASE_ANGULAR_FREQUENCY",
    "BASE_FREQUENCY_HZ",
    "KuramotoTrace",
    "MIN_OSCILLATORS",
    "order_parameter",
    "simulate",
    "step",
]
