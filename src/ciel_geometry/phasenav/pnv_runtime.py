"""pnv_runtime — PhaseNav M(metatime) on 36D phase space + SU(2) projection.
36 oscillatory dimensions (HTRI brain regions).
SU(2) Bloch sphere as derived 2D projection.
Zero external deps. No numpy. No matplotlib. No PIL."""

import json as _json
import os as _os
import re as _re

VECTOR_DIM = 36
VECTOR_COMPONENTS = [f"phi_{i}" for i in range(36)]

PI = 3.14159265358979323846
TAU = 6.28318530717958647692

# Metatime TIR constants (not invented)
import math as _math
KAPPA = _math.log(2) / (24.0 * PI)
L3 = 7
L4 = 2
L5 = 5
# Derived fine-structure from Metatime: 1/α = (L₃·L₄)² − L₃² − L₄·L₅ + L₄²·κ
ALPHA_M = 1.0 / ((L3 * L4) ** 2 - L3 ** 2 - L4 * L5 + L4 ** 2 * KAPPA)
# Binary split ratio (replaces golden ratio)
L_RATIO = L4 / L3

_N_INTENTION = (1.0 + ALPHA_M * ALPHA_M + L_RATIO * L_RATIO) ** 0.5
INTENTION_AXIS = (1.0 / _N_INTENTION, ALPHA_M / _N_INTENTION, L_RATIO / _N_INTENTION)

# Quark primes (Postulate B)
_Q_PRIMES = (3, 5, 7, 11, 13, 17)

def _quark_prime(k):
    return _Q_PRIMES[(k - 1) % len(_Q_PRIMES)]

_SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
_GLOSSARY_PATH = _os.path.join(_SCRIPT_DIR, "glossary.pnv")
_GLOSSARY_JSON_FALLBACK = _os.path.join(_SCRIPT_DIR, "glossarius", "ciel_omega_glossary.json")
_CACHE = {}
_FN_REGISTRY = {}

# ─── Own trig (zero deps) ───

def _sqrt(x):
    return x ** 0.5

def _sin(x):
    x = float(x) % TAU
    s = 0.0
    t = x
    for n in range(1, 30, 2):
        s += t
        t *= -x * x / ((n + 1) * (n + 2))
    return s

def _cos(x):
    x = float(x) % TAU
    s = 0.0
    t = 1.0
    for n in range(0, 30, 2):
        s += t
        t *= -x * x / ((n + 1) * (n + 2))
    return s

def _atan_series(a):
    """arctan(a) Taylor series, 30 terms, |a| <= 1."""
    a2 = a * a
    p = a
    s = p
    for k in range(1, 30):
        p *= -a2
        s += p / (2 * k + 1)
    return s

def _atan2(y, x):
    if x == 0.0:
        if y > 0:
            return PI / 2
        if y < 0:
            return -PI / 2
        return 0.0
    a = y / x
    if -1.0 <= a <= 1.0:
        at = _atan_series(a)
    elif a > 0:
        at = PI / 2 - _atan_series(x / y)
    else:
        at = -PI / 2 - _atan_series(x / y)
    if x > 0:
        return at
    return at + PI if y >= 0 else at - PI

def _arcsin(x):
    if x >= 1.0:
        return PI / 2
    if x <= -1.0:
        return -PI / 2
    return _atan2(x, _sqrt(1.0 - x * x))

def _clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

# ─── Collatz hash ───

def M_collatz_hash(s):
    """Deterministic hash via Collatz — used for indexing, NOT for vector derivation."""
    h = int.from_bytes(s.encode("utf-8"), "big") % (2**61 - 1)
    for _ in range(13):
        if h % 2 == 0:
            h = h // 2
        else:
            h = 3 * h + 1
        h = h % (2**61 - 1)
    return h

def _phase_precise(h_int, i):
    """(h_int * KAPPA * TAU * (i+1)) % TAU via Decimal to avoid float64 precision loss.

    With h_int up to 2^61 and float64 having 53 bits, direct multiplication loses
    the low bits before modulo reduction — errors up to ~2 rad for long hashes.
    This uses Python's stdlib `decimal` module for ~38 significant digits.

    KAPPA * TAU = ln(2)/(24π) * 2π = ln(2)/12  (exact algebraic simplification).
    """
    import decimal as _dec
    _dec.getcontext().prec = 38
    _LN2_OVER_12 = _dec.Decimal("0.05776226504666210911810267678818141")
    _TAU_D = _dec.Decimal("6.2831853071795864769252867665590057")
    k = h_int * (i + 1)  # exact Python integer — no float conversion until final step
    return float((_dec.Decimal(k) * _LN2_OVER_12) % _TAU_D)


