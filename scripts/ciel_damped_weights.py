#!/usr/bin/env python3
"""ciel_damped_weights.py — Macierz wag tłumionych dla kryształu PhaseNav.

Model wagi krawędzi:

    |W_ij| = cos(d_ij / 2) * exp(-beta * d_ij)

gdzie:
    d_ij  — odległość 36D między fasetami i oraz j (metryka torusowa L2)
    beta  — stała tłumienia (domyślnie: 1.0)

Formuła łączy trzy filary predyktywnej teorii pola efektywnego:
  1. Geometria fazowa kryształu (36D oscylacyjna przestrzeń faz)
  2. Tłumienie wykładnicze — zanik długich połączeń
  3. Modulacja kosinusoidalna — interferencja fazowa między węzłami

Wynik: rzadka macierz CSR, opcjonalnie zapis do pliku .npz.

Użycie:
    python3 scripts/ciel_damped_weights.py
    python3 scripts/ciel_damped_weights.py --beta 0.5 --sample 512
    python3 scripts/ciel_damped_weights.py --beta 1.0 --sample 0 --out weights.npz
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from scipy import sparse
from scipy.spatial import cKDTree

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))

from ciel_geometry.phasenav.htri_hypercrystal import load_crystal_arrays

_EPS = 1.0e-12


def torus_distance_36d(a: np.ndarray, b: np.ndarray) -> float:
    """Odległość L2 na torusie T^36 (każdy wymiar zawinięty do [0, 2π))."""
    diff = np.abs(a - b)
    diff = np.minimum(diff, 2.0 * np.pi - diff)
    return float(np.sqrt(np.dot(diff, diff)))


def build_damped_weight_matrix(
    phase_vectors: np.ndarray,
    *,
    beta: float = 1.0,
    neighbours: int = 16,
    min_weight: float = 1e-6,
) -> sparse.csr_matrix:
    """Zbuduj rzadką macierz wag |W_ij| = cos(d_ij/2) * exp(-beta * d_ij).

    Tylko k najbliższych sąsiadów na krysztale.  Macierz jest symetryczna
    (|W_ij| = |W_ji|) i rzeczywista.

    Parameters
    ----------
    phase_vectors : (N, 36) float64
    beta          : stała tłumienia > 0
    neighbours    : liczba sąsiadów w drzewie kNN
    min_weight    : wagi poniżej tego progu są odrzucane
    """
    phases = np.asarray(phase_vectors, dtype=np.float64)
    if phases.ndim != 2 or phases.shape[1] != 36:
        raise ValueError(f"Oczekiwano (N, 36), otrzymano {phases.shape}")
    if beta <= 0.0:
        raise ValueError("beta musi być > 0")

    n = phases.shape[0]
    k = min(max(1, int(neighbours)), n - 1)

    # kNN na reprezentacji cyklicznej (cos, sin) w R^72
    features = np.concatenate((np.cos(phases), np.sin(phases)), axis=1)
    tree = cKDTree(features)
    _, nbrs = tree.query(features, k=k + 1)

    pair_set: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j_raw in np.atleast_1d(nbrs[i])[1:]:
            j = int(j_raw)
            if i == j:
                continue
            a, b = (i, j) if i < j else (j, i)
            if (a, b) not in pair_set:
                pair_set[(a, b)] = torus_distance_36d(phases[a], phases[b])

    rows, cols, data = [], [], []
    for (i, j), d in pair_set.items():
        w = float(np.cos(d / 2.0) * np.exp(-beta * d))
        if abs(w) < min_weight:
            continue
        rows.extend((i, j))
        cols.extend((j, i))
        data.extend((w, w))

    return sparse.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()


def weight_statistics(W: sparse.csr_matrix) -> dict:
    """Statystyki macierzy wag."""
    d = W.data
    return {
        "n_facets":    W.shape[0],
        "nnz":         int(W.nnz),
        "density":     float(W.nnz) / float(W.shape[0] ** 2),
        "w_mean":      float(np.mean(d)),
        "w_std":       float(np.std(d)),
        "w_min":       float(np.min(d)),
        "w_max":       float(np.max(d)),
        "w_negative":  int(np.sum(d < 0)),
        "symmetric":   bool(abs((W - W.T).max()) < 1e-12),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beta",       type=float, default=1.0,
                        help="Stała tłumienia β (domyślnie: 1.0)")
    parser.add_argument("--sample",     type=int,   default=512,
                        help="Liczba facetów (0 = pełny kryształ)")
    parser.add_argument("--neighbours", type=int,   default=16,
                        help="Liczba sąsiadów kNN (domyślnie: 16)")
    parser.add_argument("--seed",       type=int,   default=42)
    parser.add_argument("--out",        type=str,   default=None,
                        help="Plik wyjściowy .npz (opcjonalnie)")
    args = parser.parse_args()

    sample = None if args.sample == 0 else args.sample
    phases, metadata = load_crystal_arrays(sample=sample, seed=args.seed)
    print(f"Załadowano {phases.shape[0]} facetów × 36D")

    W = build_damped_weight_matrix(
        phases,
        beta=args.beta,
        neighbours=args.neighbours,
    )
    stats = weight_statistics(W)
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    if args.out:
        out_path = Path(args.out)
        sparse.save_npz(str(out_path), W)
        print(f"Zapisano: {out_path}  ({out_path.stat().st_size / 1e3:.1f} kB)")


if __name__ == "__main__":
    main()
