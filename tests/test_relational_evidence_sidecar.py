import hashlib
import json

import pytest

from ciel_geometry.phasenav.relational_evidence import (
    RelationalEvidenceSidecarError,
    attach_relational_evidence,
)


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _gremlin(*, state="CONSISTENT", admissible=True):
    packet = {
        "schema": "GREMLIN_CROSS_MODAL_RELATIONAL_EVIDENCE_PACKET_V0_1",
        "status": "CANDIDATE_ONLY",
        "consistency_state": state,
        "source_attribution_admissible": admissible,
        "physical_source_selected": False,
        "phase_identifiability": {
            "phase_count": 2,
            "cycle_rank": 2,
            "jacobian_rank": 2,
            "fisher_rank": 2,
            "fully_identifiable": True,
        },
        "channels": [
            {
                "name": "orbital",
                "observed": 1.2,
                "predicted": 0.0,
                "sigma": 1.0,
                "residual": 1.2,
                "normalized_residual": 1.2,
                "independently_constrained": True,
                "circular_fit": False,
                "provenance": {
                    "repository": "AdrianLipa90/Informational-Dynamics-of-Time",
                    "branch": "candidate/idt-eb-bec-orbital-acoustic-v0.1",
                    "commit": "a" * 40,
                    "schema": "IDT_02JQ",
                    "receipt": "github-actions:reference",
                    "epistemic": "CHYBA",
                },
            }
        ],
        "consistency": {
            "chi_square": 1.44,
            "residual_dof": 1,
            "max_abs_normalized_residual": 1.2,
            "per_channel_sigma_threshold": 3.0,
            "residual_resolution_sigma": 1.0,
        },
        "source_attribution": {
            "known_sectors_independently_constrained": True,
            "circular_fit_present": False,
            "residual_resolved": True,
            "required_source_bindings_admitted": admissible,
            "admissible": admissible,
        },
    }
    packet["packet_sha256"] = hashlib.sha256(_canonical(packet)).hexdigest()
    return packet


def _route(state, admissible):
    if state == "INCONSISTENT":
        return "STOP_DECLARED_MODEL"
    if state == "UNDERDETERMINED":
        return "REQUEST_MORE_CONSTRAINTS"
    if not admissible:
        return "NO_SOURCE_ROUTE"
    return "ALLOW_CANDIDATE_SOURCE_TESTS"


def _pncs(*, state="CONSISTENT", admissible=True):
    gremlin = _gremlin(state=state, admissible=admissible)
    return {
        "schema": "PNCS_RELATIONAL_EVIDENCE_PACKET_V0_1",
        "status": "CANDIDATE_ONLY",
        "route": _route(state, admissible),
        "consistency_state": state,
        "source_attribution_admissible": admissible,
        "physical_source_selected": False,
        "flatten_into_t36": False,
        "semantic_holonomy_equivalence": "OPEN",
        "epistemic": "CHYBA",
        "candidate_only": True,
        "upstream": {
            "repository": "AdrianLipa90/GREMLIN",
            "branch": "integrate/relational-phase-observation-v0.1",
            "commit": "b" * 40,
            "receipt": "github-actions:fail-loud-audit",
            "schema": "GREMLIN_CROSS_MODAL_RELATIONAL_EVIDENCE_PACKET_V0_1",
            "packet_sha256": gremlin["packet_sha256"],
        },
        "gremlin_evidence": gremlin,
    }


@pytest.mark.parametrize(
    ("state", "admissible", "route"),
    [
        ("INCONSISTENT", False, "STOP_DECLARED_MODEL"),
        ("UNDERDETERMINED", False, "REQUEST_MORE_CONSTRAINTS"),
        ("CONSISTENT", False, "NO_SOURCE_ROUTE"),
        ("CONSISTENT", True, "ALLOW_CANDIDATE_SOURCE_TESTS"),
    ],
)
def test_all_conservative_routes_are_accepted(state, admissible, route):
    result = attach_relational_evidence(
        [0.25] * 36,
        _pncs(state=state, admissible=admissible),
    )
    meta = result["relational_evidence"]
    assert meta["route"] == route
    assert meta["consistency_state"] == state
    assert meta["t36_dimension"] == 36
    assert meta["t36_modified"] is False
    assert meta["physical_source_selected"] is False


def test_exact_t36_is_preserved():
    phase = [i / 100.0 for i in range(36)]
    result = attach_relational_evidence(phase, _pncs())
    assert result["phase_vector_36d"] == tuple(phase)


def test_embedded_gremlin_hash_tamper_is_rejected():
    packet = _pncs()
    packet["gremlin_evidence"]["channels"][0]["observed"] = 99.0
    with pytest.raises(RelationalEvidenceSidecarError, match="hash mismatch"):
        attach_relational_evidence([0.0] * 36, packet)


def test_route_mismatch_is_rejected():
    packet = _pncs(state="CONSISTENT", admissible=True)
    packet["route"] = "NO_SOURCE_ROUTE"
    with pytest.raises(RelationalEvidenceSidecarError, match="route inconsistent"):
        attach_relational_evidence([0.0] * 36, packet)


def test_wrapper_state_mismatch_is_rejected():
    packet = _pncs(state="CONSISTENT", admissible=False)
    packet["consistency_state"] = "UNDERDETERMINED"
    packet["route"] = "REQUEST_MORE_CONSTRAINTS"
    with pytest.raises(RelationalEvidenceSidecarError, match="differs"):
        attach_relational_evidence([0.0] * 36, packet)


def test_wrapper_admissibility_mismatch_is_rejected():
    packet = _pncs(state="CONSISTENT", admissible=True)
    packet["source_attribution_admissible"] = False
    packet["route"] = "NO_SOURCE_ROUTE"
    with pytest.raises(RelationalEvidenceSidecarError, match="differs"):
        attach_relational_evidence([0.0] * 36, packet)


@pytest.mark.parametrize(
    "phase",
    [
        [0.0] * 35,
        [0.0] * 37,
        [0.0] * 35 + [float("nan")],
    ],
)
def test_t36_domain_fails_closed(phase):
    with pytest.raises(RelationalEvidenceSidecarError):
        attach_relational_evidence(phase, _pncs())


def test_physical_source_selection_is_rejected():
    packet = _pncs()
    packet["physical_source_selected"] = True
    with pytest.raises(
        RelationalEvidenceSidecarError,
        match="physical_source_selected",
    ):
        attach_relational_evidence([0.0] * 36, packet)


def test_semantic_holonomy_promotion_is_rejected():
    packet = _pncs()
    packet["semantic_holonomy_equivalence"] = "PASS"
    with pytest.raises(RelationalEvidenceSidecarError, match="OPEN"):
        attach_relational_evidence([0.0] * 36, packet)
