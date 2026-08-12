"""Strict 36D PhaseNav operator algebra and runtime loaders."""
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

RUNTIME_OPERATORS: dict[str, np.ndarray] = {}
CONCEPT_PHASES: dict[str, np.ndarray] = {}

_NOEMA_ROOT = Path(__file__).resolve().parents[3]
_RUNTIME_JSONL = (
    _NOEMA_ROOT
    / "runtime"
    / "phasenav"
    / "latest"
    / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
)
_CONCEPT_JSONL = (
    _NOEMA_ROOT
    / "runtime"
    / "phasenav"
    / "latest"
    / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl"
)


class OperatorRuntimeIntegrityError(RuntimeError):
    """Malformed runtime operator/concept data."""


def _require_operator(op_id: str) -> str:
    key = str(op_id).upper()
    if key not in _OPERATOR_ID_SET:
        raise KeyError(f"unknown PhaseNav operator: {op_id}")
    return key


def _finite_36(value, *, label: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != (VECTOR_DIM,):
        raise OperatorRuntimeIntegrityError(
            f"{label}: expected {(VECTOR_DIM,)}, got {arr.shape}"
        )
    if not np.all(np.isfinite(arr)):
        raise OperatorRuntimeIntegrityError(f"{label}: non-finite coordinate")
    return arr


@lru_cache(maxsize=None)
def operator_vector_36d(op_id: str) -> list[float]:
    return [float(x) for x in _phase36_from_id(_require_operator(op_id))]


def operator_vector_24d(op_id: str) -> list[float]:
    """Legacy API name; the returned canonical vector is 36D."""
    return operator_vector_36d(op_id)


def operator_signature(op_name: str) -> np.ndarray:
    return np.asarray(operator_vector_36d(_require_operator(op_name)), dtype=np.float64)


def concept_to_operator(concept_id: str) -> tuple[str, list[float]]:
    if concept_id == "__no_registered_anchor__":
        return "UNCERTAINTY", operator_vector_36d("UNCERTAINTY")
    if not ALL_OPERATOR_IDS:
        raise RuntimeError("PhaseNav operator registry is empty")
    idx = M_collatz_hash(str(concept_id)) % len(ALL_OPERATOR_IDS)
    op_id = ALL_OPERATOR_IDS[idx]
    return op_id, operator_vector_36d(op_id)


def generate_operator_map() -> dict[str, list[float]]:
    result = {op_id: operator_vector_36d(op_id) for op_id in ALL_OPERATOR_IDS}
    if not result:
        raise RuntimeError("PhaseNav operator registry resolved to zero operators")
    return result


def generate_operator_jsonl(path: str | None = None) -> str:
    records = []
    for op_id in ALL_OPERATOR_IDS:
        vector = operator_vector_36d(op_id)
        records.append(
            {
                "schema": "PHASENAV_OPERATOR_VECTOR_V2",
                "canonical_name": "PhaseNav",
                "card_id": op_id,
                "operator_id": op_id,
                "operator_name": op_id,
                "vector_dim": OPERATOR_DIM,
                "vector_semantics": "phase_angles_radians",
                "vector_36d": [round(float(x), 10) for x in vector],
                "orbit_vector": [round(float(x), 10) for x in vector],
                "semantic_mass": round(float(vector[0]), 10),
            }
        )
    if not records:
        raise RuntimeError("refusing empty operator JSONL")
    content = "\n".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True)
        for record in records
    ) + "\n"
    if path:
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
        return 0.5 * (
            _math.sin(float(v3) - float(v1))
            + _math.sin(float(v4) - float(v2))
        )
    raise TypeError(
        "connection expects either (vector_a, vector_b) or "
        "(scalar1, scalar2, scalar3, scalar4)"
    )


