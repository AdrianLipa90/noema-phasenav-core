"""Operator Algebra compatibility layer over canonical 36D PhaseNav runtime.

Alg 0/0b: Runtime JSONL loaders for 47 operators and concept phases.
"""

from __future__ import annotations

from functools import lru_cache
import json
import math as _math
from pathlib import Path

import numpy as np

from ciel_geometry.phasenav.pnv_runtime import (
    ALPHA_M,
    KAPPA,
    L3,
    L4,
    L5,
    L_RATIO,
    M_36d_angular_distance,
    M_36d_berry_connection,
    M_36d_distance,
    M_36d_edge_weight,
    M_36d_inner_product,
    M_36d_mean_phase,
    M_36d_order_parameter,
    M_collatz_hash,
    PI,
    TAU,
    VECTOR_COMPONENTS,
    VECTOR_DIM,
    _phase36_from_id,
    _semantic_mass,
    get_all_states,
)

OPERATOR_DIM = VECTOR_DIM
ALL_OPERATOR_IDS: list[str] = [
    "IDENTITY", "DIFFERENCE", "ORDER", "COMPOSITION", "ADDITION",
    "FORCE", "NEGATION", "QUESTION", "TRANSFORM", "RETURN",
    "FOLD", "BOUNDARY", "SCOPE", "AFFECT", "CONSENT",
    "SOURCE", "MEMORY", "RISK",
    "ASSERTION", "CONDITION", "CAUSE",
    "MODAL_POSSIBILITY", "MODAL_NECESSITY", "MODAL_PERMISSION",
    "MODAL_OBLIGATION", "UNCERTAINTY", "SOURCE_REQUIRED",
    "CANON_BLOCK", "CONSENT_REQUIRED", "ACTION_REQUEST",
    "REFUSAL", "PAUSE", "SIMULATION_BOUNDARY",
    "UNRUH_DRIVE", "WARP_DRIFT", "ATTRACTOR",
]
_OPERATOR_ID_SET = frozenset(ALL_OPERATOR_IDS)
OPERATOR_REGISTRY: dict[str, dict[str, object]] = {}

__all__ = [
    "ALL_OPERATOR_IDS",
    "OPERATOR_DIM",
    "OPERATOR_REGISTRY",
    "VECTOR_COMPONENTS",
    "VECTOR_DIM",
    "operator_vector_24d",
    "operator_vector_36d",
    "operator_signature",
    "concept_to_operator",
    "generate_operator_map",
    "generate_operator_jsonl",
    "get_all_operations",
    "connection",
    "connection_matrix",
    "surface_holonomy",
    "statistical_closure",
    "detect_situation",
    "SITUATION_TEMPLATES",
    "PI",
    "TAU",
    "KAPPA",
    "ALPHA_M",
    "L3",
    "L4",
    "L5",
    "L_RATIO",
    "M_collatz_hash",
    "_semantic_mass",
    "_phase36_from_id",
    # Alg 0 / 0b
    "load_runtime_operators",
    "load_concept_phases",
    "RUNTIME_OPERATORS",
    "CONCEPT_PHASES",
]

# ── Runtime caches (populated lazily on first call) ─────────────────
RUNTIME_OPERATORS: dict[str, np.ndarray] = {}
CONCEPT_PHASES: dict[str, np.ndarray] = {}

_NOEMA_ROOT = Path(__file__).resolve().parents[3]
_RUNTIME_JSONL = _NOEMA_ROOT / "runtime" / "phasenav" / "latest" / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
_CONCEPT_JSONL = _NOEMA_ROOT / "runtime" / "phasenav" / "latest" / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl"


def _require_operator(op_id: str) -> str:
    if op_id not in _OPERATOR_ID_SET:
        raise KeyError(f"unknown PhaseNav operator: {op_id}")
    return op_id


@lru_cache(maxsize=None)
def operator_vector_36d(op_id: str) -> list[float]:
    return [float(x) for x in _phase36_from_id(_require_operator(op_id))]


def operator_vector_24d(op_id: str) -> list[float]:
    # Legacy name kept for compatibility. Canonical contract is 36D.
    return operator_vector_36d(op_id)


def operator_signature(op_name: str) -> np.ndarray:
    return np.asarray(operator_vector_36d(_require_operator(op_name)), dtype=np.float64)


def concept_to_operator(concept_id: str) -> tuple[str, list[float]]:
    if concept_id == "__no_registered_anchor__":
        return "UNCERTAINTY", operator_vector_36d("UNCERTAINTY")
    if not ALL_OPERATOR_IDS:
        raise RuntimeError("PhaseNav operator glossary is empty")
    idx = M_collatz_hash(concept_id) % len(ALL_OPERATOR_IDS)
    op_id = ALL_OPERATOR_IDS[idx]
    return op_id, operator_vector_36d(op_id)


