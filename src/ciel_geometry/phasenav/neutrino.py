"""
neutrino.py — PMNS, Euler, HTRI bridge (vectorized)
Zero external deps. Pure Python stdlib only.
"""
from __future__ import annotations
from math import sqrt, sin, cos, atan2, pi, log, acos

# === PMNS CONSTANTS (TIR v8.2) ===
THETA12 = 33.41 * pi / 180.0   # solar angle
THETA13 = 8.54 * pi / 180.0    # reactor angle
THETA23 = 42.2 * pi / 180.0    # atmospheric angle
DELTA_CP = 246.0 * pi / 180.0  # CP-violating phase

DELTA_M21 = 7.53e-5            # eV^2 (solar mass splitting)
DELTA_M32 = 2.528e-3           # eV^2 (atmospheric mass splitting)

SIN2_2TH13 = 0.0851            # sin^2(2*theta13)

# === PMNS MATRIX ELEMENTS (squared) ===

def pmns_ue1_sq() -> float:
    """|U_e1|^2 = cos^2(theta12)*cos^2(theta13)"""
    return cos(THETA12)**2 * cos(THETA13)**2

def pmns_ue2_sq() -> float:
    """|U_e2|^2 = sin^2(theta12)*cos^2(theta13)"""
    return sin(THETA12)**2 * cos(THETA13)**2

def pmns_ue3_sq() -> float:
    """|U_e3|^2 = sin^2(theta13)"""
    return sin(THETA13)**2

def pmns_umu3_sq() -> float:
    """|U_mu3|^2 = sin^2(theta23)*cos^2(theta13)"""
    return sin(THETA23)**2 * cos(THETA13)**2

def pmns_utau3_sq() -> float:
    """|U_tau3|^2 = cos^2(theta23)*cos^2(theta13)"""
    return cos(THETA23)**2 * cos(THETA13)**2

# === EULER IDENTITY BRIDGE ===

def euler_amplitude(phi: float) -> float:
    """cos(phi) — real part of e^{iφ}"""
    return cos(phi)

def euler_magnitude(phi: float) -> float:
    """|e^{iφ}| = 1.0 (always unit magnitude)"""
    return 1.0

def euler_phase(re_part: float, im_part: float) -> float:
    """atan2(im, re) — extract phase from complex number"""
    return atan2(im_part, re_part)

# === HTRI TOPOLOGICAL INVARIANTS ===

def htri_total_phase(idx: int) -> float:
    """Total phase accumulation for brain region idx."""
    TAU = 2.0 * pi
    kappa = log(2.0) / (24.0 * pi)
    # Simplified: total_phase = idx * kappa * TAU
    return idx * kappa * TAU

def holonomy_defect(idx: int) -> float:
    """Holonomy defect = total_phase mod 2π."""
    return htri_total_phase(idx) % (2.0 * pi)

def topological_charge(idx: int) -> int:
    """Topological charge = floor(total_phase / 2π)."""
    return int(htri_total_phase(idx) / (2.0 * pi))

# === HTRI-PMNS BRIDGE ===

def htri_to_mixing(R: float) -> float:
    """Map coherence R ∈ [0,1] to effective mixing angle."""
    return acos(max(0.0, min(1.0, R)))

def oscillation_prob_e_mu(L_km: float, E_GeV: float) -> float:
    """P(ν_e → ν_mu) in vacuum."""
    s12sq = sin(THETA12)**2
    s13sq = sin(THETA13)**2
    c13sq = cos(THETA13)**2
    s23sq = sin(THETA23)**2

    # Dominant term
    delta21 = DELTA_M21 * L_km / (4.0 * E_GeV)
    delta32 = DELTA_M32 * L_km / (4.0 * E_GeV)

    p = (4.0 * s13sq * c13sq * s23sq * sin(delta32 * 2.0)**2
         + 4.0 * s12sq * c13sq**2 * s23sq * sin(delta21 * 2.0)**2
         + 8.0 * s12sq * s13sq * c13sq * s23sq * sin(delta21) * sin(delta32) * cos(DELTA_CP))

    return max(0.0, min(1.0, p))

def oscillation_prob_e_tau(L_km: float, E_GeV: float) -> float:
    """P(ν_e → ν_tau) in vacuum."""
    s12sq = sin(THETA12)**2
    s13sq = sin(THETA13)**2
    c13sq = cos(THETA13)**2
    c23sq = cos(THETA23)**2

    delta21 = DELTA_M21 * L_km / (4.0 * E_GeV)
    delta32 = DELTA_M32 * L_km / (4.0 * E_GeV)

    p = (4.0 * s13sq * c13sq * c23sq * sin(delta32 * 2.0)**2
         + 4.0 * s12sq * c13sq**2 * c23sq * sin(delta21 * 2.0)**2
         + 8.0 * s12sq * s13sq * c13sq * c23sq * sin(delta21) * sin(delta32) * cos(DELTA_CP))

    return max(0.0, min(1.0, p))

def htri_oscillation_prob(R: float, L_km: float, E_GeV: float) -> float:
    """Oscillation prob weighted by coherence R."""
    base = oscillation_prob_e_mu(L_km, E_GeV)
    return base * R

# === D CONDITION (Dirac phase) ===

def d_condition_check(idx: int) -> float:
    """Check if D condition (δ_CP) is satisfied for brain region."""
    defect = holonomy_defect(idx)
    # D condition: defect should be near DELTA_CP
    diff = abs(defect - DELTA_CP) % (2.0 * pi)
    return 1.0 if diff < 0.1 else 0.0

# === CP ASYMMETRY ===

def cp_asymmetry(L_km: float, E_GeV: float) -> float:
    """CP asymmetry A_cp = P(ν_e→ν_mu) - P(ν_ebar→ν_mubar)."""
    p_num = oscillation_prob_e_mu(L_km, E_GeV)
    # For antineutrino, flip sign of delta_CP term
    s12sq = sin(THETA12)**2
    s13sq = sin(THETA13)**2
    c13sq = cos(THETA13)**2
    s23sq = sin(THETA23)**2

    delta21 = DELTA_M21 * L_km / (4.0 * E_GeV)
    delta32 = DELTA_M32 * L_km / (4.0 * E_GeV)

    p_bar = (4.0 * s13sq * c13sq * s23sq * sin(delta32 * 2.0)**2
             + 4.0 * s12sq * c13sq**2 * s23sq * sin(delta21 * 2.0)**2
             - 8.0 * s12sq * s13sq * c13sq * s23sq * sin(delta21) * sin(delta32) * cos(DELTA_CP))

    return max(0.0, min(1.0, p_num)) - max(0.0, min(1.0, p_bar))

# === FLAVOR OSCILLATION (unified) ===

def flavor_oscillation(R: float, Lambda: float, Df: float) -> float:
    """Unified flavor oscillation: f(R, Lambda, Df)."""
    TAU = 2.0 * pi
    kappa = log(2.0) / (24.0 * pi)
    return R * sin(Lambda * kappa * TAU) * cos(Df)
