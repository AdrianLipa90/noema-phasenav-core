import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_8 import (
    validate_bridge_packet_v08,
)


def _base():
    left = [0.015 * j for j in range(36)]
    right = [x + 0.21 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.8",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full ARPL inverse-limit hull",
            "unrepresented active prime channels",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1],
        "branch_isometry_witness_ref": "on-primes://normalized-hit-cylinder-embedding",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        "ifs_covariance_mode": "OVERLAP_GRAM_COVARIANT",
        "overlap_level": 1,
        "overlap_gram_witness_ref": "on-primes://ARPL-phase-covering-Gram",
        "local_relation_family_witness_ref": "on-primes://ARPL-local-relation-family",
        "gram_compatibility_residual": 2e-13,
        "overlap_intertwiner_residual": 3e-13,
        "local_relation_unitarity_residual": 4e-13,
        "overlap_kernel_ledger": [
            "linear dependencies among normalized hit-cylinder indicators",
        ],
        "quotient_reconstruction_contract": "GRAM_QUOTIENT_ONLY",
        "depth_mode": "FINITE_LEVEL_ONLY",
    }


def _arpl():
    return {
        "overlap_source_subtype": "ARPL_HIT_OVERLAP_GRAM",
        "arpl_bridge_witness_ref": (
            "github://AdrianLipa90/On-Primes@"
            "705872f11aaf8b933ab3b713fb10443326fde62b/"
            "receipts/ARPL_FRACTAL_ORBITAL_BLOCK_COCYCLE_BRIDGE_V0_2.md"
        ),
        "arpl_gram_witness_ref": "on-primes://ARPL_PHASE_COVERING_GRAM_CRITERION_V0_1",
        "arpl_normalized_gram_witness_ref": "on-primes://fractal-orbital-bridge-v0.2",
        "arpl_separation_h": 6,
        "arpl_prime_support": [5, 7, 11, 13, 19],
        "arpl_gram_normalization_residual": 2e-13,
    }


def test_h6_failed_scalar_adapter_is_preserved_as_fail_without_rejecting_source():
    p = _base()
    p.update(_arpl())
    p.update(
        arithmetic_pulse_scalar_adapter_status="FAIL_STABILIZER",
        arithmetic_pulse_scalar_adapter_residual=1.0236181222825256,
    )
    out = validate_bridge_packet_v08(p)
    rec = out["arpl_overlap_source_receipt"]
    assert rec["scalar_orbital_pulse_promotion"] is False
    assert rec["arithmetic_pulse_scalar_adapter_status"] == "FAIL_STABILIZER"
    assert out["status"] == "PASS"


def test_pass_status_rejects_large_adapter_residual():
    p = _base()
    p.update(_arpl())
    p.update(
        arithmetic_pulse_scalar_adapter_status="PASS_STABILIZER",
        arithmetic_pulse_scalar_adapter_residual=1.0236181222825256,
    )
    with pytest.raises(FractalMoire36Error, match="PASS_STABILIZER"):
        validate_bridge_packet_v08(p)


def test_fail_status_rejects_small_adapter_residual():
    p = _base()
    p.update(_arpl())
    p.update(
        arithmetic_pulse_scalar_adapter_status="FAIL_STABILIZER",
        arithmetic_pulse_scalar_adapter_residual=0.0,
    )
    with pytest.raises(FractalMoire36Error, match="FAIL_STABILIZER"):
        validate_bridge_packet_v08(p)


def test_not_claimed_adapter_passes_without_residual():
    p = _base()
    p.update(_arpl())
    p["arithmetic_pulse_scalar_adapter_status"] = "NOT_CLAIMED"
    out = validate_bridge_packet_v08(p)
    assert out["arpl_overlap_source_receipt"]["scalar_orbital_pulse_promotion"] is False


def test_duplicate_prime_support_fails():
    p = _base()
    p.update(_arpl())
    p["arpl_prime_support"] = [5, 7, 7]
    p["arithmetic_pulse_scalar_adapter_status"] = "NOT_CLAIMED"
    with pytest.raises(FractalMoire36Error, match="distinct"):
        validate_bridge_packet_v08(p)


def test_bad_arpl_separation_fails():
    p = _base()
    p.update(_arpl())
    p["arpl_separation_h"] = 10
    p["arithmetic_pulse_scalar_adapter_status"] = "NOT_CLAIMED"
    with pytest.raises(FractalMoire36Error, match="divisible by 6"):
        validate_bridge_packet_v08(p)


def test_arpl_overlap_subtype_requires_overlap_mode():
    p = _base()
    p.update(_arpl())
    p["ifs_covariance_mode"] = "COMPRESSION_ONLY"
    p["arithmetic_pulse_scalar_adapter_status"] = "NOT_CLAIMED"
    with pytest.raises(FractalMoire36Error, match="requires OVERLAP"):
        validate_bridge_packet_v08(p)


def test_exact_36_firewall_inherited():
    p = _base()
    p.update(_arpl())
    p["arithmetic_pulse_scalar_adapter_status"] = "NOT_CLAIMED"
    p["left_phase36"] = p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v08(p)
