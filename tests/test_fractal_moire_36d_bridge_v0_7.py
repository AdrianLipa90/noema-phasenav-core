import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_7 import (
    validate_bridge_packet_v07,
)


def _base():
    left = [0.01 * j for j in range(36)]
    right = [x + 0.25 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.7",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full branch algebra",
            "unrepresented higher levels",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1],
        "branch_isometry_witness_ref": "orbital://cuntz-branches",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        "ifs_covariance_mode": "COMPRESSION_ONLY",
    }


def _noisy():
    return {
        "depth_mode": "SUMMABLE_DEFECT_INDUCTIVE_COVARIANCE",
        "defect_model": "GEOMETRIC_ENVELOPE",
        "defect_model_witness_ref": "data://geometric-envelope-fit-independent",
        "summability_witness_ref": "orbital://summable-defect-v0.7",
        "limit_theorem_witness_ref": "orbital://inductive-stability-v0.7",
        "noisy_family_witness_ref": "data://cross-level-family",
        "current_level_index": 5,
        "defect_envelope_amplitude": 0.2,
        "defect_envelope_ratio": 0.5,
        "current_intertwiner_defect": 0.005,
        "noisy_depth_information_loss_ledger": [
            "unobserved infinite tail replaced by certified envelope",
        ],
        "noisy_limit_reconstruction_contract": "TAIL_BOUND_ONLY",
    }


def test_noisy_geometric_envelope_passes_and_computes_tail():
    p = _base()
    p.update(_noisy())
    out = validate_bridge_packet_v07(p)
    rec = out["depth_receipt"]
    assert rec["limit_unitary_claim"] is True
    assert rec["current_envelope"] == 0.00625
    assert rec["remaining_tail_bound"] == 0.0125
    assert rec["mismatch_tail_bound"] == 0.025


def test_ratio_one_or_larger_fails_closed():
    for q in (1.0, 1.2):
        p = _base()
        p.update(_noisy())
        p["defect_envelope_ratio"] = q
        with pytest.raises(FractalMoire36Error, match="0 <= q < 1"):
            validate_bridge_packet_v07(p)


def test_observed_defect_above_envelope_fails():
    p = _base()
    p.update(_noisy())
    p["current_intertwiner_defect"] = 0.02
    with pytest.raises(FractalMoire36Error, match="exceeds"):
        validate_bridge_packet_v07(p)


def test_missing_summability_witness_fails():
    p = _base()
    p.update(_noisy())
    del p["summability_witness_ref"]
    with pytest.raises(FractalMoire36Error, match="summability_witness_ref"):
        validate_bridge_packet_v07(p)


def test_exact_v06_depth_mode_still_passes_through():
    p = _base()
    p["depth_mode"] = "FINITE_LEVEL_ONLY"
    out = validate_bridge_packet_v07(p)
    assert out["depth_receipt"]["mode"] == "FINITE_LEVEL_ONLY"


def test_exact_36_firewall_inherited():
    p = _base()
    p.update(_noisy())
    p["right_phase36"] = p["right_phase36"][:-1]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v07(p)
