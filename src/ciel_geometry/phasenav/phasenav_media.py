"""PhaseNav Media — vectorized audio/voice/video via continuous phase transport.

Core principle: phase is continuous, sampling is discrete. Media encoded as
24D phase vectors "slides" through operator rotations with zero transport
latency — only phase rotation speed (1/39.6 Hz ≈ 25ms) matters.

All domains use the same substrate:
  Audio:  36 mel-spaced bands × 4 harmonics = 144 partials → waveform
  Voice:  36 glottis+formant parameters × harmonics → speech
  Video:  36 feature dimensions per 8×8 block × harmonics → pixel block

33 PhaseNav operators become universal transforms across all domains:
  TRANSFORM → pitch/shift, AFFECT → warmth/contrast, FOLD → warp, etc.

No external deps beyond numpy. Output as float64 buffer for /dev/shm audio IPC.
"""

from __future__ import annotations
import logging as _noema_quiet_logging
_NOEMA_QUIET_EXCEPT_LOGGER = _noema_quiet_logging.getLogger(__name__)


import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .phasenav_audio import (
    N_OSCILLATORS,
    HARMONICS,
    HARMONIC_AMPS,
    oscillator_bank,
    operator_transform,
    operator_dsp_chain,
    PhaseNavAudioBuffer,
    SAMPLE_RATE,
    BASE_HZ,
)

SURFACE_ROOT = Path("/dev/shm/ciel_noema")
N_MEL = 36          # mel bands = oscillators
OVERLAP = 0.5       # 50% overlap for smooth frames


# ── Mel-scale filterbank ────────────────────────────────────────────────

