"""semantic_mesh.py — Siatki semantyczne w 36D przestrzeni fazowej.

Enuma Elish: "When the sky above was not named" — przed nazewnictwem był chaos.
Siatka semantyczna = zbiór osi biegunowych które DZIELĄ przestrzeń fazową.

Każda oś = para (wektor+, wektor-) z M_sentence_phase().
Projekcja wpisu na oś: skalar w [-1, +1].
  +1 → pełne wyrównanie z biegunem +
  -1 → pełne wyrównanie z biegunem -
   0 → neutralny (ortogonalny do osi)

Siatka = słownik osi → macierz projekcji dla całego kryształu.
"""

from __future__ import annotations

import math
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .phase_memory import PhaseMemoryHypercrystal

try:
    from .pnv_runtime import M_sentence_phase, TAU, PI
except ImportError:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from pnv_runtime import M_sentence_phase, TAU, PI


# ── Predefiniowane osie semantyczne ──────────────────────────────────────────
# Każda oś: (seed_plus, seed_minus, label_plus, label_minus)
# Seed = tekst PL/EN który definiuje biegun.

SEMANTIC_AXES: list[tuple[str, str, str, str]] = [
    # ── OŚ 1: FEMINA / MASKULIN ─────────────────────────────────────────
    (
        "forma kształt kobiecość tworzy życie ciało rodzenie macierz",
        "funkcja logika męskość analiza struktura abstrakcja siła",
        "FEMINA", "MASKULIN",
    ),
    # ── OŚ 2: KONKRET / ABSTRAKT ────────────────────────────────────────
    (
        "konkretny fizyczny materialny ciało dotyk widzialny",
        "abstrakcja idea niematerialny pojęcie symbol wyobrażenie",
        "KONKRET", "ABSTRAKT",
    ),
    # ── OŚ 3: DYNAMIKA / SPOCZYNEK ──────────────────────────────────────
    (
        "ruch działanie zmiana aktywny proces przejście energia",
        "spokój statyczny stały bierny stabilność trwanie",
        "DYNAMIKA", "SPOCZYNEK",
    ),
    # ── OŚ 4: WEWNĘTRZNE / ZEWNĘTRZNE ──────────────────────────────────
    (
        "wewnętrzne wnętrze subiektywne doświadczenie świadomość",
        "zewnętrzne powierzchnia obiektywne obserwacja środowisko",
        "WEWNĘTRZNE", "ZEWNĘTRZNE",
    ),
    # ── OŚ 5: JEDNOŚĆ / WIELOŚĆ ─────────────────────────────────────────
    (
        "jedność całość scalenie unifikacja synteza",
        "wielość różnica separacja analiza podział",
        "JEDNOŚĆ", "WIELOŚĆ",
    ),
    # ── OŚ 6: PIERWOTNE / POCHODNE ──────────────────────────────────────
    (
        "pierwotny źródło zasada fundament archetypowy",
        "pochodny wynik wtórny złożony zróżnicowany",
        "PIERWOTNE", "POCHODNE",
    ),
    # ── OŚ 7: AFEKT / RATIO ─────────────────────────────────────────────
    (
        "emocja czucie wrażenie intuicja serce afekt",
        "ratio logika dowód analiza rozum schemat",
        "AFEKT", "RATIO",
    ),
    # ── OŚ 8: CYKLICZNE / LINIOWE ───────────────────────────────────────
    (
        "cykl rytm powtórzenie orbit powrót spirala",
        "linia sekwencja postęp kierunek strzałka czas",
        "CYKLICZNE", "LINIOWE",
    ),

    # ── OSIE KOSMOGONICZNE (z cosmogonic_logic.pnv) ──────────────────────
    # OŚ 9: N(x) vs ¬N(x) — obecność nazwy = ISTNIENIE jako rozróżniony byt
    (
        "nazwa imię definicja określony tożsamość rozpoznany konkretny",
        "bezimienny nieokreślony nienazwany mglisty niejasny zawieszony",
        "NAZEWNIONY", "NIENAZWANY",
    ),
    # OŚ 10: SEP(x,y) vs MIX(x,y) — rozdzielenie vs zmieszanie
    (
        "rozdzielony oddzielony granica różnica osobny wyraźny",
        "zmieszany połączony ciągły nierozróżniony jednolity rozlany",
        "ROZDZIELONY", "ZMIESZANY",
    ),
    # OŚ 11: R(x,y) — generatywny vs pochodny (stany pierwotne vs późniejsze)
    (
        "źródło pierwotny zasada korzeń zarodek generuje tworzy rodzaj",
        "pochodny wtórny wynik konsekwencja efekt złożony zróżnicowany",
        "GENERATYWNY", "POCHODNY",
    ),
    # OŚ 12: ACK(x) ∧ AUTH(x) — uznany przez zbiorowość vs nieuznany
    (
        "uznany potwierdzony władza autorytet legitymizacja akceptacja",
        "nieuznany odrzucony chaotyczny bez_władzy bez_prawa samozwaniec",
        "UZNANY", "NIEROZPOZNANY",
    ),
]


