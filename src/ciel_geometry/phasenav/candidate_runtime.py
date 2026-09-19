from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WorkingStatus(str, Enum):
    CANONICAL = "CANONICAL"
    CANDIDATE = "CANDIDATE"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class WorkingRouteAdmission:
    component_id: str
    status: WorkingStatus
    admitted: bool
    executable: bool
    canonical_default: bool
    provenance_required: bool
    reason: str


def admit_working_component(component_id: str, status: str | WorkingStatus) -> WorkingRouteAdmission:
    if not isinstance(component_id, str) or not component_id.strip():
        raise ValueError("component_id must be a non-empty string")
    try:
        resolved = status if isinstance(status, WorkingStatus) else WorkingStatus(str(status))
    except ValueError as exc:
        raise ValueError(f"unknown working status: {status!r}") from exc

    if resolved is WorkingStatus.CANONICAL:
        return WorkingRouteAdmission(
            component_id=component_id,
            status=resolved,
            admitted=True,
            executable=True,
            canonical_default=True,
            provenance_required=True,
            reason="canonical component admitted",
        )
    if resolved is WorkingStatus.CANDIDATE:
        return WorkingRouteAdmission(
            component_id=component_id,
            status=resolved,
            admitted=True,
            executable=True,
            canonical_default=False,
            provenance_required=True,
            reason="candidate is an active working component with mandatory status provenance",
        )

    return WorkingRouteAdmission(
        component_id=component_id,
        status=resolved,
        admitted=False,
        executable=False,
        canonical_default=False,
        provenance_required=True,
        reason=f"{resolved.value.lower()} component excluded from working routes except diagnosis",
    )


def assert_working_executable(component_id: str, status: str | WorkingStatus) -> WorkingRouteAdmission:
    admission = admit_working_component(component_id, status)
    if not admission.executable:
        raise RuntimeError(
            f"{component_id} is {admission.status.value} and is not executable on working routes"
        )
    return admission
