"""phase_gate_engine.py — CielEngine replacement via PhaseNav phase gates.

Spec: ciel_engine.pnv
Cold start: ~0ms (vs ~50s for CielEngine).
API: PhaseGateEngine().step(text, context=None) → same dict as CielEngine.step().
Zero external deps beyond pnv_runtime.py (pure Python stdlib only).
"""

import math as _math

try:
    from .pnv_runtime import (
        M_collatz_hash, _phase36_from_id, M_36d_order_parameter,
        M_36d_berry_connection, M_36d_angular_distance, M_36d_mean_phase,
        M_36d_inner_product, _sin, _cos, _atan2, PI, TAU, KAPPA, ALPHA_M,
        M_sentence_phase, M_quantum_features, M_fine_tune_36d,
        M_superposition_36d,
    )
except ImportError:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from pnv_runtime import (
        M_collatz_hash, _phase36_from_id, M_36d_order_parameter,
        M_36d_berry_connection, M_36d_angular_distance, M_36d_mean_phase,
        M_36d_inner_product, _sin, _cos, _atan2, PI, TAU, KAPPA, ALPHA_M,
        M_sentence_phase, M_quantum_features, M_fine_tune_36d,
        M_superposition_36d,
    )

# ─── Stałe ───

_AFFECT_BAND = list(range(42, 66))
_AFFECT_NAMES = {
    42: "Love",       43: "Desire",      44: "Fear",        45: "Joy",
    46: "Grief",      47: "Anger",       48: "Awe",         49: "Trust",
    50: "Anticipation", 51: "Surprise",  52: "Sadness",     53: "Disgust",
    54: "Curiosity",  55: "Acceptance",  56: "Compassion",  57: "Gratitude",
    58: "Humility",   59: "Pride",       60: "Shame",       61: "Guilt",
    62: "Nostalgia",  63: "Hope",        64: "Loneliness",  65: "Wonder",
}
_ETHICS_IDS  = [39, 88, 100]   # Truth(039), Justice(088), Ethos(100)
_SOUL_IDS    = list(range(1, 8))  # Resonance..Bloch_Resonance (k=001..007)
_MAX_ORBIT   = 64

# Wektory precomputed przy imporcie modułu (0-deps, ~0ms)
_AFFECT_VECS = {k: _phase36_from_id(str(k)) for k in _AFFECT_BAND}
_ETHICS_VECS = {k: _phase36_from_id(str(k)) for k in _ETHICS_IDS}
_SOUL_VECS   = [_phase36_from_id(str(k)) for k in _SOUL_IDS]


# ─── G02 AFFECT ───

def _g02_affect(v36):
    """φ_36d → (dominant_emotion: str, mood: float [0,1])."""
    best_k = 54  # Curiosity jako default
    best_d = float("inf")
    for k, ev in _AFFECT_VECS.items():
        d = M_36d_angular_distance(v36, ev)
        if d < best_d:
            best_d = d
            best_k = k
    mood = M_36d_order_parameter(v36)
    return _AFFECT_NAMES[best_k], round(mood, 6)


# ─── G03 COLLATZ ───

def _g03_collatz(text, v36):
    """text + φ → collatz_runtime dict (spec: ciel_engine.pnv § G03)."""
    seed = M_collatz_hash(text) % (2 ** 32)
    orbit = []
    n = max(seed, 1)
    for _ in range(_MAX_ORBIT):
        orbit.append(n)
        if n == 1:
            break
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    orbit_length = len(orbit)
    attractor_score = round(1.0 / (1.0 + orbit_length / 64.0), 6)

    seed32 = seed & 0xFFFFFFFF
    ones = bin(seed32).count("1")
    p1 = ones / 32.0
    p0 = 1.0 - p1
    parity_entropy = 0.0
    if 0.0 < p1 < 1.0:
        parity_entropy = -p1 * _math.log2(p1) - p0 * _math.log2(p0)
    parity_entropy = round(parity_entropy, 6)

    R_H = M_36d_order_parameter(v36)
    mean_ph = M_36d_mean_phase(v36)
    lie4 = _atan2(_sin(4.0 * mean_ph), _cos(4.0 * mean_ph))

    return {
        "seed":            seed,
        "orbit_length":    orbit_length,
        "attractor_score": attractor_score,
        "parity_entropy":  parity_entropy,
        "phase": {
            "R_H":  round(R_H, 6),
            "lie4": round(lie4, 6),
        },
    }


