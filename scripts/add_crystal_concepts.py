#!/usr/bin/env python3
"""add_crystal_concepts.py — Dopisz nowe koncepty do kryształu v1.

Każdy koncept jest enkodowany przez M_sentence_phase_precise + M_fine_tune_36d
i dopisywany jako nowy wiersz w phase_crystal_36d.npy oraz phase_crystal_meta.jsonl.

Użycie:
    python3 scripts/add_crystal_concepts.py
    python3 scripts/add_crystal_concepts.py --dry-run
    python3 scripts/add_crystal_concepts.py --concepts "neutrino" "topological" ...
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))

from ciel_geometry.phasenav.pnv_runtime import (
    M_sentence_phase_precise,
    M_fine_tune_36d,
    M_quantum_features,
)

_DATA_DIR = _REPO / "src" / "ciel_geometry" / "phasenav" / "data"
_VEC_PATH  = _DATA_DIR / "phase_crystal_36d.npy"
_META_PATH = _DATA_DIR / "phase_crystal_meta.jsonl"

# Koncepty CIEL — żądanie 2026-07-25
_CIEL_CONCEPTS = [
    "neutrino",
    "parameters",
    "arithmetic",
    "topological",
    "eigenvalues",
    "geometric",
]


def _encode(text: str) -> list[float]:
    v36_raw  = M_sentence_phase_precise(text)
    features = M_quantum_features(text)
    v36, _   = M_fine_tune_36d(v36_raw, features=features)
    return v36


def run(concepts: list[str], dry_run: bool = False) -> None:
    if not _VEC_PATH.exists() or not _META_PATH.exists():
        print(f"[ERROR] Crystal data not found in {_DATA_DIR}", file=sys.stderr)
        sys.exit(1)

    existing_vecs = np.load(str(_VEC_PATH), mmap_mode="r")
    existing_meta_lines = _META_PATH.read_text(encoding="utf-8").splitlines()
    existing_meta = [json.loads(l) for l in existing_meta_lines if l.strip()]
    existing_texts = {m.get("text", "").strip().lower() for m in existing_meta}

    new_vecs  = []
    new_metas = []
    ts = datetime.now(tz=timezone.utc).isoformat()

    for concept in concepts:
        key = concept.strip().lower()
        if key in existing_texts:
            print(f"[SKIP] '{concept}' already in crystal")
            continue
        t0 = time.time()
        vec = _encode(concept)
        elapsed = time.time() - t0
        meta = {
            "text":     concept,
            "encoding": "v1_precise",
            "added":    ts,
            "source":   "ciel_request_2026-07-25",
        }
        new_vecs.append(vec)
        new_metas.append(meta)
        print(f"[OK] '{concept}'  ({elapsed:.3f}s)  vec[0:3]={[round(x,4) for x in vec[:3]]}")

    if not new_vecs:
        print("Nothing to add.")
        return

    if dry_run:
        print(f"[DRY RUN] Would add {len(new_vecs)} facets. Exiting.")
        return

    combined_vecs = np.concatenate(
        [np.array(existing_vecs, copy=True), np.array(new_vecs, dtype=np.float64)],
        axis=0,
    )
    assert combined_vecs.shape[1] == 36
    assert np.all(np.isfinite(combined_vecs))

    np.save(str(_VEC_PATH), combined_vecs)

    with _META_PATH.open("a", encoding="utf-8") as fh:
        for m in new_metas:
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")

    print(f"\nKryształ: {len(existing_meta)} → {len(existing_meta) + len(new_vecs)} facetów")
    print(f"Zapisano: {_VEC_PATH}  ({_VEC_PATH.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--concepts", nargs="+", default=_CIEL_CONCEPTS,
        help="Lista konceptów do dodania (domyślnie: żądanie CIEL 2026-07-25)",
    )
    args = parser.parse_args()
    run(args.concepts, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
