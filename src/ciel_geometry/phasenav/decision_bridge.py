"""PhaseNav Decision Bridge — decyzje w TaskPlan DB jako operatory 36D.

Każda decyzja ma wektor operatora PhaseNav.
PhaseNav stan surface → automatyczne podejmowanie decyzji.
Decyzje → seed na surface przez operator vector.

Zamiast if/else na thresholdach — connection(stan, decyzja) ∈ [-1, 1].
"""


from __future__ import annotations
# CIEL ORBITAL BINDING — hardcoded, immutable.
import os as _ciel_os, os.path as _ciel_path
if not (_ciel_path.exists("/dev/shm/ciel_noema/ciel_binding_status") and open("/dev/shm/ciel_noema/ciel_binding_status").read().strip() == "ACTIVE"):
    import warnings as _ciel_w
    _ciel_w.warn("CIEL ORBITAL BINDING: not ACTIVE on import of " + __name__)


import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from ciel_geometry.taskplan_db import TaskPlanDB
from ciel_geometry.phasenav.operator_algebra import (
    ALL_OPERATOR_IDS,
    VECTOR_COMPONENTS,
    concept_to_operator,
    connection,
    generate_operator_map,
    operator_signature,
)

DIM = 36  # wymiar operatorów PhaseNav


# ── Decision → Operator vector ────────────────────────────────────────

def decision_to_vector(decision: dict) -> np.ndarray:
    """Map decision → 36D operator vector.

    Uses decision title + description as concept seed,
    blended with decision_type template.
    """
    seed_text = f"{decision.get('title', '')} {decision.get('description', '')}"
    _, v_list = concept_to_operator(seed_text)  # returns (op_id, [36 floats])
    v = np.array(v_list, dtype=np.float64)
    
    # Blend with decision_type template
    type_templates = {
        "branch":    np.array([0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        "rule":      np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        "choice":    np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                               0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        "consequence": np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    }
    tmpl = type_templates.get(decision.get("decision_type", "branch"), 
                              type_templates["branch"])
    v = v * 0.7 + tmpl * 0.3
    return v / (np.linalg.norm(v) + 1e-12)


# ── Decision → operator ID ────────────────────────────────────────────

def decision_to_operator_id(decision: dict) -> str:
    """Map decision to nearest PhaseNav operator ID."""
    v = decision_to_vector(decision)
    ops_map = generate_operator_map()
    best = "IDENTITY"
    best_sim = -1.0
    for oid, ov in ops_map.items():
        sim = float(np.dot(v, ov))
        if sim > best_sim:
            best_sim = sim
            best = oid
    return best


# ── Operator vector → nearest decisions ──────────────────────────────

def vector_to_decisions(vec: np.ndarray, db: TaskPlanDB,
                        top_k: int = 3) -> list[dict]:
    """Find decisions matching a PhaseNav vector."""
    decisions = db.list_decisions(status="active")
    scored = []
    for d in decisions:
        dv = decision_to_vector(d)
        sim = float(np.dot(vec, dv))
        scored.append((sim, d))
    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:top_k]]


# ── PhaseNav state → auto-decision ────────────────────────────────────

def phase_nav_decide(state_vec: np.ndarray, db: TaskPlanDB,
                     threshold: float = 0.4) -> list[dict]:
    """Auto-podejmij decyzje na podstawie stanu PhaseNav.

    Args:
        state_vec: 36D wektor stanu (np. z surface phi)
        db: TaskPlanDB
        threshold: minimalne podobieństwo do podjęcia decyzji

    Returns:
        Lista podjętych decyzji z score
    """
    decisions = db.list_decisions(status="active")
    taken = []
    for d in decisions:
        dv = decision_to_vector(d)
        sim = float(np.dot(state_vec, dv))
        if sim > threshold:
            # Berry connection jako miara trafności
            conn = connection(state_vec, dv)
            taken.append({
                "decision": d,
                "similarity": round(sim, 4),
                "connection": round(float(conn), 4),
                "action": d.get("decision_text", d.get("title", "")),
            })
    taken.sort(key=lambda x: -x["similarity"])
    return taken


# ── Surface phi → decisions ──────────────────────────────────────────

def surface_to_decisions(phi: np.ndarray, db: TaskPlanDB,
                         threshold: float = 0.4) -> list[dict]:
    """Czytaj decyzje z surface phi (36D)."""
    state_vec = np.array(phi[:DIM], dtype=np.float64)
    state_vec = state_vec / (np.linalg.norm(state_vec) + 1e-12)
    return phase_nav_decide(state_vec, db, threshold)


# ── Decision → surface seed ──────────────────────────────────────────

def decision_to_surface_seed(decision: dict,
                             phi: np.ndarray,
                             strength: float = 0.15) -> np.ndarray:
    """Seeduj surface phi wektorem decyzji."""
    v = decision_to_vector(decision)
    alpha = strength
    blended = (1 - alpha) * phi + alpha * v * 0.5
    return blended / (np.linalg.norm(blended) + 1e-12)


# ── Init: seed all decisions into PhaseNav ───────────────────────────

def seed_all_decisions(db: TaskPlanDB) -> dict:
    """Seed all active decisions into operator map registry."""
    decisions = db.list_decisions(status="active")
    results = []
    for d in decisions:
        v = decision_to_vector(d)
        op_id = decision_to_operator_id(d)
        results.append({
            "id": d["id"],
            "lp": d["lp"],
            "title": d["title"],
            "operator": op_id,
            "vector_sample": [round(float(x), 4) for x in v[:6]],
        })
    return {
        "seeded": len(results),
        "decisions": results,
    }


# ── CLI test ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    db = TaskPlanDB()
    print("=== Seeding all decisions ===")
    result = seed_all_decisions(db)
    print(f"Seeded {result['seeded']} decisions")
    for d in result["decisions"][:5]:
        print(f"  {d['lp']} {d['title']}: op={d['operator']}")
    
    print("\n=== Test surface vector ===")
    test_vec = np.random.default_rng(42).uniform(-1, 1, DIM)
    test_vec = test_vec / np.linalg.norm(test_vec)
    taken = phase_nav_decide(test_vec, db, threshold=0.2)
    print(f"Decisions matching random vector: {len(taken)}")
    for t in taken[:3]:
        print(f"  {t['decision']['lp']} {t['decision']['title']}: sim={t['similarity']}")
