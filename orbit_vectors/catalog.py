"""Canonical 36D phase-orbit catalogue.

This module deliberately separates phase-orbit coordinates from the historical
11-feature schema. ``orbit_vector`` is always finite T^36 phase data.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from ciel_geometry.phasenav.artifact_registry import build_canonical_runtime_bundle


VECTOR_DIM = 36
DIMS = tuple(f"phi_{i}" for i in range(VECTOR_DIM))


def records() -> list[dict[str, Any]]:
    rows = list(build_canonical_runtime_bundle().records["orbit_vectors"])
    for row in rows:
        vector = [float(x) for x in row["orbit_vector"]]
        if len(vector) != VECTOR_DIM or not all(math.isfinite(x) for x in vector):
            raise RuntimeError(f"invalid orbit vector for {row.get('card_id')}")
    return rows


def vector(card_id: str) -> list[float]:
    key = str(card_id).removeprefix("concept:").zfill(3)
    for row in records():
        if str(row["card_id"]) == key:
            return [float(x) for x in row["orbit_vector"]]
    raise KeyError(key)


def export_jsonl(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = records()
    if not rows:
        raise RuntimeError("orbit catalogue is empty")
    target.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return target


__all__ = ["DIMS", "VECTOR_DIM", "export_jsonl", "records", "vector"]