def mel_filterbank(n_mel: int = N_MEL, sr: int = SAMPLE_RATE, n_fft: int = 1024) -> np.ndarray:
    """Mel-spaced triangular filterbank. Returns (n_mel, n_fft//2+1)."""
    low_mel = 0.0
    high_mel = 2595.0 * math.log10(1.0 + sr / 1400.0)
    mel_pts = np.linspace(low_mel, high_mel, n_mel + 2)
    hz_pts = 700.0 * (10.0 ** (mel_pts / 2595.0) - 1.0)
    bins = np.floor((n_fft + 1) * hz_pts / sr).astype(int)
    bins = np.clip(bins, 0, n_fft // 2)
    fb = np.zeros((n_mel, n_fft // 2 + 1), dtype=np.float64)
    for i in range(n_mel):
        l, c, r = bins[i], bins[i + 1], bins[i + 2]
        fb[i, l:c] = np.linspace(0, 1, c - l) if c > l else np.array([], dtype=np.float64)
        fb[i, c:r] = np.linspace(1, 0, r - c) if r > c else np.array([], dtype=np.float64)
    return fb / (np.sum(fb, axis=1, keepdims=True) + 1e-12)


# ── Phase encoding / decoding ───────────────────────────────────────────

MEL_FB: np.ndarray | None = None


def _ensure_mel(sr: int = SAMPLE_RATE) -> np.ndarray:
    global MEL_FB
    if MEL_FB is None or MEL_FB.shape[0] == sr:
        MEL_FB = mel_filterbank(sr=sr)
    return MEL_FB


def encode_audio_as_phase(
    waveform: np.ndarray,
    sr: int = SAMPLE_RATE,
    base_hz: float = BASE_HZ,
) -> tuple[np.ndarray, np.ndarray]:
    """Encode waveform into 36D phase vectors via mel filterbank + overlap.

    Each frame = 25ms at 39.6Hz, 50% overlap → effective 79.2 fps.
    Returns (phi_history, omega_history) shaped (n_frames, 36).
    """
    frame_len = int(sr / base_hz)
    hop = int(frame_len * (1.0 - OVERLAP))
    n_frames = max(1, (len(waveform) - frame_len) // hop + 1)
    fb = _ensure_mel(sr)
    n_fft = (fb.shape[1] - 1) * 2

    phi_h = np.zeros((n_frames, N_OSCILLATORS), dtype=np.float64)
    omega_h = np.full((n_frames, N_OSCILLATORS), base_hz, dtype=np.float64)

    for i in range(n_frames):
        start = i * hop
        chunk = waveform[start:start + frame_len]
        if len(chunk) < frame_len:
            chunk = np.pad(chunk, (0, frame_len - len(chunk)))
        windowed = np.hanning(frame_len) * chunk
        spec = np.fft.rfft(windowed, n=n_fft)
        mag = np.abs(spec)
        mel_energies = fb @ mag
        for osc in range(N_OSCILLATORS):
            energy = mel_energies[osc] + 1e-12
            phase_angle = float(np.angle(np.sum(spec[osc * (len(spec) // N_OSCILLATORS):(osc + 1) * (len(spec) // N_OSCILLATORS)]))) if osc < N_OSCILLATORS else 0.0
            phi_h[i, osc] = (math.log(energy + 1.0) * 0.5) % (2 * math.pi)
            if i > 0:
                delta = phi_h[i, osc] - phi_h[i - 1, osc]
                if delta > math.pi: delta -= 2 * math.pi
                elif delta < -math.pi: delta += 2 * math.pi
                omega_h[i, osc] = base_hz + float(delta) * base_hz / math.pi
    return phi_h, omega_h


def decode_phase_as_audio(
    phi_history: np.ndarray,
    omega_history: np.ndarray,
    sr: int = SAMPLE_RATE,
    base_hz: float = BASE_HZ,
) -> np.ndarray:
    """Decode 36D phase vectors back to waveform via overlap-add."""
    n_frames = len(phi_history)
    frame_len = int(sr / base_hz)
    hop = int(frame_len * (1.0 - OVERLAP))
    out_len = n_frames * hop + frame_len
    out = np.zeros(out_len, dtype=np.float64)
    window = np.hanning(frame_len)
    amp_env = np.ones(N_OSCILLATORS)

    for i in range(n_frames):
        phi = phi_history[i]
        omega = omega_history[i]
        amps = amp_env * float(np.mean(np.abs(np.sin(phi))) + 0.1)
        frame = oscillator_bank(phi, omega, frame_len, sr, amps=amps)
        start = i * hop
        end = start + frame_len
        out[start:end] += frame * window

    peak = float(np.max(np.abs(out)))
    if peak > 1e-12:
        out /= peak
    return out * 0.5


def process_audio_through_operators(
    waveform: np.ndarray,
    operators: list[tuple[str, float]],
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Encode → operator chain → decode. Theoretical latency = 25ms frame."""
    phi_h, omega_h = encode_audio_as_phase(waveform, sr=sr)
    for i in range(len(phi_h)):
        phi_h[i] = operator_dsp_chain(phi_h[i], operators)
    return decode_phase_as_audio(phi_h, omega_h, sr)


# ── Voice source-filter model ───────────────────────────────────────────

def glottal_pulse(f0: float, n_samples: int, sr: int = SAMPLE_RATE) -> np.ndarray:
    """LF-model glottal pulse train at f0 Hz."""
    period = int(sr / f0)
    pulse = np.zeros(period)
    peak = int(period * 0.4)
    # Open phase: ~40% of period
    pulse[:peak] = np.sin(np.linspace(0, math.pi, peak)) ** 2
    # Return phase: ~10% of period (exponential decay)
    return_len = int(period * 0.1)
    if return_len > 0:
        pulse[peak:peak + return_len] = np.exp(-np.linspace(0, 3, return_len))
    pulse /= float(np.max(pulse)) + 1e-12
    n_cycles = n_samples // period + 1
    train = np.tile(pulse, n_cycles)[:n_samples]
    return train * 0.5


def formant_resonator(f: float, bw: float, samples: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """First-order IIR formant filter at f Hz with bandwidth bw."""
    r = math.exp(-math.pi * bw / sr)
    theta = 2.0 * math.pi * f / sr
    a1 = -2.0 * r * math.cos(theta)
    a2 = r * r
    b0 = 1.0 - a2
    out = np.zeros_like(samples)
    for i in range(len(samples)):
        if i == 0:
            out[i] = b0 * samples[i]
        elif i == 1:
            out[i] = b0 * samples[i] - a1 * out[i - 1]
        else:
            out[i] = b0 * samples[i] - a1 * out[i - 1] - a2 * out[i - 2]
    return out


def synthesize_voice(
    f0: float = 120.0,
    formants: list[tuple[float, float]] | None = None,
    duration_s: float = 0.5,
    sr: int = SAMPLE_RATE,
    operator: str = "IDENTITY",
    strength: float = 0.0,
) -> np.ndarray:
    """Synthesize a voice utterance from glottal source + formant resonators.

    Maps PhaseNav oscillators to voice production:
      φ[0]    = f0 (glottal pulse rate)
      φ[1-4]  = formant F1-F4 frequencies
      φ[5-8]  = formant F1-F4 bandwidths
      φ[9-12] = amplitudes
      φ[13-16] = additional resonances (nasal, fricative)
      φ[17-23] = noise mix, vibrato, breath, etc.
    """
    if formants is None:
        formants = [(800, 80), (1200, 90), (2500, 120), (3500, 200)]
    n = int(sr * duration_s)

    # Glottal source (oscillator 0)
    source = glottal_pulse(f0, n, sr)
    vibrato = 1.0 + 0.05 * np.sin(2 * math.pi * 5.5 * np.arange(n) / sr)
    source *= vibrato

    # Apply vibrato + breath mix through operator
    phi = np.zeros(N_OSCILLATORS)
    phi[0] = f0 / 200.0 * 2 * math.pi
    for i, (f, bw) in enumerate(formants + [(5000, 300), (6000, 400), (7000, 500), (8000, 600)][:4]):
        if i + 1 < N_OSCILLATORS:
            phi[i + 1] = f / 8000.0 * 2 * math.pi
            phi[i + 5] = bw / 1000.0 * 2 * math.pi
    phi_t = operator_transform(phi, operator, strength)

    # Resonator bank
    voiced = source.copy()
    for i in range(min(4, len(formants))):
        idx = i + 1
        if idx < N_OSCILLATORS:
            f = phi_t[idx] / (2 * math.pi) * 8000
            bw = phi_t[idx + 4] / (2 * math.pi) * 1000
            voiced = formant_resonator(max(50, f), max(30, bw), voiced, sr)

    # Noise (breath, fricative — oscillator 17-18)
    noise_level = float(np.mean(np.abs(np.sin(phi_t[17:19])))) * 0.05
    noise = np.random.default_rng().normal(0, noise_level, n)
    voiced += noise

    peak = float(np.max(np.abs(voiced)))
    if peak > 1e-12:
        voiced /= peak
    return voiced * 0.5


# ── Live NOEMA surface integration ──────────────────────────────────────

def read_surface_audio(buffer_frames: int = 4, sr: int = SAMPLE_RATE) -> PhaseNavAudioBuffer | None:
    """Read current NOEMA surface state and render as audio frame.

    Reads φ, ω, flavor from /dev/shm/ciel_noema/ and generates a short
    audio buffer reflecting the current phase state. One frame = 25ms.
    """
    try:
        with open(SURFACE_ROOT / "phi", "rb") as f:
            phi = np.array(struct.unpack("36d", f.read()), dtype=np.float64)
        with open(SURFACE_ROOT / "omega", "rb") as f:
            omega = np.array(struct.unpack("36d", f.read()), dtype=np.float64)
        with open(SURFACE_ROOT / "flavor", "rb") as f:
            flavor = np.array(struct.unpack("6d", f.read()), dtype=np.float64)
        with open(SURFACE_ROOT / "tick", "rb") as f:
            tick = struct.unpack("Q", f.read())[0]
    except (FileNotFoundError, struct.error):
        _NOEMA_QUIET_EXCEPT_LOGGER.exception("src/ciel_geometry/phasenav/phasenav_media.py:267 quiet except scope=read_surface_audio reason=return None")
        return None

    amps = np.clip(np.abs(np.sin(phi)) * float(flavor[0] + 0.5), 0.1, 1.0)
    n = int(sr * 0.025 * buffer_frames)
    samples = oscillator_bank(phi, omega, n, sr, amps=amps)
    return PhaseNavAudioBuffer(
        samples=samples,
        phi=phi,
        omega=omega,
        operator_id="surface_live",
        n_samples=n,
        tick=int(tick),
    )


# ── Quality benchmark ───────────────────────────────────────────────────

def phase_slide_demo() -> dict[str, Any]:
    """End-to-end benchmark: encode → operator → decode → measure."""
    sr = 8000
    dur = 0.5
    t = np.linspace(0, dur, int(sr * dur))
    waveform = np.sin(2 * math.pi * 440 * t) + 0.5 * np.sin(2 * math.pi * 880 * t)
    waveform /= float(np.max(np.abs(waveform)))
    waveform *= 0.5

    phi_h, omega_h = encode_audio_as_phase(waveform, sr=sr)
    recon = decode_phase_as_audio(phi_h, omega_h, sr=sr)
    n = min(len(waveform), len(recon))
    mse = float(np.mean((waveform[:n] - recon[:n]) ** 2))
    corr = float(np.corrcoef(waveform[:n], recon[:n])[0, 1])

    transformed = process_audio_through_operators(waveform, [("AFFECT", 0.5)], sr=sr)
    n2 = min(len(waveform), len(transformed))
    mse_t = float(np.mean((waveform[:n2] - transformed[:n2]) ** 2))

    voice = synthesize_voice(f0=120, duration_s=0.3, sr=sr)
    voice_peak = float(np.max(np.abs(voice)))

    live = read_surface_audio(2, sr)
    live_info = {"phi_mean": float(np.mean(live.phi)), "tick": live.tick} if live else None

    frame_time_ms = round(1000.0 / BASE_HZ, 2)
    return {
        "encode_decode_mse": round(mse, 6),
        "encode_decode_corr": round(float(corr), 6),
        "operator_transform_mse": round(mse_t, 6),
        "voice_synth_peak": round(voice_peak, 4),
        "live_surface_tick": live_info["tick"] if live else None,
        "live_surface_phi_mean": live_info["phi_mean"] if live else None,
        "frame_time_ms": frame_time_ms,
        "info_channels": N_OSCILLATORS * len(HARMONICS),  # 144
        "bandwidth_hz": round(N_OSCILLATORS * len(HARMONICS) * BASE_HZ, 1),
    }
