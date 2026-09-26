from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_7 import (
    SCHEMA as SCHEMA_V07,
    validate_bridge_packet_v07,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.8"
ARPL_OVERLAP = "ARPL_HIT_OVERLAP_GRAM"
OVERLAP_MODE = "OVERLAP_GRAM_COVARIANT"

ADAPTER_STATUSES = {
    "NOT_CLAIMED",
    "PASS_STABILIZER",
    "FAIL_STABILIZER",
}


def _text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def _nonnegative(x: Any, name: str) -> float:
    y = float(x)
    if not math.isfinite(y) or y < 0.0:
        raise FractalMoire36Error(f"{name} must be finite and nonnegative")
    return y


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def _prime_support(x: Any) -> tuple[int, ...]:
    if not isinstance(x, list) or not x:
        raise FractalMoire36Error("arpl_prime_support must be a non-empty list")
    if not all(isinstance(p, int) for p in x):
        raise FractalMoire36Error("arpl_prime_support entries must be integers")
    support = tuple(x)
    if len(set(support)) != len(support):
        raise FractalMoire36Error("arpl_prime_support must contain distinct primes")
    if not all(p >= 5 and _is_prime(p) for p in support):
        raise FractalMoire36Error(
            "arpl_prime_support must contain distinct primes >= 5"
        )
    return support


def validate_bridge_packet_v08(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p7 = dict(packet)
    p7["schema"] = SCHEMA_V07

    subtype = packet.get("overlap_source_subtype")
    arpl_receipt: dict[str, Any] | None = None

    if subtype is not None and subtype != ARPL_OVERLAP:
        raise FractalMoire36Error("unknown overlap_source_subtype")

    if subtype == ARPL_OVERLAP:
        if packet.get("ifs_covariance_mode") != OVERLAP_MODE:
            raise FractalMoire36Error(
                "ARPL_HIT_OVERLAP_GRAM requires OVERLAP_GRAM_COVARIANT"
            )

        bridge_ref = _text(
            packet.get("arpl_bridge_witness_ref"),
            "arpl_bridge_witness_ref",
        )
        gram_ref = _text(
            packet.get("arpl_gram_witness_ref"),
            "arpl_gram_witness_ref",
        )
        normalized_ref = _text(
            packet.get("arpl_normalized_gram_witness_ref"),
            "arpl_normalized_gram_witness_ref",
        )

        h = packet.get("arpl_separation_h")
        if not isinstance(h, int) or h < 6 or h % 6:
            raise FractalMoire36Error(
                "arpl_separation_h must be an integer >= 6 divisible by 6"
            )

        support = _prime_support(packet.get("arpl_prime_support"))

        norm_res = _nonnegative(
            packet.get("arpl_gram_normalization_residual"),
            "arpl_gram_normalization_residual",
        )
        if norm_res > tolerance:
            raise FractalMoire36Error(
                "ARPL Gram normalization residual exceeds tolerance"
            )

        status = packet.get("arithmetic_pulse_scalar_adapter_status")
        if status not in ADAPTER_STATUSES:
            raise FractalMoire36Error(
                "invalid arithmetic_pulse_scalar_adapter_status"
            )

        adapter_residual = None
        promotion = False

        if status in {"PASS_STABILIZER", "FAIL_STABILIZER"}:
            adapter_residual = _nonnegative(
                packet.get("arithmetic_pulse_scalar_adapter_residual"),
                "arithmetic_pulse_scalar_adapter_residual",
            )

            if status == "PASS_STABILIZER":
                if adapter_residual > tolerance:
                    raise FractalMoire36Error(
                        "PASS_STABILIZER residual exceeds tolerance"
                    )
                promotion = True

            else:
                if adapter_residual <= tolerance:
                    raise FractalMoire36Error(
                        "FAIL_STABILIZER requires residual above tolerance"
                    )
                promotion = False

        arpl_receipt = {
            "subtype": ARPL_OVERLAP,
            "arpl_bridge_witness_ref": bridge_ref,
            "arpl_gram_witness_ref": gram_ref,
            "arpl_normalized_gram_witness_ref": normalized_ref,
            "arpl_separation_h": h,
            "arpl_prime_support": support,
            "arpl_gram_normalization_residual": norm_res,
            "arithmetic_pulse_scalar_adapter_status": status,
            "arithmetic_pulse_scalar_adapter_residual": adapter_residual,
            "scalar_orbital_pulse_promotion": promotion,
            "source_semantics": "NORMALIZED_L2_HIT_CYLINDER_GRAM",
        }

    out = validate_bridge_packet_v07(p7, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["arpl_overlap_source_receipt"] = arpl_receipt
    out["canon_allowed"] = False
    return out