def connection_matrix(
    ops: dict[str, list[float]] | None = None,
) -> list[list[float]]:
    ops = generate_operator_map() if ops is None else ops
    vectors = np.asarray(list(ops.values()), dtype=np.float64)
    if vectors.size == 0:
        raise OperatorRuntimeIntegrityError("cannot build matrix from zero operators")
    if vectors.ndim != 2 or vectors.shape[1] != VECTOR_DIM:
        raise OperatorRuntimeIntegrityError(
            f"operator matrix requires N×36 vectors, got {vectors.shape}"
        )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0.0):
        raise OperatorRuntimeIntegrityError("zero-norm operator vector")
    normalized = vectors / norms
    return (normalized @ normalized.T).tolist()


def surface_holonomy(phi: np.ndarray) -> tuple[float, int]:
    values = np.asarray(phi, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("surface_holonomy expects a non-empty 1D phase array")
    dphi = np.diff(values, append=values[0])
    wrapped = ((dphi + np.pi) % (2 * np.pi)) - np.pi
    gamma = float(np.sum(wrapped))
    winding = int(round(gamma / (2 * np.pi)))
    gamma_mod = float(gamma % (2 * np.pi))
    if gamma_mod > 2 * np.pi - 1e-9:
        gamma_mod = 0.0
    return gamma_mod, winding


def statistical_closure(v36: list[float]) -> float:
    arr = _finite_36(v36, label="statistical_closure")
    r = M_36d_order_parameter(arr)
    var = float(np.mean((np.mod(arr, TAU) - _math.pi) ** 2))
    return min(1.0, r + 0.5 * max(0.0, 1.0 - var / (TAU * TAU / 12.0)))


SITUATION_TEMPLATES: dict[str, list[float]] = {
    op_id: operator_vector_36d(op_id) for op_id in ALL_OPERATOR_IDS
}


def detect_situation(phi: list[float] | np.ndarray) -> dict[str, object]:
    state_vec = _finite_36(phi, label="situation")
    state_norm = float(np.linalg.norm(state_vec))
    if state_norm == 0.0:
        raise ValueError("cannot classify zero-norm PhaseNav state")
    template_ids = list(SITUATION_TEMPLATES)
    template_vectors = np.asarray(
        [SITUATION_TEMPLATES[op_id] for op_id in template_ids],
        dtype=np.float64,
    )
    template_norms = np.linalg.norm(template_vectors, axis=1)
    sims = (template_vectors @ state_vec) / (template_norms * state_norm)
    best_idx = int(np.argmax(sims))
    return {
        "operator_id": template_ids[best_idx],
        "score": float(sims[best_idx]),
        "coherence": float(M_36d_order_parameter(state_vec)),
        "semantic_mass": float(state_vec[0]),
    }


def _runtime_operator_fallback() -> dict[str, np.ndarray]:
    return {op_id: operator_signature(op_id) for op_id in ALL_OPERATOR_IDS}


def load_runtime_operators(
    jsonl_path: Path | str | None = None,
    noema_root: Path | str | None = None,
    force_reload: bool = False,
) -> dict[str, np.ndarray]:
    """Load strict finite 36D runtime operators.

    Missing files use the canonical built-in operator registry. Existing malformed
    files fail closed; they are never silently replaced.
    """
    global RUNTIME_OPERATORS
    if RUNTIME_OPERATORS and not force_reload:
        return RUNTIME_OPERATORS

    if jsonl_path is None:
        jsonl_path = (
            Path(noema_root)
            / "runtime"
            / "phasenav"
            / "latest"
            / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
            if noema_root is not None
            else _RUNTIME_JSONL
        )

    path = Path(jsonl_path)
    if not path.exists():
        RUNTIME_OPERATORS = _runtime_operator_fallback()
        return RUNTIME_OPERATORS

    ops: dict[str, np.ndarray] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise OperatorRuntimeIntegrityError(
                f"invalid operator JSONL {path}:{line_number}: {exc}"
            ) from exc

        op_name = str(
            rec.get("operator_name")
            or rec.get("operator_id")
            or rec.get("card_id")
            or ""
        ).removeprefix("op:").upper()
        raw = (
            rec.get("vector_36d")
            or rec.get("phase_vector_36d")
            or rec.get("orbit_vector")
        )
        if not op_name:
            raise OperatorRuntimeIntegrityError(
                f"{path}:{line_number}: missing operator name"
            )
        if raw is None:
            raise OperatorRuntimeIntegrityError(
                f"{path}:{line_number}: missing 36D operator vector"
            )
        ops[op_name] = np.mod(
            _finite_36(raw, label=f"{path}:{line_number}"), TAU
        )

    if not ops:
        raise OperatorRuntimeIntegrityError(f"{path}: zero operator records")
    RUNTIME_OPERATORS = ops
    return ops


def _scalar_to_36d_phase(scalar: float) -> np.ndarray:
    base = float(scalar) % (2 * np.pi)
    offsets = np.linspace(0, 2 * np.pi, VECTOR_DIM, endpoint=False)
    return (base + offsets) % (2 * np.pi)


def _canonical_concept_fallback() -> dict[str, np.ndarray]:
    concepts: dict[str, np.ndarray] = {}
    for sid, state in get_all_states().items():
        arr = _finite_36(state["vector_36d"], label=f"canonical concept {sid}")
        concepts[sid] = arr
        concepts[f"concept:{sid}"] = arr
    if not concepts:
        raise OperatorRuntimeIntegrityError(
            "canonical concept fallback resolved to zero states"
        )
    return concepts


def load_concept_phases(
    jsonl_path: Path | str | None = None,
    noema_root: Path | str | None = None,
    force_reload: bool = False,
) -> dict[str, np.ndarray]:
    """Load concept phases as finite 36D vectors.

    Missing files use canonical states. Existing malformed/empty files fail closed.
    Scalar legacy records are expanded deterministically and remain identifiable by
    their source file rather than being treated as native vector records.
    """
    global CONCEPT_PHASES
    if CONCEPT_PHASES and not force_reload:
        return CONCEPT_PHASES

    if jsonl_path is None:
        jsonl_path = (
            Path(noema_root)
            / "runtime"
            / "phasenav"
            / "latest"
            / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl"
            if noema_root is not None
            else _CONCEPT_JSONL
        )

    path = Path(jsonl_path)
    if not path.exists():
        CONCEPT_PHASES = _canonical_concept_fallback()
        return CONCEPT_PHASES

    concepts: dict[str, np.ndarray] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise OperatorRuntimeIntegrityError(
                f"invalid concept JSONL {path}:{line_number}: {exc}"
            ) from exc
        cid = str(rec.get("concept_card_id") or rec.get("state_id") or "")
        if not cid:
            raise OperatorRuntimeIntegrityError(
                f"{path}:{line_number}: missing concept id"
            )
        raw = rec.get("phase_vector_36d") or rec.get("vector_36d")
        if raw is not None:
            arr = _finite_36(raw, label=f"{path}:{line_number}")
        else:
            phase_val = rec.get("geometric_phase_rad", rec.get("phase"))
            if phase_val is None:
                raise OperatorRuntimeIntegrityError(
                    f"{path}:{line_number}: missing phase/vector"
                )
            arr = _scalar_to_36d_phase(float(phase_val))
        key = cid.removeprefix("concept:")
        concepts[key] = arr
        concepts[cid] = arr

    if not concepts:
        raise OperatorRuntimeIntegrityError(f"{path}: zero concept records")
    CONCEPT_PHASES = concepts
    return concepts


def get_runtime_operator_phi(op_name: str) -> np.ndarray:
    """Return a strict operator vector; unknown names are errors, not placeholders."""
    name = str(op_name).upper()
    ops = RUNTIME_OPERATORS or load_runtime_operators()
    if name in ops:
        return _finite_36(ops[name], label=f"runtime operator {name}")
    if name in _OPERATOR_ID_SET:
        return operator_signature(name)
    raise KeyError(f"unknown runtime PhaseNav operator: {op_name}")


__all__ = [
    "ALL_OPERATOR_IDS",
    "OPERATOR_DIM",
    "OPERATOR_REGISTRY",
    "OperatorRuntimeIntegrityError",
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
    "load_runtime_operators",
    "load_concept_phases",
    "get_runtime_operator_phi",
    "RUNTIME_OPERATORS",
    "CONCEPT_PHASES",
]
