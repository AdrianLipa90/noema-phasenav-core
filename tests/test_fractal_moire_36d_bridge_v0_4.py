import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_4 import (
    validate_bridge_packet_v04,
)


def _base():
    left = [0.05 * j for j in range(36)]
    right = [x + 0.4 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.4",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full direct-integral state",
            "full overlap operator spectrum",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1],
        "branch_isometry_witness_ref": "orbital://overlap-embedding-v0.4",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
    }


def _overlap_fields():
    return {
        "ifs_covariance_mode": "OVERLAP_GRAM_COVARIANT",
        "overlap_level": 2,
        "overlap_gram_witness_ref": "orbital://gram-level-2",
        "local_relation_family_witness_ref": "orbital://local-Rw-family",
        "gram_compatibility_residual": 2e-13,
        "overlap_intertwiner_residual": 3e-13,
        "local_relation_unitarity_residual": 4e-13,
        "overlap_kernel_ledger": [
            "coefficient null combinations quotient out under synthesis",
        ],
        "quotient_reconstruction_contract": "GRAM_QUOTIENT_ONLY",
    }


def test_overlap_gram_packet_passes():
    p = _base()
    p.update(_overlap_fields())
    out = validate_bridge_packet_v04(p)
    assert out["status"] == "PASS"
    rec = out["overlap_covariance_receipt"]
    assert rec["quotient_unitary_claim"] is True
    assert rec["operator_semantics"] == "D^* G D = G and R W = W D"
    assert out["projective_residual36"] >= 0.0


def test_overlap_requires_kernel_ledger():
    p = _base()
    p.update(_overlap_fields())
    p["overlap_kernel_ledger"] = []
    with pytest.raises(FractalMoire36Error, match="overlap_kernel_ledger"):
        validate_bridge_packet_v04(p)


def test_overlap_rejects_bad_gram_residual():
    p = _base()
    p.update(_overlap_fields())
    p["gram_compatibility_residual"] = 1e-4
    with pytest.raises(FractalMoire36Error, match="Gram"):
        validate_bridge_packet_v04(p)


def test_overlap_rejects_bad_intertwiner_residual():
    p = _base()
    p.update(_overlap_fields())
    p["overlap_intertwiner_residual"] = 1e-5
    with pytest.raises(FractalMoire36Error, match="intertwiner"):
        validate_bridge_packet_v04(p)


def test_overlap_rejects_bad_local_unitarity():
    p = _base()
    p.update(_overlap_fields())
    p["local_relation_unitarity_residual"] = 1e-3
    with pytest.raises(FractalMoire36Error, match="unitarity"):
        validate_bridge_packet_v04(p)


def test_overlap_requires_ifs_compression():
    p = _base()
    p.update(_overlap_fields())
    p["scale_semantics"] = "UNITARY_DILATION"
    with pytest.raises(FractalMoire36Error, match="requires IFS_COMPRESSION"):
        validate_bridge_packet_v04(p)


def test_v03_fixed_branch_mode_still_passes_through_v04():
    p = _base()
    p.update(
        ifs_covariance_mode="FIXED_BRANCH_UNITARY_INTERTWINER",
        orbital_ifs_covariance_witness_ref="orbital://covariance-v0.3",
        local_relation_witness_ref="orbital://word-01",
        intertwiner_residual=0.0,
        local_unitarity_residual=0.0,
        reducing_commutator_residual=0.0,
    )
    out = validate_bridge_packet_v04(p)
    assert out["status"] == "PASS"
    assert out["overlap_covariance_receipt"] is None


def test_exact_36_firewall_is_inherited():
    p = _base()
    p.update(_overlap_fields())
    p["left_phase36"] = p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v04(p)