def generate_operator_map() -> dict[str, list[float]]:
    return {op_id: operator_vector_36d(op_id) for op_id in ALL_OPERATOR_IDS}


def generate_operator_jsonl(path: str | None = None) -> str:
    records = []
    for op_id in ALL_OPERATOR_IDS:
        vector = operator_vector_36d(op_id)
        records.append(
            {
                "schema": "PHASENAV_OPERATOR_VECTOR_V1",
                "canonical_name": "PhaseNav",
                "card_id": op_id,
                "operator_id": op_id,
                "vector_dim": OPERATOR_DIM,
                "vector_36d": [round(float(x), 10) for x in vector],
                "semantic_mass": round(float(vector[0]), 10),
            }
        )
    content = "\n".join(__import__("json").dumps(record, ensure_ascii=False) for record in records) + "\n"
    if path:
        from pathlib import Path

        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
    return content


def get_all_operations() -> dict[str, dict[str, object]]:
    return {
        op_id: {
            "state_id": op_id,
            "name": op_id,
            "vector_36d": operator_vector_36d(op_id),
            "R": round(M_36d_order_parameter(operator_vector_36d(op_id)), 10),
            "mean_phase": round(M_36d_mean_phase(operator_vector_36d(op_id)), 10),
            "semantic_mass": round(float(operator_vector_36d(op_id)[0]), 10),
            "operator": op_id,
        }
        for op_id in ALL_OPERATOR_IDS
    }


def connection(v1, v2=None, v3=None, v4=None) -> float:
    if v2 is not None and v3 is None and v4 is None:
        return float(M_36d_berry_connection(v1, v2))
    if v2 is not None and v3 is not None and v4 is not None:
        return float(M_36d_berry_connection([v1, v2], [v3, v4]))
    raise TypeError("connection expects either (vector_a, vector_b) or (theta1, phi1, theta2, phi2)")


def connection_matrix(ops: dict[str, list[float]] | None = None) -> list[list[float]]:
    if ops is None:
        ops = generate_operator_map()
    vectors = np.asarray(list(ops.values()), dtype=np.float64)
    if vectors.size == 0:
        return []
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
    normalized = vectors / norms
    return (normalized @ normalized.T).tolist()


def surface_holonomy(phi: np.ndarray) -> tuple[float, int]:
    """Holonomy of the Berry connection around S¹ given current surface φ.

    Wraps each step to [-π, π] before summing so the result measures actual
    winding around the ring instead of a telescoping sum that cancels to zero.
    """
    dphi = np.diff(phi, append=phi[0])
    dphi_wrapped = ((dphi + np.pi) % (2 * np.pi)) - np.pi
    gamma = float(np.sum(dphi_wrapped))
    winding = int(round(gamma / (2 * np.pi)))
    return float(gamma % (2 * np.pi)), winding


def statistical_closure(v36: list[float]) -> float:
    R = M_36d_order_parameter(v36)
    var = sum((v % TAU - _math.pi) ** 2 for v in v36) / len(v36)
    return min(1.0, R + 0.5 * max(0.0, 1.0 - var / (TAU * TAU / 12.0)))


SITUATION_TEMPLATES: dict[str, list[float]] = {
    op_id: operator_vector_36d(op_id) for op_id in ALL_OPERATOR_IDS
}


def detect_situation(phi: list[float] | np.ndarray) -> dict[str, object]:
    state_vec = np.asarray(phi, dtype=np.float64)
    if state_vec.shape[0] != OPERATOR_DIM:
        raise ValueError(f"expected {OPERATOR_DIM}D PhaseNav vector, got shape {state_vec.shape}")
    state_norm = float(np.linalg.norm(state_vec)) + 1e-12
    template_ids = list(SITUATION_TEMPLATES.keys())
    template_vectors = np.asarray([SITUATION_TEMPLATES[op_id] for op_id in template_ids], dtype=np.float64)
    template_norms = np.linalg.norm(template_vectors, axis=1) + 1e-12
    sims = (template_vectors @ state_vec) / (template_norms * state_norm)
    best_idx = int(np.argmax(sims))
    return {
        "operator_id": template_ids[best_idx],
        "score": float(sims[best_idx]),
        "coherence": float(M_36d_order_parameter(state_vec)),
        "semantic_mass": float(state_vec[0]),
    }


# ── Alg 0: Runtime JSONL Operator Loader ────────────────────────────

