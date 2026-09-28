from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_8 import (
    SCHEMA as SCHEMA_V08,
    validate_bridge_packet_v08,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.9"
OVERLAP_MODE = "OVERLAP_GRAM_COVARIANT"

INTERNAL_MODES = {
    "TRIVIAL_INTERNAL_TENSOR",
    "FULL_RANK_FRAME_CONJUGACY",
    "RANK_DEFICIENT_STABILIZER",
    "GENERAL_MATRIX_GRAM_STABILIZER",
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


def _positive_int(x: Any, name: str, minimum: int = 1) -> int:
    if not isinstance(x, int) or x < minimum:
        raise FractalMoire36Error(f"{name} must be an integer >= {minimum}")
    return x


def _residual(packet: Mapping[str, Any], key: str, tolerance: float) -> float:
    value = _nonnegative(packet.get(key), key)
    if value > tolerance:
        raise FractalMoire36Error(f"{key} exceeds tolerance")
    return value


def validate_bridge_packet_v09(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p8 = dict(packet)
    p8["schema"] = SCHEMA_V08

    mode = packet.get("overlap_internal_mode")
    internal_receipt: dict[str, Any] | None = None

    if mode is not None and mode not in INTERNAL_MODES:
        raise FractalMoire36Error("unknown overlap_internal_mode")

    if mode is not None:
        if packet.get("ifs_covariance_mode") != OVERLAP_MODE:
            raise FractalMoire36Error(
                "matrix overlap internal mode requires OVERLAP_GRAM_COVARIANT"
            )

        d = _positive_int(packet.get("internal_dimension"), "internal_dimension")
        stab = _residual(packet, "internal_stabilizer_residual", tolerance)

        if mode == "TRIVIAL_INTERNAL_TENSOR":
            witness = _text(
                packet.get("internal_overlap_witness_ref"),
                "internal_overlap_witness_ref",
            )
            equality = _residual(
                packet,
                "local_unitary_equality_residual",
                tolerance,
            )
            components = _positive_int(
                packet.get("overlap_component_count"),
                "overlap_component_count",
            )
            claim = packet.get("channel_dependent_internal_claim")
            if claim is not False:
                raise FractalMoire36Error(
                    "TRIVIAL_INTERNAL_TENSOR forbids channel-dependent internal claim"
                )

            internal_receipt = {
                "mode": mode,
                "internal_dimension": d,
                "internal_overlap_witness_ref": witness,
                "internal_stabilizer_residual": stab,
                "local_unitary_equality_residual": equality,
                "overlap_component_count": components,
                "channel_dependent_internal_claim": False,
                "independent_unitaries_per_component": 1,
            }

        elif mode == "FULL_RANK_FRAME_CONJUGACY":
            witness = _text(
                packet.get("internal_overlap_witness_ref"),
                "internal_overlap_witness_ref",
            )
            frame_u = _residual(
                packet,
                "frame_unitarity_residual",
                tolerance,
            )
            external_equal = _residual(
                packet,
                "external_operator_equality_residual",
                tolerance,
            )
            independent = packet.get("independent_external_dynamics_claim")
            if independent is not False:
                raise FractalMoire36Error(
                    "FULL_RANK_FRAME_CONJUGACY forbids independent external dynamics claim"
                )

            internal_receipt = {
                "mode": mode,
                "internal_dimension": d,
                "internal_overlap_witness_ref": witness,
                "internal_stabilizer_residual": stab,
                "frame_unitarity_residual": frame_u,
                "external_operator_equality_residual": external_equal,
                "independent_external_dynamics_claim": False,
                "semantics": "ONE_EXTERNAL_UNITARY_IN_CHANNEL_FRAMES",
            }

        elif mode == "RANK_DEFICIENT_STABILIZER":
            witness = _text(
                packet.get("internal_overlap_witness_ref"),
                "internal_overlap_witness_ref",
            )
            hidden_ref = _text(
                packet.get("hidden_freedom_witness_ref"),
                "hidden_freedom_witness_ref",
            )
            rank = packet.get("cross_gram_rank")
            if not isinstance(rank, int) or rank < 0 or rank >= d:
                raise FractalMoire36Error(
                    "cross_gram_rank must satisfy 0 <= rank < internal_dimension"
                )
            visible = _residual(
                packet,
                "visible_support_consistency_residual",
                tolerance,
            )

            internal_receipt = {
                "mode": mode,
                "internal_dimension": d,
                "cross_gram_rank": rank,
                "kernel_dimension_lower_bound": d - rank,
                "internal_overlap_witness_ref": witness,
                "internal_stabilizer_residual": stab,
                "hidden_freedom_witness_ref": hidden_ref,
                "visible_support_consistency_residual": visible,
                "genuine_hidden_local_freedom_candidate": True,
            }

        else:
            gram_ref = _text(
                packet.get("matrix_gram_witness_ref"),
                "matrix_gram_witness_ref",
            )
            stabilizer_ref = _text(
                packet.get("matrix_stabilizer_witness_ref"),
                "matrix_stabilizer_witness_ref",
            )
            lo = packet.get("matrix_gram_rank_lower_bound")
            hi = packet.get("matrix_gram_rank_upper_bound")
            if not isinstance(lo, int) or not isinstance(hi, int):
                raise FractalMoire36Error(
                    "matrix Gram rank bounds must be integers"
                )
            if lo < 0 or hi < lo or hi > d:
                raise FractalMoire36Error(
                    "matrix Gram rank bounds must satisfy 0 <= lower <= upper <= internal_dimension"
                )

            internal_receipt = {
                "mode": mode,
                "internal_dimension": d,
                "matrix_gram_witness_ref": gram_ref,
                "matrix_stabilizer_witness_ref": stabilizer_ref,
                "internal_stabilizer_residual": stab,
                "matrix_gram_rank_lower_bound": lo,
                "matrix_gram_rank_upper_bound": hi,
                "semantics": "SOURCE_OWNED_MATRIX_GRAM_STABILIZER",
            }

    out = validate_bridge_packet_v08(p8, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["internal_overlap_receipt"] = internal_receipt
    out["canon_allowed"] = False
    return out
