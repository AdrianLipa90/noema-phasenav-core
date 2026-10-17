"""PhaseNav 36D runtime core.

Importing this module is side-effect free: it never materializes runtime files.
Persistent/runtime JSONL surfaces are written only by explicit calls and are
delegated to the validated artifact registry.
"""
from __future__ import annotations

import decimal as _dec
import json as _json
import math as _math
import os as _os
import re as _re

VECTOR_DIM = 36
VECTOR_COMPONENTS = [f"phi_{i}" for i in range(VECTOR_DIM)]

PI = 3.14159265358979323846
TAU = 6.28318530717958647692
KAPPA = _math.log(2) / (24.0 * PI)
L3, L4, L5 = 7, 2, 5
ALPHA_M = 1.0 / ((L3 * L4) ** 2 - L3 ** 2 - L4 * L5 + L4 ** 2 * KAPPA)
L_RATIO = L4 / L3

_N_INTENTION = (1.0 + ALPHA_M * ALPHA_M + L_RATIO * L_RATIO) ** 0.5
INTENTION_AXIS = (1.0 / _N_INTENTION, ALPHA_M / _N_INTENTION, L_RATIO / _N_INTENTION)
_Q_PRIMES = (3, 5, 7, 11, 13, 17)

_SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
_GLOSSARY_PATH = _os.path.join(_SCRIPT_DIR, "glossary.pnv")
_GLOSSARY_JSON_FALLBACK = _os.path.join(_SCRIPT_DIR, "glossarius", "ciel_omega_glossary.json")
_CACHE = {}
_FN_REGISTRY = {}


def _quark_prime(k):
    return _Q_PRIMES[(k - 1) % len(_Q_PRIMES)]


def _sqrt(x):
    return x ** 0.5


def _sin(x):
    return _math.sin(float(x))


def _cos(x):
    return _math.cos(float(x))


def _atan2(y, x):
    return _math.atan2(float(y), float(x))


def _arcsin(x):
    return _math.asin(max(-1.0, min(1.0, float(x))))


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def M_collatz_hash(s):
    """Deterministic Collatz-derived index hash; not a cryptographic hash."""
    h = int.from_bytes(str(s).encode("utf-8"), "big") % (2**61 - 1)
    for _ in range(13):
        h = h // 2 if h % 2 == 0 else 3 * h + 1
        h %= 2**61 - 1
    return h


def _phase_precise(h_int, i):
    _dec.getcontext().prec = 38
    ln2_over_12 = _dec.Decimal("0.05776226504666210911810267678818141")
    tau_d = _dec.Decimal("6.2831853071795864769252867665590057")
    return float((_dec.Decimal(int(h_int) * (i + 1)) * ln2_over_12) % tau_d)


PHASE_ADDRESS_CONTRACT = "PNCS_TERNARY36_IDENTITY_V0_2_CANDIDATE"
TERNARY_CONTROL_GROUPS = 12
TERNARY_CONTROL_CAPACITY = 3 ** TERNARY_CONTROL_GROUPS


