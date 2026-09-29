import math
import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_13 import (
    validate_bridge_packet_v13,
)


MATRIX_SHA="8781f4a685257eced538daa7462ec4fc48093a6b"
FRONTIER_SHA="deac8af3ae12ac80f0cfab21b440b6e727c0b342"


def _base():
    left=[0.01*j for j in range(36)]
    right=[x+0.13 for x in left]
    return {
        "schema":"phasenav.fractal-moire-36d-bridge/v0.13",
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
        "arpl_source_commit_sha":MATRIX_SHA,
        "arpl_source_files":[
            "proofs/ARPL_CLOCK_FIBRE_MATRIX_GRAM_V0_1.md",
            "proofs/ARPL_CLOCK_FIBRE_NETWORK_VISIBILITY_V0_1.md",
            "src/on_primes/clock_fibre_gram.py",
            "receipts/ARPL_CLOCK_FIBRE_NETWORK_VISIBILITY_V0_1_VALIDATION_20260926.md",
        ],
        "arpl_source_pin_witness_ref":"gremlin://arpl-clock-fibre-pin",
        "infinite_support_visibility_mode":"GRH_SOURCE_PRIME_REPLICATION",
        "grh_assumption_declared":True,
        "unconditional_infinite_exposure_claim":False,
        "physical_observability_claim":False,
        "grh_visibility_theorem_ref":"on-primes://grh-source-prime-replication-v0.1",
        "arpl_visibility_repository":"AdrianLipa90/On-Primes",
        "arpl_visibility_branch":"research/arpl-infinite-clock-visibility-frontier-v0.1-20260926",
        "arpl_visibility_commit_sha":FRONTIER_SHA,
        "arpl_visibility_source_files":[
            "proofs/ARPL_GRH_SOURCE_PRIME_REPLICATION_THEOREM_V0_1.md",
            "receipts/ARPL_GRH_SOURCE_PRIME_REPLICATION_THEOREM_V0_1_VALIDATION_20260926.md",
            "src/on_primes/visibility_frontier.py",
        ],
        "arpl_visibility_pin_witness_ref":"gremlin://grh-exposure-frontier-pin",
        "relational_zero_operator_mode":"ARPL_RELATIONAL_ZERO_PROJECTORS",
        "relational_operator_storage":"UPSTREAM_WITNESS_ONLY",
        "physical_quantum_observable_claim":False,
        "relational_zero_operator_source_ref":(
            "github://AdrianLipa90/On-Primes@"
            "605119b2b2e50ff6eb4cab550382b48630f14c67/"
            "receipts/ARPL_RELATIONAL_ZERO_EXPOSURE_OPERATORS_V0_1_VALIDATION_20260928.md"
        ),
    }


def test_q31_operator_receipt_is_pure_activity_defect():
    p=_base()
    p.update(
        ambient_group_order=30,
        base_subgroup_order=5,
        activity_subgroup_order=15,
        total_subgroup_order=15,
        declared_relational_zero=False,
        declared_total_defect_rank=4,
        activity_projection_residual=3e-16,
        depth_projection_residual=0.0,
        total_projection_residual=3e-16,
        orthogonal_layer_residual=2e-16,
        operator_decomposition_residual=2e-16,
    )
    out=validate_bridge_packet_v13(p)
    rec=out["relational_zero_operator_receipt"]
    assert rec["activity_defect_rank"]==4
    assert rec["depth_defect_rank"]==0
    assert rec["total_defect_rank"]==4
    assert rec["relational_zero"] is False
    assert math.isclose(rec["normalized_relational_defect"],2/3)
    assert rec["operator_spectrum_bound"]==(0,1)


def test_q61_operator_receipt_is_exact_relational_zero():
    p=_base()
    p.update(
        ambient_group_order=60,
        base_subgroup_order=30,
        activity_subgroup_order=30,
        total_subgroup_order=30,
        declared_relational_zero=True,
        declared_total_defect_rank=0,
    )
    out=validate_bridge_packet_v13(p)
    rec=out["relational_zero_operator_receipt"]
    assert rec["activity_defect_rank"]==0
    assert rec["depth_defect_rank"]==0
    assert rec["total_defect_rank"]==0
    assert rec["relational_zero"] is True
    assert rec["normalized_relational_defect"]==0.0


def test_pure_depth_defect_is_distinct_from_activity_defect():
    p=_base()
    p.update(
        ambient_group_order=30,
        base_subgroup_order=6,
        activity_subgroup_order=6,
        total_subgroup_order=30,
        declared_relational_zero=False,
        declared_total_defect_rank=4,
    )
    out=validate_bridge_packet_v13(p)
    rec=out["relational_zero_operator_receipt"]
    assert rec["activity_defect_rank"]==0
    assert rec["depth_defect_rank"]==4
    assert rec["total_defect_rank"]==4


def test_invalid_subgroup_chain_fails_closed():
    p=_base()
    p.update(
        ambient_group_order=30,
        base_subgroup_order=5,
        activity_subgroup_order=6,
        total_subgroup_order=30,
    )
    with pytest.raises(FractalMoire36Error,match="base .* activity .* total .* ambient"):
        validate_bridge_packet_v13(p)


def test_false_zero_declaration_is_rejected():
    p=_base()
    p.update(
        ambient_group_order=30,
        base_subgroup_order=5,
        activity_subgroup_order=15,
        total_subgroup_order=15,
        declared_relational_zero=True,
    )
    with pytest.raises(FractalMoire36Error,match="declared_relational_zero"):
        validate_bridge_packet_v13(p)


def test_physical_quantum_observable_promotion_fails_closed():
    p=_base()
    p.update(
        ambient_group_order=60,
        base_subgroup_order=30,
        activity_subgroup_order=30,
        total_subgroup_order=30,
        physical_quantum_observable_claim=True,
    )
    with pytest.raises(FractalMoire36Error,match="physical quantum observable"):
        validate_bridge_packet_v13(p)


def test_operator_storage_cannot_claim_36d_embedding():
    p=_base()
    p.update(
        ambient_group_order=60,
        base_subgroup_order=30,
        activity_subgroup_order=30,
        total_subgroup_order=30,
        relational_operator_storage="EMBEDDED_IN_36D",
    )
    with pytest.raises(FractalMoire36Error,match="UPSTREAM_WITNESS_ONLY"):
        validate_bridge_packet_v13(p)


def test_exact_36_firewall_remains_inherited():
    p=_base()
    p.update(
        ambient_group_order=60,
        base_subgroup_order=30,
        activity_subgroup_order=30,
        total_subgroup_order=30,
    )
    p["left_phase36"]=p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error,match="exactly 36"):
        validate_bridge_packet_v13(p)
