import pytest

from ciel_geometry.phasenav.candidate_runtime import (
    WorkingStatus,
    admit_working_component,
    assert_working_executable,
)


def test_candidate_is_active_working_not_default_canon():
    a = admit_working_component("pncs.600cell_s3.v0.1", WorkingStatus.CANDIDATE)
    assert a.admitted
    assert a.executable
    assert not a.canonical_default
    assert a.provenance_required
    assert a.status is WorkingStatus.CANDIDATE


def test_canonical_is_executable_and_default_eligible():
    a = admit_working_component("phasenav.canon", "CANONICAL")
    assert a.admitted
    assert a.executable
    assert a.canonical_default


@pytest.mark.parametrize("status", ["QUARANTINED", "FAILED"])
def test_quarantined_and_failed_are_not_working_routes(status):
    a = admit_working_component("x", status)
    assert not a.admitted
    assert not a.executable
    with pytest.raises(RuntimeError):
        assert_working_executable("x", status)


def test_unknown_status_fails_closed():
    with pytest.raises(ValueError, match="unknown working status"):
        admit_working_component("x", "EXPERIMENTAL_MAYBE")


def test_empty_component_id_rejected():
    with pytest.raises(ValueError):
        admit_working_component("", "CANDIDATE")
