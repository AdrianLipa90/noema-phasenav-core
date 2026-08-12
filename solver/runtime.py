"""Repository-level executable façade for the package PhaseNav solver."""
from __future__ import annotations

from pathlib import Path

from ciel_geometry.phasenav.solver import PhaseNavSolver, PhaseNavTrace


def load(base_path: str | Path | None = None) -> PhaseNavSolver:
    return PhaseNavSolver.load(base_path)


def trace(card_ids: list[str], base_path: str | Path | None = None) -> PhaseNavTrace:
    if len(card_ids) < 2:
        raise ValueError("trace requires at least two card ids")
    return load(base_path).trace(card_ids)


__all__ = ["load", "trace"]
