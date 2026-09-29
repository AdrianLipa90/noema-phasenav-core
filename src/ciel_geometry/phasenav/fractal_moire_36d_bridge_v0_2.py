from __future__ import annotations

import cmath
import math
from typing import Any, Mapping, Sequence


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.2"
SCALE_SEMANTICS = {"IFS_COMPRESSION", "UNITARY_DILATION"}


class FractalMoire36Error(ValueError):
    pass


def _finite_float(x: Any, name: str) -> float:
    y = float(x)
    if not math.isfinite(y):
        raise FractalMoire36Error(f"{name} must be finite")
    return y


def _nonempty_text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def _phase36(values: Sequence[float], name: str) -> tuple[float, ...]:
    if len(values) != 36:
        raise FractalMoire36Error(f"{name} must have exactly 36 coordinates")
    out = tuple(_finite_float(v, name) for v in values)
    return out


def coherence36(left: Sequence[float], right: Sequence[float]) -> complex:
    a = _phase36(left, "left")
    b = _phase36(right, "right")
    return sum(cmath.exp(1j * (y - x)) for x, y in zip(a, b)) / 36.0


def projective_residual36(left: Sequence[float], right: Sequence[float]) -> float:
    c = coherence36(left, right)
    return max(0.0, 2.0 * (1.0 - abs(c)))


def validate_bridge_packet(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    left = _phase36(packet.get("left_phase36", ()), "left_phase36")
    right = _phase36(packet.get("right_phase36", ()), "right_phase36")

    representation_type = _nonempty_text(
        packet.get("representation_type"), "representation_type"
    )
    coordinate_ordering = _nonempty_text(
        packet.get("coordinate_ordering"), "coordinate_ordering"
    )

    if not isinstance(packet.get("global_u1_quotiented"), bool):
        raise FractalMoire36Error("global_u1_quotiented must be boolean")

    loss = packet.get("information_loss_ledger")
    if not isinstance(loss, list) or not loss:
        raise FractalMoire36Error("information_loss_ledger must be a non-empty list")
    for i, item in enumerate(loss):
        _nonempty_text(item, f"information_loss_ledger[{i}]")

    reconstruction = _nonempty_text(
        packet.get("reconstruction_contract"), "reconstruction_contract"
    )

    semantics = packet.get("scale_semantics")
    if semantics not in SCALE_SEMANTICS:
        raise FractalMoire36Error(
            "scale_semantics must be IFS_COMPRESSION or UNITARY_DILATION"
        )

    scale_receipt: dict[str, Any]
    if semantics == "IFS_COMPRESSION":
        word = packet.get("branch_word")
        if not isinstance(word, list) or not word:
            raise FractalMoire36Error("IFS_COMPRESSION requires non-empty branch_word")
        if not all(isinstance(x, int) and x >= 0 for x in word):
            raise FractalMoire36Error("branch_word symbols must be non-negative integers")

        witness = _nonempty_text(
            packet.get("branch_isometry_witness_ref"),
            "branch_isometry_witness_ref",
        )
        source = packet.get("compressed_mismatch_source")
        if source != "GLOBAL_POSITIVE_OPERATOR_COMPRESSION":
            raise FractalMoire36Error(
                "IFS_COMPRESSION requires GLOBAL_POSITIVE_OPERATOR_COMPRESSION"
            )

        reducing = packet.get("branch_reducing_for_relation")
        local_unitary = packet.get("local_relative_unitary_claim")
        if not isinstance(reducing, bool) or not isinstance(local_unitary, bool):
            raise FractalMoire36Error(
                "branch_reducing_for_relation and local_relative_unitary_claim "
                "must be boolean"
            )
        if local_unitary and not reducing:
            raise FractalMoire36Error(
                "nonreducing IFS branch cannot claim local relative unitarity"
            )

        commutator_residual = None
        if reducing:
            commutator_residual = _finite_float(
                packet.get("reducing_commutator_residual"),
                "reducing_commutator_residual",
            )
            if commutator_residual < 0.0 or commutator_residual > tolerance:
                raise FractalMoire36Error(
                    "reducing commutator residual exceeds tolerance"
                )

        scale_receipt = {
            "branch_word": tuple(word),
            "branch_isometry_witness_ref": witness,
            "compressed_mismatch_source": source,
            "branch_reducing_for_relation": reducing,
            "local_relative_unitary_claim": local_unitary,
            "reducing_commutator_residual": commutator_residual,
            "operator_semantics": "V_w^* Delta V_w",
        }

    else:
        witness = _nonempty_text(
            packet.get("unitary_scale_witness_ref"), "unitary_scale_witness_ref"
        )
        unitary_residual = _finite_float(
            packet.get("unitarity_residual"), "unitarity_residual"
        )
        intertwining_residual = _finite_float(
            packet.get("intertwining_residual"), "intertwining_residual"
        )
        if unitary_residual < 0.0 or unitary_residual > tolerance:
            raise FractalMoire36Error("unitarity residual exceeds tolerance")
        if intertwining_residual < 0.0 or intertwining_residual > tolerance:
            raise FractalMoire36Error("intertwining residual exceeds tolerance")

        scale_receipt = {
            "unitary_scale_witness_ref": witness,
            "unitarity_residual": unitary_residual,
            "intertwining_residual": intertwining_residual,
            "operator_semantics": "D_w^-1 A D_w",
        }

    coh = coherence36(left, right)
    residual = max(0.0, 2.0 * (1.0 - abs(coh)))

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "representation_type": representation_type,
        "coordinate_ordering": coordinate_ordering,
        "global_u1_quotiented": packet["global_u1_quotiented"],
        "information_loss_ledger": tuple(loss),
        "reconstruction_contract": reconstruction,
        "scale_semantics": semantics,
        "scale_receipt": scale_receipt,
        "coherence36_real": coh.real,
        "coherence36_imag": coh.imag,
        "coherence36_abs": abs(coh),
        "projective_residual36": residual,
        "canon_allowed": False,
    }
