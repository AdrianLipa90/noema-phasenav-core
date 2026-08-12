"""Executable concept-phase catalogue backed by the canonical PhaseNav registry."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ciel_geometry.phasenav.artifact_registry import build_canonical_runtime_bundle


def records() -> list[dict[str, Any]]:
    return list(build_canonical_runtime_bundle().records["concept_phases"])


def by_id(concept_id: str) -> dict[str, Any]:
    key = str(concept_id).removeprefix("concept:").zfill(3)
    for record in records():
        if str(record["state_id"]) == key:
            return record
    raise KeyError(key)


def export_jsonl(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = records()
    if not rows:
        raise RuntimeError("concept phase catalogue is empty")
    target.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return target


__all__ = ["by_id", "export_jsonl", "records"]
