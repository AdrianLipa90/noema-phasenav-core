import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_10 import (
    arpl_source_usage,
    validate_bridge_packet_v10,
)


CURRENT_SHA = "22171349917c97392db7d35605f15be1441fa5bb"
OLD_SHA = "705872f11aaf8b933ab3b713fb10443326fde62b"


def _overlap_packet():
    left = [0.011 * j for j in range(36)]
    right = [x + 0.17 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.10",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full ARPL inverse-limit hull",
            "unrepresented active channels",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1],
        "branch_isometry_witness_ref": "on-primes://normalized-hit-cylinder",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        "ifs_covariance_mode": "OVERLAP_GRAM_COVARIANT",
        "overlap_level": 1,
        "overlap_gram_witness_ref": "on-primes://phase-covering-gram",
        "local_relation_family_witness_ref": "on-primes://local-family",
        "gram_compatibility_residual": 2e-13,
        "overlap_intertwiner_residual": 3e-13,
        "local_relation_unitarity_residual": 4e-13,
        "overlap_kernel_ledger": [
            "linear dependencies among hit-cylinder indicators",
        ],
        "quotient_reconstruction_contract": "GRAM_QUOTIENT_ONLY",
        "depth_mode": "FINITE_LEVEL_ONLY",
        "overlap_source_subtype": "ARPL_HIT_OVERLAP_GRAM",
        "arpl_bridge_witness_ref": "on-primes://bridge-v0.2-r4",
        "arpl_gram_witness_ref": "on-primes://phase-covering-gram-v0.1",
        "arpl_normalized_gram_witness_ref": "on-primes://normalized-gram-v0.2",
        "arpl_separation_h": 6,
        "arpl_prime_support": [5, 7, 11, 13, 19],
        "arpl_gram_normalization_residual": 2e-13,
        "arithmetic_pulse_scalar_adapter_status": "FAIL_STABILIZER",
        "arithmetic_pulse_scalar_adapter_residual": 1.0236181222825256,
    }


def _pin():
    return {
        "arpl_source_repository": "AdrianLipa90/On-Primes",
        "arpl_source_branch": (
            "integrate/arpl-fractal-orbital-bridge-v0.2-20260926-r4"
        ),
        "arpl_source_commit_sha": CURRENT_SHA,
        "arpl_source_files": [
            "proofs/ARPL_FRACTAL_ORBITAL_BLOCK_COCYCLE_BRIDGE_V0_2.md",
            "src/on_primes/fractal_orbital_bridge.py",
            "tests/test_fractal_orbital_bridge.py",
        ],
        "arpl_source_pin_witness_ref": "gremlin://arpl-r4-pin-20260926",
    }


def test_arpl_usage_detects_overlap_surface():
    p = _overlap_packet()
    assert arpl_source_usage(p) == ("ARPL_HIT_OVERLAP_GRAM",)


def test_current_r4_immutable_pin_passes():
    p = _overlap_packet()
    p.update(_pin())
    out = validate_bridge_packet_v10(p)
    rec = out["arpl_source_pin_receipt"]
    assert rec["commit_sha"] == CURRENT_SHA
    assert rec["immutable_pin"] is True
    assert rec["arpl_surfaces"] == ("ARPL_HIT_OVERLAP_GRAM",)


def test_arpl_packet_without_pin_fails():
    p = _overlap_packet()
    with pytest.raises(FractalMoire36Error, match="arpl_source_repository"):
        validate_bridge_packet_v10(p)


def test_old_superseded_pin_is_rejected():
    p = _overlap_packet()
    p.update(_pin())
    p["arpl_source_commit_sha"] = OLD_SHA
    with pytest.raises(FractalMoire36Error, match="superseded"):
        validate_bridge_packet_v10(p)


def test_malformed_sha_is_rejected():
    p = _overlap_packet()
    p.update(_pin())
    p["arpl_source_commit_sha"] = "1234"
    with pytest.raises(FractalMoire36Error, match="40 hexadecimal"):
        validate_bridge_packet_v10(p)


def test_empty_source_file_ledger_is_rejected():
    p = _overlap_packet()
    p.update(_pin())
    p["arpl_source_files"] = []
    with pytest.raises(FractalMoire36Error, match="non-empty list"):
        validate_bridge_packet_v10(p)


def test_non_arpl_packet_does_not_require_arpl_pin():
    p = _overlap_packet()
    p.pop("overlap_source_subtype")
    p.pop("arpl_bridge_witness_ref")
    p.pop("arpl_gram_witness_ref")
    p.pop("arpl_normalized_gram_witness_ref")
    p.pop("arpl_separation_h")
    p.pop("arpl_prime_support")
    p.pop("arpl_gram_normalization_residual")
    p.pop("arithmetic_pulse_scalar_adapter_status")
    p.pop("arithmetic_pulse_scalar_adapter_residual")
    out = validate_bridge_packet_v10(p)
    assert out["arpl_source_pin_receipt"] is None


def test_exact_36_firewall_is_inherited():
    p = _overlap_packet()
    p.update(_pin())
    p["left_phase36"] = p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v10(p)
