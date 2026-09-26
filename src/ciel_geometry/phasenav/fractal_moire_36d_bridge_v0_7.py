from __future__ import annotations

import math
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_6 import (
    SCHEMA as SCHEMA_V06,
    validate_bridge_packet_v06,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.7"
NOISY_MODE = "SUMMABLE_DEFECT_INDUCTIVE_COVARIANCE"
GEOMETRIC = "GEOMETRIC_ENVELOPE"


def _text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def _nonnegative(x: Any, name: str) -> float:
    y = float(x)
    if not math.isfinite(y) or y < 0.0:
        raise FractalMoire36Error(f"{name} must be finite and nonnegative")
    return y


def _level(x: Any, name: str) -> int:
    if not isinstance(x, int) or x < 0:
        raise FractalMoire36Error(f"{name} must be a nonnegative integer")
    return x


def validate_bridge_packet_v07(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    depth_mode = packet.get("depth_mode")
    p6 = dict(packet)
    p6["schema"] = SCHEMA_V06

    noisy_receipt = None

    if depth_mode == NOISY_MODE:
        if packet.get("defect_model") != GEOMETRIC:
            raise FractalMoire36Error(
                "SUMMABLE_DEFECT mode currently requires GEOMETRIC_ENVELOPE"
            )

        model_ref = _text(
            packet.get("defect_model_witness_ref"),
            "defect_model_witness_ref",
        )
        sum_ref = _text(
            packet.get("summability_witness_ref"),
            "summability_witness_ref",
        )
        theorem_ref = _text(
            packet.get("limit_theorem_witness_ref"),
            "limit_theorem_witness_ref",
        )
        family_ref = _text(
            packet.get("noisy_family_witness_ref"),
            "noisy_family_witness_ref",
        )

        N = _level(packet.get("current_level_index"), "current_level_index")
        A = _nonnegative(
            packet.get("defect_envelope_amplitude"),
            "defect_envelope_amplitude",
        )
        q = float(packet.get("defect_envelope_ratio"))
        if not math.isfinite(q) or q < 0.0 or q >= 1.0:
            raise FractalMoire36Error(
                "defect_envelope_ratio must satisfy 0 <= q < 1"
            )

        observed = _nonnegative(
            packet.get("current_intertwiner_defect"),
            "current_intertwiner_defect",
        )
        current_envelope = A * (q ** N)
        if observed > current_envelope + tolerance:
            raise FractalMoire36Error(
                "current intertwiner defect exceeds geometric envelope"
            )

        tail = current_envelope / (1.0 - q)

        ledger = packet.get("noisy_depth_information_loss_ledger")
        if not isinstance(ledger, list) or not ledger:
            raise FractalMoire36Error(
                "noisy_depth_information_loss_ledger must be non-empty"
            )
        for i, item in enumerate(ledger):
            _text(item, f"noisy_depth_information_loss_ledger[{i}]")

        reconstruction = _text(
            packet.get("noisy_limit_reconstruction_contract"),
            "noisy_limit_reconstruction_contract",
        )

        noisy_receipt = {
            "mode": NOISY_MODE,
            "defect_model": GEOMETRIC,
            "defect_model_witness_ref": model_ref,
            "summability_witness_ref": sum_ref,
            "limit_theorem_witness_ref": theorem_ref,
            "noisy_family_witness_ref": family_ref,
            "current_level_index": N,
            "defect_envelope_amplitude": A,
            "defect_envelope_ratio": q,
            "current_intertwiner_defect": observed,
            "current_envelope": current_envelope,
            "remaining_tail_bound": tail,
            "mismatch_tail_bound": 2.0 * tail,
            "unitary_spectral_distance_bound": tail,
            "mismatch_spectral_distance_bound": 2.0 * tail,
            "noisy_depth_information_loss_ledger": tuple(ledger),
            "noisy_limit_reconstruction_contract": reconstruction,
            "limit_unitary_claim": True,
        }

        # Preserve all lower-level v0.6 checks while bypassing only its exact
        # cross-level depth mode.
        p6["depth_mode"] = "FINITE_LEVEL_ONLY"
        p6["infinite_depth_claim"] = False

    out = validate_bridge_packet_v06(p6, tolerance=tolerance)
    out["schema"] = SCHEMA

    if noisy_receipt is not None:
        out["depth_receipt"] = noisy_receipt

    out["canon_allowed"] = False
    return out
