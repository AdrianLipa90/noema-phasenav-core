from __future__ import annotations

import pytest

from ciel_geometry.phasenav.working_implementation_registry import (
    WorkingImplementation,
    WorkingImplementationError,
    WorkingImplementationRegistry,
    WorkingStatus,
)


def test_candidate_is_executable_when_explicitly_admitted():
    registry = WorkingImplementationRegistry()
    registry.register(
        WorkingImplementation(
            implementation_id="candidate.test",
            version="0.1",
            status=WorkingStatus.CANDIDATE,
            executable=True,
            default_enabled=False,
            validated_domain="fixture",
            unresolved_domain="none",
            handler=lambda x: x + 1,
        )
    )

    with pytest.raises(WorkingImplementationError, match="allow_candidate"):
        registry.execute("candidate.test", 4)

    receipt = registry.execute("candidate.test", 4, allow_candidate=True)
    assert receipt.result == 5
    assert receipt.status is WorkingStatus.CANDIDATE


def test_candidate_cannot_silently_become_default():
    registry = WorkingImplementationRegistry()
    with pytest.raises(WorkingImplementationError, match="default route"):
        registry.register(
            WorkingImplementation(
                implementation_id="candidate.default",
                version="0.1",
                status=WorkingStatus.CANDIDATE,
                executable=True,
                default_enabled=True,
                validated_domain="fixture",
                unresolved_domain="none",
                handler=lambda x: x,
            )
        )


def test_canonical_executes_without_candidate_flag():
    registry = WorkingImplementationRegistry()
    registry.register(
        WorkingImplementation(
            implementation_id="canonical.test",
            version="1.0",
            status=WorkingStatus.CANONICAL,
            executable=True,
            default_enabled=True,
            validated_domain="fixture",
            unresolved_domain="none",
            handler=lambda x: x * 2,
        )
    )
    receipt = registry.execute("canonical.test", 3)
    assert receipt.result == 6
    assert receipt.status is WorkingStatus.CANONICAL


@pytest.mark.parametrize("status", [WorkingStatus.QUARANTINED, WorkingStatus.FAILED])
def test_nonworking_routes_require_diagnostic_override(status):
    registry = WorkingImplementationRegistry()
    registry.register(
        WorkingImplementation(
            implementation_id=f"{status.value.lower()}.test",
            version="0.1",
            status=status,
            executable=True,
            default_enabled=False,
            validated_domain="diagnostic only",
            unresolved_domain="known failure",
            handler=lambda x: x,
        )
    )
    with pytest.raises(WorkingImplementationError, match="diagnostic_override"):
        registry.execute(f"{status.value.lower()}.test", 1)
    receipt = registry.execute(
        f"{status.value.lower()}.test", 1, diagnostic_override=True
    )
    assert receipt.status is status