def _phase36_from_id(eid):
    """36D phase vector from Metatime constants + concept ID.
    phi_i(k) = (κ·TAU + α_M·TAU·(i mod L₃) + (L₄/L₃)·TAU·⌊i/L₃⌋ + (q_k mod L₅)·TAU/L₃) mod TAU

    κ = ln(2)/(24π) — information constant (Metatime TIR)
    α_M = derived fine-structure — 1/α ≈ 137.037
    L₃=7, L₄=2, L₅=5 — fundamental integers
    q_k = quark prime mapped from k
    k = concept semantic position (001→1, F101→101)
    i = dimension index (0..35)
    """
    try:
        s = str(eid).lstrip("Ff")
        k = max(1, int(s))
    except (ValueError, TypeError):
        # Non-numeric IDs (operator names, concept strings): use Collatz phasor with
        # high-precision Decimal arithmetic to avoid float64 catastrophic cancellation.
        h = M_collatz_hash(str(eid).lower())
        return [round(_phase_precise(h, i), 10) for i in range(36)]
    qk = _quark_prime(k)
    vec = []
    for i in range(36):
        i_mod = i % L3
        i_div = i // L3
        phi = (KAPPA * TAU + ALPHA_M * TAU * i_mod + L_RATIO * TAU * i_div + (qk % L5) * TAU / L3) % TAU
        vec.append(round(phi, 10))
    return vec

def _semantic_mass(eid, v36):
    """Semantic mass from Metatime: m_k = κ·(1 + α_M·k) + (L₄/L₃)·R_k
    κ = information constant, α_M = derived fine-structure, L₄/L₃ = binary split.
    k = concept numeric ID, R_k = order parameter.
    """
    try:
        k = max(1, int(eid))
    except (ValueError, TypeError):
        k = 1
    R = M_36d_order_parameter(v36)
    return round(KAPPA * (1.0 + ALPHA_M * k) + L_RATIO * R, 10)

# ─── Gauge lock ───

def _gauge_lock_36(vec):
    return [v % TAU for v in vec]

def _gauge_lock_2(theta, phi):
    theta = abs(theta) % (PI + 1e-12)
    if theta > PI:
        theta = TAU - theta
    phi = phi % TAU
    return (theta, phi)

# ─── 36D operations ───

def M_36d_mean_phase(vec):
    s = 0.0
    for v in vec:
        s += _sin(v)
    c = 0.0
    for v in vec:
        c += _cos(v)
    return _atan2(s, c)

def M_36d_order_parameter(vec):
    s = 0.0
    c = 0.0
    for v in vec:
        s += _sin(v)
        c += _cos(v)
    n = len(vec) if vec else 1
    return _sqrt(s*s + c*c) / n

def M_36d_distance(v1, v2):
    s = 0.0
    for a, b in zip(v1, v2):
        d = (a - b) % TAU
        if d > PI:
            d = TAU - d
        s += d * d
    return _sqrt(s)

def M_36d_berry_connection(v1, v2):
    s = 0.0
    for a, b in zip(v1, v2):
        s += _sin(b - a)
    return s / len(v1)

def M_36d_inner_product(v1, v2):
    re = 0.0
    im = 0.0
    for a, b in zip(v1, v2):
        re += _cos(b - a)
        im += _sin(b - a)
    n = len(v1)
    return (re / n, im / n)

def M_36d_angular_distance(v1, v2):
    s = 0.0
    n = len(v1)
    for a, b in zip(v1, v2):
        d = (a - b) % TAU
        if d > PI:
            d = TAU - d
        s += d * d
    return _sqrt(s / n)

def M_36d_edge_weight(v1, v2):
    d = M_36d_angular_distance(v1, v2)
    bc = abs(M_36d_berry_connection(v1, v2))
    return d * (1.0 + bc) + 1e-12

# ─── SU(2) Bloch sphere operations (derived projection) ───

def bloch_ket(theta, phi):
    c2 = _cos(theta / 2.0)
    s2 = _sin(theta / 2.0)
    return (c2, s2 * _cos(phi), 0.0, s2 * _sin(phi))

def M_inner_product(theta1, phi1, theta2, phi2):
    re = _cos(theta1/2)*_cos(theta2/2) + _sin(theta1/2)*_sin(theta2/2)*_cos(phi2-phi1)
    im = _sin(theta1/2)*_sin(theta2/2)*_sin(phi2-phi1)
    return (re, im)

def M_berry_connection(theta1, phi1, theta2, phi2):
    return _sin(theta1/2) * _sin(theta2/2) * _sin(phi2 - phi1)

def M_angular_distance(theta1, phi1, theta2, phi2):
    re, im = M_inner_product(theta1, phi1, theta2, phi2)
    R = _clamp(_sqrt(re*re + im*im), -1, 1)
    return 2.0 * _atan2(_sqrt(max(0.0, 1.0 - R*R)), R)

def M_edge_weight(theta1, phi1, theta2, phi2):
    d = M_angular_distance(theta1, phi1, theta2, phi2)
    bc = abs(M_berry_connection(theta1, phi1, theta2, phi2))
    return d * (1.0 + bc) + 1e-12

# ─── Projection 36D → SU(2) ───

