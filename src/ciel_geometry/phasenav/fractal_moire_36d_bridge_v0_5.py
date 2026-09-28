from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_4 import (
    SCHEMA as SCHEMA_V04,
    validate_bridge_packet_v04,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.5"
PERMUTATION_MODE = "BRANCH_PERMUTATION_UNITARY"
COCYCLE_MODE = "CUNTZ_BLOCK_COCYCLE_UNITARY"
ARPL_CARRY = "ARPL_ODOMETER_CARRY"


def _finite_nonnegative(x: Any, name: str) -> float:
    y = float(x)
    if not math.isfinite(y) or y < 0.0:
        raise FractalMoire36Error(f"{name} must be finite and nonnegative")
    return y


def _nonempty_text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def _positive_int(x: Any, name: str, minimum: int = 1) -> int:
    if not isinstance(x, int) or x < minimum:
        raise FractalMoire36Error(f"{name} must be an integer >= {minimum}")
    return x


def _block_residuals(packet: Mapping[str, Any], tolerance: float) -> dict[str, float]:
    unitary = _finite_nonnegative(
        packet.get("block_unitarity_residual"), "block_unitarity_residual"
    )
    reconstruction = _finite_nonnegative(
        packet.get("block_reconstruction_residual"),
        "block_reconstruction_residual",
    )
    mismatch = _finite_nonnegative(
        packet.get("block_mismatch_residual"), "block_mismatch_residual"
    )
    if unitary > tolerance:
        raise FractalMoire36Error("block unitarity residual exceeds tolerance")
    if reconstruction > tolerance:
        raise FractalMoire36Error("block reconstruction residual exceeds tolerance")
    if mismatch > tolerance:
        raise FractalMoire36Error("block mismatch residual exceeds tolerance")
    return {
        "block_unitarity_residual": unitary,
        "block_reconstruction_residual": reconstruction,
        "block_mismatch_residual": mismatch,
    }


def validate_bridge_packet_v05(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    mode = packet.get("ifs_covariance_mode")
    p4 = dict(packet)
    p4["schema"] = SCHEMA_V04

    block_receipt: dict[str, Any] | None = None

    if mode in {PERMUTATION_MODE, COCYCLE_MODE}:
        if packet.get("scale_semantics") != "IFS_COMPRESSION":
            raise FractalMoire36Error(
                "Cuntz block modes require IFS_COMPRESSION"
            )

        branch_count = _positive_int(packet.get("branch_count"), "branch_count", 2)
        block_ref = _nonempty_text(
            packet.get("block_covariance_witness_ref"),
            "block_covariance_witness_ref",
        )
        residuals = _block_residuals(packet, tolerance)

        if mode == PERMUTATION_MODE:
            perm = packet.get("branch_permutation")
            if not isinstance(perm, list) or len(perm) != branch_count:
                raise FractalMoire36Error(
                    "branch_permutation must have branch_count entries"
                )
            if sorted(perm) != list(range(branch_count)):
                raise FractalMoire36Error(
                    "branch_permutation must be a bijection"
                )
            block_receipt = {
                "mode": mode,
                "branch_count": branch_count,
                "branch_permutation": tuple(perm),
                "block_covariance_witness_ref": block_ref,
                **residuals,
                "operator_semantics": "R V_i = V_sigma(i) R_i",
                "fixed_branch": False,
            }

        else:
            ledger = packet.get("offdiagonal_transition_ledger")
            if not isinstance(ledger, list) or not ledger:
                raise FractalMoire36Error(
                    "offdiagonal_transition_ledger must be a non-empty list"
                )
            for i, item in enumerate(ledger):
                _nonempty_text(item, f"offdiagonal_transition_ledger[{i}]")
            cocycle_ref = _nonempty_text(
                packet.get("cocycle_witness_ref"),
                "cocycle_witness_ref",
            )

            subtype = packet.get("cocycle_subtype")
            arpl_receipt = None
            if subtype is not None:
                if subtype != ARPL_CARRY:
                    raise FractalMoire36Error("unknown cocycle_subtype")
                arpl_ref = _nonempty_text(
                    packet.get("arpl_refinement_witness_ref"),
                    "arpl_refinement_witness_ref",
                )
                L = _positive_int(
                    packet.get("coarse_clock_size"),
                    "coarse_clock_size",
                    1,
                )
                b = _positive_int(
                    packet.get("refinement_branching"),
                    "refinement_branching",
                    2,
                )
                carry = _finite_nonnegative(
                    packet.get("carry_cocycle_residual"),
                    "carry_cocycle_residual",
                )
                if carry > tolerance:
                    raise FractalMoire36Error(
                        "carry cocycle residual exceeds tolerance"
                    )
                if branch_count != b:
                    raise FractalMoire36Error(
                        "ARPL branch_count must equal refinement_branching"
                    )
                arpl_receipt = {
                    "subtype": ARPL_CARRY,
                    "arpl_refinement_witness_ref": arpl_ref,
                    "coarse_clock_size": L,
                    "refinement_branching": b,
                    "fine_clock_size": L * b,
                    "carry_cocycle_residual": carry,
                }

            block_receipt = {
                "mode": mode,
                "branch_count": branch_count,
                "block_covariance_witness_ref": block_ref,
                "cocycle_witness_ref": cocycle_ref,
                "offdiagonal_transition_ledger": tuple(ledger),
                **residuals,
                "operator_semantics": "R V_i = sum_j V_j R_ji",
                "fixed_branch": False,
                "arpl": arpl_receipt,
            }

        # v0.4 validates the underlying positive-compression contract.
        p4["ifs_covariance_mode"] = "COMPRESSION_ONLY"
        p4["local_relative_unitary_claim"] = False

    out = validate_bridge_packet_v04(p4, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["block_covariance_receipt"] = block_receipt
    if block_receipt is not None:
        out["ifs_covariance_receipt"] = {
            "mode": mode,
            "operator_semantics": block_receipt["operator_semantics"],
            "recursive_unitary_branch": False,
            "block_unitary_claim": True,
        }
    out["canon_allowed"] = False
    return out
