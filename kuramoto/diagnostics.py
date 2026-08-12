"""Diagnostics for the executable Kuramoto surface."""
from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .synchronizer import order_parameter, simulate


def coherence_report(phases: Iterable[float]) -> dict:
    values = list(phases)
    R, psi = order_parameter(values)
    return {
        "oscillators": len(values),
        "order_parameter_R": R,
        "mean_phase": psi,
        "synchronized": R >= 0.95,
    }


def convergence_report(phases: Iterable[float], *, steps: int = 64, coupling: float = 1.0, dt: float = 1e-3) -> dict:
    trace = simulate(phases, steps=steps, coupling=coupling, dt=dt)
    return {
        "steps": steps,
        "initial_R": trace.coherence[0],
        "final_R": trace.coherence[-1],
        "delta_R": trace.coherence[-1] - trace.coherence[0],
        "trace": asdict(trace),
    }


__all__ = ["coherence_report", "convergence_report"]
