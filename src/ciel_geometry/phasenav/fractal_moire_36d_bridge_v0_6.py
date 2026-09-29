from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_5 import (
    SCHEMA as SCHEMA_V05,
    validate_bridge_packet_v05,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.6"

DEPTH_MODES = {
    "FINITE_LEVEL_ONLY",
    "INDUCTIVE_STEP_COVARIANT",
    "INDUCTIVE_LIMIT_COVARIANT",
}

ARPL_LIMIT = "ARPL_PROCYCLIC_ODOMETER_LIMIT"


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


def _check_residual(packet: Mapping[str, Any], key: str, tolerance: float) -> float:
    value = _nonnegative(packet.get(key), key)
    if value > tolerance:
        raise FractalMoire36Error(f"{key} exceeds tolerance")
    return value


def validate_bridge_packet_v06(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p5 = dict(packet)
    p5["schema"] = SCHEMA_V05

    depth_mode = packet.get("depth_mode")
    if depth_mode not in DEPTH_MODES:
        raise FractalMoire36Error("invalid depth_mode")

    depth_receipt: dict[str, Any]

    if depth_mode == "FINITE_LEVEL_ONLY":
        if packet.get("infinite_depth_claim") is True:
            raise FractalMoire36Error(
                "FINITE_LEVEL_ONLY cannot claim infinite depth"
            )
        depth_receipt = {
            "mode": depth_mode,
            "infinite_depth_claim": False,
        }

    else:
        level = _positive_int(packet.get("level_index"), "level_index", 0)
        coarse_id = _text(packet.get("coarse_level_id"), "coarse_level_id")
        fine_id = _text(packet.get("fine_level_id"), "fine_level_id")
        embedding_ref = _text(
            packet.get("embedding_witness_ref"),
            "embedding_witness_ref",
        )

        iso = _check_residual(
            packet, "embedding_isometry_residual", tolerance
        )
        inter = _check_residual(
            packet, "cross_level_intertwiner_residual", tolerance
        )
        mismatch = _check_residual(
            packet, "mismatch_intertwiner_residual", tolerance
        )
        nesting = _check_residual(
            packet, "spectral_nesting_residual", tolerance
        )

        depth_receipt = {
            "mode": depth_mode,
            "level_index": level,
            "coarse_level_id": coarse_id,
            "fine_level_id": fine_id,
            "embedding_witness_ref": embedding_ref,
            "embedding_isometry_residual": iso,
            "cross_level_intertwiner_residual": inter,
            "mismatch_intertwiner_residual": mismatch,
            "spectral_nesting_residual": nesting,
            "infinite_depth_claim": depth_mode == "INDUCTIVE_LIMIT_COVARIANT",
        }

        if depth_mode == "INDUCTIVE_LIMIT_COVARIANT":
            family_ref = _text(
                packet.get("inductive_family_witness_ref"),
                "inductive_family_witness_ref",
            )
            theorem_ref = _text(
                packet.get("limit_theorem_witness_ref"),
                "limit_theorem_witness_ref",
            )
            cofinal_ref = _text(
                packet.get("cofinality_witness_ref"),
                "cofinality_witness_ref",
            )
            count = _positive_int(
                packet.get("validated_level_count"),
                "validated_level_count",
                2,
            )
            ledger = packet.get("infinite_depth_information_loss_ledger")
            if not isinstance(ledger, list) or not ledger:
                raise FractalMoire36Error(
                    "infinite_depth_information_loss_ledger must be non-empty"
                )
            for i, item in enumerate(ledger):
                _text(item, f"infinite_depth_information_loss_ledger[{i}]")
            reconstruction = _text(
                packet.get("limit_reconstruction_contract"),
                "limit_reconstruction_contract",
            )

            depth_receipt.update({
                "inductive_family_witness_ref": family_ref,
                "limit_theorem_witness_ref": theorem_ref,
                "cofinality_witness_ref": cofinal_ref,
                "validated_level_count": count,
                "infinite_depth_information_loss_ledger": tuple(ledger),
                "limit_reconstruction_contract": reconstruction,
            })

            subtype = packet.get("infinite_depth_subtype")
            if subtype is not None:
                if subtype != ARPL_LIMIT:
                    raise FractalMoire36Error("unknown infinite_depth_subtype")

                arpl_ref = _text(
                    packet.get("arpl_infinite_spectrum_witness_ref"),
                    "arpl_infinite_spectrum_witness_ref",
                )
                L = _positive_int(
                    packet.get("current_clock_size"),
                    "current_clock_size",
                    2,
                )
                M = _positive_int(
                    packet.get("next_clock_size"),
                    "next_clock_size",
                    2,
                )
                if M % L:
                    raise FractalMoire36Error(
                        "ARPL next_clock_size must be divisible by current_clock_size"
                    )
                first_gap = _nonnegative(
                    packet.get("first_positive_mismatch"),
                    "first_positive_mismatch",
                )
                if first_gap <= 0.0:
                    raise FractalMoire36Error(
                        "first_positive_mismatch must be positive"
                    )
                spectrum_ref = _text(
                    packet.get("finite_spectrum_summary_ref"),
                    "finite_spectrum_summary_ref",
                )

                depth_receipt["arpl"] = {
                    "subtype": ARPL_LIMIT,
                    "arpl_infinite_spectrum_witness_ref": arpl_ref,
                    "current_clock_size": L,
                    "next_clock_size": M,
                    "refinement_branching": M // L,
                    "first_positive_mismatch": first_gap,
                    "finite_spectrum_summary_ref": spectrum_ref,
                    "limit_unitary_spectrum": "S^1",
                    "limit_mismatch_spectrum": "[0,4]",
                    "positive_limit_gap": False,
                }

    out = validate_bridge_packet_v05(p5, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["depth_receipt"] = depth_receipt
    out["canon_allowed"] = False
    return out
