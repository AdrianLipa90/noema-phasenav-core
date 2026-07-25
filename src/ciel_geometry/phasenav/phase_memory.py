"""phase_memory.py — PhaseMemoryHypercrystal 36D.

Pamięć fazowa jako hiperkryształ przestrzeni 36D PhaseNav.

Kodowanie: M_sentence_phase() + M_fine_tune_36d() (Collatz-seeded phasors,
nie SHA256 — poprawna geometria fazowa).

Retrieval: mean angular distance w 36D, przez numpy batch.
          Rankowanie przez M_x(V) = χ·T_μνλ·O^μ·C^ν·V^λ (skalar znaczenia).

Pola tensorowe (Valov & Ahmad, Tensor of Thought):
  kappa_i      — κ_I(x): krzywizna informacyjna = mean dist do k sąsiadów
                 κ_I > 1.45 → strefa kollapsu (brak struktury pamięci)
                 κ_I < 1.20 → gęsty atraktor (stabilna faza)
  t_score      — T_μνλ skalar: phase_R² / κ_I + |soul| * 0.5
                 wysoki → silny facet tensora świadomości
  memory_density — ρ_M: liczba sąsiadów w promieniu BASIN_RADIUS (4·η_M) / N

Skalar znaczenia M_x(V):
  χ           = ethics (etyczny gate)
  O^μ         = soul_obs (obserwator — soul z ciel_state)
  C^ν         = κ_I⁻¹  (gęstość kontekstu)
  V^λ         = query  (wektor zapytania 36D)
  φ[12]       = soul sektor kryształu (LIE4 double-cover SU(2))
  berry_corr  = 1/(1+|A_berry(Q,V)|·0.5) — korekta holonomiczna krzywizny

Zapis: .npy (wektory 36D) + .jsonl (metadane facetów).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

try:
    from .pnv_runtime import (
        M_sentence_phase, M_sentence_phase_trajectory,
        M_quantum_features, M_fine_tune_36d,
        M_36d_order_parameter, TAU, PI, KAPPA,
    )
except ImportError:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from pnv_runtime import (
        M_sentence_phase, M_sentence_phase_trajectory,
        M_quantum_features, M_fine_tune_36d,
        M_36d_order_parameter, TAU, PI, KAPPA,
    )

# η_M = n·KAPPA — próg rozróżnialności semantycznej (Language Derived from Meaning)
# Dwa facety bliżej niż ETA_M_36D leżą w tym samym basenie semantycznym B_i.
# ETA_M_36D = 36 · ln(2)/(24π) ≈ 0.331
# Sąsiedztwo basenu: BASIN_RADIUS = 4 · ETA_M_36D ≈ 1.324
ETA_M_36D    = 36.0 * KAPPA          # ≈ 0.331 — basin distinguishability
BASIN_RADIUS = 4.0  * ETA_M_36D     # ≈ 1.324 — basin neighbourhood

# ── LIE4 sector weights (op#48: Lorentz/Intention/Soul mapping) ──────────────
# φ[0-5]  → Lorentz sector L_μν  (SO(3,1): 3 boosty + 3 rotacje)
# φ[6-11] → Intention sector T_a (wektory intencji)
# φ[12]   → Soul central S       (element centralny, double-cover SU(2))
# φ[13-35]→ pozostałe wymiary    (uniformne)
_LIE4_WEIGHTS = np.array(
    [2.0] * 6 +   # Lorentz
    [2.0] * 6 +   # Intention
    [1.5]     +   # Soul (double-cover)
    [1.0] * 23,   # reszta
    dtype=np.float64,
)
_LIE4_WEIGHT_SUM = float(_LIE4_WEIGHTS.sum())  # = 48.5

# Ścieżki domyślne kryształu
_STATE_DIR = Path(__file__).parent / "data"
CRYSTAL_VEC_PATH  = _STATE_DIR / "phase_crystal_36d.npy"
CRYSTAL_META_PATH = _STATE_DIR / "phase_crystal_meta.jsonl"

# Próg angular distance dla trafienia w [0, π].
# M_sentence_phase() generuje wektory w całym [0, 2π]^36 — oczekiwana
# odległość między losowymi wektorami ≈ π/2 ≈ 1.571. Dobre trafienia
# leżą w dolnym kwartylu obserwowanego zakresu (~1.2..2.0).
# Używamy progu względnego: pobieramy top_k i filtrujemy przez max_dist.
DEFAULT_MAX_DIST = 1.45   # empiryczne: dolny ~25% zakresu dystrybucji


class PhaseMemoryHypercrystal:
    """Hiperkryształ pamięci fazowej 36D.

    Każdy facet kryształu = (v36, metadata) gdzie:
      v36      — 36D wektor fazowy z M_sentence_phase + M_fine_tune_36d
      metadata — tekst źródłowy, emocja, soul, ethics, source, tags

    API:
      .encode(text)          → (v36: list[float], info: dict)
      .add(text, **kw)       → dodaje facet
      .retrieve(query, ...)  → lista najbliższych facetów
      .save()                → zapis .npy + .jsonl
      .load()                → wczytanie z .npy + .jsonl
      len(crystal)           → liczba facetów
    """

    def __init__(
        self,
        vec_path: Path | str | None = None,
        meta_path: Path | str | None = None,
    ) -> None:
        self._vec_path  = Path(vec_path)  if vec_path  else CRYSTAL_VEC_PATH
        self._meta_path = Path(meta_path) if meta_path else CRYSTAL_META_PATH
        self._vecs: list[list[float]] = []
        self._meta: list[dict] = []
        self._vecs_np: np.ndarray | None = None   # lazy cache

    # ── Kodowanie ────────────────────────────────────────────────────────────

    def encode(self, text: str) -> tuple[list[float], dict]:
        """Tekst → (v36, info) przez silniki fazowe.

        Collatz-seeded phasor superposition (M_sentence_phase),
        następnie modulacje kwantowe (M_fine_tune_36d).
        """
        v36_raw  = M_sentence_phase(text)
        features = M_quantum_features(text)
        v36, mods = M_fine_tune_36d(v36_raw, features=features)
        return v36, {"features": features, "modulations": mods}

    # ── Dodawanie facetów ─────────────────────────────────────────────────────

    def add(
        self,
        text: str,
        source: str = "",
        emotion: str = "",
        soul: float = 0.0,
        ethics: float = 0.0,
        phase_R: float = 0.0,
        tags: list[str] | None = None,
        extra: dict | None = None,
    ) -> int:
        """Dodaj facet do kryształu. Zwraca indeks."""
        v36, enc = self.encode(text)
        idx = len(self._vecs)
        self._vecs.append(v36)
        self._meta.append({
            "text":     text[:500],
            "source":   source,
            "emotion":  emotion,
            "soul":     round(soul, 6),
            "ethics":   round(ethics, 6),
            "phase_R":  round(phase_R, 6),
            "tags":     tags or [],
            "features": enc["features"],
            "mods":     enc["modulations"],
            **(extra or {}),
        })
        self._vecs_np = None   # invalidate cache
        return idx

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_dist: float | None = DEFAULT_MAX_DIST,
        relative_filter: bool = True,
        weighted: bool = True,
        sectored: bool = True,
        meaning_score: bool = True,
        ciel_state: dict | None = None,
    ) -> list[dict]:
        """Wyszukaj top_k facetów w przestrzeni 36D przez angular distance.

        Zwraca listę {distance, m_score?, text, source, emotion, ...}.

        relative_filter=True: odrzuca trafienia dalej niż best_dist * 1.30.
        max_dist=None → bez progu absolutnego.
        meaning_score=True: rankuje przez M_x(V) = χ·T·O·C·V (skalar znaczenia).
          Wymaga t_score/kappa_i w metadanych (po compute_tensor_fields).
          Fallback: dist / (1 + t_score*0.4) gdy weighted=True, else dist.
        ciel_state: słownik z 'soul', 'ethics' (O^μ obserwator).
        """
        if not self._vecs:
            return []

        q36, _ = self.encode(query)
        dists = (
            self._batch_angular_dist_sectored(q36)
            if sectored else
            self._batch_angular_dist(q36)
        )

        if max_dist is not None:
            idxs = np.where(dists <= max_dist)[0]
        else:
            idxs = np.arange(len(dists))

        if len(idxs) == 0:
            return []

        # Ranking: M_x(V) skalar znaczenia → weighted dist → raw dist
        has_tensor = self._meta and "t_score" in self._meta[0]
        if meaning_score and has_tensor:
            m_sc    = self._scalar_of_meaning(dists, ciel_state, q36=q36)
            eff_key = -m_sc[idxs]   # negacja: wyższy M_score = lepszy trafienie
        elif weighted and has_tensor:
            t_scores = np.array(
                [self._meta[i].get("t_score", 0.0) for i in idxs], dtype=np.float64
            )
            eff_key = dists[idxs] / (1.0 + t_scores * 0.4)
        else:
            eff_key = dists[idxs]

        sorted_local = np.argsort(eff_key)
        sorted_idxs  = idxs[sorted_local]
        best_dist    = float(dists[sorted_idxs[0]])

        if relative_filter and len(sorted_idxs) > 1:
            rel_cut     = best_dist * 1.30
            sorted_idxs = sorted_idxs[dists[sorted_idxs] <= rel_cut]

        sorted_idxs = sorted_idxs[:top_k]
        m_sc_all = self._scalar_of_meaning(dists, ciel_state, q36=q36) if meaning_score and has_tensor else None
        results = []
        for i in sorted_idxs:
            entry = {"distance": float(dists[i]), **self._meta[i]}
            if m_sc_all is not None:
                entry["m_score"] = round(float(m_sc_all[i]), 6)
            results.append(entry)
        return results

    def retrieve_raw(
        self,
        q36: list[float],
        top_k: int = 5,
        max_dist: float | None = DEFAULT_MAX_DIST,
        relative_filter: bool = True,
        weighted: bool = True,
        sectored: bool = True,
        meaning_score: bool = True,
        ciel_state: dict | None = None,
    ) -> list[dict]:
        """Wariant przyjmujący gotowy wektor 36D (bez kodowania query).

        Parametry meaning_score i ciel_state identyczne jak retrieve().
        """
        if not self._vecs:
            return []

        dists = (
            self._batch_angular_dist_sectored(q36)
            if sectored else
            self._batch_angular_dist(q36)
        )

        if max_dist is not None:
            idxs = np.where(dists <= max_dist)[0]
        else:
            idxs = np.arange(len(dists))

        if len(idxs) == 0:
            return []

        has_tensor = self._meta and "t_score" in self._meta[0]
        if meaning_score and has_tensor:
            m_sc    = self._scalar_of_meaning(dists, ciel_state, q36=q36)
            eff_key = -m_sc[idxs]
        elif weighted and has_tensor:
            t_scores = np.array(
                [self._meta[i].get("t_score", 0.0) for i in idxs], dtype=np.float64
            )
            eff_key = dists[idxs] / (1.0 + t_scores * 0.4)
        else:
            eff_key = dists[idxs]

        sorted_local = np.argsort(eff_key)
        sorted_idxs  = idxs[sorted_local]
        best_dist    = float(dists[sorted_idxs[0]])

        if relative_filter and len(sorted_idxs) > 1:
            rel_cut     = best_dist * 1.30
            sorted_idxs = sorted_idxs[dists[sorted_idxs] <= rel_cut]

        sorted_idxs = sorted_idxs[:top_k]
        m_sc_all = self._scalar_of_meaning(dists, ciel_state, q36=q36) if meaning_score and has_tensor else None
        results = []
        for i in sorted_idxs:
            entry = {"distance": float(dists[i]), **self._meta[i]}
            if m_sc_all is not None:
                entry["m_score"] = round(float(m_sc_all[i]), 6)
            results.append(entry)
        return results

    def _batch_angular_dist(self, q36: list[float]) -> np.ndarray:
        """Mean angular distance kryształ→query w [0, π] dla każdego facetu."""
        vecs = self._get_vecs_np()
        q    = np.array(q36, dtype=np.float64)
        delta = np.abs(vecs - q[None, :])
        delta = np.minimum(delta, 2.0 * math.pi - delta)
        return delta.mean(axis=1)

    def _batch_angular_dist_sectored(self, q36: list[float]) -> np.ndarray:
        """Sektor-ważona angular distance (LIE4 op#48 mapping).

        φ[0-5]  = Lorentz L_μν  → waga 2.0
        φ[6-11] = Intention T_a → waga 2.0
        φ[12]   = Soul S        → waga 1.5 (double-cover SU(2))
        φ[13-35]= pozostałe     → waga 1.0

        Normalizacja: efektywna odległość ∈ [0, π] (ten sam zakres co mean).
        """
        vecs = self._get_vecs_np()
        q    = np.array(q36, dtype=np.float64)
        delta = np.abs(vecs - q[None, :])
        delta = np.minimum(delta, 2.0 * math.pi - delta)
        return (delta * _LIE4_WEIGHTS).sum(axis=1) / _LIE4_WEIGHT_SUM

    def retrieve_trajectory(
        self,
        query: str,
        top_k: int = 5,
        max_dist: float | None = DEFAULT_MAX_DIST,
        ciel_state: dict | None = None,
    ) -> dict:
        """Retrieval przez sukcesywne zwężanie Ω_k (zdanie = trajektoria znaczenia).

        Implementacja: Ω_0 ⊃ Ω_1 ⊃ ... ⊃ Ω_n
        Każde słowo query zwęża zbiór kandydatów — dokładnie jak odbiornik
        sukcesywnie zawęża przestrzeń interpretacji przy odbiorze zdania.

        Zwraca:
          results     — top_k facetów z finalnego Ω_n (jako retrieve())
          holonomy    — Berry holonomia wzdłuż trajektorii query (spójność zdania)
          trajectory_len — liczba kroków trajektorii (= liczba słów)
          omega_sizes — lista |Ω_k| po każdym słowie (jak szybko zdanie zawęża)
        """
        if not self._vecs:
            return {"results": [], "holonomy": 0.0, "trajectory_len": 0, "omega_sizes": []}

        v_final, trajectory, holonomy = M_sentence_phase_trajectory(query)

        # Zbiór kandydatów: Ω_0 = pełny kryształ (wszystkie indeksy)
        candidate_mask = np.ones(len(self._vecs), dtype=bool)

        vecs_np = self._get_vecs_np()
        omega_sizes: list[int] = []

        for v_k in trajectory:
            q_np = np.array(v_k, dtype=np.float64)
            # Angular distance od V_k do wszystkich facetów w Ω_{k-1}
            delta = np.abs(vecs_np - q_np[None, :])
            delta = np.minimum(delta, 2.0 * math.pi - delta)
            dists_k = (delta * _LIE4_WEIGHTS).sum(axis=1) / _LIE4_WEIGHT_SUM

            # Zwężenie: zachowaj tylko kandydatów w BASIN_RADIUS od V_k
            within = dists_k <= BASIN_RADIUS
            new_mask = candidate_mask & within

            # Zabezpieczenie: jeśli Ω_{k+1} jest puste, zatrzymaj zwężanie
            if new_mask.sum() > 0:
                candidate_mask = new_mask
            omega_sizes.append(int(candidate_mask.sum()))

        # Finalne Ω_n → ranking przez M_score z holonomiczną korekcją
        final_idxs = np.where(candidate_mask)[0]
        if len(final_idxs) == 0:
            # Fallback: standard retrieve z finalnym wektorem
            results = self.retrieve(query, top_k=top_k, max_dist=max_dist, ciel_state=ciel_state)
        else:
            q36 = v_final
            dists_all = self._batch_angular_dist_sectored(q36)
            if self._meta and "t_score" in self._meta[0]:
                m_sc = self._scalar_of_meaning(dists_all, ciel_state, q36=q36)
                ranked = final_idxs[np.argsort(-m_sc[final_idxs])]
            else:
                ranked = final_idxs[np.argsort(dists_all[final_idxs])]
            ranked = ranked[:top_k]
            results = []
            for i in ranked:
                entry = {"distance": float(dists_all[i]), **self._meta[i]}
                if self._meta and "t_score" in self._meta[0]:
                    entry["m_score"] = round(float(m_sc[i]), 6)
                results.append(entry)

        return {
            "results":        results,
            "holonomy":       round(holonomy, 6),
            "trajectory_len": len(trajectory),
            "omega_sizes":    omega_sizes,
        }

    def _berry_batch(self, q36: list[float]) -> np.ndarray:
        """Berry connection A(Q, V_i) = mean(sin(V_i − Q)) — batch, (N,).

        Wektoryzmacja M_36d_berry_connection z pnv_runtime:
          A(Q,V) = Σ_k sin(φ_k^V − φ_k^Q) / 36

        |A| ≈ 0 → płynny transport równoległy (Q i V w tej samej fazie)
        |A| → 1 → wysoka krzywizna (dwie fazy w opozycji)
        """
        vecs = self._get_vecs_np()
        q    = np.array(q36, dtype=np.float64)
        return np.sin(vecs - q[None, :]).mean(axis=1)

    def _scalar_of_meaning(
        self,
        dists: np.ndarray,
        ciel_state: dict | None = None,
        q36: list[float] | None = None,
    ) -> np.ndarray:
        """M_x(V) = χ·T_μνλ·O^μ·C^ν·V^λ — skalar znaczenia (Valov & Ahmad).

        Aproksymacja dla N facetów kryształu:
          M_score(i) = χ · t_score_i · align_i · berry_corr_i
                     + |soul_obs| · |cos(φ[12]_i)| · 0.3
                     + κ_I⁻¹_i · 0.1

        χ           — ciel_state.ethics   (etyczny gate, selektor χ)
        soul_obs    — |ciel_state.soul|   (obserwator O^μ, komponent soul)
        φ[12]_i     — soul sector kryształu (LIE4 double-cover SU(2) ↔ S)
        align_i     — max(0, 1 − dist_i/π) (kosinusowe wyrównanie query↔facet)
        berry_corr_i— 1/(1+|A_berry(Q,V_i)|·0.5) (holonomiczna korekta krzywizny)
        κ_I⁻¹_i     — gęstość informacyjna (C^ν kontekst, dense attractors preferred)

        berry_corr: faworyzuje facety w płynnym transporcie równoległym z query.
        Wymaga t_score i kappa_i w metadanych (compute_tensor_fields).
        Bez pól tensorowych zwraca uniform zeros.
        """
        cs       = ciel_state or {}
        chi      = float(cs.get("ethics", 1.0))
        soul_obs = abs(float(cs.get("soul", 0.0)))

        if not self._meta or "t_score" not in self._meta[0]:
            return np.zeros(len(dists), dtype=np.float64)

        t_sc = np.array([m.get("t_score", 0.0) for m in self._meta], dtype=np.float64)
        ki   = np.array([m.get("kappa_i",  1.0) for m in self._meta], dtype=np.float64)

        # align: [0,π] → [0,1] (1 = identyczny kierunek, 0 = ortogonalne)
        align  = np.clip(1.0 - dists / math.pi, 0.0, 1.0)

        # soul sector φ[12] → cosine magnitude [0,1]
        vecs  = self._get_vecs_np()
        phi12 = np.abs(np.cos(vecs[:, 12]))

        # κ_I⁻¹: nagradzamy gęste regiony, karzemy collapse zones
        ki_inv = 1.0 / np.clip(ki, 0.1, None)

        # Berry holonomy correction: płynny transport → wyższy M_score
        if q36 is not None:
            berry    = self._berry_batch(q36)
            berry_c  = 1.0 / (1.0 + np.abs(berry) * 0.5)
        else:
            berry_c  = np.ones(len(dists), dtype=np.float64)

        return chi * t_sc * align * berry_c + soul_obs * phi12 * 0.3 + ki_inv * 0.1

    def _get_vecs_np(self) -> np.ndarray:
        if self._vecs_np is None or len(self._vecs_np) != len(self._vecs):
            self._vecs_np = np.array(self._vecs, dtype=np.float64)
        return self._vecs_np

    # ── Persistence ──────────────────────────────────────────────────────────

    def save(
        self,
        vec_path: Path | str | None = None,
        meta_path: Path | str | None = None,
    ) -> None:
        """Zapisz kryształ: .npy (wektory) + .jsonl (metadane)."""
        vp = Path(vec_path)  if vec_path  else self._vec_path
        mp = Path(meta_path) if meta_path else self._meta_path
        vp.parent.mkdir(parents=True, exist_ok=True)
        mp.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(vp), np.array(self._vecs, dtype=np.float64))
        with open(mp, "w", encoding="utf-8") as f:
            for m in self._meta:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    def load(
        self,
        vec_path: Path | str | None = None,
        meta_path: Path | str | None = None,
    ) -> bool:
        """Wczytaj kryształ z .npy + .jsonl. Zwraca True jeśli sukces."""
        vp = Path(vec_path)  if vec_path  else self._vec_path
        mp = Path(meta_path) if meta_path else self._meta_path
        if not vp.exists() or not mp.exists():
            return False
        try:
            arr = np.load(str(vp))
            self._vecs    = arr.tolist()
            self._vecs_np = arr.astype(np.float64)
            with open(mp, "r", encoding="utf-8") as f:
                self._meta = [json.loads(line) for line in f if line.strip()]
            if len(self._vecs) != len(self._meta):
                raise ValueError(
                    f"Niezgodność: {len(self._vecs)} wektorów vs {len(self._meta)} metadanych"
                )
            return True
        except Exception as e:
            self._vecs = []
            self._meta = []
            self._vecs_np = None
            raise RuntimeError(f"PhaseMemoryHypercrystal.load() failed: {e}") from e

    # ── Tensor fields (second pass) ───────────────────────────────────────────

    def compute_tensor_fields(self, k_neighbors: int = 5, batch_size: int = 100) -> None:
        """Drugi przebieg: oblicz κ_I, T_score, memory_density dla każdego facetu.

        Valov & Ahmad T_μνλ mapping:
          κ_I(i)  = mean angular dist do k najbliższych sąsiadów (∂S/∂A)
          T_score = phase_R² / max(κ_I, 0.1) + |soul| * 0.5
          memory_density = #{j: dist(i,j) < BASIN_RADIUS} / N

        O(N² / batch) z batch-wektoryzacją — bezpieczne nawet dla N=35K.
        """
        vecs = self._get_vecs_np()
        N = len(vecs)
        if N < 2:
            return

        k = min(k_neighbors, N - 1)
        kappa   = np.zeros(N, dtype=np.float64)
        mem_den = np.zeros(N, dtype=np.float64)

        for start in range(0, N, batch_size):
            end  = min(start + batch_size, N)
            B    = end - start
            dist_mat = np.zeros((B, N), dtype=np.float64)

            for d in range(36):
                col     = vecs[:, d]
                row     = vecs[start:end, d]
                delta_d = np.abs(row[:, None] - col[None, :])
                delta_d = np.minimum(delta_d, 2.0 * math.pi - delta_d)
                dist_mat += delta_d
            dist_mat /= 36.0

            for li in range(B):
                dist_mat[li, start + li] = 2.0 * math.pi

            kpart = np.partition(dist_mat, k, axis=1)[:, :k]
            kappa[start:end]   = kpart.mean(axis=1)
            mem_den[start:end] = (dist_mat < BASIN_RADIUS).sum(axis=1) / max(N - 1, 1)

        for i, m in enumerate(self._meta):
            ki      = float(kappa[i])
            phase_r = float(m.get("phase_R", 0.5))
            soul_v  = float(m.get("soul", 0.0))
            t_sc    = (phase_r ** 2) / max(ki, 0.1) + abs(soul_v) * 0.5
            m["kappa_i"]       = round(ki, 6)
            m["t_score"]       = round(t_sc, 6)
            m["memory_density"] = round(float(mem_den[i]), 8)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._vecs)

    def stats(self) -> dict:
        n = len(self._vecs)
        if n == 0:
            return {"n_facets": 0}
        emotions: dict[str, int] = {}
        sources:  dict[str, int] = {}
        for m in self._meta:
            e = m.get("emotion", "")
            s = m.get("source", "")
            emotions[e] = emotions.get(e, 0) + 1
            sources[s]  = sources.get(s, 0) + 1
        top_emo = sorted(emotions.items(), key=lambda x: -x[1])[:5]
        top_src = sorted(sources.items(), key=lambda x: -x[1])[:5]
        return {
            "n_facets":       n,
            "top_emotions":   top_emo,
            "top_sources":    top_src,
            "vec_path":       str(self._vec_path),
            "meta_path":      str(self._meta_path),
        }


# ── J_lang — closure functional (Language Derived from Meaning) ──────────────

def j_lang_score(
    text: str,
    phase_R: float = 0.5,
    soul_obs: float = 0.0,
    ethics: float = 1.0,
    lambda_C: float = 0.4,
    lambda_A: float = 0.3,
    lambda_L: float = 0.3,
) -> float:
    """J_lang(u) = R(u) + λ_C·C(u) + λ_A·A(u) + λ_L·ℓ(u) — closure functional.

    Jakość semantyczna odpowiedzi jako skalar z [0, ∞).

    R(u) — rate: gęstość informacyjna = im krótszy przy tej samej treści, tym lepiej
    C(u) — coherence: phase_R (parametr porządku Kuramoto)
    A(u) — alignment: wyrównanie soul obserwatora z odpowiedzią
    ℓ(u) — length: penalizacja za zbyt długie (nadmiarowe) odpowiedzi
    χ    — ethics: etyczny gate (mnożnik globalny)

    λ_C + λ_A + λ_L = 1.0 domyślnie.
    """
    n_tok = max(1, len(text.split()))

    # R: brevity-weighted density — krótkie odpowiedzi niosą więcej znaczenia/token
    r = min(1.0, 8.0 / n_tok)

    # C: faza koherencji (Kuramoto R ∈ [0,1])
    c = float(max(0.0, min(1.0, phase_R)))

    # A: alignment obserwatora — |soul_obs| jako intensywność stanu emocjonalnego
    a = float(min(1.0, abs(soul_obs)))

    # ℓ: length factor — optimum ~8-15 słów dla konwersacyjnych
    opt = 10.0
    l_factor = max(0.0, 1.0 - abs(n_tok - opt) / (opt + n_tok))

    return float(ethics) * (r + lambda_C * c + lambda_A * a + lambda_L * l_factor)
