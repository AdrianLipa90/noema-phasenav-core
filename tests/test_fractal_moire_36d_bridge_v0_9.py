import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_9 import (
    validate_bridge_packet_v09,
)


def _base():
    left = [0.012 * j for j in range(36)]
    right = [x + 0.19 for x in left]
    return {
        "schema": "phasenav.fractal-moire-36d-bridge/v0.9",
        "left_phase36": left,
        "right_phase36": right,
        "representation_type": "PHASE36",
        "coordinate_ordering": "index-0-to-35",
        "global_u1_quotiented": True,
        "information_loss_ledger": [
            "full overlap matrix family",
            "full direct-integral state",
        ],
        "reconstruction_contract": "NO_EXACT_RECONSTRUCTION",
        "scale_semantics": "IFS_COMPRESSION",
        "branch_word": [0, 1],
        "branch_isometry_witness_ref": "orbital://matrix-overlap-embedding",
        "compressed_mismatch_source": "GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        "ifs_covariance_mode": "OVERLAP_GRAM_COVARIANT",
        "overlap_level": 1,
        "overlap_gram_witness_ref": "orbital://matrix-gram",
        "local_relation_family_witness_ref": "orbital://local-unitaries",
        "gram_compatibility_residual": 2e-13,
        "overlap_intertwiner_residual": 3e-13,
        "local_relation_unitarity_residual": 4e-13,
        "overlap_kernel_ledger": [
            "coefficient null combinations quotient under synthesis",
        ],
        "quotient_reconstruction_contract": "GRAM_QUOTIENT_ONLY",
        "depth_mode": "FINITE_LEVEL_ONLY",
    }


def test_trivial_internal_tensor_passes_only_without_channel_dependent_claim():
    p = _base()
    p.update(
        overlap_internal_mode="TRIVIAL_INTERNAL_TENSOR",
        internal_dimension=4,
        internal_overlap_witness_ref="orbital://g-times-I4",
        internal_stabilizer_residual=2e-13,
        local_unitary_equality_residual=3e-13,
        overlap_component_count=1,
        channel_dependent_internal_claim=False,
    )
    out = validate_bridge_packet_v09(p)
    rec = out["internal_overlap_receipt"]
    assert rec["independent_unitaries_per_component"] == 1


def test_trivial_internal_tensor_rejects_channel_dependent_claim():
    p = _base()
    p.update(
        overlap_internal_mode="TRIVIAL_INTERNAL_TENSOR",
        internal_dimension=4,
        internal_overlap_witness_ref="orbital://g-times-I4",
        internal_stabilizer_residual=0.0,
        local_unitary_equality_residual=0.0,
        overlap_component_count=1,
        channel_dependent_internal_claim=True,
    )
    with pytest.raises(FractalMoire36Error, match="forbids"):
        validate_bridge_packet_v09(p)


def test_full_rank_frame_conjugacy_passes_as_one_external_operator():
    p = _base()
    p.update(
        overlap_internal_mode="FULL_RANK_FRAME_CONJUGACY",
        internal_dimension=3,
        internal_overlap_witness_ref="orbital://unitary-channel-frames",
        internal_stabilizer_residual=2e-13,
        frame_unitarity_residual=3e-13,
        external_operator_equality_residual=4e-13,
        independent_external_dynamics_claim=False,
    )
    out = validate_bridge_packet_v09(p)
    assert (
        out["internal_overlap_receipt"]["semantics"]
        == "ONE_EXTERNAL_UNITARY_IN_CHANNEL_FRAMES"
    )


def test_full_rank_frame_rejects_independent_external_dynamics_claim():
    p = _base()
    p.update(
        overlap_internal_mode="FULL_RANK_FRAME_CONJUGACY",
        internal_dimension=2,
        internal_overlap_witness_ref="orbital://unitary-channel-frames",
        internal_stabilizer_residual=0.0,
        frame_unitarity_residual=0.0,
        external_operator_equality_residual=0.0,
        independent_external_dynamics_claim=True,
    )
    with pytest.raises(FractalMoire36Error, match="forbids"):
        validate_bridge_packet_v09(p)


def test_rank_deficient_mode_exposes_hidden_kernel_dimension():
    p = _base()
    p.update(
        overlap_internal_mode="RANK_DEFICIENT_STABILIZER",
        internal_dimension=4,
        cross_gram_rank=2,
        internal_overlap_witness_ref="orbital://rank2-cross-gram",
        internal_stabilizer_residual=2e-13,
        hidden_freedom_witness_ref="orbital://kernel-sector",
        visible_support_consistency_residual=3e-13,
    )
    out = validate_bridge_packet_v09(p)
    rec = out["internal_overlap_receipt"]
    assert rec["kernel_dimension_lower_bound"] == 2
    assert rec["genuine_hidden_local_freedom_candidate"] is True


def test_rank_deficient_mode_rejects_full_rank():
    p = _base()
    p.update(
        overlap_internal_mode="RANK_DEFICIENT_STABILIZER",
        internal_dimension=3,
        cross_gram_rank=3,
        internal_overlap_witness_ref="orbital://full-rank",
        internal_stabilizer_residual=0.0,
        hidden_freedom_witness_ref="orbital://none",
        visible_support_consistency_residual=0.0,
    )
    with pytest.raises(FractalMoire36Error, match="cross_gram_rank"):
        validate_bridge_packet_v09(p)


def test_general_matrix_gram_bounds_pass():
    p = _base()
    p.update(
        overlap_internal_mode="GENERAL_MATRIX_GRAM_STABILIZER",
        internal_dimension=6,
        matrix_gram_witness_ref="orbital://matrix-gram-family",
        matrix_stabilizer_witness_ref="orbital://matrix-stabilizer",
        internal_stabilizer_residual=4e-13,
        matrix_gram_rank_lower_bound=2,
        matrix_gram_rank_upper_bound=5,
    )
    out = validate_bridge_packet_v09(p)
    rec = out["internal_overlap_receipt"]
    assert rec["matrix_gram_rank_lower_bound"] == 2
    assert rec["matrix_gram_rank_upper_bound"] == 5


def test_internal_mode_requires_overlap_semantics():
    p = _base()
    p.update(
        overlap_internal_mode="TRIVIAL_INTERNAL_TENSOR",
        internal_dimension=2,
        internal_overlap_witness_ref="orbital://gI",
        internal_stabilizer_residual=0.0,
        local_unitary_equality_residual=0.0,
        overlap_component_count=1,
        channel_dependent_internal_claim=False,
    )
    p["ifs_covariance_mode"] = "COMPRESSION_ONLY"
    with pytest.raises(FractalMoire36Error, match="requires OVERLAP"):
        validate_bridge_packet_v09(p)


def test_exact_36_firewall_is_inherited():
    p = _base()
    p["left_phase36"] = p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error, match="exactly 36"):
        validate_bridge_packet_v09(p)