def _ternary_phase_offset(k, i):
    """Reversible 12-trit address, repeated over 36 phase lanes and C^2048.

    Each of 12 trits modulates three adjacent phase lanes by 2π/3.
    This is a candidate phase ADDRESS, not semantic identity or authority.
    """
    if type(k) is not int or not 1 <= k <= TERNARY_CONTROL_CAPACITY:
        raise ValueError("phase address outside 12-trit canonical capacity")
    if type(i) is not int or i < 0:
        raise ValueError("phase lane index must be nonnegative")
    digit = ((k - 1) // (3 ** ((i // 3) % TERNARY_CONTROL_GROUPS))) % 3
    return digit * TAU / 3.0


def _phase36_from_id_legacy_v1(eid):
    try:
        k = max(1, int(str(eid).lstrip("Ff")))
    except (ValueError, TypeError):
        h = M_collatz_hash(str(eid).lower())
        return [round(_phase_precise(h, i), 10) for i in range(VECTOR_DIM)]
    qk = _quark_prime(k)
    out = []
    for i in range(VECTOR_DIM):
        phi = (
            KAPPA * TAU
            + ALPHA_M * TAU * (i % L3)
            + L_RATIO * TAU * (i // L3)
            + (qk % L5) * TAU / L3
        ) % TAU
        out.append(round(phi, 10))
    return out


def _phase36_from_id(eid):
    """Collision-free candidate numeric PhaseNav address for 1..3**12.

    Historical mapping is preserved as _phase36_from_id_legacy_v1.
    Non-numeric IDs retain the historical hash-based projection and
    require independent semantic identity, as before.
    """
    try:
        k = int(str(eid).lstrip("Ff"))
    except (ValueError, TypeError):
        return _phase36_from_id_legacy_v1(eid)
    if not 1 <= k <= TERNARY_CONTROL_CAPACITY:
        raise ValueError("numeric phase ID outside supported 12-trit range")
    qk = _quark_prime(k)
    out = []
    for i in range(VECTOR_DIM):
        phi = (
            KAPPA * TAU
            + ALPHA_M * TAU * (i % L3)
            + L_RATIO * TAU * (i // L3)
            + (qk % L5) * TAU / L3
            + _ternary_phase_offset(k, i)
        ) % TAU
        out.append(round(phi, 10))
    return out



def _gauge_lock_36(vec):
    return [float(v) % TAU for v in vec]


def _gauge_lock_2(theta, phi):
    theta = abs(float(theta)) % TAU
    if theta > PI:
        theta = TAU - theta
    return theta, float(phi) % TAU


def _require_vector36(vec, label="vector"):
    out = [float(x) for x in vec]
    if len(out) != VECTOR_DIM:
        raise ValueError(f"{label}: expected 36 values, got {len(out)}")
    if not all(_math.isfinite(x) for x in out):
        raise ValueError(f"{label}: non-finite coordinate")
    return out


def M_36d_mean_phase(vec):
    v = _require_vector36(vec)
    return _atan2(sum(_sin(x) for x in v), sum(_cos(x) for x in v))


def M_36d_order_parameter(vec):
    v = [float(x) for x in vec]
    if not v:
        return 0.0
    s = sum(_sin(x) for x in v)
    c = sum(_cos(x) for x in v)
    return _sqrt(s * s + c * c) / len(v)


def _wrapped_delta(a, b):
    d = (float(a) - float(b)) % TAU
    return TAU - d if d > PI else d


def M_36d_distance(v1, v2):
    a, b = _require_vector36(v1, "v1"), _require_vector36(v2, "v2")
    return _sqrt(sum(_wrapped_delta(x, y) ** 2 for x, y in zip(a, b)))


def M_36d_angular_distance(v1, v2):
    return M_36d_distance(v1, v2) / _sqrt(VECTOR_DIM)


def M_36d_berry_connection(v1, v2):
    a, b = _require_vector36(v1, "v1"), _require_vector36(v2, "v2")
    return sum(_sin(y - x) for x, y in zip(a, b)) / VECTOR_DIM


def M_36d_inner_product(v1, v2):
    a, b = _require_vector36(v1, "v1"), _require_vector36(v2, "v2")
    return (
        sum(_cos(y - x) for x, y in zip(a, b)) / VECTOR_DIM,
        sum(_sin(y - x) for x, y in zip(a, b)) / VECTOR_DIM,
    )


def M_36d_edge_weight(v1, v2):
    d = M_36d_angular_distance(v1, v2)
    return d * (1.0 + abs(M_36d_berry_connection(v1, v2))) + 1e-12


def bloch_ket(theta, phi):
    return (
        _cos(theta / 2.0),
        _sin(theta / 2.0) * _cos(phi),
        0.0,
        _sin(theta / 2.0) * _sin(phi),
    )


def M_inner_product(theta1, phi1, theta2, phi2):
    return (
        _cos(theta1 / 2) * _cos(theta2 / 2)
        + _sin(theta1 / 2) * _sin(theta2 / 2) * _cos(phi2 - phi1),
        _sin(theta1 / 2) * _sin(theta2 / 2) * _sin(phi2 - phi1),
    )


def M_berry_connection(theta1, phi1, theta2, phi2):
    return _sin(theta1 / 2) * _sin(theta2 / 2) * _sin(phi2 - phi1)


def M_angular_distance(theta1, phi1, theta2, phi2):
    re, im = M_inner_product(theta1, phi1, theta2, phi2)
    r = _clamp(_sqrt(re * re + im * im), 0.0, 1.0)
    return 2.0 * _atan2(_sqrt(max(0.0, 1.0 - r * r)), r)


def M_edge_weight(theta1, phi1, theta2, phi2):
    return M_angular_distance(theta1, phi1, theta2, phi2) * (
        1.0 + abs(M_berry_connection(theta1, phi1, theta2, phi2))
    ) + 1e-12


def M_project_bloch(v36):
    v = _require_vector36(v36)
    r = _clamp(M_36d_order_parameter(v), 0.0, 1.0)
    theta = 2.0 * _atan2(_sqrt(max(0.0, 1.0 - r * r)), r)
    return _gauge_lock_2(theta, M_36d_mean_phase(v))


def _semantic_mass(eid, v36):
    try:
        k = max(1, int(eid))
    except (ValueError, TypeError):
        k = 1
    return round(KAPPA * (1.0 + ALPHA_M * k) + L_RATIO * M_36d_order_parameter(v36), 10)


def _parse_pnv_glossary(path):
    if not _os.path.exists(path):
        return None
    result = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or ":" not in line or line.startswith("Μ("):
                continue
            eid, rest = line.split(":", 1)
            if not rest.strip().startswith("name="):
                continue
            fields = {}
            for part in rest.split(","):
                if "=" in part:
                    key, value = part.split("=", 1)
                    fields[key.strip()] = value.strip()
            result[eid.strip()] = fields
    return result


def _seed_fallback():
    """Load the compact seed ledger lazily; no file writes and no invented rows."""
    try:
        from .canon.seed_data import SEED_ROWS
    except (ImportError, AttributeError):
        return {}
    result = {}
    for raw in SEED_ROWS.splitlines():
        if not raw.strip():
            continue
        gid, name, operator, card_type, _status = raw.split("|", 4)
        vector = _phase36_from_id(gid)
        result[gid] = {
            "name": name,
            "operator": operator,
            "type": card_type,
            "v36": vector,
            "v2": list(M_project_bloch(vector)),
            "semantic_mass": _semantic_mass(gid, vector),
        }
    return result


def _load_glossary():
    def _load():
        pnv = _parse_pnv_glossary(_GLOSSARY_PATH)
        if pnv is None and _os.path.exists(_GLOSSARY_JSON_FALLBACK):
            with open(_GLOSSARY_JSON_FALLBACK, encoding="utf-8") as fh:
                pnv = _json.load(fh)
        if pnv is None:
            return _seed_fallback()
        result = {}
        for eid, raw in pnv.items():
            entry = dict(raw)
            vector = entry.get("v36")
            if not isinstance(vector, (list, tuple)) or len(vector) != VECTOR_DIM:
                vector = _phase36_from_id(eid)
            vector = _require_vector36(vector, f"glossary {eid}")
            entry["v36"] = vector
            if not isinstance(entry.get("v2"), (list, tuple)) or len(entry["v2"]) != 2:
                entry["v2"] = list(M_project_bloch(vector))
            entry.setdefault("semantic_mass", _semantic_mass(eid, vector))
            result[str(eid)] = entry
        return result
    if "glossary" not in _CACHE:
        _CACHE["glossary"] = _load()
    return _CACHE["glossary"]


def state_vector_36d(eid):
    gl = _load_glossary()
    key = str(eid)
    return list(gl[key]["v36"]) if key in gl else _phase36_from_id(key)


def state_vector_bloch(eid):
    gl = _load_glossary()
    key = str(eid)
    if key in gl:
        return tuple(gl[key]["v2"])
    return M_project_bloch(state_vector_36d(key))


def state_vector(eid, dim="36d"):
    return state_vector_bloch(eid) if dim in {"bloch", "su2"} else state_vector_36d(eid)


def M_nearest_neighbors_36d(target_v36, candidates, k=3):
    scored = [(M_36d_edge_weight(target_v36, v), cid, v) for cid, v in candidates]
    return sorted(scored, key=lambda item: item[0])[:k]


def M_all_states_except_36d(exclude_ids):
    excluded = set(exclude_ids)
    return [
        (eid, entry["v36"])
        for eid, entry in _load_glossary().items()
        if eid not in excluded
    ]


def M_find_path_36d(start_id, end_id, max_steps=5):
    end_vec = state_vector_36d(end_id)
    path = [str(start_id)]
    for _ in range(max_steps):
        nearest = M_nearest_neighbors_36d(end_vec, M_all_states_except_36d(path), k=1)
        if not nearest:
            break
        nid = nearest[0][1]
        path.append(nid)
        if M_36d_angular_distance(state_vector_36d(nid), end_vec) < 0.1:
            break
    if path[-1] != str(end_id):
        path.append(str(end_id))
    return path


def M_resolve_situation_36d(state_v36, templates):
    rankings = {}
    for name, target in templates.items():
        re, im = M_36d_inner_product(state_v36, target)
        rankings[name] = round(re * re + im * im, 6)
    rankings = dict(sorted(rankings.items(), key=lambda item: -item[1]))
    best = next(iter(rankings.items()), (None, 0.0))
    return {"situation": best[0], "confidence": best[1], "rankings": rankings}


def M_berry_holonomy_36d(path_vectors):
    vectors = [_require_vector36(v) for v in path_vectors]
    if len(vectors) < 2:
        return 0.0
    gamma = sum(
        M_36d_berry_connection(vectors[i], vectors[(i + 1) % len(vectors)])
        for i in range(len(vectors))
    )
    return _atan2(_sin(gamma), _cos(gamma))


def intention_apply_36d(vec, strength=1.0):
    v = _require_vector36(vec)
    nx, ny, _nz = INTENTION_AXIS
    mean_phase, r = M_36d_mean_phase(v), M_36d_order_parameter(v)
    return [
        (x + strength * KAPPA * (nx * _sin(x) * r + ny * _cos(x) * _sin(mean_phase))) % TAU
        for x in v
    ]


def M_solve_36d(start_id, end_id, options=None):
    options = options or {}
    path = M_find_path_36d(start_id, end_id, options.get("max_steps", 5))
    vectors = [state_vector_36d(sid) for sid in path]
    steps, total_holonomy, total_path = [], 0.0, 0.0
    for i, (sid, vector) in enumerate(zip(path, vectors)):
        theta, phi = M_project_bloch(vector)
        step = {
            "id": sid,
            "v36": vector,
            "bloch": [round(theta, 10), round(phi, 10)],
            "R": round(M_36d_order_parameter(vector), 10),
            "mean_phase": round(M_36d_mean_phase(vector), 10),
        }
        if i:
            bc = M_36d_berry_connection(vectors[i - 1], vector)
            dist = M_36d_angular_distance(vectors[i - 1], vector)
            total_holonomy += bc
            total_path += dist
            step.update(berry_connection=round(bc, 10), distance=round(dist, 10))
        steps.append(step)
    total_holonomy = _atan2(_sin(total_holonomy), _cos(total_holonomy))
    return {
        "path": path,
        "total_holonomy": round(total_holonomy, 10),
        "total_path_length": round(total_path, 10),
        "steps": steps,
        "path_integral": round(total_holonomy * total_path, 10),
    }


def parse_pnv_file(path):
    if not _os.path.exists(path):
        return {"sections": [], "operators": {}, "situations": {}, "functions": {}}
    text = open(path, encoding="utf-8").read()
    result = {"sections": [], "operators": {}, "situations": {}, "functions": {}}
    for raw in text.splitlines():
        line = raw.strip()
        section = _re.match(r"───\s+(.+?)\s+───", line)
        if section:
            result["sections"].append(section.group(1).strip())
            continue
        if not line or line.startswith("#"):
            continue
        for prefix, key in (("op", "operators"), ("sit", "situations")):
            match = _re.match(rf"{prefix}\s+(\w+)\s*:\s*(.+)", line)
            if match:
                result[key][match.group(1)] = match.group(2).strip()
                break
        else:
            match = _re.match(r"Μ\((\w+),\s*(.+)\)\s*→\s*(\w+)", line)
            if match:
                result["functions"][match.group(1)] = {
                    "args": [x.strip() for x in match.group(2).split(",")],
                    "return_type": match.group(3),
                }
    return result


def load_pnv_files():
    if not _os.path.isdir(_SCRIPT_DIR):
        return {}
    return {
        name: parse_pnv_file(_os.path.join(_SCRIPT_DIR, name))
        for name in sorted(_os.listdir(_SCRIPT_DIR))
        if name.endswith(".pnv")
    }


def _write_state_jsonl(base_path="/dev/shm/ciel_noema/phasenav"):
    """Explicit, validated runtime materialization. Never called during import."""
    from .artifact_registry import write_runtime_artifacts
    return write_runtime_artifacts(base_path)


def _write_lines(path, lines):
    """Legacy helper retained for callers; refuses empty writes."""
    rows = [str(line) for line in lines if str(line).strip()]
    if not rows:
        raise ValueError(f"refusing empty PhaseNav write: {path}")
    directory = _os.path.dirname(path)
    if directory:
        _os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")


def _init():
    """Initialize in-memory parser cache only. No filesystem mutation."""
    _CACHE["pnv_files"] = load_pnv_files()


ALL_STATE_IDS = []
ALL_OPERATOR_IDS = []
_init()


def get_all_states():
    result = {}
    for sid, entry in _load_glossary().items():
        vector = _require_vector36(entry["v36"], f"state {sid}")
        result[sid] = {
            "state_id": sid,
            "name": entry.get("name", sid),
            "vector_36d": [round(x, 10) for x in vector],
            "vector_bloch": [round(float(x), 10) for x in entry["v2"]],
            "R": round(M_36d_order_parameter(vector), 10),
            "mean_phase": round(M_36d_mean_phase(vector), 10),
            "semantic_mass": entry.get("semantic_mass", _semantic_mass(sid, vector)),
            "operator": entry.get("operator", ""),
        }
    return result


def generate_state_map():
    return {eid: list(entry["v2"]) for eid, entry in _load_glossary().items()}


def generate_state_jsonl(path=None):
    rows = []
    for sid, entry in _load_glossary().items():
        vector = _require_vector36(entry["v36"], f"state {sid}")
        rows.append(_json.dumps({
            "state_id": sid,
            "name": entry.get("name", sid),
            "vector_36d": [round(x, 10) for x in vector],
            "vector_bloch": [round(float(x), 10) for x in entry["v2"]],
            "R": round(M_36d_order_parameter(vector), 10),
            "semantic_mass": entry.get("semantic_mass", _semantic_mass(sid, vector)),
            "operator": entry.get("operator", ""),
        }))
    if not rows:
        raise RuntimeError("PhaseNav state registry resolved to zero rows")
    content = "\n".join(rows) + "\n"
    if path:
        directory = _os.path.dirname(path)
        if directory:
            _os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    return content


def write_state_vectors(base_path=None):
    base_path = base_path or "/dev/shm/ciel_noema/phasenav"
    path = _os.path.join(base_path, "STATE_VECTORS_36D.noema.jsonl")
    generate_state_jsonl(path)
    return path


def _operator_algebra():
    from . import operator_algebra as algebra
    return algebra


def generate_operator_map():
    return _operator_algebra().generate_operator_map()


def generate_operator_jsonl(path=None):
    return _operator_algebra().generate_operator_jsonl(path)


def write_operator_algebra(base_path=None):
    base_path = base_path or "/dev/shm/ciel_noema/phasenav"
    path = _os.path.join(base_path, "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl")
    generate_operator_jsonl(path)
    return path


def operator_vector_24d(op_id):
    """Legacy name; canonical result is 36D."""
    return _operator_algebra().operator_vector_36d(op_id)


def operator_vector_36d(op_id):
    return _operator_algebra().operator_vector_36d(op_id)


def concept_to_operator(concept_id):
    return _operator_algebra().concept_to_operator(concept_id)


def get_all_operations():
    return _operator_algebra().get_all_operations()


def operator_signature(op_name):
    return operator_vector_36d(op_name)


def connection(t1, p1, t2, p2):
    return M_berry_connection(t1, p1, t2, p2)


def connection_matrix(ops=None):
    ops = ops or generate_state_map()
    ids = list(ops)
    return [[M_berry_connection(*ops[a], *ops[b]) for b in ids] for a in ids]


def holonomy(path, ops=None):
    ops = ops or generate_state_map()
    nodes = list(path)
    if len(nodes) < 2:
        return 0.0
    if nodes[0] != nodes[-1]:
        nodes.append(nodes[0])
    gamma = sum(
        M_berry_connection(*ops[nodes[i]], *ops[nodes[i + 1]])
        for i in range(len(nodes) - 1)
    )
    return _atan2(_sin(gamma), _cos(gamma))


def intention_apply(theta, phi, strength=1.0):
    nx, ny, _nz = INTENTION_AXIS
    theta_eff = theta + strength * KAPPA * nx * _sin(theta)
    phi_eff = phi + strength * KAPPA * ny
    return _gauge_lock_2(theta_eff, phi_eff)


def statistical_closure(v36):
    vector = _require_vector36(v36)
    r = M_36d_order_parameter(vector)
    variance = sum((_wrapped_delta(x, 0.0)) ** 2 for x in vector) / VECTOR_DIM
    return min(1.0, r + 0.5 * max(0.0, 1.0 - variance / (TAU * TAU / 12.0)))


PHASE_GRAMMAR = {
    "NOUN": "IDENTITY",
    "VERB": "DIFFERENTIAL",
    "EMOTION": "AFFECT",
    "CYCLE": "ORBIT",
}
_PHASE_GRAMMAR_INV = {value: key for key, value in PHASE_GRAMMAR.items()}
GRAMMAR_RULES = {
    ("NOUN", "VERB"): ("VERB", 0.7),
    ("VERB", "NOUN"): ("NOUN", 0.4),
    ("EMOTION", "NOUN"): ("EMOTION", 0.6),
    ("NOUN", "EMOTION"): ("EMOTION", 0.4),
    ("CYCLE", "VERB"): ("VERB", 0.5),
    ("EMOTION", "EMOTION"): ("EMOTION", 0.5),
    ("VERB", "VERB"): ("VERB", 0.5),
    ("NOUN", "NOUN"): ("NOUN", 0.3),
    ("CYCLE", "NOUN"): ("CYCLE", 0.4),
    ("CYCLE", "EMOTION"): ("EMOTION", 0.5),
}


def M_operator_gram_type(eid):
    entry = _load_glossary().get(str(eid), {})
    return _PHASE_GRAMMAR_INV.get(entry.get("operator", "IDENTITY"), "NOUN")


def M_superposition_36d(v1, v2, weight=0.3):
    a, b = _require_vector36(v1, "v1"), _require_vector36(v2, "v2")
    w2, w1 = float(weight), 1.0 - float(weight)
    return [
        _atan2(w1 * _sin(x) + w2 * _sin(y), w1 * _cos(x) + w2 * _cos(y)) % TAU
        for x, y in zip(a, b)
    ]


def M_grammar_compose(eid1, eid2):
    t1, t2 = M_operator_gram_type(eid1), M_operator_gram_type(eid2)
    result_type, blend = GRAMMAR_RULES.get((t1, t2), ("NOUN", 0.5))
    return (
        M_superposition_36d(state_vector_36d(eid1), state_vector_36d(eid2), blend),
        result_type,
        blend,
    )


_QF_NEG = {"nie", "bez", "żaden", "nigdy", "nikt", "nic", "not", "no", "never", "nothing", "none"}
_QF_COND = {"jeśli", "jeżeli", "gdyby", "gdy", "kiedy", "if", "unless", "whenever", "provided"}
_QF_IRONY = {"oczywiście", "naturalnie", "jasne", "pewnie", "obviously", "sure", "certainly"}
_QF_TEMP = {"wcześniej", "później", "przed", "po", "potem", "zanim", "before", "after", "later", "already"}
_QF_AMBIG = {"może", "chyba", "prawdopodobnie", "podobno", "maybe", "perhaps", "possibly", "probably"}
_QF_META_WORDS = {"jakby", "niczym", "niby"}
_QF_META_PHRASES = ("jak gdyby", "as if", "as though", "like a", "similar to")


def M_quantum_features(text):
    lowered = str(text).lower()
    words = set(lowered.split())
    return {
        "negation": bool(words & _QF_NEG),
        "conditional": bool(words & _QF_COND),
        "irony": bool(words & _QF_IRONY),
        "temporal": bool(words & _QF_TEMP),
        "metaphor": bool(words & _QF_META_WORDS) or any(p in lowered for p in _QF_META_PHRASES),
        "question": lowered.rstrip().endswith("?"),
        "imperative": lowered.rstrip().endswith("!"),
        "ambiguity": bool(words & _QF_AMBIG),
    }


def _sentence_phase(text, precise):
    words = str(text).lower().split()
    if not words:
        return _phase36_from_id("1")
    sums_s, sums_c = [0.0] * VECTOR_DIM, [0.0] * VECTOR_DIM
    for word in words:
        h = M_collatz_hash(word)
        for i in range(VECTOR_DIM):
            phi = _phase_precise(h, i) if precise else (h * KAPPA * TAU * (i + 1)) % TAU
            sums_s[i] += _sin(phi)
            sums_c[i] += _cos(phi)
    return [_atan2(s, c) % TAU for s, c in zip(sums_s, sums_c)]


def M_sentence_phase(text):
    return _sentence_phase(text, precise=False)


def M_sentence_phase_precise(text):
    return _sentence_phase(text, precise=True)


def M_sentence_phase_trajectory(text):
    words = str(text).lower().split()
    if not words:
        vector = _phase36_from_id("1")
        return vector, [vector], 0.0
    trajectory = [M_sentence_phase(" ".join(words[:i])) for i in range(1, len(words) + 1)]
    holonomy = sum(
        M_36d_berry_connection(trajectory[i], trajectory[i + 1])
        for i in range(len(trajectory) - 1)
    )
    return trajectory[-1], trajectory, holonomy


def M_fine_tune_36d(v36, features=None, text=None):
    vector = _require_vector36(v36)
    if features is None:
        if text is None:
            return vector, []
        features = M_quantum_features(text)
    applied = []
    gates = {
        "conditional": ("151", 0.25),
        "temporal": ("152", 0.20),
        "metaphor": ("154", 0.20),
        "ambiguity": ("155", 0.15),
    }
    if features.get("negation"):
        gate = _phase36_from_id("150")
        delta = M_36d_berry_connection(vector, gate) * ALPHA_M
        vector = [(x - delta) % TAU for x in vector]
        applied.append("negation")
    for feature, (gate_id, weight) in gates.items():
        if features.get(feature):
            vector = M_superposition_36d(vector, _phase36_from_id(gate_id), weight)
            applied.append(feature)
    if features.get("irony"):
        gate = _phase36_from_id("153")
        delta = M_36d_berry_connection(vector, gate) * ALPHA_M
        vector = [(x + PI + delta) % TAU for x in vector]
        applied.append("irony")
    if features.get("question"):
        vector = [(x + KAPPA * PI / 2.0) % TAU for x in vector]
        applied.append("question")
    if features.get("imperative"):
        gate = _phase36_from_id("158")
        delta = M_36d_berry_connection(vector, gate) * ALPHA_M * 2.0
        vector = [(x + delta) % TAU for x in vector]
        applied.append("imperative")
    return vector, applied
