import math
import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
    projective_residual36,
    validate_bridge_packet,
)


def _base_packet():
    left = [0.1 * j for j in range(36)]
    right = [x + 0.7 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.2",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full direct-integral state",
            "branch operator spectrum",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
    }


def test_projective_residual_is_common_phase_blind():
    p = _base_packet()
    residual = projective_residual36(p["left_phase36"], p["right_phase36"])\n    assert 0.0 <= residual < 1e-12


def test_projective_residual_detects_heterogeneous_relative_phase():
    left = [0.0] * 36
    right = [0.0] * 18 + [math.pi] * 18
    assert projective_residual36(left, right) > 1.9


def test_ifs_packet_requires_branch_witness():
    p = _base_packet()
    p.update(
        scale_semantics="IFS_COMPRESSION",
        branch_word=[0, 1],
        compressed_mismatch_source="GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        branch_reducing_for_relation=False,
        local_relative_unitary_claim=False,
    )
    with pytest.raises(FractalMoire36Error, match="branch_isometry_witness_ref"):
        validate_bridge_packet(p)


def test_nonreducing_ifs_branch_cannot_claim_local_unitary():
    p = _base_packet()
    p.update(
        scale_semantics="IFS_COMPRESSION",
        branch_word=[0],
        branch_isometry_witness_ref="orbital://fractal-scale-v0.2",
        compressed_mismatch_source="GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        branch_reducing_for_relation=False,
        local_relative_unitary_claim=True,
    )
    with pytest.raises(FractalMoire36Error, match="nonreducing"):
        validate_bridge_packet(p)


def test_reducing_ifs_branch_passes_with_commutator_receipt():
    p = _base_packet()
    p.update(
        scale_semantics="IFS_COMPRESSION",
        branch_word=[1, 0, 1],
        branch_isometry_witness_ref="orbital://fractal-scale-v0.2",
        compressed_mismatch_source="GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        branch_reducing_for_relation=True,
        local_relative_unitary_claim=True,
        reducing_commutator_residual=2e-13,
    )
    out = validate_bridge_packet(p)
    assert out["status"] == "PASS"
    assert out["scale_receipt"]["operator_semantics"] == "V_w^* Delta V_w"


def test_unitary_dilation_requires_witness():
    p = _base_packet()
    p.update(
        scale_semantics="UNITARY_DILATION",
        unitarity_residual=0.0,
        intertwining_residual=0.0,
    )
    with pytest.raises(FractalMoire36Error, match="unitary_scale_witness_ref"):
        validate_bridge_packet(p)


def test_unitary_dilation_passes_with_residuals():
    p = _base_packet()
    p.update(
        scale_semantics="UNITARY_DILATION",
        unitary_scale_witness_ref="scale://unitary-dilation-control",
        unitarity_residual=1e-13,
        intertwining_residual=3e-13,
    )
    out = validate_bridge_packet(p)
    assert out["status"] == "PASS"
    assert out["scale_receipt"]["operator_semantics"] == "D_w^-1 A D_w"


def test_non_36_packet_fails_closed():
    p = _base_packet()
    p["left_phase36"] = p["left_phase36"][:-1]
    p.update(
        scale_semantics="UNITARY_DILATION",
        unitary_scale_witness_ref="scale://unitary-dilation-control",
        unitarity_residual=0.0,
        intertwining_residual=0.0,
    )
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet(p)
