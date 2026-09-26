import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_11 import (
    validate_bridge_packet_v11,
)

SOURCE_SHA="98e5cb10460a233946ce7e2afdbc521b6a234886"


def _base():
    left=[0.01*j for j in range(36)]
    right=[x+0.13 for x in left]
    return {
        "schema":"phasenav.fractal-moire-36d-bridge/v0.11",
        "left_phase36":left,
        "right_phase36":right,
        "representation_type":"PHASE36",
        "coordinate_ordering":"index-0-to-35",
        "global_u1_quotiented":True,
        "information_loss_ledger":["full rectangular matrices remain upstream"],
        "reconstruction_contract":"NO_EXACT_RECONSTRUCTION",
        "scale_semantics":"IFS_COMPRESSION",
        "branch_word":[0,1],
        "branch_isometry_witness_ref":"on-primes://clock-fibre-pullbacks",
        "compressed_mismatch_source":"GLOBAL_POSITIVE_OPERATOR_COMPRESSION",
        "ifs_covariance_mode":"OVERLAP_GRAM_COVARIANT",
        "overlap_level":1,
        "overlap_gram_witness_ref":"on-primes://clock-fibre-matrix-gram",
        "local_relation_family_witness_ref":"on-primes://local-odometers",
        "gram_compatibility_residual":0.0,
        "overlap_intertwiner_residual":0.0,
        "local_relation_unitarity_residual":0.0,
        "overlap_kernel_ledger":["rectangular pairwise kernels remain upstream"],
        "quotient_reconstruction_contract":"HETEROGENEOUS_GRAM_WITNESS_ONLY",
        "depth_mode":"FINITE_LEVEL_ONLY",
        "matrix_overlap_source_subtype":"ARPL_CLOCK_FIBRE_MATRIX_GRAM",
        "orbital_heterogeneous_theorem_ref":"orbital://heterogeneous-overlap-v0.9",
        "matrix_storage_contract":"UPSTREAM_WITNESS_ONLY",
        "arpl_separation_h":6,
        "arpl_prime_support":[5,7,11,13,19],
        "max_pair_odometer_intertwiner_residual":0.0,
        "max_pair_mismatch_intertwiner_residual":0.0,
        "heterogeneous_fibre_information_loss_ledger":[
            "full local fibre vectors",
            "full rectangular cross-Gram matrices",
            "infinite active-channel tail",
        ],
        "arpl_source_repository":"AdrianLipa90/On-Primes",
        "arpl_source_branch":"integrate/arpl-clock-fibre-matrix-gram-v0.1-20260926",
        "arpl_source_commit_sha":SOURCE_SHA,
        "arpl_source_files":[
            "proofs/ARPL_CLOCK_FIBRE_MATRIX_GRAM_V0_1.md",
            "proofs/ARPL_CLOCK_FIBRE_NETWORK_VISIBILITY_V0_1.md",
            "src/on_primes/clock_fibre_gram.py",
            "receipts/ARPL_CLOCK_FIBRE_NETWORK_VISIBILITY_V0_1_VALIDATION_20260926.md",
        ],
        "arpl_source_pin_witness_ref":"gremlin://arpl-clock-fibre-pin",
    }


def test_h6_clock_fibre_packet_computes_periods_ranks_and_hidden_modes():
    out=validate_bridge_packet_v11(_base())
    rec=out["heterogeneous_arpl_matrix_receipt"]
    assert rec["local_clock_periods"]==(2,3,5,6,9)
    assert rec["common_clock_size"]==90
    assert rec["local_fibre_dimension_sum"]==25
    assert rec["network_hidden_dimensions"]==(0,0,4,2,6)
    assert rec["pair_rank_matrix"][2][4]==1
    assert rec["pair_rank_matrix"][3][4]==3
    assert rec["phasenav_dimension_identified_with_fibre_sum"] is False


def test_wrong_intertwiner_residual_fails():
    p=_base()
    p["max_pair_odometer_intertwiner_residual"]=1e-4
    with pytest.raises(FractalMoire36Error,match="odometer"):
        validate_bridge_packet_v11(p)


def test_inactive_channel_fails():
    p=_base()
    p["arpl_prime_support"]=[5,7,11,13,19,3]
    with pytest.raises(FractalMoire36Error):
        validate_bridge_packet_v11(p)


def test_duplicate_support_fails():
    p=_base()
    p["arpl_prime_support"]=[5,7,7]
    with pytest.raises(FractalMoire36Error,match="distinct"):
        validate_bridge_packet_v11(p)


def test_matrix_payload_cannot_be_silently_claimed_embedded():
    p=_base()
    p["matrix_storage_contract"]="EMBEDDED_IN_36D"
    with pytest.raises(FractalMoire36Error,match="UPSTREAM_WITNESS_ONLY"):
        validate_bridge_packet_v11(p)


def test_exact_36_firewall_inherited():
    p=_base()
    p["left_phase36"]=p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error,match="exactly 36"):
        validate_bridge_packet_v11(p)
