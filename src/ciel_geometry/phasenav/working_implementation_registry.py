from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class WorkingStatus(str, Enum):
    CANONICAL = "CANONICAL"
    CANDIDATE = "CANDIDATE"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"


class WorkingImplementationError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkingImplementation(Generic[T, R]):
    implementation_id: str
    version: str
    status: WorkingStatus
    executable: bool
    default_enabled: bool
    validated_domain: str
    unresolved_domain: str
    handler: Callable[[T], R]


@dataclass(frozen=True)
class WorkingExecutionReceipt(Generic[R]):
    implementation_id: str
    version: str
    status: WorkingStatus
    result: R


class WorkingImplementationRegistry:
    """Small fail-closed registry for canonical and candidate implementations.

    CANDIDATE means active working implementation. Candidate routes may execute
    when explicitly admitted but their receipts remain candidate-labelled.
    """

    def __init__(self) -> None:
        self._items: dict[str, WorkingImplementation] = {}

    def register(self, implementation: WorkingImplementation) -> None:
        if not implementation.implementation_id:
            raise WorkingImplementationError("implementation_id must be non-empty")
        if implementation.implementation_id in self._items:
            raise WorkingImplementationError(
                f"duplicate implementation_id: {implementation.implementation_id}"
            )
        if implementation.status in {WorkingStatus.QUARANTINED, WorkingStatus.FAILED}:
            if implementation.default_enabled:
                raise WorkingImplementationError(
                    f"{implementation.status.value} implementation cannot be default-enabled"
                )
        if implementation.status is WorkingStatus.CANDIDATE and implementation.default_enabled:
            raise WorkingImplementationError(
                "candidate implementation cannot silently become the default route"
            )
        self._items[implementation.implementation_id] = implementation

    def get(self, implementation_id: str) -> WorkingImplementation:
        try:
            return self._items[implementation_id]
        except KeyError as exc:
            raise WorkingImplementationError(
                f"unknown implementation_id: {implementation_id}"
            ) from exc

    def execute(
        self,
        implementation_id: str,
        payload,
        *,
        allow_candidate: bool = False,
        diagnostic_override: bool = False,
    ) -> WorkingExecutionReceipt:
        impl = self.get(implementation_id)
        if not impl.executable:
            raise WorkingImplementationError(
                f"implementation is not executable: {implementation_id}"
            )

        if impl.status is WorkingStatus.CANDIDATE and not allow_candidate:
            raise WorkingImplementationError(
                "candidate route requires allow_candidate=True"
            )

        if impl.status in {WorkingStatus.QUARANTINED, WorkingStatus.FAILED}:
            if not diagnostic_override:
                raise WorkingImplementationError(
                    f"{impl.status.value} route requires diagnostic_override=True"
                )

        result = impl.handler(payload)
        return WorkingExecutionReceipt(
            implementation_id=impl.implementation_id,
            version=impl.version,
            status=impl.status,
            result=result,
        )

    def statuses(self) -> dict[str, str]:
        return {key: item.status.value for key, item in sorted(self._items.items())}
