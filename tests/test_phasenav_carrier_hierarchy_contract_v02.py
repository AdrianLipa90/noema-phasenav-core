import json
from pathlib import Path

from ciel_geometry.phasenav.candidate_runtime import WorkingStatus, admit_working_component


CONTRACT = Path("candidate_contracts/phasenav_carrier_hierarchy_v02.json")


def _load():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_contract_remains_active_candidate_not_default_canon():
    contract = _load()
    admission = admit_working_component(contract["contract_id"], WorkingStatus.CANDIDATE)
    assert admission.admitted
    assert admission.executable
    assert not admission.canonical_default
    assert contract["runtime_default"] is False
    assert contract["canon_write_authority"] is False
    assert contract["epistemic"] == "CHYBA"


def test_carrier_ladder_is_exactly_1q_to_4q():
    contract = _load()
    assert contract["supported_qubits"] == [1, 2, 3, 4]
    assert contract["candidate_ceiling_qubits"] == 4
    assert [
        (item["qubits"], item["complex_dim"], item["real_dim"], item["projective_space"])
        for item in contract["carrier_levels"]
    ] == [
        (1, 2, 4, "CP^1"),
        (2, 4, 8, "CP^3"),
        (3, 8, 16, "CP^7"),
        (4, 16, 32, "CP^15"),
    ]


def test_physical_bindings_are_open_and_5q_is_quarantined():
    contract = _load()
    assert all(value == "OPEN" for value in contract["physical_bindings"].values())
    assert "qubit_count_above_candidate_ceiling" in contract["quarantine_on"]
    assert "fail_closed_above_4q" in contract["required_invariants"]


def test_entanglement_and_intertwiner_gates_are_required():
    required = set(_load()["required_invariants"])
    assert "old_subsystem_gate_intertwining_zero" in required
    assert "ghz_2q_3q_4q_exact" in required
    assert "ghz_schmidt_rank_two_all_nontrivial_contiguous_splits" in required
