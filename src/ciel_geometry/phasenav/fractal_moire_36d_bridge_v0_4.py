from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_3 import (
    SCHEMA as SCHEMA_V03,
    validate_bridge_packet_v03,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.4"
OVERLAP_MODE = "OVERLAP_GRAM_COVARIANT"


def _finite_nonnegative(x: Any, name: str) -> float:
    y = float(x)
    if not math.isfinite(y) or y < 0.0:
        raise FractalMoire36Error(f"{name} must be finite and nonnegative")
    return y


def _nonempty_text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def validate_bridge_packet_v04(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    mode = packet.get("ifs_covariance_mode")
    p3 = dict(packet)
    p3["schema"] = SCHEMA_V03

    overlap_receipt: dict[str, Any] | None = None

    if mode == OVERLAP_MODE:
        if packet.get("scale_semantics") != "IFS_COMPRESSION":
            raise FractalMoire36Error(
                "OVERLAP_GRAM_COVARIANT requires IFS_COMPRESSION"
            )

        level = packet.get("overlap_level")
        if not isinstance(level, int) or level < 1:
            raise FractalMoire36Error("overlap_level must be a positive integer")

        gram_ref = _nonempty_text(
            packet.get("overlap_gram_witness_ref"),
            "overlap_gram_witness_ref",
        )
        local_ref = _nonempty_text(
            packet.get("local_relation_family_witness_ref"),
            "local_relation_family_witness_ref",
        )
        quotient_contract = _nonempty_text(
            packet.get("quotient_reconstruction_contract"),
            "quotient_reconstruction_contract",
        )

        ledger = packet.get("overlap_kernel_ledger")
        if not isinstance(ledger, list) or not ledger:
            raise FractalMoire36Error(
                "overlap_kernel_ledger must be a non-empty list"
            )
        for i, item in enumerate(ledger):
            _nonempty_text(item, f"overlap_kernel_ledger[{i}]")

        gram = _finite_nonnegative(
            packet.get("gram_compatibility_residual"),
            "gram_compatibility_residual",
        )
        inter = _finite_nonnegative(
            packet.get("overlap_intertwiner_residual"),
            "overlap_intertwiner_residual",
        )
        local_u = _finite_nonnegative(
            packet.get("local_relation_unitarity_residual"),
            "local_relation_unitarity_residual",
        )

        if gram > tolerance:
            raise FractalMoire36Error(
                "Gram compatibility residual exceeds tolerance"
            )
        if inter > tolerance:
            raise FractalMoire36Error(
                "overlap intertwiner residual exceeds tolerance"
            )
        if local_u > tolerance:
            raise FractalMoire36Error(
                "local relation unitarity residual exceeds tolerance"
            )

        # v0.3 validates the underlying positive compression surface.
        p3["ifs_covariance_mode"] = "COMPRESSION_ONLY"
        p3["local_relative_unitary_claim"] = False
        p3.pop("reducing_commutator_residual", None)
        p3.pop("orbital_ifs_covariance_witness_ref", None)
        p3.pop("local_relation_witness_ref", None)
        p3.pop("intertwiner_residual", None)
        p3.pop("local_unitarity_residual", None)

        overlap_receipt = {
            "mode": OVERLAP_MODE,
            "overlap_level": level,
            "overlap_gram_witness_ref": gram_ref,
            "local_relation_family_witness_ref": local_ref,
            "gram_compatibility_residual": gram,
            "overlap_intertwiner_residual": inter,
            "local_relation_unitarity_residual": local_u,
            "overlap_kernel_ledger": tuple(ledger),
            "quotient_reconstruction_contract": quotient_contract,
            "operator_semantics": "D^* G D = G and R W = W D",
            "quotient_unitary_claim": True,
        }

    out = validate_bridge_packet_v03(p3, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["overlap_covariance_receipt"] = overlap_receipt
    if overlap_receipt is not None:
        out["ifs_covariance_receipt"] = {
            "mode": OVERLAP_MODE,
            "operator_semantics": "OVERLAP_GRAM_QUOTIENT",
            "recursive_unitary_branch": False,
            "quotient_unitary_claim": True,
        }
    out["canon_allowed"] = False
    return out
