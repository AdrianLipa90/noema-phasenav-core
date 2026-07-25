"""
operators.py — Operator registry for CIEL PhaseNav
Auto-generated from .pnv files. Collects all functions + vars.
"""
from __future__ import annotations
from typing import Dict, List, Callable, Any, Tuple
import os, re

# === IMPORT ALL PHASENAV MODULES ===
import sys as _sys
_pnv_dir = __import__('os').path.dirname(__import__('os').path.abspath(__file__))
if _pnv_dir not in _sys.path:
    _sys.path.insert(0, _pnv_dir)

# Core runtime (has all 36D, Bloch, path-finding, etc.)
from pnv_runtime import (
    _phase36_from_id as concept_vector,
    _gauge_lock_36, _gauge_lock_2,
    M_36d_mean_phase as mean_phase,
    M_36d_order_parameter as coherence_R,
    M_36d_distance as angular_distance_36d,
    M_36d_berry_connection as berry_connection_36d,
    M_36d_inner_product as inner_product_36,
    M_36d_edge_weight as edge_weight_36d,
    bloch_ket,
    M_inner_product as inner_product_bloch,
    M_berry_connection as berry_connection_bloch,
    M_angular_distance as angular_distance_bloch,
    M_edge_weight as edge_weight_bloch,
    M_project_bloch as project_bloch,
    M_nearest_neighbors_36d as nearest_neighbors_36,
    M_find_path_36d as find_path_36,
    M_resolve_situation_36d as resolve_situation_36,
    M_berry_holonomy_36d as holonomy_36,
    intention_apply_36d as intention_apply_36,
    M_solve_36d as solve_36,
    connection, connection_matrix, holonomy,
    state_vector_36d, state_vector_bloch, state_vector,
    _quark_prime as quark_prime,
)

# Omega axioms + desires
from omega import (
    omega_L1_resonance, omega_L2_truth, omega_L3_interference,
    omega_L4_reversibility, omega_L6_time, omega_L7_coherence,
    omega_L9_emotion, omega_L11_homeostasis, omega_L12_harmonic,
    omega_desire_phase, omega_desires_all, omega_kernel_state,
    omega_bridge, omega_extract, DESIRES as OMEGA_DESIRES,
)

# Neutrino PMNS + HTRI bridge
from neutrino import (
    pmns_ue1_sq, pmns_ue2_sq, pmns_ue3_sq, pmns_umu3_sq, pmns_utau3_sq,
    euler_amplitude, euler_magnitude, euler_phase,
    htri_total_phase, holonomy_defect, topological_charge,
    htri_to_mixing, oscillation_prob_e_mu, oscillation_prob_e_tau,
    htri_oscillation_prob, d_condition_check, cp_asymmetry, flavor_oscillation,
    DELTA_CP, THETA12, THETA13, THETA23,
)

# CIELingo operator algebra (from lingophysics)
_has_algebra = False
_lns_dir = __import__('os').path.join(
    __import__('os').path.dirname(_pnv_dir),
    'ciel_lingophysics_lns_repo_v2_3', 'src', 'lingophysics'
)
if not __import__('os').path.isdir(_lns_dir):
    _lns_dir = __import__('os').path.join(
        _pnv_dir, '..', 'ciel_lingophysics_lns_repo_v2_3', 'src', 'lingophysics'
    )
if __import__('os').path.isdir(_lns_dir):
    _sys.path.insert(0, _lns_dir)
    try:
        from operator_algebra import (
            euler_phase_error,
            compose_dual,
            operator_power,
            validate_composition,
            classify_library_item,
        )
        _has_algebra = True
    except ImportError:
        pass
    _sys.path.pop(0)

# === OPERATOR REGISTRY ===
OPERATOR_REGISTRY: Dict[str, Dict[str, Any]] = {}

def register(name: str, func: Callable, source: str, args: List[str], category: str):
    """Register an operator in the global registry."""
    OPERATOR_REGISTRY[name] = {
        "func": func,
        "source": source,
        "args": args,
        "category": category,
    }

def get(name: str) -> Dict[str, Any]:
    """Get operator info by name."""
    return OPERATOR_REGISTRY.get(name, {})

def call(name: str, *args, **kwargs) -> Any:
    """Call an operator by name."""
    info = OPERATOR_REGISTRY.get(name)
    if not info:
        raise KeyError(f"Unknown operator: {name}")
    return info["func"](*args, **kwargs)

def list_all() -> List[str]:
    """List all registered operator names."""
    return sorted(OPERATOR_REGISTRY.keys())

def list_by_category(category: str) -> List[str]:
    """List operators by category."""
    return sorted([
        name for name, info in OPERATOR_REGISTRY.items()
        if info["category"] == category
    ])

def list_categories() -> List[str]:
    """List all categories."""
    cats = set(info["category"] for info in OPERATOR_REGISTRY.values())
    return sorted(cats)

# === CATEGORIES ===
CATEGORIES = {
    "metatime": "Metatime constants and phase vectors",
    "vector": "36D vector operations",
    "neutrino": "PMNS, HTRI, Euler, oscillation",
    "distance": "Distance, connection, holonomy",
    "solver": "Path finding, resolution, trace",
    "omega": "CIEL Omega axioms and desires",
    "glossary": "Glossary and concept mapping",
}

