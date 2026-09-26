from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
    SCHEMA as SCHEMA_V02,
    validate_bridge_packet as validate_v02,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.3"
IFS_COVARIANCE_MODES = {
    "COMPRESSION_ONLY",
    "FIXED_BRANCH_UNITARY_INTERTWINER",
}


def _finite_nonnegative(x: Any, name: str) -> float:
    y = float(x)
    if not math.isfinite(y) or y < 0.0:
        raise FractalMoire36Error(f"{name} must be finite and nonnegative")
    return y


def _nonempty_text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def validate_bridge_packet_v03(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    semantics = packet.get("scale_semantics")
    p2 = dict(packet)
    p2["schema"] = SCHEMA_V02

    covariance_receipt: dict[str, Any] | None = None

    if semantics == "IFS_COMPRESSION":
        mode = packet.get("ifs_covariance_mode")
        if mode not in IFS_COVARIANCE_MODES:
            raise FractalMoire36Error(
                "IFS_COMPRESSION requires a valid ifs_covariance_mode"
            )

        if mode == "COMPRESSION_ONLY":
            if packet.get("local_relative_unitary_claim") is True:
                raise FractalMoire36Error(
                    "COMPRESSION_ONLY cannot claim local relative unitarity"
                )
            p2["branch_reducing_for_relation"] = False
            p2["local_relative_unitary_claim"] = False
            p2.pop("reducing_commutator_residual", None)
            covariance_receipt = {
                "mode": mode,
                "operator_semantics": "V_w^* Delta V_w",
                "recursive_unitary_branch": False,
            }

        else:
            covariance_ref = _nonempty_text(
                packet.get("orbital_ifs_covariance_witness_ref"),
                "orbital_ifs_covariance_witness_ref",
            )
            local_ref = _nonempty_text(
                packet.get("local_relation_witness_ref"),
                "local_relation_witness_ref",
            )
            inter = _finite_nonnegative(
                packet.get("intertwiner_residual"),
                "intertwiner_residual",
            )
            unitary = _finite_nonnegative(
                packet.get("local_unitarity_residual"),
                "local_unitarity_residual",
            )
            comm = _finite_nonnegative(
                packet.get("reducing_commutator_residual"),
                "reducing_commutator_residual",
            )

            if inter > tolerance:
                raise FractalMoire36Error("intertwiner residual exceeds tolerance")
            if unitary > tolerance:
                raise FractalMoire36Error("local unitarity residual exceeds tolerance")
            if comm > tolerance:
                raise FractalMoire36Error(
                    "reducing commutator residual exceeds tolerance"
                )

            p2["branch_reducing_for_relation"] = True
            p2["local_relative_unitary_claim"] = True
            p2["reducing_commutator_residual"] = comm

            covariance_receipt = {
                "mode": mode,
                "orbital_ifs_covariance_witness_ref": covariance_ref,
                "local_relation_witness_ref": local_ref,
                "intertwiner_residual": inter,
                "local_unitarity_residual": unitary,
                "reducing_commutator_residual": comm,
                "operator_semantics": "R V_w = V_w R_w",
                "mismatch_semantics": (
                    "V_w^* Delta V_w = (I-R_w)^*(I-R_w)"
                ),
                "recursive_unitary_branch": True,
            }

    elif semantics == "UNITARY_DILATION":
        if packet.get("ifs_covariance_mode") is not None:
            raise FractalMoire36Error(
                "UNITARY_DILATION packet must not declare ifs_covariance_mode"
            )
    else:
        # v0.2 will produce the canonical scale-semantics error.
        pass

    out = validate_v02(p2, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["ifs_covariance_receipt"] = covariance_receipt
    out["canon_allowed"] = False
    return out
