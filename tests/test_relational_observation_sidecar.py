import pytest

from ciel_geometry.phasenav.relational_observation import (
    RelationalObservationSidecarError,
    attach_relational_observation,
)


def _packet(**overrides):
    packet = {
        "schema": "PNCS_RELATIONAL_OBSERVATION_PACKET_V0_1",
        "observables": {
            "frequency": 1.5,
            "intensity": 2.0,
            "phase": 0.25,
            "linewidth": 0.05,
            "coherence": 0.9,
        },
        "identifiability": {
            "phase_count": 2,
            "cycle_rank": 2,
            "jacobian_rank": 2,
            "fisher_rank": 2,
            "fully_identifiable": True,
        },
        "provenance": {
            "repository": "AdrianLipa90/Orbital-Eclipse-Spectroscopy",
            "branch": "integrate/relational-phase-observation-v0.1",
            "commit": "a" * 40,
            "schema": "OES_H1_HOLONOMY_RESPONSE_IDENTIFIABILITY_V0_1",
            "receipt": "github-actions:reference",
        },
        "epistemic": "CHYBA",
        "candidate_only": True,
        "flatten_into_t36": False,
        "semantic_holonomy_equivalence": "OPEN",
    }
    for key, value in overrides.items():
        packet[key] = value
    return packet


def test_attach_preserves_exact_t36_and_sidecar_status():
    phase = [0.1] * 36
    result = attach_relational_observation(phase, _packet())
    assert len(result["phase_vector_36d"]) == 36
    assert result["phase_vector_36d"] == tuple(phase)
    meta = result["relational_observation"]
    assert meta["t36_dimension"] == 36
    assert meta["t36_modified"] is False
    assert meta["physical_source_inferred"] is False
    assert meta["semantic_holonomy_equivalence"] == "OPEN"


def test_rank_deficient_but_declared_nonidentifiable_packet_is_valid():
    packet = _packet()
    packet["identifiability"] = {
        "phase_count": 2,
        "cycle_rank": 2,
        "jacobian_rank": 1,
        "fisher_rank": 1,
        "fully_identifiable": False,
    }
    result = attach_relational_observation([0.0] * 36, packet)
    assert result["relational_observation"]["observation_packet"]["identifiability"][
        "fully_identifiable"
    ] is False


@pytest.mark.parametrize(
    "phase",
    [
        [0.0] * 35,
        [0.0] * 37,
        [0.0] * 35 + [float("nan")],
    ],
)
def test_phase_vector_fail_closed(phase):
    with pytest.raises(RelationalObservationSidecarError):
        attach_relational_observation(phase, _packet())


def test_flatten_request_rejected():
    packet = _packet(flatten_into_t36=True)
    with pytest.raises(RelationalObservationSidecarError):
        attach_relational_observation([0.0] * 36, packet)


def test_semantic_holonomy_promotion_rejected():
    packet = _packet(semantic_holonomy_equivalence="PASS")
    with pytest.raises(RelationalObservationSidecarError):
        attach_relational_observation([0.0] * 36, packet)


def test_impossible_identifiability_declaration_rejected():
    packet = _packet()
    packet["identifiability"]["jacobian_rank"] = 1
    packet["identifiability"]["fisher_rank"] = 1
    packet["identifiability"]["fully_identifiable"] = True
    with pytest.raises(RelationalObservationSidecarError):
        attach_relational_observation([0.0] * 36, packet)
