#!/usr/bin/env python3
"""reencode_crystal_precise.py — Re-encode crystal vectors with high-precision Decimal arithmetic.

The v0 crystal was built with M_sentence_phase() which uses float64 arithmetic.
For large Collatz hashes (h up to 2^61), float64 loses ~9 bits before modulo
reduction, causing phase errors up to ~2 rad per dimension.

This script re-encodes every facet using M_sentence_phase_precise() (Decimal-based,
~38 significant digits) while keeping all metadata (text, emotion, soul, ethics, etc.)
unchanged. Result: new phase_crystal_36d.npy, same phase_crystal_meta.jsonl.

Usage:
    python3 scripts/reencode_crystal_precise.py
    python3 scripts/reencode_crystal_precise.py --dry-run     # check counts, no write
    python3 scripts/reencode_crystal_precise.py --batch 1000  # progress every N facets
"""
from __future__ import annotations

import argparse
import json
import sys
import time
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


def _encode_precise(text: str) -> list[float]:
    """High-precision encode: M_sentence_phase_precise + M_fine_tune_36d."""
    v36_raw  = M_sentence_phase_precise(text)
    features = M_quantum_features(text)
    v36, _   = M_fine_tune_36d(v36_raw, features=features)
    return v36


def run(dry_run: bool = False, batch_size: int = 500) -> None:
    if not _VEC_PATH.exists() or not _META_PATH.exists():
        print(f"[ERROR] Crystal data not found in {_DATA_DIR}", file=sys.stderr)
        sys.exit(1)

    # Load metadata
    meta_lines = _META_PATH.read_text(encoding="utf-8").splitlines()
    meta = [json.loads(line) for line in meta_lines if line.strip()]
    n_facets = len(meta)
    print(f"Crystal: {n_facets} facets loaded from {_META_PATH.name}")

    if dry_run:
        print("[DRY RUN] Would re-encode {n_facets} facets. Exiting.")
        return

    # Re-encode all facets
    new_vecs = np.zeros((n_facets, 36), dtype=np.float64)
    t0 = time.time()
    errors = 0

    for i, entry in enumerate(meta):
        text = entry.get("text", "").strip()
        if not text:
            errors += 1
            continue
        try:
            v36 = _encode_precise(text)
            new_vecs[i] = v36
        except Exception as e:
            print(f"[WARN] facet {i}: {e}", file=sys.stderr)
            errors += 1

        if (i + 1) % batch_size == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (n_facets - i - 1) / rate
            print(f"  [{i+1:>6}/{n_facets}]  {rate:.0f} facets/s  ETA {eta:.0f}s")

    elapsed = time.time() - t0
    print(f"\nRe-encoded {n_facets - errors}/{n_facets} facets in {elapsed:.1f}s")
    if errors:
        print(f"[WARN] {errors} facets had empty text or errors — kept as zeros")

    # Verify shape
    assert new_vecs.shape == (n_facets, 36), f"Shape mismatch: {new_vecs.shape}"
    assert np.all(np.isfinite(new_vecs)), "Non-finite values in output!"
    assert np.all((new_vecs >= 0) & (new_vecs < 2 * np.pi)), "Values outside [0, 2π)!"

    # Save
    np.save(str(_VEC_PATH), new_vecs)
    print(f"Saved: {_VEC_PATH}  ({_VEC_PATH.stat().st_size / 1e6:.1f} MB)")
    print("Metadata (phase_crystal_meta.jsonl) unchanged.")
    print("Done. Crystal is now encoded with M_sentence_phase_precise (v1).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=500,
                        help="Progress report interval (default: 500)")
    args = parser.parse_args()
    run(dry_run=args.dry_run, batch_size=args.batch)


if __name__ == "__main__":
    main()