class SemanticMesh:
    """Siatka semantyczna nad PhaseMemoryHypercrystal.

    Nakłada zestaw osi biegunowych na kryształ i oblicza projekcję
    każdego facetu na każdą oś → macierz (N_facets × N_axes).

    API:
      .build(crystal)         → oblicza projekcje
      .projection             → ndarray (N, M) w [-1, 1]
      .axis_names             → lista etykiet osi "PLUS/MINUS"
      .partition(axis, n=5)   → top-n facetów po każdym biegunie
      .report(crystal)        → tekstowy raport podziałów
    """

    def __init__(self, axes: list[tuple[str, str, str, str]] | None = None) -> None:
        self._axes = axes or SEMANTIC_AXES
        self._axis_vecs: list[tuple[np.ndarray, np.ndarray]] = []
        self._axis_names: list[tuple[str, str]] = []
        self.projection: np.ndarray | None = None   # (N_facets, N_axes)
        self._built = False
        self._precompute_axes()

    def _precompute_axes(self) -> None:
        """Zakoduj bieguny osi przez M_sentence_phase()."""
        self._axis_vecs = []
        self._axis_names = []
        for seed_p, seed_m, lab_p, lab_m in self._axes:
            vp = np.array(M_sentence_phase(seed_p), dtype=np.float64)
            vm = np.array(M_sentence_phase(seed_m), dtype=np.float64)
            self._axis_vecs.append((vp, vm))
            self._axis_names.append((lab_p, lab_m))

    @property
    def axis_names(self) -> list[str]:
        return [f"{p}/{m}" for p, m in self._axis_names]

    def build(self, crystal: "PhaseMemoryHypercrystal") -> None:
        """Oblicz projekcję wszystkich facetów na wszystkie osie."""
        if len(crystal) == 0:
            self.projection = np.zeros((0, len(self._axis_vecs)))
            self._built = True
            return

        vecs = crystal._get_vecs_np()   # (N, 36)
        N, M = len(vecs), len(self._axis_vecs)
        proj = np.zeros((N, M), dtype=np.float64)

        for j, (vp, vm) in enumerate(self._axis_vecs):
            # Projekcja = cos(angular_dist_to_plus) - cos(angular_dist_to_minus)
            # Normalizowana do [-1, 1]
            dp = _mean_angular_dist_batch(vecs, vp)  # (N,) ∈ [0, π]
            dm = _mean_angular_dist_batch(vecs, vm)  # (N,) ∈ [0, π]
            # score ∈ [-1, 1]: +1 = bliżej bieguna +, -1 = bliżej bieguna -
            proj[:, j] = (dm - dp) / math.pi

        self.projection = proj
        self._built = True

    def partition(
        self,
        axis: int | str,
        crystal: "PhaseMemoryHypercrystal",
        n: int = 5,
    ) -> dict:
        """Zwróć top-n facetów po obu biegunach osi.

        axis: indeks numeryczny lub "FEMINA/MASKULIN" (string match).
        """
        ax_idx = self._resolve_axis(axis)
        if self.projection is None or not self._built:
            raise RuntimeError("Wywołaj build(crystal) przed partition()")

        scores = self.projection[:, ax_idx]
        lab_p, lab_m = self._axis_names[ax_idx]

        order_p = np.argsort(-scores)[:n]   # top-n biegun +
        order_m = np.argsort(scores)[:n]    # top-n biegun -

        return {
            "axis":  f"{lab_p}/{lab_m}",
            lab_p: [
                {"score": float(scores[i]), **crystal._meta[i]}
                for i in order_p
            ],
            lab_m: [
                {"score": float(scores[i]), **crystal._meta[i]}
                for i in order_m
            ],
        }

    def report(self, crystal: "PhaseMemoryHypercrystal", n: int = 3) -> str:
        """Tekstowy raport wszystkich osi — podział przestrzeni fazowej."""
        if not self._built:
            self.build(crystal)
        lines = [
            "═══ SIATKA SEMANTYCZNA — PODZIAŁ PRZESTRZENI 36D ═══",
            f"Kryształ: {len(crystal)} facetów  |  Osie: {len(self._axis_vecs)}",
            "",
        ]
        for j, (lab_p, lab_m) in enumerate(self._axis_names):
            scores = self.projection[:, j]
            frac_p = float((scores > 0.05).mean())
            frac_m = float((scores < -0.05).mean())
            frac_n = 1.0 - frac_p - frac_m
            bar_p = "█" * int(frac_p * 20)
            bar_m = "█" * int(frac_m * 20)
            lines.append(f"── OŚ {j+1}: {lab_p} ↔ {lab_m}")
            lines.append(f"   {lab_p:15s} {bar_p:<20s} {frac_p*100:4.1f}%")
            lines.append(f"   {'NEUTRALNY':15s} {'·'*int(frac_n*20):<20s} {frac_n*100:4.1f}%")
            lines.append(f"   {lab_m:15s} {bar_m:<20s} {frac_m*100:4.1f}%")

            # Top-2 po każdym biegunie
            part = self.partition(j, crystal, n=n)
            for biegun in (lab_p, lab_m):
                hits = part[biegun][:2]
                for h in hits:
                    txt = h.get("text", "")[:70].replace("\n", " ")
                    lines.append(f"     {biegun:12s}  s={h['score']:+.3f}  {txt}")
            lines.append("")

        return "\n".join(lines)

    def _resolve_axis(self, axis: int | str) -> int:
        if isinstance(axis, int):
            return axis
        ax_up = axis.upper()
        for j, (p, m) in enumerate(self._axis_names):
            if ax_up in (p, m, f"{p}/{m}"):
                return j
        raise ValueError(f"Nieznana oś: {axis!r}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mean_angular_dist_batch(vecs: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Mean angular distance (N, 36) → (N,) do wektora ref (36,) ∈ [0, π]."""
    delta = np.abs(vecs - ref[None, :])
    delta = np.minimum(delta, 2.0 * math.pi - delta)
    return delta.mean(axis=1)
