import math
import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_6 import (
    validate_bridge_packet_v06,
)


def _base():
    left = [0.02 * j for j in range(36)]
    right = [x + 0.3 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.6",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full branch algebra",
            "higher refinement levels",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1],
        "branch_isometry_witness_ref": "orbital://cuntz-branches",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        "ifs_covariance_mode": "COMPRESSION_ONLY",
    }


def _step():
    return {
        "level_index": 4,
        "coarse_level_id": "L4",
        "fine_level_id": "L5",
        "embedding_witness_ref": "orbital://coarse-pullback-v0.6",
        "embedding_isometry_residual": 2e-13,
        "cross_level_intertwiner_residual": 3e-13,
        "mismatch_intertwiner_residual": 4e-13,
        "spectral_nesting_residual": 5e-13,
    }


def test_finite_only_passes_without_limit_claim():
    p = _base()
    p["depth_mode"] = "FINITE_LEVEL_ONLY"
    out = validate_bridge_packet_v06(p)
    assert out["depth_receipt"]["infinite_depth_claim"] is False


def test_inductive_step_passes():
    p = _base()
    p["depth_mode"] = "INDUCTIVE_STEP_COVARIANT"
    p.update(_step())
    out = validate_bridge_packet_v06(p)
    assert out["depth_receipt"]["mode"] == "INDUCTIVE_STEP_COVARIANT"


def test_limit_requires_family_witnesses():
    p = _base()
    p["depth_mode"] = "INDUCTIVE_LIMIT_COVARIANT"
    p.update(_step())
    with pytest.raises(FractalMoire36Error, match="inductive_family_witness_ref"):
        validate_bridge_packet_v06(p)


def test_arpl_inductive_limit_packet_passes():
    p = _base()
    p["depth_mode"] = "INDUCTIVE_LIMIT_COVARIANT"
    p.update(_step())
    p.update(
        inductive_family_witness_ref="on-primes://procyclic-refinement",
        limit_theorem_witness_ref="orbital://inductive-limit-v0.6",
        cofinality_witness_ref="on-primes://L_N-to-infinity",
        validated_level_count=6,
        infinite_depth_information_loss_ledger=[
            "all levels above the current finite packet",
            "full infinite operator spectrum",
        ],
        limit_reconstruction_contract="THEOREM_REFERENCE_ONLY",
        infinite_depth_subtype="ARPL_PROCYCLIC_ODOMETER_LIMIT",
        arpl_infinite_spectrum_witness_ref="on-primes://spectrum-v0.3",
        current_clock_size=30,
        next_clock_size=90,
        first_positive_mismatch=4.0 * math.sin(math.pi / 30.0) ** 2,
        finite_spectrum_summary_ref="on-primes://roots-L30",
    )
    out = validate_bridge_packet_v06(p)
    arpl = out["depth_receipt"]["arpl"]
    assert arpl["refinement_branching"] == 3
    assert arpl["limit_unitary_spectrum"] == "S^1"
    assert arpl["limit_mismatch_spectrum"] == "[0,4]"


def test_arpl_nondivisible_clock_refinement_fails():
    p = _base()
    p["depth_mode"] = "INDUCTIVE_LIMIT_COVARIANT"
    p.update(_step())
    p.update(
        inductive_family_witness_ref="on-primes://procyclic-refinement",
        limit_theorem_witness_ref="orbital://inductive-limit-v0.6",
        cofinality_witness_ref="on-primes://L_N-to-infinity",
        validated_level_count=3,
        infinite_depth_information_loss_ledger=["higher levels"],
        limit_reconstruction_contract="THEOREM_REFERENCE_ONLY",
        infinite_depth_subtype="ARPL_PROCYCLIC_ODOMETER_LIMIT",
        arpl_infinite_spectrum_witness_ref="on-primes://spectrum-v0.3",
        current_clock_size=30,
        next_clock_size=91,
        first_positive_mismatch=0.04,
        finite_spectrum_summary_ref="on-primes://roots-L30",
    )
    with pytest.raises(FractalMoire36Error, match="divisible"):
        validate_bridge_packet_v06(p)


def test_bad_step_residual_fails_closed():
    p = _base()
    p["depth_mode"] = "INDUCTIVE_STEP_COVARIANT"
    p.update(_step())
    p["cross_level_intertwiner_residual"] = 1e-3
    with pytest.raises(FractalMoire36Error, match="cross_level"):
        validate_bridge_packet_v06(p)


def test_exact_36_firewall_is_inherited():
    p = _base()
    p["depth_mode"] = "FINITE_LEVEL_ONLY"
    p["left_phase36"] = p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v06(p)