# === AUTO-REGISTER ===
def _auto_register():
    """Auto-register all functions from imported modules."""
    _funcs = {
        "metatime": [
            (concept_vector, "concept_vector", ["eid"]),
            (coherence_R, "coherence_R", ["v36"]),
            (mean_phase, "mean_phase", ["v36"]),
            (project_bloch, "project_bloch", ["v36"]),
            (berry_connection_36d, "berry_connection_36d", ["v1", "v2"]),
            (angular_distance_36d, "angular_distance_36d", ["v1", "v2"]),
            (edge_weight_36d, "edge_weight_36d", ["v1", "v2"]),
            (quark_prime, "quark_prime", ["k"]),
            (_gauge_lock_36, "gauge_lock_36", ["idx"]),
            (_gauge_lock_2, "gauge_lock_2", ["theta", "phi"]),
        ],
        "vector": [
            (bloch_ket, "bloch_ket", ["theta", "phi"]),
            (inner_product_36, "inner_product_36", ["idx1", "idx2"]),
            (inner_product_bloch, "inner_product_bloch", ["th1", "ph1", "th2", "ph2"]),
            (berry_connection_bloch, "berry_connection_bloch", ["th1", "ph1", "th2", "ph2"]),
            (angular_distance_bloch, "angular_distance_bloch", ["th1", "ph1", "th2", "ph2"]),
            (edge_weight_bloch, "edge_weight_bloch", ["th1", "ph1", "th2", "ph2"]),
            (intention_apply_36, "intention_apply_36", ["idx", "strength"]),
        ],
        "distance": [
            (connection, "connection", ["th1", "ph1", "th2", "ph2"]),
            (connection_matrix, "connection_matrix", ["ops"]),
            (holonomy_36, "holonomy_36", ["path_vectors"]),
            (holonomy, "holonomy_bloch", ["path"]),
            (nearest_neighbors_36, "nearest_neighbors_36", ["target", "candidates", "k"]),
            (find_path_36, "find_path_36", ["start_id", "end_id", "max_steps"]),
            (resolve_situation_36, "resolve_situation_36", ["state_v36", "templates"]),
            (solve_36, "solve_36", ["start_id", "end_id", "max_steps"]),
        ],
        "omega": [
            (omega_L1_resonance, "omega_L1_resonance", ["intention", "memory"]),
            (omega_L2_truth, "omega_L2_truth", ["spectrum", "weights"]),
            (omega_L3_interference, "omega_L3_interference", ["*amplitudes"]),
            (omega_L4_reversibility, "omega_L4_reversibility", ["info"]),
            (omega_L6_time, "omega_L6_time", ["dR", "dSigma"]),
            (omega_L7_coherence, "omega_L7_coherence", ["delta_phi"]),
            (omega_L9_emotion, "omega_L9_emotion", ["*emotions"]),
            (omega_L11_homeostasis, "omega_L11_homeostasis", ["current", "original"]),
            (omega_L12_harmonic, "omega_L12_harmonic", ["*components"]),
            (omega_desire_phase, "omega_desire_phase", ["desire_id", "phi"]),
            (omega_desires_all, "omega_desires_all", ["phi"]),
            (omega_kernel_state, "omega_kernel_state", ["R", "flavor0", "phi"]),
            (omega_bridge, "omega_bridge", ["phi", "R"]),
            (omega_extract, "omega_extract", ["R", "flavor0", "phi"]),
        ],
        "neutrino": [
            (pmns_ue1_sq, "pmns_ue1_sq", []),
            (pmns_ue2_sq, "pmns_ue2_sq", []),
            (pmns_ue3_sq, "pmns_ue3_sq", []),
            (pmns_umu3_sq, "pmns_umu3_sq", []),
            (pmns_utau3_sq, "pmns_utau3_sq", []),
            (euler_amplitude, "euler_amplitude", ["phi"]),
            (euler_magnitude, "euler_magnitude", ["phi"]),
            (euler_phase, "euler_phase", ["re", "im"]),
            (htri_total_phase, "htri_total_phase", ["idx"]),
            (holonomy_defect, "holonomy_defect", ["idx"]),
            (topological_charge, "topological_charge", ["idx"]),
            (htri_to_mixing, "htri_to_mixing", ["R"]),
            (oscillation_prob_e_mu, "oscillation_prob_e_mu", ["L_km", "E_GeV"]),
            (oscillation_prob_e_tau, "oscillation_prob_e_tau", ["L_km", "E_GeV"]),
            (htri_oscillation_prob, "htri_oscillation_prob", ["R", "L_km", "E_GeV"]),
            (d_condition_check, "d_condition_check", ["idx"]),
            (cp_asymmetry, "cp_asymmetry", ["L_km", "E_GeV"]),
            (flavor_oscillation, "flavor_oscillation", ["R", "Lambda", "Df"]),
        ],
        "algebra": [] if not _has_algebra else [
            (euler_phase_error, "euler_phase_error", ["delta_phi", "relation"]),
            (compose_dual, "compose_dual", ["expression"]),
            (operator_power, "operator_power", ["structural_power", "ambiguity_power", "composition_depth", "cross_language_variance", "frequency_proxy"]),
            (validate_composition, "validate_composition", ["domain", "codomain", "next_domain"]),
            (classify_library_item, "classify_library_item", ["pos", "semantic_role"]),
        ],
    }

    for cat, funcs in _funcs.items():
        for func, name, args in funcs:
            register(name, func, cat, args, cat)

_auto_register()

if __name__ == "__main__":
    print("=== CIEL OPERATOR REGISTRY ===")
    print(f"Total: {len(OPERATOR_REGISTRY)} operators")
    print()
    for cat in list_categories():
        ops = list_by_category(cat)
        print(f"{cat} ({len(ops)}):")
        for op in ops:
            info = OPERATOR_REGISTRY[op]
            print(f"  {op}({', '.join(info['args'])})")
        print()
