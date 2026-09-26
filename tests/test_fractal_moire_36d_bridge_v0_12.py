import pytest

from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_2 import (
    FractalMoire36Error,
)
from ciel_geometry.phasenav.fractal_moire_36d_bridge_v0_12 import (
    validate_bridge_packet_v12,
)


MATRIX_SHA="8781f4a685257eced538daa7462ec4fc48093a6b"
FRONTIER_SHA="dc1cdbb401dd618738c8a23249fa4c23c8fe5515"


def _base():
    left=[0.01*j for j in range(36)]
    right=[x+0.13 for x in left]
    return {
        "schema":"phasenav.fractal-moire-36d-bridge/v0.12",
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
            "proofs/ARPL_INFINITE_CLOCK_FIBRE_VISIBILITY_FRONTIER_V0_1.md",
            "src/on_primes/visibility_frontier.py",
            "receipts/ARPL_INFINITE_CLOCK_FIBRE_VISIBILITY_FRONTIER_V0_1_VALIDATION_20260926.md",
        ],
        "arpl_visibility_pin_witness_ref":"gremlin://grh-exposure-frontier-pin",
    }


def test_h6_p5_grh_visibility_closes_all_fixed_local_hidden_modes_conditionally():
    out=validate_bridge_packet_v12(_base())
    rec=out["grh_infinite_visibility_receipt"]
    assert rec["local_clock_periods"]==(2,3,5,6,9)
    assert rec["required_denominator_sets"]==(
        (2,),
        (3,),
        (5,),
        (2,3,6),
        (3,9),
    )
    assert rec["replication_certificate_count"]==8
    assert rec["finite_support_hidden_dimensions"]==(0,0,4,2,6)
    assert rec["infinite_support_hidden_dimensions_under_grh"]==(0,0,0,0,0)
    assert rec["positive_lower_density_exposure_claim_under_grh"] is True
    assert rec["full_exposure_set_natural_density_claim"] is False
    assert rec["unconditional_status"]=="OPEN"


def test_certificate_moduli_include_known_h6_controls():
    out=validate_bridge_packet_v12(_base())
    rows=out["grh_infinite_visibility_receipt"]["replication_certificates"]
    by_pair={(r["source_prime"],r["denominator"]):r for r in rows}
    assert by_pair[(11,5)]["cyclotomic_modulus"]==25
    assert by_pair[(13,6)]["cyclotomic_modulus"]==72
    assert by_pair[(19,9)]["cyclotomic_modulus"]==27


def test_grh_declaration_is_required():
    p=_base()
    p["grh_assumption_declared"]=False
    with pytest.raises(FractalMoire36Error,match="GRH"):
        validate_bridge_packet_v12(p)


def test_unconditional_promotion_fails_closed():
    p=_base()
    p["unconditional_infinite_exposure_claim"]=True
    with pytest.raises(FractalMoire36Error,match="unconditional"):
        validate_bridge_packet_v12(p)


def test_physical_observability_promotion_fails_closed():
    p=_base()
    p["physical_observability_claim"]=True
    with pytest.raises(FractalMoire36Error,match="physical"):
        validate_bridge_packet_v12(p)


def test_frontier_pin_is_separate_from_matrix_pin():
    p=_base()
    p["arpl_visibility_repository"]="Wrong/Repo"
    with pytest.raises(FractalMoire36Error,match="arpl_visibility_repository"):
        validate_bridge_packet_v12(p)


def test_exact_36_firewall_is_inherited():
    p=_base()
    p["left_phase36"]=p["left_phase36"][:-1]
    with pytest.raises(FractalMoire36Error,match="exactly 36"):
        validate_bridge_packet_v12(p)
