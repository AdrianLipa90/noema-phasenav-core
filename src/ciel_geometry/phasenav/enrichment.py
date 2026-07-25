"""PhaseNav Enrichment — augment card generators with operator phase data.

Each card (word, orbital, object, etc.) gets:
  - operator_id       — deterministic mapping to one of 33 operators
  - operator_vector   — 24D semantic vector
  - harmonic_imprint  — R₁, R₃, R₆, R₉ if seeded onto 24 oscillators
  - kappa_potential   — synchronizability proxy
  - semantic_mass     — operator's semantic density
"""
from __future__ import annotations

from typing import Any

import numpy as np

from .operator_algebra import (
    ALL_OPERATOR_IDS, concept_to_operator, operator_signature,
)


def harmonic_imprint(vector_36d: np.ndarray | list[float]) -> dict[str, float]:
    """Project 36D vector onto 36 oscillator phases, compute 3-6-9 R."""
    v = np.asarray(vector_36d, dtype=np.float64)
    phases = np.arctan2(v[1::2], v[0::2])
    if len(phases) < 36:
        phases = np.pad(phases, (0, 36 - len(phases)), constant_values=0.0)
    phases = (phases + 2 * np.pi) % (2 * np.pi)
    R = {}
    for h in (1, 3, 6, 9):
        Z = np.mean(np.exp(1j * h * phases))
        R[f"R_{h}"] = round(float(abs(Z)), 6)
    return R


def operator_harmonic_fingerprint(vector_36d: np.ndarray | list[float]) -> str:
    """Classify operator as HLLH etc based on harmonic R_h thresholds."""
    R = harmonic_imprint(vector_36d)
    parts = []
    for h in (1, 3, 6, 9):
        parts.append("H" if R[f"R_{h}"] > 0.5 else "L")
    return "".join(parts)


def phasenav_enrich(card_id: str, name: str = "") -> dict[str, Any]:
    """Enrich a card with PhaseNav operator data.

    Args:
        card_id: Unique card identifier (deterministic → operator).
        name: Optional human-readable name (adjusts operator mapping).

    Returns:
        dict with operator_id, vector_24d, harmonic_imprint, fingerprint, etc.
    """
    seed_str = f"{card_id}::{name}" if name else card_id
    op_id, vec_list = concept_to_operator(seed_str)
    vec_np = np.array(vec_list, dtype=np.float64)
    H = harmonic_imprint(vec_np)
    fp = operator_harmonic_fingerprint(vec_np)

    return {
        "operator_id": op_id,
        "operator_vector_24d": vec_list,
        "harmonic_imprint": H,
        "harmonic_fingerprint": fp,
        "kappa_potential": round(float(vec_np[23]), 6),
        "semantic_mass": round(float(vec_np[0]), 6),
        "card_kind": round(float(vec_np[21]), 6),
    }


def operator_id_from_card(card_id: str, name: str = "") -> str:
    """Quick lookup: just the operator ID for a card."""
    seed_str = f"{card_id}::{name}" if name else card_id
    return ALL_OPERATOR_IDS[abs(hash(seed_str)) % len(ALL_OPERATOR_IDS)]
