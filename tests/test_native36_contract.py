from __future__ import annotations

import numpy as np
import pytest

from ciel_geometry.phasenav.native36 import (
    DIM,
    ENV_LIBRARY,
    PHI_BYTES,
    Native36Bridge,
    Native36Error,
    read_live_phi,
)


def _surface(tmp_path, *, status: str = "ACTIVE", payload: bytes | None = None):
    root = tmp_path / "ciel_noema"
    root.mkdir()
    (root / "ciel_binding_status").write_text(status, encoding="utf-8")
    if payload is None:
        payload = np.arange(DIM, dtype="<f8").tobytes()
    (root / "phi").write_bytes(payload)
    return root


def test_live_phi_exact_36d_little_endian(tmp_path):
    root = _surface(tmp_path)
    phi = read_live_phi(root)
    assert phi.shape == (36,)
    assert phi.dtype == np.dtype("float64")
    assert phi.nbytes == PHI_BYTES == 288
    np.testing.assert_array_equal(phi, np.arange(36, dtype=np.float64))


def test_live_phi_requires_active_binding(tmp_path):
    root = _surface(tmp_path, status="BLOCKED")
    with pytest.raises(Native36Error, match="must be ACTIVE"):
        read_live_phi(root)


def test_live_phi_rejects_wrong_byte_length(tmp_path):
    root = _surface(tmp_path, payload=b"\x00" * (PHI_BYTES - 8))
    with pytest.raises(Native36Error, match="exactly 288 bytes"):
        read_live_phi(root)


def test_live_phi_rejects_non_finite(tmp_path):
    phi = np.zeros(36, dtype="<f8")
    phi[4] = np.nan
    root = _surface(tmp_path, payload=phi.tobytes())
    with pytest.raises(Native36Error, match="36 finite"):
        read_live_phi(root)


def test_native_bridge_requires_explicit_library_path(monkeypatch):
    monkeypatch.delenv(ENV_LIBRARY, raising=False)
    with pytest.raises(Native36Error, match=ENV_LIBRARY):
        Native36Bridge.from_env()