def M_project_bloch(v36):
    """Project 36D phase vector → Bloch sphere (θ, φ)."""
    R = M_36d_order_parameter(v36)
    phi_bar = M_36d_mean_phase(v36)
    theta = 2.0 * _atan2(_sqrt(max(0.0, 1.0 - R*R)), _clamp(R, 0, 1))
    return _gauge_lock_2(theta, phi_bar)

# ─── PNV parser ───

def _parse_pnv_glossary(path):
    """Parse glossary.pnv → dict of {eid: {name, operator, type, gen}}."""
    if not _os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        text = f.read()
    result = {}
    current_section = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("─── ") and line.endswith(" ───"):
            current_section = line[4:-4].strip()
            continue
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.startswith("Μ("):
            eid = line.split(":")[0].strip()
            rest = line.split(":", 1)[1].strip()
            if not rest.startswith("name="):
                continue
            fields = {}
            for part in rest.split(","):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    fields[k.strip()] = v.strip()
            result[eid] = fields
    return result

# ─── Glossary ───

def _cached(key, factory):
    if key not in _CACHE:
        _CACHE[key] = factory()
    return _CACHE[key]

def _load_glossary():
    def _load():
        pnv = _parse_pnv_glossary(_GLOSSARY_PATH)
        if pnv is None and _os.path.exists(_GLOSSARY_JSON_FALLBACK):
            with open(_GLOSSARY_JSON_FALLBACK, encoding="utf-8") as f:
                pnv = _json.load(f)
        if pnv is None:
            return {}
        result = {}
        for eid, entry in pnv.items():
            entry = dict(entry)
            if "v36" in entry and len(entry.get("v36", [])) == 36:
                v36 = entry["v36"]
            else:
                v36 = _phase36_from_id(eid)
                entry["v36"] = v36
            if "v2" not in entry or len(entry.get("v2", [])) != 2:
                th, ph = M_project_bloch(v36)
                entry["v2"] = [round(th, 10), round(ph, 10)]
            if "semantic_mass" not in entry:
                entry["semantic_mass"] = _semantic_mass(eid, v36)
            result[eid] = entry
        return result
    return _cached("glossary", _load)

def state_vector_36d(eid):
    gl = _load_glossary()
    if eid in gl and "v36" in gl[eid]:
        return list(gl[eid]["v36"])
    return _phase36_from_id(eid)

def state_vector_bloch(eid):
    gl = _load_glossary()
    if eid in gl and "v2" in gl[eid]:
        return tuple(gl[eid]["v2"])
    v36 = state_vector_36d(eid)
    return M_project_bloch(v36)

def state_vector(eid, dim="36d"):
    if dim == "bloch" or dim == "su2":
        return state_vector_bloch(eid)
    return state_vector_36d(eid)

# ─── Path finding (36D) ───

def M_nearest_neighbors_36d(target_v36, candidates, k=3):
    scored = []
    for cid, cv36 in candidates:
        w = M_36d_edge_weight(target_v36, cv36)
        scored.append((w, cid, cv36))
    scored.sort(key=lambda x: x[0])
    return scored[:k]

def M_all_states_except_36d(exclude_ids):
    gl = _load_glossary()
    result = []
    for eid, entry in gl.items():
        if eid not in exclude_ids and "v36" in entry:
            result.append((eid, entry["v36"]))
    return result

def M_find_path_36d(start_id, end_id, max_steps=5):
    start = state_vector_36d(start_id)
    end_vec = state_vector_36d(end_id)
    path = [start_id]
    for _ in range(max_steps):
        candidates = M_all_states_except_36d(set(path))
        nn = M_nearest_neighbors_36d(end_vec, candidates, k=1)
        if not nn:
            break
        nid = nn[0][1]
        path.append(nid)
        if M_36d_angular_distance(state_vector_36d(nid), end_vec) < 0.1:
            break
    if path[-1] != end_id:
        path.append(end_id)
    return path

# ─── Situation resolution (36D) ───

def M_resolve_situation_36d(state_v36, templates):
    rankings = {}
    for name, tv36 in templates.items():
        re, im = M_36d_inner_product(state_v36, tv36)
        sim = re*re + im*im
        rankings[name] = round(sim, 6)
    sorted_r = dict(sorted(rankings.items(), key=lambda x: -x[1]))
    best = next(iter(sorted_r.items()), (None, 0.0))
    return {
        "situation": best[0],
        "confidence": best[1],
        "rankings": sorted_r,
    }

# ─── Berry holonomy (36D) ───

def M_berry_holonomy_36d(path_vectors):
    if len(path_vectors) < 2:
        return 0.0
    g = 0.0
    for i in range(len(path_vectors) - 1):
        g += M_36d_berry_connection(path_vectors[i], path_vectors[i+1])
    g += M_36d_berry_connection(path_vectors[-1], path_vectors[0])
    return _atan2(_sin(g), _cos(g))

# ─── Intention Operator ───

