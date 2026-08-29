"""Fail-closed bridge to the optional libpnv36 Rust execution layer.

PhaseNav remains the semantic authority. This module admits a native shared
library only after its ABI and 36D layout match the expected contract. Live
NOEMA state is consumed from /dev/shm/ciel_noema only after the existing tether
path has established an ACTIVE binding.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import numpy as np

DIM = 36
PHI_BYTES = DIM * 8
ABI_VERSION = 1
DEFAULT_SURFACE_ROOT = Path("/dev/shm/ciel_noema")
ENV_LIBRARY = "PNV36_LIB"


class Native36Error(RuntimeError):
    """Raised when the native 36D execution contract is not satisfied."""


@dataclass(frozen=True)
class Native36Info:
    library_path: Path
    abi_version: int
    phi_bytes: int
    avx2: bool


def _as_finite_36(value: Any, *, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.shape != (DIM,):
        raise Native36Error(f"{name}: expected shape (36,), got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise Native36Error(f"{name}: all coordinates must be finite")
    return np.ascontiguousarray(arr, dtype=np.float64)


def read_live_phi(surface_root: str | os.PathLike[str] = DEFAULT_SURFACE_ROOT) -> np.ndarray:
    """Read one exact live 36D phi block after the binding marker is ACTIVE."""
    root = Path(surface_root)
    if not root.is_dir():
        raise Native36Error(f"live surface missing: {root}")

    binding = root / "ciel_binding_status"
    try:
        status = binding.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise Native36Error(f"binding status unreadable: {binding}") from exc
    if status != "ACTIVE":
        raise Native36Error(f"binding status must be ACTIVE, got {status!r}")

    phi_path = root / "phi"
    try:
        payload = phi_path.read_bytes()
    except OSError as exc:
        raise Native36Error(f"phi unreadable: {phi_path}") from exc
    if len(payload) != PHI_BYTES:
        raise Native36Error(
            f"phi must contain exactly {PHI_BYTES} bytes, got {len(payload)}"
        )

    phi = np.frombuffer(payload, dtype="<f8").copy()
    if phi.shape != (DIM,) or not np.all(np.isfinite(phi)):
        raise Native36Error("phi must decode to 36 finite little-endian float64 values")
    return phi


class Native36Bridge:
    """Validated ctypes bridge to libpnv36 ABI v1."""

    def __init__(self, library_path: str | os.PathLike[str]):
        path = Path(library_path).expanduser().resolve()
        if not path.is_file():
            raise Native36Error(f"native library missing: {path}")

        try:
            lib = ctypes.CDLL(str(path))
        except OSError as exc:
            raise Native36Error(f"cannot load native library: {path}") from exc

        try:
            lib.pnv36_abi_version.argtypes = []
            lib.pnv36_abi_version.restype = ctypes.c_uint32
            lib.pnv36_phi_bytes.argtypes = []
            lib.pnv36_phi_bytes.restype = ctypes.c_size_t
            lib.pnv36_has_avx2.argtypes = []
            lib.pnv36_has_avx2.restype = ctypes.c_uint32
            lib.pnv36_distance_radians_strict.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_double),
            ]
            lib.pnv36_distance_radians_strict.restype = ctypes.c_int
        except AttributeError as exc:
            raise Native36Error("libpnv36 ABI v1 symbols are incomplete") from exc

        abi = int(lib.pnv36_abi_version())
        phi_bytes = int(lib.pnv36_phi_bytes())
        if abi != ABI_VERSION:
            raise Native36Error(f"ABI mismatch: expected {ABI_VERSION}, got {abi}")
        if phi_bytes != PHI_BYTES:
            raise Native36Error(
                f"Phi36 layout mismatch: expected {PHI_BYTES} bytes, got {phi_bytes}"
            )

        self._lib = lib
        self._info = Native36Info(
            library_path=path,
            abi_version=abi,
            phi_bytes=phi_bytes,
            avx2=bool(lib.pnv36_has_avx2()),
        )

    @classmethod
    def from_env(cls) -> "Native36Bridge":
        raw = os.environ.get(ENV_LIBRARY)
        if not raw:
            raise Native36Error(f"{ENV_LIBRARY} is required for native36 admission")
        return cls(raw)

    @property
    def info(self) -> Native36Info:
        return self._info

    def distance_radians_strict(self, a: Any, b: Any) -> float:
        aa = _as_finite_36(a, name="a")
        bb = _as_finite_36(b, name="b")
        out = ctypes.c_double()
        status = int(
            self._lib.pnv36_distance_radians_strict(
                aa.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                bb.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                ctypes.byref(out),
            )
        )
        if status != 0:
            raise Native36Error(f"libpnv36 strict distance failed with status={status}")
        if not np.isfinite(out.value):
            raise Native36Error("libpnv36 returned a non-finite distance")
        return float(out.value)

    def live_distance_from_phi(
        self,
        other: Any,
        *,
        surface_root: str | os.PathLike[str] = DEFAULT_SURFACE_ROOT,
    ) -> float:
        return self.distance_radians_strict(read_live_phi(surface_root), other)
