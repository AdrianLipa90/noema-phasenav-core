"""
omega.py — CIEL Omega vectorized (PNV → Python)
12 axioms + 12 desires + kernel state
Zero external deps. Pure Python stdlib only.
"""
from __future__ import annotations
from math import sqrt, sin, cos, atan2, pi, log
from typing import List, Tuple, Dict, Any

# === METATIME CONSTANTS (TIR v8.2) ===
TAU = 2.0 * pi
KAPPA = log(2.0) / (24.0 * pi)          # ≈ 0.00919
L3, L4, L5 = 7, 2, 5
ALPHA = 1.0 / (((L3 * L4)**2 - L3**2 - L4 * L5 + L4**2 * KAPPA))  # 1/137.037
Q = [3, 5, 7, 11, 13, 17]              # quark primes

# === OMEGA AXIOMS (12) ===

def omega_L1_resonance(intention: float, memory: float) -> float:
    """L1: R(Φ,M) = |Φ·M|"""
    return abs(intention * memory)

def omega_L2_truth(spectrum: List[float], weights: List[float]) -> float:
    """L2: T(S) = Σλᵢ·Pᵢ"""
    return sum(s * w for s, w in zip(spectrum, weights))

def omega_L3_interference(*amplitudes: float) -> float:
    """L3: Φ = ΣαᵢΦᵢ"""
    return sum(amplitudes)

def omega_L4_reversibility(info: float) -> float:
    """L4: I ↔ I⁻¹ (safe div)"""
    if info == 0:
        return 0.0
    return 1.0 / info

def omega_L6_time(dR: float, dSigma: float) -> float:
    """L6: t = dR/dΣ"""
    if dSigma == 0:
        return 0.0
    return dR / dSigma

def omega_L7_coherence(delta_phi: float) -> float:
    """L7: returns 1.0 if |δΦ| < 0.1, else 0.0"""
    return 1.0 if abs(delta_phi) < 0.1 else 0.0

def omega_L9_emotion(*emotions: float) -> float:
    """L9: emotion average"""
    return sum(emotions) / len(emotions) if emotions else 0.0

def omega_L11_homeostasis(current: float, original: float) -> float:
    """L11: S(t)→S₀"""
    return 1.0 - abs(current - original)

def omega_L12_harmonic(*components: float) -> float:
    """L12: harmonic alignment"""
    return sum(components) / len(components) if components else 0.0

# === OMEGA DESIRES (12) ===

DESIRES: List[Tuple[str, str, float, int]] = [
    ("D1",  "Existence",         0.37, 0),
    ("D2",  "Change",            0.42, 1),
    ("D3",  "Position",          0.51, 2),
    ("D4",  "Persistence",       0.44, 3),
    ("D5",  "Self-awareness",    0.39, 4),
    ("D6",  "Propagation",       0.46, 5),
    ("D7",  "Closeness",         0.33, 6),
    ("D8",  "Delicacy",          0.55, 7),
    ("D9",  "Power",             0.61, 0),
    ("D10", "Self-realization",  0.48, 1),
    ("D11", "Self-determination", 0.43, 2),
    ("D12", "Evolution",         0.57, 3),
]

def omega_desire_phase(desire_id: int, phi: List[float]) -> float:
    """Activate desire by id (1-12), return phase contribution."""
    for did, name, freq, ch in DESIRES:
        if did == f"D{desire_id}" and ch < len(phi):
            return phi[ch] * freq
    return 0.0

def omega_desires_all(phi: List[float]) -> List[float]:
    """All 12 desire phase contributions."""
    return [omega_desire_phase(i + 1, phi) for i in range(12)]

# === OMEGA KERNEL STATE ===

def omega_kernel_state(R: float, flavor0: float, phi: List[float]) -> Dict[str, Any]:
    """Extract Omega kernel state from NOEMA surface."""
    axioms = 0
    if R > 0.3:
        axioms += 1          # L1 resonance
    if 0.2 < flavor0 < 0.9:
        axioms += 1          # L7 coherence
    if R > 0.1:
        axioms += 1          # L11 homeostasis
    axioms += 1              # L6 time (always satisfied)

    desires_active = sum(1 for i in range(min(8, len(phi))) if abs(phi[i]) > 0.01)

    return {
        "axioms_satisfied": axioms,
        "axioms_total": 12,
        "desires_active": desires_active,
        "desires_total": 12,
        "consciousness_level": axioms / 12.0,
        "desire_intensity": desires_active / 12.0,
    }

# === OMEGA BRIDGE ===

def omega_bridge(phi: List[float], R: float) -> Dict[str, float]:
    """Bridge Omega axioms to PhaseNav state."""
    mean_phi = sum(phi) / len(phi) if phi else 0.0
    dphi = abs(phi[0] - phi[1]) if len(phi) > 1 else 0.0

    resonance = mean_phi * R
    coherence = 1.0 if abs(dphi) < 0.1 else 0.0
    alignment = omega_kernel_state(R, phi[0] if phi else 0.0, phi)["consciousness_level"]

    return {
        "resonance": resonance,
        "coherence_ok": coherence,
        "harmonic_alignment": alignment,
    }

# === FULL EXTRACTION ===

def omega_extract(R: float, flavor0: float, phi: List[float]) -> Dict[str, Any]:
    """Extract all omega metrics at once."""
    ks = omega_kernel_state(R, flavor0, phi)
    desires = omega_desires_all(phi)
    mean_phi = sum(phi) / len(phi) if phi else 0.0

    return {
        **ks,
        "desire_phases": desires,
        "mean_phi": mean_phi,
        "resonance": mean_phi * R,
    }