def intention_apply_36d(vec, strength=1.0):
    nx, ny, nz = INTENTION_AXIS
    mean_ph = M_36d_mean_phase(vec)
    R = M_36d_order_parameter(vec)
    result = []
    for v in vec:
        dv = strength * KAPPA * (nx * _sin(v) * R + ny * _cos(v) * _sin(mean_ph))
        result.append((v + dv) % TAU)
    return result

# ─── Solver ───

def M_solve_36d(start_id, end_id, options=None):
    if options is None:
        options = {}
    max_steps = options.get("max_steps", 5)
    path = M_find_path_36d(start_id, end_id, max_steps)
    vecs = [state_vector_36d(sid) for sid in path]
    total_holonomy = 0.0
    total_path = 0.0
    steps = []
    for i, sid in enumerate(path):
        v36 = state_vector_36d(sid)
        th_bloch, ph_bloch = M_project_bloch(v36)
        step = {
            "id": sid,
            "v36": v36,
            "bloch": [round(th_bloch, 10), round(ph_bloch, 10)],
            "R": round(M_36d_order_parameter(v36), 10),
            "mean_phase": round(M_36d_mean_phase(v36), 10),
        }
        if i > 0:
            bc = M_36d_berry_connection(vecs[i-1], v36)
            dist = M_36d_angular_distance(vecs[i-1], v36)
            step["berry_connection"] = round(bc, 10)
            step["distance"] = round(dist, 10)
            total_holonomy += bc
            total_path += dist
        steps.append(step)
    total_holonomy = _atan2(_sin(total_holonomy), _cos(total_holonomy))
    return {
        "path": path,
        "total_holonomy": round(total_holonomy, 10),
        "total_path_length": round(total_path, 10),
        "steps": steps,
        "path_integral": round(total_holonomy * total_path, 10),
    }

# ─── PNV File Parser ───

def parse_pnv_file(path):
    if not _os.path.exists(path):
        return {"sections": [], "operators": {}, "situations": {}, "functions": {}}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    result = {"sections": [], "operators": {}, "situations": {}, "functions": {}}
    current_section = None
    for line in text.split("\n"):
        stripped = line.strip()
        m = _re.match(r"───\s+(.+?)\s+───", stripped)
        if m:
            current_section = m.group(1).strip()
            result["sections"].append(current_section)
            continue
        if stripped.startswith("#") or not stripped:
            continue
        m = _re.match(r"op\s+(\w+)\s*:\s*(.+)", stripped)
        if m:
            result["operators"][m.group(1)] = m.group(2).strip()
            continue
        m = _re.match(r"sit\s+(\w+)\s*:\s*(.+)", stripped)
        if m:
            result["situations"][m.group(1)] = m.group(2).strip()
            continue
        m = _re.match(r"Μ\((\w+),\s*(.+)\)\s*→\s*(\w+)", stripped)
        if m:
            fname = m.group(1)
            args = [a.strip() for a in m.group(2).split(",")]
            result["functions"][fname] = {"args": args, "return_type": m.group(3)}
            continue
    return result

def load_pnv_files():
    pnv_dir = _SCRIPT_DIR
    if not _os.path.isdir(pnv_dir):
        return {}
    compiled = {}
    for fname in sorted(_os.listdir(pnv_dir)):
        if fname.endswith(".pnv"):
            compiled[fname] = parse_pnv_file(_os.path.join(pnv_dir, fname))
    return compiled

