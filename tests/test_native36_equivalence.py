from __future__ import annotations

import os

import numpy as np
import pytest

from ciel_geometry.phasenav.native36 import ENV_LIBRARY, Native36Bridge
from ciel_geometry.phasenav.pnv_runtime import M_36d_distance


def _deterministic_corpus() -> list[tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(360198)
    corpus: list[tuple[np.ndarray, np.ndarray]] = []

    zeros = np.zeros(36, dtype=np.float64)
    corpus.append((zeros, zeros.copy()))
    corpus.append((zeros, np.full(36, np.pi, dtype=np.float64)))
    corpus.append((
        np.linspace(-8.0 * np.pi, 8.0 * np.pi, 36, dtype=np.float64),
        np.linspace(8.0 * np.pi, -8.0 * np.pi, 36, dtype=np.float64),
    ))

    for _ in range(256):
        a = rng.uniform(-32.0 * np.pi, 32.0 * np.pi, size=36).astype(np.float64)
        b = rng.uniform(-32.0 * np.pi, 32.0 * np.pi, size=36).astype(np.float64)
        corpus.append((a, b))
    return corpus


@pytest.mark.skipif(not os.environ.get(ENV_LIBRARY), reason=f"{ENV_LIBRARY} not configured")
def test_rust_strict_distance_matches_canonical_pnv_runtime_exactly():
    bridge = Native36Bridge.from_env()
    max_abs_error = 0.0

    for a, b in _deterministic_corpus():
        reference = float(M_36d_distance(a, b))
        candidate = bridge.distance_radians_strict(a, b)
        error = abs(reference - candidate)
        max_abs_error = max(max_abs_error, error)
        assert candidate == reference, (
            f"strict equivalence failure: candidate={candidate!r} "
            f"reference={reference!r} abs_error={error!r}"
        )

    assert max_abs_error == 0.0