# ─── G04 SOUL ───

def _g04_soul(v36):
    """φ → soul_invariant: float [-1,1] via Berry holonomy (spec: G04)."""
    path = [v36] + _SOUL_VECS
    gamma = 0.0
    for i in range(len(path) - 1):
        gamma += M_36d_berry_connection(path[i], path[i + 1])
    gamma += M_36d_berry_connection(path[-1], v36)  # zamknięcie pętli
    return round(_atan2(_sin(gamma), _cos(gamma)) / PI, 6)


# ─── G05 ETHICS ───

def _g05_ethics(v36):
    """φ → ethical_score: float [0,1] via wyrównanie do Truth/Justice/Ethos."""
    scores = []
    for k, ev in _ETHICS_VECS.items():
        re, im = M_36d_inner_product(v36, ev)
        scores.append(re * re + im * im)
    return round(sum(scores) / len(scores), 6)


# ─── G06 NONLOCAL ───

def _g06_nonlocal(v36):
    """φ → nonlocal_runtime dict (spec: G06)."""
    univ_vec   = _phase36_from_id("22")   # Universal_Operator
    cosmos_vec = _phase36_from_id("94")   # Cosmos
    eba_defect     = M_36d_angular_distance(v36, univ_vec)
    nonlocal_phase = M_36d_berry_connection(v36, cosmos_vec)
    R              = M_36d_order_parameter(v36)
    information_flow = R * KAPPA
    euler_bridge     = R * (1.0 - eba_defect / PI)
    return {
        "eba_defect":       round(eba_defect, 6),
        "nonlocal_phase":   round(nonlocal_phase, 6),
        "information_flow": round(information_flow, 8),
        "euler_bridge":     round(euler_bridge, 6),
    }


# ─── GŁÓWNY SILNIK ───

class PhaseGateEngine:
    """CielEngine replacement via PhaseNav phase gates.

    Zimny start: ~0ms (CielEngine: ~50s).
    API-kompatybilny: .step(text, context=None) → dict z tymi samymi kluczami.

    Pipeline (spec: ciel_engine.pnv § P01):
      G01 TOKENIZE → G07 FINE_TUNE → G02 AFFECT → G03 COLLATZ
      → G04 SOUL → G05 ETHICS → G06 NONLOCAL → emit
    """

    def step(self, text, context=None):
        if not isinstance(text, str):
            text = str(text)

        # G01: text → 36D wektor fazowy
        v36 = M_sentence_phase(text)

        # Detekcja cech zdania kwantowego
        features = M_quantum_features(text)

        # G07: fine-tune modulacje
        v36_t, modulations = M_fine_tune_36d(v36, features=features)

        # G02: emocja dominująca + nastrój
        emotion, mood = _g02_affect(v36_t)

        # G03: Collatz runtime
        collatz = _g03_collatz(text, v36_t)

        # G04: soul invariant
        soul = _g04_soul(v36_t)

        # G05: wynik etyczny
        ethics = _g05_ethics(v36_t)

        # G06: nielokalność
        nl = _g06_nonlocal(v36_t)

        return {
            "dominant_emotion":  emotion,
            "mood":              mood,
            "soul_invariant":    soul,
            "ethical_score":     ethics,
            "collatz_runtime":   collatz,
            "nonlocal_runtime":  nl,
            "euler_bridge":      nl["euler_bridge"],
            "information_flow":  nl["information_flow"],
            "phase_R":           round(M_36d_order_parameter(v36_t), 6),
            "quantum_features":  features,
            "phase_modulations": modulations,
        }