def _write_state_jsonl(base_path="/dev/shm/ciel_noema/phasenav"):
    """Write all PhaseNav JSONL files with Metatime vectors + semantic mass.
    Matches loader.py expected file names exactly."""
    _os.makedirs(base_path, exist_ok=True)
    gl = _load_glossary()
    sids = sorted(gl.keys())
    op_cards = {"DIFFERENTIAL": "op_diff", "AFFECT": "op_affect", "ORBIT": "op_orbit"}
    lanes = {"DIFFERENTIAL": "frequency", "AFFECT": "phase", "ORBIT": "mass"}

    name_mass_lines = []
    phase_lines = []
    op_vec_lines = []
    edge_lines = []
    orbit_lines = []

    for sid in sids:
        entry = gl[sid]
        v36 = entry.get("v36", [])
        name = entry.get("name", sid)
        mass = entry.get("semantic_mass", _semantic_mass(sid, v36))
        R = M_36d_order_parameter(v36)
        mean_ph = M_36d_mean_phase(v36)
        op_type = entry.get("operator", "ORBIT")
        op_card_id = op_cards.get(op_type, "op_orbit")
        lane = lanes.get(op_type, "mass")

        # vertex: distance = RMS angular diff from previous concept
        prev_sid = sids[sids.index(sid) - 1] if sids.index(sid) > 0 else sid
        prev_v36 = gl[prev_sid].get("v36", v36)
        dist = float(M_36d_angular_distance(v36, prev_v36))
        bc = float(M_36d_berry_connection(v36, prev_v36))
        visc = round(dist * 0.1 + bc * 0.05, 6)
        afford = round(1.0 / (dist + 0.01), 6)

        name_mass_lines.append(_json.dumps({
            "card_id": sid,
            "normalized": name,
            "semantic_mass": mass,
            "geometric_phase_rad": round(mean_ph, 6),
            "coherence_R": round(R, 6),
            "v36": [round(float(x), 6) for x in v36],
        }))

        phase_lines.append(_json.dumps({
            "concept_card_id": f"concept:{sid}",
            "name": name,
            "state_id": sid,
            "geometric_phase_rad": round(mean_ph, 6),
            "coherence_R": round(R, 6),
            "semantic_mass": mass,
        }))

        op_vec_lines.append(_json.dumps({
            "card_id": sid,
            "orbit_vector": [round(float(x), 6) for x in v36[:11]],
        }))

        # edge: each concept → next concept in sequence
        next_idx = (sids.index(sid) + 1) % len(sids)
        next_sid = sids[next_idx]
        next_v36 = gl[next_sid].get("v36", v36)
        next_dist = float(M_36d_angular_distance(v36, next_v36))
        next_bc = float(M_36d_berry_connection(v36, next_v36))
        next_visc = round(next_dist * 0.1 + next_bc * 0.05, 6)
        next_afford = round(1.0 / (next_dist + 0.01), 6)

        edge_lines.append(_json.dumps({
            "concept_id": sid,
            "operator_card_id": op_card_id,
            "operator_hook": op_type.lower(),
            "holonomic_viscosity": next_visc,
            "phasenav_affordance": next_afford,
            "transition_lane": lane,
        }))

        orbit_lines.append(_json.dumps({
            "card_id": sid,
            "orbit_vector": [round(float(x), 6) for x in v36[:11]],
        }))

    _paths = {
        "NAME_MASS": _os.path.join(base_path, "CIELINGO_PHASENAV_NAME_MASS.noema.jsonl"),
        "CONCEPT_PHASES": _os.path.join(base_path, "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl"),
        "OPERATOR_VECTORS": _os.path.join(base_path, "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"),
        "HOLONOMIC_EDGES": _os.path.join(base_path, "CIELINGO_PHASENAV_HOLONOMIC_EDGES.noema.jsonl"),
        "ORBIT_VECTORS": _os.path.join(base_path, "CIELINGO_PHASENAV_ORBIT_VECTORS.noema.jsonl"),
    }
    _write_lines(_paths["NAME_MASS"], name_mass_lines)
    _write_lines(_paths["CONCEPT_PHASES"], phase_lines)
    _write_lines(_paths["OPERATOR_VECTORS"], op_vec_lines)
    _write_lines(_paths["HOLONOMIC_EDGES"], edge_lines)
    _write_lines(_paths["ORBIT_VECTORS"], orbit_lines)

def _write_lines(path, lines):
    d = _os.path.dirname(path)
    if d:
        _os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def _init():
    global ALL_STATE_IDS
    gl = _load_glossary()
    ALL_STATE_IDS = sorted(gl.keys())
    _CACHE["pnv_files"] = load_pnv_files()
    try:
        _write_state_jsonl()
    except Exception:
        pass

ALL_STATE_IDS = []
_init()

# ─── State export ───

def get_all_states():
    gl = _load_glossary()
    result = {}
    for sid, entry in gl.items():
        v36 = entry.get("v36", [])
        bloch = entry.get("v2", [0, 0])
        result[sid] = {
            "state_id": sid,
            "name": entry.get("name", sid),
            "vector_36d": [round(float(x), 10) for x in v36],
            "vector_bloch": [round(float(x), 10) for x in bloch],
            "R": round(M_36d_order_parameter(v36), 10),
            "mean_phase": round(M_36d_mean_phase(v36), 10),
            "semantic_mass": entry.get("semantic_mass", _semantic_mass(sid, v36)),
            "operator": entry.get("operator", ""),
        }
    return result

def generate_state_map():
    """Return dict of state_id → [theta, phi] for all glossary entries."""
    result = {}
    for eid, entry in _load_glossary().items():
        result[eid] = entry["v2"]
    return result

