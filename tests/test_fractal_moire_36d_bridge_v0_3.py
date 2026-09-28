import math
import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_3 import (
    validate_bridge_packet_v03,
)


def _base():
    left = [0.07 * j for j in range(36)]
    right = [x + 0.5 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.3",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full direct-integral state",
            "unrepresented cylinder relations",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
    }


def _ifs_common():
    return {
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1, 1],
        "branch_isometry_witness_ref": "orbital://fractal-scale-v0.2",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
    }


def test_compression_only_passes_without_unitary_promotion():
    p = _base()
    p.update(_ifs_common())
    p["ifs_covariance_mode"] = "COMPRESSION_ONLY"
    out = validate_bridge_packet_v03(p)
    assert out["status"] == "PASS"
    assert out["ifs_covariance_receipt"]["recursive_unitary_branch"] is False


def test_compression_only_rejects_local_unitary_claim():
    p = _base()
    p.update(_ifs_common())
    p.update(
        ifs_covariance_mode="COMPRESSION_ONLY",
        local_relative_unitary_claim=True,
    )
    with pytest.raises(FractalMoire36Error, match="COMPRESSION_ONLY"):
        validate_bridge_packet_v03(p)


def test_fixed_branch_intertwiner_passes():
    p = _base()
    p.update(_ifs_common())
    p.update(
        ifs_covariance_mode="FIXED_BRANCH_UNITARY_INTERTWINER",
        orbital_ifs_covariance_witness_ref="orbital://covariance-v0.3",
        local_relation_witness_ref="orbital://word-011-relation",
        intertwiner_residual=2.0e-13,
        local_unitarity_residual=3.0e-13,
        reducing_commutator_residual=4.0e-13,
    )
    out = validate_bridge_packet_v03(p)
    rec = out["ifs_covariance_receipt"]
    assert rec["recursive_unitary_branch"] is True
    assert rec["operator_semantics"] == "R V_w = V_w R_w"
    assert out["projective_residual36"] >= 0.0


def test_fixed_branch_rejects_failed_intertwiner():
    p = _base()
    p.update(_ifs_common())
    p.update(
        ifs_covariance_mode="FIXED_BRANCH_UNITARY_INTERTWINER",
        orbital_ifs_covariance_witness_ref="orbital://covariance-v0.3",
        local_relation_witness_ref="orbital://word-011-relation",
        intertwiner_residual=1.0e-5,
        local_unitarity_residual=0.0,
        reducing_commutator_residual=0.0,
    )
    with pytest.raises(FractalMoire36Error, match="intertwiner"):
        validate_bridge_packet_v03(p)


def test_fixed_branch_rejects_failed_local_unitarity():
    p = _base()
    p.update(_ifs_common())
    p.update(
        ifs_covariance_mode="FIXED_BRANCH_UNITARY_INTERTWINER",
        orbital_ifs_covariance_witness_ref="orbital://covariance-v0.3",
        local_relation_witness_ref="orbital://word-011-relation",
        intertwiner_residual=0.0,
        local_unitarity_residual=1.0e-4,
        reducing_commutator_residual=0.0,
    )
    with pytest.raises(FractalMoire36Error, match="unitarity"):
        validate_bridge_packet_v03(p)


def test_unitary_dilation_remains_separate():
    p = _base()
    p.update(
        scale_semantics="UNITARY_DILATION",
        unitary_scale_witness_ref="scale://unitary-control",
        unitarity_residual=1.0e-13,
        intertwining_residual=2.0e-13,
    )
    out = validate_bridge_packet_v03(p)
    assert out["status"] == "PASS"
    assert out["ifs_covariance_receipt"] is None


def test_unitary_dilation_rejects_ifs_mode_mix():
    p = _base()
    p.update(
        scale_semantics="UNITARY_DILATION",
        unitary_scale_witness_ref="scale://unitary-control",
        unitarity_residual=0.0,
        intertwining_residual=0.0,
        ifs_covariance_mode="COMPRESSION_ONLY",
    )
    with pytest.raises(FractalMoire36Error, match="must not"):
        validate_bridge_packet_v03(p)


def test_exact_36_firewall_is_inherited():
    p = _base()
    p.update(_ifs_common())
    p["ifs_covariance_mode"] = "COMPRESSION_ONLY"
    p["right_phase36"] = p["right_phase36"] + [0.0]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v03(p)
