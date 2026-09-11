import json
from pathlib import Path


RECEIPT = Path("candidate_contracts/phasenav_carrier_hierarchy_v02_provenance.json")


def _load():
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_receipt_is_candidate_only_and_non_physical():
    receipt = _load()
    assert receipt["status"] == "CANDIDATE_VALIDATED_ACROSS_DECLARED_SOFTWARE_GATES"
    assert receipt["canonical_promotion_authority"] is False
    assert receipt["main_or_master_merge_authority"] is False
    assert receipt["physical_binding_verified"] is False
    assert receipt["physical_ion_binding"] == "OPEN"


def test_all_declared_components_have_green_hosted_gates():
    receipt = _load()
    components = receipt["components"]
    assert len(components) == 8
    assert all(component["conclusion"] == "success" for component in components)
    assert all(component["hosted_gate"] for component in components)
    assert all(len(component["commit"]) == 40 for component in components)


def test_cross_repo_roles_are_unique_and_complete():
    roles = {component["role"] for component in _load()["components"]}
    assert roles == {
        "execution_owner",
        "independent_mathematical_validator",
        "connection_curvature_bridge",
        "qgt_spectroscopy_interface",
        "candidate_lifecycle",
        "mas_consumer",
        "ciel_noema_consumer",
        "time_parameter_adapter",
    }


def test_validated_ladder_is_exactly_1q_to_4q():
    ladder = _load()["validated_representation_ladder"]
    assert [(x["qubits"], x["complex_dim"], x["real_dim"], x["projective_space"]) for x in ladder] == [
        (1, 2, 4, "CP^1"),
        (2, 4, 8, "CP^3"),
        (3, 8, 16, "CP^7"),
        (4, 16, 32, "CP^15"),
    ]


def test_idt_temporal_core_nonmutation_is_recorded():
    idt = next(x for x in _load()["components"] if x["role"] == "time_parameter_adapter")
    assert idt["temporal_core_mutated"] is False


def test_nonclaims_include_physical_and_5q_boundaries():
    text = "\n".join(_load()["explicit_non_claims"])
    assert "not evidence of a realised 16-ion device" in text
    assert "not evidence of a realised 32-ion device" in text
    assert "5Q and higher" in text
    assert "must fail closed" in text