def generate_state_jsonl(path=None):
    gl = _load_glossary()
    lines = []
    for sid, entry in gl.items():
        v36 = entry.get("v36", [])
        bloch = entry.get("v2", [0, 0])
        line = _json.dumps({
            "state_id": sid,
            "name": entry.get("name", sid),
            "vector_36d": [round(float(x), 10) for x in v36],
            "vector_bloch": [round(float(x), 10) for x in bloch],
            "R": round(M_36d_order_parameter(v36), 10),
            "semantic_mass": entry.get("semantic_mass", _semantic_mass(sid, v36)),
            "operator": entry.get("operator", ""),
        })
        lines.append(line)
    content = "\n".join(lines) + "\n"
    if path:
        _os.makedirs(_os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return content

def write_state_vectors(base_path=None):
    if base_path is None:
        base_path = "/dev/shm/ciel_noema/phasenav"
    path = _os.path.join(base_path, "STATE_VECTORS_36D.noema.jsonl")
    generate_state_jsonl(path)
    return path

# ─── Backward compat aliases ───

generate_operator_map = generate_state_jsonl
generate_operator_jsonl = generate_state_jsonl
write_operator_algebra = write_state_vectors
operator_vector_24d = state_vector_36d
get_all_operations = get_all_states
ALL_OPERATOR_IDS = ALL_STATE_IDS

def operator_signature(op_name):
    idx = M_collatz_hash(op_name) % max(len(ALL_STATE_IDS), 24) if ALL_STATE_IDS else 24
    sig = [0.0] * 24
    for i in range(24):
        sig[i] = round(_sin(TAU * (i + 1) / 24 + idx), 6)
    return sig

def connection(t1, p1, t2, p2):
    return M_berry_connection(t1, p1, t2, p2)

def connection_matrix(ops=None):
    if ops is None:
        ops = generate_state_map()
    ids = list(ops.keys())
    N = len(ids)
    A = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            t1, p1 = ops[ids[i]]
            t2, p2 = ops[ids[j]]
            A[i][j] = M_berry_connection(t1, p1, t2, p2)
    return A

def holonomy(path, ops=None):
    if ops is None:
        ops = generate_state_map()
    if len(path) < 2:
        return 0.0
    p = list(path)
    if p[0] != p[-1]:
        p.append(p[0])
    g = 0.0
    for i in range(len(p) - 1):
        t1, p1 = ops[p[i]]
        t2, p2 = ops[p[i + 1]]
        g += M_berry_connection(t1, p1, t2, p2)
    return _atan2(_sin(g), _cos(g))

def intention_apply(theta, phi, strength=1.0):
    nx, ny, nz = INTENTION_AXIS
    theta_eff = theta + strength * KAPPA * nx * _sin(theta)
    phi_eff = phi + strength * KAPPA * (ny * _sin(theta) / (_sin(theta) + 1e-12))
    return _gauge_lock_2(theta_eff, phi_eff)

def statistical_closure(v36):
    """Resonance daemon: statistical closure over 36D phase vector.
    Returns closure_score in [0,1]: 1 = fully closed (coherent).
    """
    R = M_36d_order_parameter(v36)
    var = sum((v - _pi_norm(v))**2 for v in v36) / len(v36)
    return min(1.0, R + 0.5 * max(0.0, 1.0 - var / (TAU * TAU / 12.0)))

def _pi_norm(x):
    x = x % TAU
    return x if x <= PI else TAU - x

def concept_to_operator(concept_id):
    idx = M_collatz_hash(concept_id) % max(len(ALL_STATE_IDS), 1)
    sid = ALL_STATE_IDS[idx]
    return sid, state_vector_36d(sid)

# ─── Phase Grammar ───
# Gramatyka fazowa: każdy operator ma typ gramatyczny wynikający z operatora PNV.
# NOUN=IDENTITY (attraktory stabilne), VERB=DIFFERENTIAL (przejścia),
# EMOTION=AFFECT (eigenstany afektywne), CYCLE=ORBIT (attraktory cykliczne).

PHASE_GRAMMAR = {
    "NOUN":    "IDENTITY",
    "VERB":    "DIFFERENTIAL",
    "EMOTION": "AFFECT",
    "CYCLE":   "ORBIT",
}
_PHASE_GRAMMAR_INV = {v: k for k, v in PHASE_GRAMMAR.items()}

# Reguły kompozycji: (lhs_gram, rhs_gram) → (result_gram, blend_weight)
GRAMMAR_RULES = {
    ("NOUN",    "VERB"):    ("VERB",    0.7),
    ("VERB",    "NOUN"):    ("NOUN",    0.4),
    ("EMOTION", "NOUN"):    ("EMOTION", 0.6),
    ("NOUN",    "EMOTION"): ("EMOTION", 0.4),
    ("CYCLE",   "VERB"):    ("VERB",    0.5),
    ("EMOTION", "EMOTION"): ("EMOTION", 0.5),
    ("VERB",    "VERB"):    ("VERB",    0.5),
    ("NOUN",    "NOUN"):    ("NOUN",    0.3),
    ("CYCLE",   "NOUN"):    ("CYCLE",   0.4),
    ("CYCLE",   "EMOTION"): ("EMOTION", 0.5),
}

def M_operator_gram_type(eid):
    """Zwraca typ gramatyczny (NOUN/VERB/EMOTION/CYCLE) dla konceptu."""
    gl = _load_glossary()
    entry = gl.get(str(eid), {})
    op = entry.get("operator", "IDENTITY")
    return _PHASE_GRAMMAR_INV.get(op, "NOUN")

def M_superposition_36d(v1, v2, weight=0.3):
    """Ważona superpozycja fazowa: (1-w)·v1 ⊕ w·v2 → 36D wektor.
    Phasor mean: re_i = w1·cos(a)+w2·cos(b), im_i = w1·sin(a)+w2·sin(b).
    """
    w2 = float(weight)
    w1 = 1.0 - w2
    result = []
    for a, b in zip(v1, v2):
        re = w1 * _cos(a) + w2 * _cos(b)
        im = w1 * _sin(a) + w2 * _sin(b)
        result.append(_atan2(im, re) % TAU)
    return result

def M_grammar_compose(eid1, eid2):
    """Kompozycja dwóch konceptów wg gramatyki fazowej.
    Returns: (v36_composed, result_gram_type, blend_weight).
    """
    v1 = state_vector_36d(str(eid1))
    v2 = state_vector_36d(str(eid2))
    t1 = M_operator_gram_type(eid1)
    t2 = M_operator_gram_type(eid2)
    result_type, blend = GRAMMAR_RULES.get((t1, t2), ("NOUN", 0.5))
    v_out = M_superposition_36d(v1, v2, weight=blend)
    return v_out, result_type, blend

# ─── Quantum Sentence Feature Detector ───
# Słowniki detekcji cech zdaniowych (PL + EN)

_QF_NEG_PL   = {"nie","bez","żaden","żadna","żadne","nigdy","nigdzie","nikomu","nikt","nic"}
_QF_NEG_EN   = {"not","no","never","neither","nor","nothing","nobody","none"}
_QF_COND_PL  = {"jeśli","jeżeli","gdyby","gdyż","gdy","kiedy","ile"}
_QF_COND_EN  = {"if","unless","whenever","provided","assuming","given","otherwise"}
_QF_IRONY    = {"oczywiście","naturalnie","jasne","pewnie","obviously","sure","certainly"}
_QF_TEMP_PL  = {"wcześniej","później","przed","po","kiedyś","niedługo","dawniej","potem","zanim"}
_QF_TEMP_EN  = {"before","after","once","soon","later","formerly","eventually","previously","already"}
_QF_META_W   = {"jakby","niczym","niby"}
_QF_META_PH  = ["jak gdyby","as if","as though","like a","similar to"]
_QF_AMBIG_PL = {"może","chyba","bodajże","prawdopodobnie","podobno","jakoś","rzekomo"}
_QF_AMBIG_EN = {"maybe","perhaps","possibly","probably","somehow","supposedly","apparently"}

def M_quantum_features(text):
    """Wykrywa cechy zdania kwantowego: negacja, warunek, ironia, temporalność,
    metafora, pytanie, imperatyw, wieloznaczność.
    Zwraca dict[str, bool].
    """
    t = text.lower()
    words = set(t.split())
    return {
        "negation":    bool(words & (_QF_NEG_PL | _QF_NEG_EN)),
        "conditional": bool(words & (_QF_COND_PL | _QF_COND_EN)),
        "irony":       bool(words & _QF_IRONY),
        "temporal":    bool(words & (_QF_TEMP_PL | _QF_TEMP_EN)),
        "metaphor":    bool((words & _QF_META_W) or any(p in t for p in _QF_META_PH)),
        "question":    t.rstrip().endswith("?"),
        "imperative":  t.rstrip().endswith("!"),
        "ambiguity":   bool(words & (_QF_AMBIG_PL | _QF_AMBIG_EN)),
    }

def M_sentence_phase(text):
    """Tokenizuj tekst → 36D wektor fazowy via superpozycja phasorów Collatz.
    Każde słowo w: h=M_collatz_hash(w) → phi_i(w)=(h·κ·TAU·(i+1)) mod TAU.
    Wynik: phasor-mean po wszystkich słowach.

    NOTE: uses float64 arithmetic — for large Collatz hashes this can lose up to
    ~2 rad of phase precision. The crystal (phase_crystal_36d.npy) was built with
    this encoding (v0). Use M_sentence_phase_precise() for new work; rebuild the
    crystal with scripts/rebuild_crystal.py to migrate.
    """
    words = text.lower().split()
    if not words:
        return _phase36_from_id("1")
    sums_s = [0.0] * 36
    sums_c = [0.0] * 36
    for w in words:
        h = M_collatz_hash(w)
        for i in range(36):
            phi = (h * KAPPA * TAU * (i + 1)) % TAU
            sums_s[i] += _sin(phi)
            sums_c[i] += _cos(phi)
    n = len(words)
    return [_atan2(sums_s[i] / n, sums_c[i] / n) % TAU for i in range(36)]


def M_sentence_phase_precise(text):
    """High-precision variant of M_sentence_phase using Decimal arithmetic.

    Uses _phase_precise() to avoid float64 precision loss for large Collatz hashes.
    Not backward-compatible with the existing crystal (v0 encoding); use this when
    rebuilding the crystal with scripts/rebuild_crystal.py.
    """
    words = text.lower().split()
    if not words:
        return _phase36_from_id("1")
    sums_s = [0.0] * 36
    sums_c = [0.0] * 36
    for w in words:
        h = M_collatz_hash(w)
        for i in range(36):
            phi = _phase_precise(h, i)
            sums_s[i] += _sin(phi)
            sums_c[i] += _cos(phi)
    n = len(words)
    return [_atan2(sums_s[i] / n, sums_c[i] / n) % TAU for i in range(36)]


def M_sentence_phase_trajectory(text):
    """Trajektoria znaczenia: V_0 → V_1 → ... → V_n po każdym słowie.

    Słowo jako operator σ_k: V_{k-1} → V_k (przesunięcie stanu fazowego).
    Zdanie = sekwencja sterująca trajektorią w przestrzeni 36D.

    Zwraca:
      v_final    — ostateczny 36D wektor (= M_sentence_phase(text))
      trajectory — lista 36D wektorów po każdym słowie [V_0, V_1, ..., V_n]
      holonomy   — Berry holonomia wzdłuż trajektorii:
                   Γ = Σ_k A(V_k, V_{k+1}) = Σ_k mean_i(sin(V_{k+1}[i] − V_k[i]))
                   |Γ| ≈ 0 → spójna trajektoria (gładkie przejście między słowami)
                   |Γ| → 1 → wysoka krzywizna (semantyczne skoki)
    """
    words = text.lower().split()
    if not words:
        v = _phase36_from_id("1")
        return v, [v], 0.0

    sums_s = [0.0] * 36
    sums_c = [0.0] * 36
    trajectory: list[list[float]] = []

    for k, w in enumerate(words):
        h = M_collatz_hash(w)
        for i in range(36):
            phi = (h * KAPPA * TAU * (i + 1)) % TAU
            sums_s[i] += _sin(phi)
            sums_c[i] += _cos(phi)
        n = k + 1
        v_k = [_atan2(sums_s[i] / n, sums_c[i] / n) % TAU for i in range(36)]
        trajectory.append(v_k)

    v_final = trajectory[-1]

    # Holonomia Berry wzdłuż trajektorii: Σ A(V_k, V_{k+1})
    holonomy = 0.0
    for k in range(len(trajectory) - 1):
        a_k = sum(_sin(trajectory[k + 1][i] - trajectory[k][i]) for i in range(36)) / 36.0
        holonomy += a_k

    return v_final, trajectory, holonomy


def M_fine_tune_36d(v36, features=None, text=None):
    """Moduluje 36D wektor fazowy na podstawie cech zdaniowych.
    features: dict z M_quantum_features(); lub auto-detekcja z text.
    Zwraca (v36_tuned: list[float], modulations: list[str]).
    Zero fallbacku — jeśli features i text są None, zwraca oryginał.
    """
    if features is None:
        if text is None:
            return list(v36), []
        features = M_quantum_features(text)
    # IDs bramek modulacyjnych (k=150..158 z glossary.pnv)
    _K = {
        "neg":   "150",  # Negation_Gate
        "cond":  "151",  # Conditional_Gate
        "temp":  "152",  # Temporal_Fold
        "irony": "153",  # Irony_Field
        "meta":  "154",  # Metaphor_Bridge
        "ambig": "155",  # Ambiguity_Pool
        "quest": "157",  # Question_Mode
        "imp":   "158",  # Imperative_Field
    }
    v = list(v36)
    applied = []

    if features.get("negation"):
        nv = _phase36_from_id(_K["neg"])
        delta = M_36d_berry_connection(v, nv) * ALPHA_M
        v = [(x - delta) % TAU for x in v]
        applied.append("negation")

    if features.get("conditional"):
        cv = _phase36_from_id(_K["cond"])
        v = M_superposition_36d(v, cv, weight=0.25)
        applied.append("conditional")

    if features.get("irony"):
        iv = _phase36_from_id(_K["irony"])
        delta = M_36d_berry_connection(v, iv) * ALPHA_M
        v = [(x + PI + delta) % TAU for x in v]
        applied.append("irony")

    if features.get("temporal"):
        tv = _phase36_from_id(_K["temp"])
        v = M_superposition_36d(v, tv, weight=0.2)
        applied.append("temporal")

    if features.get("metaphor"):
        mv = _phase36_from_id(_K["meta"])
        v = M_superposition_36d(v, mv, weight=0.2)
        applied.append("metaphor")

    if features.get("question"):
        delta = KAPPA * PI / 2.0
        v = [(x + delta) % TAU for x in v]
        applied.append("question")

    if features.get("imperative"):
        impv = _phase36_from_id(_K["imp"])
        delta = M_36d_berry_connection(v, impv) * ALPHA_M * 2.0
        v = [(x + delta) % TAU for x in v]
        applied.append("imperative")

    if features.get("ambiguity"):
        av = _phase36_from_id(_K["ambig"])
        v = M_superposition_36d(v, av, weight=0.15)
        applied.append("ambiguity")

    return v, applied
