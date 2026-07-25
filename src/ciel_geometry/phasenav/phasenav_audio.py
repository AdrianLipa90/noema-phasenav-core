"""PhaseNav Audio — vectorized analog voice/sound renderer via 36-oscillator surface.

Maps NOEMA's 36 Kuramoto oscillators (×4 harmonics = 144 partials) directly to
audio synthesis. Each PhaseNav operator becomes a transform on the audio phase
vector — voice modulation, filtering, spatialization, timbre shaping.

Architecture:
  Surface φ[0..35] × h[1,3,6,9] → 144 sine partials → time-domain waveform
  PhaseNav operator → audio DSP transform on the 36D phase vector
  Flavor[0..5] → mix parameters (dry/wet, pan, gain, pitch)

No external deps beyond numpy. Output as float64 buffer suitable for
pyaudio/pipewire/ALSA or direct /dev/shm audio IPC.

Internal (silent) mode: set NOEMA_AUDIO_SILENT=1 in env to suppress
any speaker output. All tests run through buffer analysis only.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Any

import numpy as np

N_OSCILLATORS = 36
HARMONICS = np.array([1, 3, 6, 9], dtype=np.float64)
HARMONIC_AMPS = np.array([1.0, 0.5, 0.33, 0.25], dtype=np.float64)
N_PARTIALS = N_OSCILLATORS * len(HARMONICS)  # 144

SAMPLE_RATE = 44100
BASE_HZ = 39.6


@dataclass
class PhaseNavAudioBuffer:
    """Single audio frame rendered from phase state."""

    samples: np.ndarray
    phi: np.ndarray
    omega: np.ndarray
    operator_id: str
    n_samples: int
    tick: int = 0


def oscillator_bank(
    phi: np.ndarray,
    omega: np.ndarray,
    n_samples: int,
    sr: int = SAMPLE_RATE,
    amps: np.ndarray | None = None,
    harmonic_amps: np.ndarray | None = None,
) -> np.ndarray:
    """Render 36×4 = 144 sine partials into a time-domain waveform.

    Each oscillator i produces 4 partials at h×ω_i with amplitude A_h.
    phi[i] sets the starting phase of each partial group.

    Returns mono float64 array of length n_samples.
    """
    amps = amps if amps is not None else np.ones(N_OSCILLATORS)
    h_amps = harmonic_amps if harmonic_amps is not None else HARMONIC_AMPS
    t = np.arange(n_samples, dtype=np.float64) / sr
    out = np.zeros(n_samples, dtype=np.float64)
    for osc_idx in range(N_OSCILLATORS):
        w = float(omega[osc_idx] if omega[osc_idx] > 0 else BASE_HZ)
        p0 = float(phi[osc_idx])
        a = float(amps[osc_idx])
        for h_idx, h in enumerate(HARMONICS):
            amp = a * float(h_amps[h_idx])
            if amp < 1e-12:
                continue
            phase = p0 + 2.0 * math.pi * w * h * t
            out += amp * np.sin(phase)
    peak = float(np.max(np.abs(out)))
    if peak > 1e-12:
        out /= peak
    return out * 0.5


def operator_transform(
    phi: np.ndarray,
    operator_id: str,
    strength: float = 0.5,
) -> np.ndarray:
    """Apply a PhaseNav operator as an audio transform on the phase vector.

    Each operator maps to a specific DSP effect on oscillator phases:
      IDENTITY        — passthrough
      TRANSFORM      — pitch shift (phase rotation per oscillator)
      AFFECT         — timbre warmth (boost low harmonics)
      MEMORY         — echo/pre-delay (phase smear)
      BOUNDARY       — bandpass (zero phases outside range)
      FOLD           — saturation (tanh on phase)
      FORCE          — compression (gain reduction)
      DIFFERENCE     — stereo spread (phase offset L/R)
      COMPOSITION    — mix two vectors
      RISK           — noise gate (threshold)
      SOURCE         — fundamental boost
      SCOPE          — spatial width
      ORDER          — harmonic reorder
      RETURN         — phase reset
      PAUSE          — silence
    """
    result = phi.copy()
    if operator_id == "IDENTITY":
        pass
    elif operator_id == "TRANSFORM":
        shift = strength * np.linspace(-math.pi, math.pi, N_OSCILLATORS)
        result = (phi + shift) % (2.0 * math.pi)
    elif operator_id == "AFFECT":
        warm = np.array([1.5, 1.3, 1.2, 1.1, 1.0, 1.0] * 4, dtype=np.float64)[:36]
        result = phi * (1.0 + strength * (warm - 1.0))
    elif operator_id == "MEMORY":
        smear = np.random.default_rng().uniform(-0.1, 0.1, N_OSCILLATORS) * strength
        result = (phi + smear) % (2.0 * math.pi)
    elif operator_id == "BOUNDARY":
        low = 0.5 - strength * 0.4
        high = 0.5 + strength * 0.4
        mask = (result / (2.0 * math.pi) < low) | (result / (2.0 * math.pi) > high)
        result[mask] = 0.0
    elif operator_id == "FOLD":
        result = np.tanh(phi * strength * 2.0) * math.pi + math.pi
    elif operator_id == "FORCE":
        gain = 1.0 / (1.0 + strength * 2.0)
        result = result * gain
    elif operator_id == "DIFFERENCE":
        offset = strength * np.array([1, -1] * 12, dtype=np.float64) * 0.3
        result = (phi + offset) % (2.0 * math.pi)
    elif operator_id == "COMPOSITION":
        mix = np.roll(phi, int(strength * 6))
        result = (phi + mix) * 0.5
    elif operator_id == "RISK":
        threshold = 1.0 - strength
        mask = result / (2.0 * math.pi) < threshold
        result[mask] *= 0.1
    elif operator_id == "SOURCE":
        result[:6] *= 1.0 + strength
    elif operator_id == "SCOPE":
        spread = strength * np.linspace(-0.5, 0.5, N_OSCILLATORS)
        result = (phi + spread) % (2.0 * math.pi)
    elif operator_id == "ORDER":
        perm = np.argsort(phi)
        result = phi[perm]
    elif operator_id == "RETURN":
        result[:] = phi  # identity with reset marker
    elif operator_id == "PAUSE":
        result[:] = 0.0
    elif operator_id == "UNRUH_DRIVE":
        # Energy from phase acceleration: boost high-velocity oscillators
        # dphi/dosc gradient = energy gradient
        grad = np.diff(phi, append=phi[0])  # spatial gradient along oscillator axis
        accel = np.diff(grad, append=grad[0])  # second difference = acceleration proxy
        # Phase boost proportional to acceleration² (Unruh: E ∝ a²)
        boost = strength * accel ** 2
        boost = np.clip(boost, -1.0, 1.0)
        result = (phi + boost) % (2.0 * math.pi)
    elif operator_id == "WARP_DRIFT":
        # Spatial offset divergence: create travelling wave across oscillators
        # Warp bubble = linear gradient of phase offsets
        t = np.linspace(0, strength * 2.0 * math.pi, N_OSCILLATORS)
        result = (phi + t) % (2.0 * math.pi)
    else:
        result = phi * (1.0 + strength * 0.1)
    return result % (2.0 * math.pi)


SILENT = bool(int(os.environ.get("NOEMA_AUDIO_SILENT", "1")))
if SILENT:
    import warnings
    warnings.warn("NOEMA_AUDIO_SILENT=1 — speaker output suppressed")


def self_test() -> dict[str, Any]:
    """Internal buffer test — no speaker output. Validates DSP pipeline."""
    rng = np.random.default_rng(42)
    phi = rng.uniform(0, 2 * math.pi, N_OSCILLATORS)
    omega = np.full(N_OSCILLATORS, BASE_HZ)
    results = {}
    for op in ("IDENTITY", "TRANSFORM", "AFFECT", "MEMORY", "FOLD"):
        buf = render_frame(phi, omega, op, 0.5, sr=8000, n_samples=800)
        peak = float(np.max(np.abs(buf.samples)))
        mean_phi = float(np.mean(buf.phi))
        results[op] = {"peak": peak, "mean_phi": round(mean_phi, 4), "samples": len(buf.samples)}
    chain = operator_dsp_chain(phi, [("AFFECT", 0.6), ("FOLD", 0.3)])
    mod = rng.uniform(0, 2 * math.pi, N_OSCILLATORS)
    voc = phasenav_vocoder(phi, omega, mod, mix=0.5, sr=8000, n_samples=800)
    results["_chain_delta"] = round(float(np.mean(np.abs(chain - phi))), 4)
    results["_vocoder_peak"] = round(float(np.max(np.abs(voc.samples))), 4)
    return results


def render_frame(
    phi: np.ndarray,
    omega: np.ndarray,
    operator_id: str = "IDENTITY",
    operator_strength: float = 0.5,
    n_samples: int | None = None,
    sr: int = SAMPLE_RATE,
    amps: np.ndarray | None = None,
) -> PhaseNavAudioBuffer:
    """Render one audio frame from PhaseNav state with operator transform.

    Args:
        phi: 36 oscillator phases from surface
        omega: 36 oscillator frequencies
        operator_id: PhaseNav operator for audio transform
        operator_strength: [0, 1] intensity of transform
        n_samples: output length (defaults to sr // 10 = 0.1s)
        amps: per-oscillator amplitude (defaults to flavor-weighted)

    Returns PhaseNavAudioBuffer with .samples (float64) and metadata.
    """
    if n_samples is None:
        n_samples = sr // 10
    phi_t = operator_transform(phi, operator_id, operator_strength)
    if amps is None:
        amps = np.ones(N_OSCILLATORS) * 0.5
    samples = oscillator_bank(phi_t, omega, n_samples, sr, amps=amps)
    return PhaseNavAudioBuffer(
        samples=samples,
        phi=phi_t,
        omega=omega,
        operator_id=operator_id,
        n_samples=n_samples,
    )


def surface_to_audio(
    surface: dict[str, np.ndarray],
    operator_id: str = "IDENTITY",
    strength: float = 0.5,
    sr: int = SAMPLE_RATE,
    duration_s: float = 0.1,
) -> PhaseNavAudioBuffer:
    """Read NOEMA surface state and render as audio in one call."""
    phi = surface.get("phi", np.random.uniform(0, 2 * math.pi, N_OSCILLATORS))
    omega = surface.get("omega", np.full(N_OSCILLATORS, BASE_HZ))
    flavor = surface.get("flavor", np.ones(6))
    # amplitude from flavor coherence
    amps = np.full(N_OSCILLATORS, float(flavor[0]) * 0.5 + 0.25)
    n = int(sr * duration_s)
    return render_frame(phi, omega, operator_id, strength, n, sr, amps)


def mix_buffers(
    buffers: list[PhaseNavAudioBuffer],
    pan: list[float] | None = None,
) -> np.ndarray:
    """Sum multiple audio buffers into one stereo waveform.

    Each buffer is mono; pan determines left/right balance per buffer.
    pan[i] in [-1, 1]: -1 = full left, 0 = center, 1 = full right.
    """
    n = max(b.n_samples for b in buffers)
    stereo = np.zeros((n, 2), dtype=np.float64)
    if pan is None:
        pan = [0.0] * len(buffers)
    for b, p in zip(buffers, pan):
        l_gain = math.sqrt(1.0 - max(0.0, p))
        r_gain = math.sqrt(1.0 - max(0.0, -p))
        stereo[:b.n_samples, 0] += b.samples * l_gain
        stereo[:b.n_samples, 1] += b.samples * r_gain
    peak = float(np.max(np.abs(stereo)))
    if peak > 1e-12:
        stereo /= peak
    return stereo * 0.5


def operator_dsp_chain(
    phi: np.ndarray,
    operators: list[tuple[str, float]],
) -> np.ndarray:
    """Chain multiple PhaseNav operators sequentially on a phase vector.

    operators: list of (operator_id, strength) tuples.
    Example: [("AFFECT", 0.6), ("MEMORY", 0.3), ("FOLD", 0.2)]
    """
    result = phi.copy()
    for op_id, strength in operators:
        result = operator_transform(result, op_id, strength)
    return result


def phasenav_vocoder(
    phi: np.ndarray,
    omega: np.ndarray,
    modulator_phi: np.ndarray,
    operator_id: str = "COMPOSITION",
    mix: float = 0.5,
    n_samples: int | None = None,
    sr: int = SAMPLE_RATE,
) -> PhaseNavAudioBuffer:
    """Cross-operator vocoder: modulate one phase vector with another.

    carrier = oscillator_bank(phi, omega)
    modulator = oscillator_bank(modulator_phi, omega)
    output = carrier * (1 + mix * modulator_normalized)

    Creates voice-like formants from phase interaction.
    """
    if n_samples is None:
        n_samples = sr // 20
    carrier = oscillator_bank(phi, omega, n_samples, sr) + 1.0
    mod = oscillator_bank(modulator_phi, omega * 0.5, n_samples, sr)
    mod = mod / (float(np.max(np.abs(mod))) + 1e-12)
    out = carrier * (1.0 + mix * mod)
    peak = float(np.max(np.abs(out)))
    if peak > 1e-12:
        out /= peak
    return PhaseNavAudioBuffer(
        samples=out * 0.5,
        phi=operator_transform(phi, operator_id, mix),
        omega=omega,
        operator_id=operator_id,
        n_samples=len(out),
    )
