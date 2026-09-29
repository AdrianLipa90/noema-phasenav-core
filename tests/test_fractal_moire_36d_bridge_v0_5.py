import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_5 import (
    validate_bridge_packet_v05,
)


def _base():
    left = [0.03 * j for j in range(36)]
    right = [x + 0.2 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.5",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full branch block matrix",
            "full direct-integral state",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1],
        "branch_isometry_witness_ref": "orbital://cuntz-branches",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
    }


def _residuals():
    return {
        "block_covariance_witness_ref": "orbital://block-v0.5",
        "block_unitarity_residual": 2e-13,
        "block_reconstruction_residual": 3e-13,
        "block_mismatch_residual": 4e-13,
    }


def test_permutation_packet_passes():
    p = _base()
    p.update(_residuals())
    p.update(
        ifs_covariance_mode="BRANCH_PERMUTATION_UNITARY",
        branch_count=2,
        branch_permutation=[1, 0],
    )
    out = validate_bridge_packet_v05(p)
    rec = out["block_covariance_receipt"]
    assert rec["branch_permutation"] == (1, 0)
    assert rec["fixed_branch"] is False


def test_invalid_permutation_fails_closed():
    p = _base()
    p.update(_residuals())
    p.update(
        ifs_covariance_mode="BRANCH_PERMUTATION_UNITARY",
        branch_count=3,
        branch_permutation=[0, 0, 2],
    )
    with pytest.raises(FractalMoire36Error, match="bijection"):
        validate_bridge_packet_v05(p)


def test_generic_cocycle_packet_passes():
    p = _base()
    p.update(_residuals())
    p.update(
        ifs_covariance_mode="CUNTZ_BLOCK_COCYCLE_UNITARY",
        branch_count=3,
        cocycle_witness_ref="orbital://controlled-cocycle",
        offdiagonal_transition_ledger=[
            "0->1 on boundary projector",
            "1->2 on boundary projector",
            "2->0 on boundary projector",
        ],
    )
    out = validate_bridge_packet_v05(p)
    assert out["block_covariance_receipt"]["mode"] == "CUNTZ_BLOCK_COCYCLE_UNITARY"


def test_arpl_odometer_carry_packet_passes():
    p = _base()
    p.update(_residuals())
    p.update(
        ifs_covariance_mode="CUNTZ_BLOCK_COCYCLE_UNITARY",
        branch_count=3,
        cocycle_witness_ref="on-primes://carry-cocycle-v0.2",
        offdiagonal_transition_ledger=[
            "c->c on I-Q",
            "c->c+1 mod b on Q",
        ],
        cocycle_subtype="ARPL_ODOMETER_CARRY",
        arpl_refinement_witness_ref="on-primes://ARPL-refinement",
        coarse_clock_size=6,
        refinement_branching=3,
        carry_cocycle_residual=0.0,
    )
    out = validate_bridge_packet_v05(p)
    arpl = out["block_covariance_receipt"]["arpl"]
    assert arpl["fine_clock_size"] == 18
    assert arpl["carry_cocycle_residual"] == 0.0


def test_arpl_branch_count_must_match_refinement():
    p = _base()
    p.update(_residuals())
    p.update(
        ifs_covariance_mode="CUNTZ_BLOCK_COCYCLE_UNITARY",
        branch_count=2,
        cocycle_witness_ref="on-primes://carry-cocycle-v0.2",
        offdiagonal_transition_ledger=["carry"],
        cocycle_subtype="ARPL_ODOMETER_CARRY",
        arpl_refinement_witness_ref="on-primes://ARPL-refinement",
        coarse_clock_size=6,
        refinement_branching=3,
        carry_cocycle_residual=0.0,
    )
    with pytest.raises(FractalMoire36Error, match="branch_count"):
        validate_bridge_packet_v05(p)


def test_bad_block_residual_fails_closed():
    p = _base()
    p.update(_residuals())
    p.update(
        ifs_covariance_mode="BRANCH_PERMUTATION_UNITARY",
        branch_count=2,
        branch_permutation=[1, 0],
        block_reconstruction_residual=1e-4,
    )
    with pytest.raises(FractalMoire36Error, match="reconstruction"):
        validate_bridge_packet_v05(p)


def test_exact_36_firewall_is_inherited():
    p = _base()
    p.update(_residuals())
    p.update(
        ifs_covariance_mode="BRANCH_PERMUTATION_UNITARY",
        branch_count=2,
        branch_permutation=[1, 0],
    )
    p["right_phase36"] = p["right_phase36"][:-1]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v05(p)
