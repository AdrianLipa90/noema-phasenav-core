from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "candidate_contracts" / "phasenav_quantum_application_state_v01.json"


def test_quantum_application_state_contract_no_early_collapse() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema"] == "PHASENAV_QUANTUM_APPLICATION_STATE_V0_1"
    assert payload["dimension"] == 36
    assert payload["carrier"] == "T^36"
    assert payload["flatten_sidecars_into_t36"] is False
    assert payload["invariant"]["never_collapse_early"] is True
    assert payload["invariant"]["implicit_boolean_projection"] is False
    assert payload["measurement"]["binary_outcome_allowed"] is True
    assert payload["measurement"]["binary_outcome_required"] is False
    assert payload["physical_quantum_claim_default"] is False
    assert "QPU_PHYSICAL" in payload["backends"]