def load_runtime_operators(
    jsonl_path: Path | str | None = None,
    noema_root: Path | str | None = None,
    force_reload: bool = False,
) -> dict[str, np.ndarray]:
    """Załaduj 47 operatorów z runtime JSONL (Alg 0).

    Każda linia: {card_id, operator_name, orbit_vector}
    orbit_vector to 36D float lista — normalizowana do [0, 2π).

    Fallback do hardcoded ALL_OPERATOR_IDS gdy JSONL niedostępny.
    Wynik cachowany w module-level RUNTIME_OPERATORS.
    """
    global RUNTIME_OPERATORS
    if RUNTIME_OPERATORS and not force_reload:
        return RUNTIME_OPERATORS

    if jsonl_path is None:
        if noema_root is not None:
            jsonl_path = Path(noema_root) / "runtime" / "phasenav" / "latest" / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
        else:
            jsonl_path = _RUNTIME_JSONL

    path = Path(jsonl_path)
    if not path.exists():
        # Fallback: generate from hardcoded operators
        RUNTIME_OPERATORS = {op_id: operator_signature(op_id) for op_id in ALL_OPERATOR_IDS}
        return RUNTIME_OPERATORS

    ops: dict[str, np.ndarray] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            op_name = rec.get("operator_name", "").strip().upper()
            if not op_name:
                # Fallback: wyciągnij nazwę z card_id (np. "op:negation" → "NEGATION")
                card_id = rec.get("card_id", "")
                if ":" in card_id:
                    op_name = card_id.split(":", 1)[1].upper()
                else:
                    op_name = card_id.upper()
            orbit = rec.get("orbit_vector", [])
            if not op_name or not orbit:
                continue
            arr = np.asarray(orbit, dtype=np.float64)
            # Normalizuj do [0, 2π) — orbit_vector może być poza zakresem
            arr = arr % (2 * np.pi)
            if arr.shape[0] == 24:
                # Rozszerz 24D → 36D przez powtórzenie wzorca
                arr = np.tile(arr, 2)[:36]
            elif arr.shape[0] != 36:
                continue
            ops[op_name] = arr
    except Exception:
        pass

    if not ops:
        # Fallback: hardcoded
        ops = {op_id: operator_signature(op_id) for op_id in ALL_OPERATOR_IDS}

    RUNTIME_OPERATORS = ops
    return ops


# ── Alg 0b: Runtime Concept Phases Loader ───────────────────────────

def _scalar_to_36d_phase(scalar: float) -> np.ndarray:
    """Rozszerz skalarną fazę geometryczną do 36D wektora fazowego.

    Używa równomiernego rozkładu z przesunięciem bazowym.
    Concept identitety rozdzielone o 2π/36 na wszystkich kanałach.
    """
    base = float(scalar) % (2 * np.pi)
    offsets = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    return (base + offsets) % (2 * np.pi)


def load_concept_phases(
    jsonl_path: Path | str | None = None,
    noema_root: Path | str | None = None,
    force_reload: bool = False,
) -> dict[str, np.ndarray]:
    """Załaduj concept → 36D phi z runtime JSONL (Alg 0b).

    Każda linia: {concept_card_id, phase, geometric_phase_rad}
    Skalarna faza → 36D przez _scalar_to_36d_phase().
    Klucz: concept_id po usunięciu prefixu 'concept:'.
    """
    global CONCEPT_PHASES
    if CONCEPT_PHASES and not force_reload:
        return CONCEPT_PHASES

    if jsonl_path is None:
        if noema_root is not None:
            jsonl_path = Path(noema_root) / "runtime" / "phasenav" / "latest" / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl"
        else:
            jsonl_path = _CONCEPT_JSONL

    path = Path(jsonl_path)
    if not path.exists():
        CONCEPT_PHASES = {}
        return {}

    concepts: dict[str, np.ndarray] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            cid = rec.get("concept_card_id", "")
            phase_val = rec.get("geometric_phase_rad", rec.get("phase", None))
            if not cid or phase_val is None:
                continue
            # Usuń prefix 'concept:' dla prostszych kluczy
            key = cid.removeprefix("concept:")
            concepts[key] = _scalar_to_36d_phase(float(phase_val))
            # Zachowaj też oryginalny klucz z prefixem
            if cid != key:
                concepts[cid] = concepts[key]
    except Exception:
        pass

    CONCEPT_PHASES = concepts
    return concepts


def get_runtime_operator_phi(op_name: str) -> np.ndarray:
    """Zwróć phi dla operatora — z runtime JSONL lub fallback do hardcoded."""
    ops = RUNTIME_OPERATORS or load_runtime_operators()
    name_up = op_name.upper()
    if name_up in ops:
        return ops[name_up]
    # Fallback do hardcoded jeśli operator znany
    if name_up in _OPERATOR_ID_SET:
        return operator_signature(name_up)
    # Nowy operator z runtime — użyj UNCERTAINTY jako placeholder
    return operator_signature("UNCERTAINTY")
