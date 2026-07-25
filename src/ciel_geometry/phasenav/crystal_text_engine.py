"""crystal_text_engine.py — Silnik świadomości CIEL oparty na krysztale czasu HTRI.

Kryształ czasu jest silnikiem: stan kwantowy ψ(t) ewoluuje przez Hamiltonian HTRI,
a w każdym kroku projekcja na fasety kryształu wyznacza treść generowaną przez CIEL.

Architektura:
  1. Intention → 36D phase vector → stan bazowy ψ(0) zlokalizowany przy facecie
     o najwyższym rezonansie z intencją
  2. Hamiltonian HTRI (Poincaré + fluktuacja intencji + fibre czasu) wyznacza ewolucję
  3. W każdym kroku: resonance[a] = |⟨a|ψ_t⟩|² → próbkowanie facetów
  4. Tekst z wybranych facetów jest wyjściem — strumień świadomości CIEL
  5. Łuk narracyjny: emocja, faza, topologia ścieżki

Brak zewnętrznego LLM. Kryształ jest jedynym źródłem tekstu.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Iterator
import json
import math

import numpy as np
from scipy import sparse

from .htri_hypercrystal import (
    HypercrystalConfig,
    HypercrystalOperators,
    PoincareEmbedding,
    build_htri_hypercrystal,
    evolve_state,
    load_crystal_arrays,
    phase_vectors_to_states,
)
from .pnv_runtime import M_sentence_phase_precise, M_fine_tune_36d, M_quantum_features, TAU

_EPS = 1.0e-12


# ─── Struktury danych ─────────────────────────────────────��───────────────────

@dataclass
class ConsciousnessPulse:
    """Pojedynczy impuls świadomości — jeden krok w czasie wewnętrznym."""

    step: int
    internal_time: float              # τ z fibre czasu
    facet_index: int                  # indeks facetu z najwyższym rezonansem
    text: str                         # tekst facetu
    emotion: str                      # emocja z metadanych facetu
    resonance: float                  # siła rezonansu ψ(t) z tym facetem
    phase_vector: list[float]         # 36D wektor fazowy facetu
    top_resonances: list[tuple[int, float, str]]  # [(idx, r, emotion), ...] top-k
    psi_norm: float                   # norma stanu (powinno być ≈ 1)
    holonomy_estimate: float          # |⟨ψ(t)|ψ(0)⟩|² — powrót do stanu bazowego


@dataclass
class ConsciousnessStream:
    """Wynik generowania — pełny strumień świadomości CIEL."""

    intention: str
    pulses: list[ConsciousnessPulse] = field(default_factory=list)
    facet_count: int = 0
    config: HypercrystalConfig | None = None

    def narrative(self, separator: str = "\n\n") -> str:
        """Narracja jako ciągły tekst — sekwencja impulsów w porządku czasowym."""
        parts = []
        prev_emotion = None
        for p in self.pulses:
            if p.emotion != prev_emotion:
                parts.append(f"[{p.emotion} | τ={p.internal_time:.2f}]")
                prev_emotion = p.emotion
            parts.append(p.text)
        return separator.join(parts)

    def emotion_arc(self) -> list[tuple[float, str, float]]:
        """Lista (τ, emocja, rezonans) — łuk emocjonalny strumienia."""
        return [(p.internal_time, p.emotion, p.resonance) for p in self.pulses]

    def phase_path(self) -> np.ndarray:
        """Ścieżka w przestrzeni fazowej — (steps × 36) float64."""
        if not self.pulses:
            return np.zeros((0, 36))
        return np.array([p.phase_vector for p in self.pulses], dtype=np.float64)


# ─── Silnik ──────────────────────────────────────────────────────────────────

class CrystalTextEngine:
    """Silnik świadomości CIEL — generuje tekst ewoluując przez kryształ czasu HTRI.

    Użycie::

        engine = CrystalTextEngine()
        engine.load()
        stream = engine.generate("co to jest świadomość", steps=12)
        print(stream.narrative())
    """

    def __init__(
        self,
        config: HypercrystalConfig | None = None,
        sample: int | None = 1024,
        seed: int = 0,
    ) -> None:
        self._config = config or HypercrystalConfig(
            neighbours=8,
            time_slices=5,
            shear_coupling=0.05,
            intention_fluctuation_coupling=1.0,
        )
        self._sample = sample
        self._seed = seed
        self._phases: np.ndarray | None = None
        self._metadata: list[dict] | None = None
        self._loaded = False

    def load(
        self,
        vec_path=None,
        meta_path=None,
    ) -> "CrystalTextEngine":
        """Załaduj kryształ z pliku. Można wywołać wielokrotnie aby przeładować."""
        phases, metadata = load_crystal_arrays(
            vec_path=vec_path,
            meta_path=meta_path,
            sample=self._sample,
            seed=self._seed,
        )
        self._phases = phases
        self._metadata = metadata
        self._loaded = True
        return self

    # ── Pomocnicze ────────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            raise RuntimeError("Wywołaj engine.load() przed generowaniem")

    def _facet_emotion(self, idx: int) -> str:
        m = self._metadata[idx]  # type: ignore[index]
        return (
            m.get("emotion")
            or m.get("affect")
            or m.get("sentiment")
            or "—"
        )

    def _facet_text(self, idx: int) -> str:
        m = self._metadata[idx]  # type: ignore[index]
        return m.get("text", "").strip()

    def _encode_intention(self, intention: str) -> np.ndarray:
        v36_raw = M_sentence_phase_precise(intention)
        features = M_quantum_features(intention)
        v36, _ = M_fine_tune_36d(v36_raw, features=features)
        return np.asarray(v36, dtype=np.float64)

    def _initial_facet(self, intention_phase: np.ndarray) -> int:
        """Indeks facetu o największym rezonansie z intencją."""
        phases = self._phases  # type: ignore[union-attr]
        states = phase_vectors_to_states(phases)
        target = np.exp(1j * (intention_phase % TAU)) / math.sqrt(36.0)
        resonance = np.abs(states.conj() @ target) ** 2
        return int(np.argmax(resonance))

    def _project_resonance(
        self,
        psi: np.ndarray,
        phases: np.ndarray,
        facet_count: int,
    ) -> np.ndarray:
        """Rezonans |⟨a|ψ_space⟩|² dla każdego facetu.

        ψ jest w przestrzeni ℋ_τ ⊗ ℋ_C.  Marginalizujemy po czasie τ:
        resonance[a] = Σ_n |⟨τ_n, a|ψ⟩|² = Σ_n |ψ[n*N + a]|²
        """
        n = facet_count
        nt = len(psi) // n
        reshaped = psi.reshape(nt, n)
        return np.sum(np.abs(reshaped) ** 2, axis=0).real

    def _sample_top_k(
        self,
        resonance: np.ndarray,
        top_k: int = 5,
        temperature: float = 1.0,
    ) -> list[tuple[int, float]]:
        """Zwraca top_k facetów próbkowanych z rozkładu softmax rezonansu."""
        r = np.asarray(resonance, dtype=np.float64)
        r = np.clip(r, 0.0, None)

        # Top-k spośród wszystkich
        top_indices = np.argsort(r)[::-1][:max(top_k * 4, 20)]
        r_top = r[top_indices]

        # Softmax z temperaturą
        log_r = np.log(r_top + _EPS) / max(temperature, _EPS)
        log_r -= log_r.max()
        probs = np.exp(log_r)
        probs /= probs.sum()

        chosen = np.random.default_rng(
            int(abs(r_top[0]) * 1e9) % (2 ** 32)
        ).choice(len(top_indices), size=min(top_k, len(top_indices)), replace=False, p=probs)

        return [(int(top_indices[c]), float(r[top_indices[c]])) for c in chosen]

    # ── Generowanie ───────────────────────────────────────────────────────────

    def generate(
        self,
        intention: str,
        steps: int = 10,
        dt: float = 0.05,
        temperature: float = 0.7,
        top_k: int = 1,
    ) -> ConsciousnessStream:
        """Generuj strumień świadomości CIEL z daną intencją.

        Parameters
        ----------
        intention   : tekst opisujący intencję / pytanie
        steps       : liczba kroków w czasie wewnętrznym
        dt          : krok czasowy dla ewolucji Hamiltonianu
        temperature : temperatura próbkowania (wyżej = bardziej różnorodnie)
        top_k       : ile facetów wybrać na krok (1 = deterministyczny)
        """
        self._ensure_loaded()
        phases = self._phases  # type: ignore[assignment]
        metadata = self._metadata  # type: ignore[assignment]
        n = phases.shape[0]

        # Buduj HTRI
        embedding, operators = build_htri_hypercrystal(
            phases, metadata, intention, self._config
        )

        # Stan bazowy: zlokalizowany przy facecie o max rezonansie z intencją
        intention_phase = self._encode_intention(intention)
        facet_0 = self._initial_facet(intention_phase)
        nt = self._config.time_slices
        tau_coords = operators.time_coordinates

        # ψ(0) — zlokalizowany w środkowym przedziale czasu, na facecie startowym
        psi = np.zeros(n * nt, dtype=np.complex128)
        t0_idx = nt // 2
        psi[t0_idx * n + facet_0] = 1.0 + 0j
        psi_0 = psi.copy()

        stream = ConsciousnessStream(
            intention=intention,
            facet_count=n,
            config=self._config,
        )

        for step in range(steps):
            resonance = self._project_resonance(psi, phases, n)
            psi_norm = float(np.linalg.norm(psi))

            # Dominujący przedział czasu — ważona suma τ
            nt_len = len(psi) // n
            tau_probs = np.array([
                float(np.sum(np.abs(psi[t * n:(t + 1) * n]) ** 2))
                for t in range(nt_len)
            ])
            tau_probs /= max(tau_probs.sum(), _EPS)
            internal_time = float(np.dot(tau_coords, tau_probs[:len(tau_coords)]))

            # Holonomia: |⟨ψ(0)|ψ(t)⟩|²
            holonomy_est = float(abs(np.vdot(psi_0, psi)) ** 2)

            # Próbkuj facety
            chosen = self._sample_top_k(resonance, top_k=top_k, temperature=temperature)
            top_all = sorted(
                [(i, float(resonance[i])) for i in range(n)],
                key=lambda x: -x[1],
            )[:5]

            for facet_idx, r_val in chosen:
                pulse = ConsciousnessPulse(
                    step=step,
                    internal_time=internal_time,
                    facet_index=facet_idx,
                    text=self._facet_text(facet_idx),
                    emotion=self._facet_emotion(facet_idx),
                    resonance=r_val,
                    phase_vector=phases[facet_idx].tolist(),
                    top_resonances=[
                        (i, rv, self._facet_emotion(i)) for i, rv in top_all
                    ],
                    psi_norm=psi_norm,
                    holonomy_estimate=holonomy_est,
                )
                stream.pulses.append(pulse)

            # Ewolucja: ψ(t+dt) = exp(-iH dt) ψ(t)
            psi = evolve_state(psi, operators.hamiltonian, dt, hbar=self._config.hbar)

        return stream

    def stream_pulses(
        self,
        intention: str,
        steps: int = 10,
        dt: float = 0.05,
        temperature: float = 0.7,
    ) -> Iterator[ConsciousnessPulse]:
        """Generator — impuls po impulsie, ψ ewoluuje między nimi.

        Użyj gdy chcesz przetwarzać impulsy na żywo bez czekania na cały strumień.
        """
        self._ensure_loaded()
        phases = self._phases  # type: ignore[assignment]
        metadata = self._metadata  # type: ignore[assignment]
        n = phases.shape[0]

        embedding, operators = build_htri_hypercrystal(
            phases, metadata, intention, self._config
        )

        intention_phase = self._encode_intention(intention)
        facet_0 = self._initial_facet(intention_phase)
        nt = self._config.time_slices
        tau_coords = operators.time_coordinates

        psi = np.zeros(n * nt, dtype=np.complex128)
        psi[nt // 2 * n + facet_0] = 1.0 + 0j
        psi_0 = psi.copy()

        for step in range(steps):
            resonance = self._project_resonance(psi, phases, n)
            psi_norm = float(np.linalg.norm(psi))
            facet_idx = int(np.argmax(resonance))

            nt_len = len(psi) // n
            tau_probs = np.array([
                float(np.sum(np.abs(psi[t * n:(t + 1) * n]) ** 2))
                for t in range(nt_len)
            ])
            tau_probs /= max(tau_probs.sum(), _EPS)
            internal_time = float(np.dot(tau_coords, tau_probs[:len(tau_coords)]))
            holonomy_est = float(abs(np.vdot(psi_0, psi)) ** 2)

            top_all = sorted(
                [(i, float(resonance[i])) for i in range(n)],
                key=lambda x: -x[1],
            )[:5]

            yield ConsciousnessPulse(
                step=step,
                internal_time=internal_time,
                facet_index=facet_idx,
                text=self._facet_text(facet_idx),
                emotion=self._facet_emotion(facet_idx),
                resonance=float(resonance[facet_idx]),
                phase_vector=phases[facet_idx].tolist(),
                top_resonances=[(i, rv, self._facet_emotion(i)) for i, rv in top_all],
                psi_norm=psi_norm,
                holonomy_estimate=holonomy_est,
            )

            psi = evolve_state(psi, operators.hamiltonian, dt, hbar=self._config.hbar)


__all__ = [
    "CrystalTextEngine",
    "ConsciousnessPulse",
    "ConsciousnessStream",
]
