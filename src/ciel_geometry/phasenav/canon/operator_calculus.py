"""Canonical PhaseNav operator calculus and semantic-state utilities.

The operators act on the same T^36 positions and tangent vectors used by the
observer-to-generation runtime. They provide deterministic semantic diff/merge,
CRC, phase compression, trajectory curvature, holonomy caching, scheduling and
forbidden-direction projection.
"""
from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import heapq
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..pnv_runtime import M_36d_order_parameter, TAU
from .context_dynamics import PhaseVector36, TangentVector36
from .model import PHASE_DIM

OPERATOR_CALCULUS_VERSION = "1.0.0"
_EPS = 1.0e-12


def _array(vector: PhaseVector36 | TangentVector36) -> np.ndarray:
    return np.asarray(vector.components, dtype=np.float64)


def _wrapped_delta(left: PhaseVector36, right: PhaseVector36) -> np.ndarray:
    return (_array(right) - _array(left) + math.pi) % TAU - math.pi


def semantic_crc(
    vector: PhaseVector36,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> str:
    payload = {
        "version": OPERATOR_CALCULUS_VERSION,
        "phase": [round(value, 15) for value in vector.components],
        "metadata": dict(metadata or {}),
    }
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class SemanticDelta:
    tangent: TangentVector36
    angular_distance: float
    max_component: float
    coherence_left: float
    coherence_right: float
    coherence_delta: float
    crc_left: str
    crc_right: str

    @property
    def unchanged(self) -> bool:
        return self.angular_distance <= _EPS


def semantic_diff(left: PhaseVector36, right: PhaseVector36) -> SemanticDelta:
    delta = _wrapped_delta(left, right)
    distance = float(np.sqrt(np.mean(delta * delta)))
    coherence_left = float(M_36d_order_parameter(list(left.components)))
    coherence_right = float(M_36d_order_parameter(list(right.components)))
    return SemanticDelta(
        tangent=TangentVector36(tuple(float(value) for value in delta)),
        angular_distance=distance,
        max_component=float(np.max(np.abs(delta))),
        coherence_left=coherence_left,
        coherence_right=coherence_right,
        coherence_delta=coherence_right - coherence_left,
        crc_left=semantic_crc(left),
        crc_right=semantic_crc(right),
    )


@dataclass(frozen=True)
class MergeResult:
    vector: PhaseVector36
    coherence: float
    resultant_amplitude: tuple[float, ...]
    cancellation: float
    source_crcs: tuple[str, ...]


def semantic_merge(
    vectors: Sequence[PhaseVector36],
    *,
    weights: Sequence[float] | None = None,
) -> MergeResult:
    if not vectors:
        raise ValueError("at least one vector is required")
    if weights is None:
        weights = (1.0,) * len(vectors)
    if len(weights) != len(vectors):
        raise ValueError("weights and vectors must align")
    w = np.asarray(weights, dtype=np.float64)
    if np.any(w < 0.0) or not np.all(np.isfinite(w)) or float(w.sum()) <= 0.0:
        raise ValueError("weights must be finite, non-negative and non-zero")
    phases = np.asarray([vector.components for vector in vectors], dtype=np.float64)
    phasors = np.sum(w[:, None] * np.exp(1j * phases), axis=0)
    amplitude = np.abs(phasors) / float(w.sum())
    merged = PhaseVector36(tuple(np.mod(np.angle(phasors), TAU)))
    cancellation = 1.0 - float(np.mean(amplitude))
    return MergeResult(
        vector=merged,
        coherence=float(M_36d_order_parameter(list(merged.components))),
        resultant_amplitude=tuple(float(value) for value in amplitude),
        cancellation=min(1.0, max(0.0, cancellation)),
        source_crcs=tuple(semantic_crc(vector) for vector in vectors),
    )


@dataclass(frozen=True)
class CompressedPhase:
    schema: str
    bits: int
    payload_b64: str
    crc_sha256: str
    maximum_error: float


def compress_phase(vector: PhaseVector36, *, bits: int = 16) -> CompressedPhase:
    if bits not in {8, 16, 32}:
        raise ValueError("bits must be 8, 16 or 32")
    maximum = (1 << bits) - 1
    quantized = np.rint(_array(vector) / TAU * maximum)
    dtype = {8: np.dtype("<u1"), 16: np.dtype("<u2"), 32: np.dtype("<u4")}[bits]
    raw = quantized.astype(dtype).tobytes(order="C")
    return CompressedPhase(
        schema="phasenav.phase-compressed/v1",
        bits=bits,
        payload_b64=base64.b64encode(raw).decode("ascii"),
        crc_sha256=hashlib.sha256(raw).hexdigest(),
        maximum_error=TAU / (2.0 * maximum),
    )


def decompress_phase(compressed: CompressedPhase) -> PhaseVector36:
    if compressed.schema != "phasenav.phase-compressed/v1":
        raise ValueError("unsupported compressed phase schema")
    dtype = {
        8: np.dtype("<u1"),
        16: np.dtype("<u2"),
        32: np.dtype("<u4"),
    }.get(compressed.bits)
    if dtype is None:
        raise ValueError("unsupported phase bit depth")
    raw = base64.b64decode(compressed.payload_b64.encode("ascii"), validate=True)
    if hashlib.sha256(raw).hexdigest() != compressed.crc_sha256:
        raise ValueError("compressed phase CRC mismatch")
    values = np.frombuffer(raw, dtype=dtype)
    if values.size != PHASE_DIM:
        raise ValueError(f"expected {PHASE_DIM} compressed coordinates")
    maximum = float((1 << compressed.bits) - 1)
    return PhaseVector36(tuple(values.astype(np.float64) / maximum * TAU))


def gauge_transform(vector: PhaseVector36, offset: float | Sequence[float]) -> PhaseVector36:
    shifts = (
        np.full(PHASE_DIM, float(offset), dtype=np.float64)
        if isinstance(offset, (int, float))
        else np.asarray(offset, dtype=np.float64)
    )
    if shifts.shape != (PHASE_DIM,) or not np.all(np.isfinite(shifts)):
        raise ValueError("gauge offset must be scalar or finite 36D sequence")
    return PhaseVector36(tuple((_array(vector) + shifts) % TAU))


def trajectory_curvature(trajectory: Sequence[PhaseVector36]) -> float:
    if len(trajectory) < 3:
        return 0.0
    tangents = [
        _wrapped_delta(trajectory[index], trajectory[index + 1])
        for index in range(len(trajectory) - 1)
    ]
    turns = []
    for left, right in zip(tangents, tangents[1:]):
        left_norm = float(np.linalg.norm(left))
        right_norm = float(np.linalg.norm(right))
        if left_norm <= _EPS or right_norm <= _EPS:
            continue
        cosine = float(np.dot(left, right) / (left_norm * right_norm))
        turns.append(math.acos(min(1.0, max(-1.0, cosine))))
    return 0.0 if not turns else float(np.sqrt(np.mean(np.square(turns))))


@dataclass(frozen=True)
class LinearPhaseOperator:
    operator_id: str
    matrix: np.ndarray

    def __post_init__(self) -> None:
        matrix = np.asarray(self.matrix, dtype=np.float64)
        if matrix.shape != (PHASE_DIM, PHASE_DIM):
            raise ValueError(f"operator matrix must be {PHASE_DIM}x{PHASE_DIM}")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("operator matrix must be finite")
        object.__setattr__(self, "matrix", matrix)

    @classmethod
    def identity(cls, operator_id: str = "I") -> "LinearPhaseOperator":
        return cls(operator_id, np.eye(PHASE_DIM))

    def apply(self, tangent: TangentVector36) -> TangentVector36:
        result = self.matrix @ _array(tangent)
        return TangentVector36(tuple(float(value) for value in result))

    def compose(self, other: "LinearPhaseOperator", *, operator_id: str | None = None) -> "LinearPhaseOperator":
        return LinearPhaseOperator(
            operator_id or f"{self.operator_id}∘{other.operator_id}",
            self.matrix @ other.matrix,
        )

    def commutator(self, other: "LinearPhaseOperator", *, operator_id: str | None = None) -> "LinearPhaseOperator":
        return LinearPhaseOperator(
            operator_id or f"[{self.operator_id},{other.operator_id}]",
            self.matrix @ other.matrix - other.matrix @ self.matrix,
        )

    def is_projection(self, *, atol: float = 1.0e-10) -> bool:
        return bool(np.allclose(self.matrix @ self.matrix, self.matrix, atol=atol))

    def is_orthogonal(self, *, atol: float = 1.0e-10) -> bool:
        return bool(np.allclose(self.matrix.T @ self.matrix, np.eye(PHASE_DIM), atol=atol))


@dataclass(frozen=True)
class ProjectionResult:
    allowed: TangentVector36
    removed: TangentVector36
    removed_norm: float
    rank: int


def project_forbidden_directions(
    tangent: TangentVector36,
    forbidden_normals: Sequence[TangentVector36],
) -> ProjectionResult:
    if not forbidden_normals:
        zero = TangentVector36((0.0,) * PHASE_DIM)
        return ProjectionResult(tangent, zero, 0.0, 0)
    normals = np.asarray([normal.components for normal in forbidden_normals], dtype=np.float64)
    rank = int(np.linalg.matrix_rank(normals))
    projector = normals.T @ np.linalg.pinv(normals @ normals.T) @ normals
    vector = _array(tangent)
    removed = projector @ vector
    allowed = vector - removed
    return ProjectionResult(
        allowed=TangentVector36(tuple(float(value) for value in allowed)),
        removed=TangentVector36(tuple(float(value) for value in removed)),
        removed_norm=float(np.sqrt(np.mean(removed * removed))),
        rank=rank,
    )


@dataclass(frozen=True)
class HolonomyCacheEntry:
    operator_id: str
    start_crc: str
    end_crc: str
    holonomy: float
    result: PhaseVector36
    result_crc: str


class HolonomyCache:
    def __init__(self, *, precision: int = 12) -> None:
        if precision < 0:
            raise ValueError("precision must be non-negative")
        self.precision = precision
        self._entries: dict[tuple[str, str, str, float], HolonomyCacheEntry] = {}

    def _key(
        self,
        operator_id: str,
        start: PhaseVector36,
        end: PhaseVector36,
        holonomy: float,
    ) -> tuple[str, str, str, float]:
        return (
            operator_id,
            semantic_crc(start),
            semantic_crc(end),
            round(float(holonomy), self.precision),
        )

    def put(
        self,
        operator_id: str,
        start: PhaseVector36,
        end: PhaseVector36,
        holonomy: float,
        result: PhaseVector36,
    ) -> HolonomyCacheEntry:
        key = self._key(operator_id, start, end, holonomy)
        entry = HolonomyCacheEntry(
            operator_id=operator_id,
            start_crc=key[1],
            end_crc=key[2],
            holonomy=key[3],
            result=result,
            result_crc=semantic_crc(result),
        )
        self._entries[key] = entry
        return entry

    def get(
        self,
        operator_id: str,
        start: PhaseVector36,
        end: PhaseVector36,
        holonomy: float,
    ) -> HolonomyCacheEntry | None:
        return self._entries.get(self._key(operator_id, start, end, holonomy))

    def __len__(self) -> int:
        return len(self._entries)


@dataclass(frozen=True)
class ScheduledState:
    state_id: str
    phase: PhaseVector36
    potential: float
    entropy: float
    urgency: float
    provenance_weight: float
    sequence: int


class SemanticScheduler:
    """Priority queue minimizing semantic cost with deterministic tie-breaking."""

    def __init__(self) -> None:
        self._heap: list[tuple[float, int, ScheduledState]] = []
        self._sequence = 0

    @staticmethod
    def cost(
        *,
        potential: float,
        entropy: float,
        urgency: float,
        provenance_weight: float,
    ) -> float:
        if provenance_weight <= 0.0:
            raise ValueError("provenance_weight must be positive")
        return (
            float(potential)
            + max(0.0, float(entropy))
            - max(0.0, float(urgency))
        ) / float(provenance_weight)

    def push(
        self,
        state_id: str,
        phase: PhaseVector36,
        *,
        potential: float,
        entropy: float,
        urgency: float = 0.0,
        provenance_weight: float = 1.0,
    ) -> ScheduledState:
        if not state_id:
            raise ValueError("state_id must not be empty")
        item = ScheduledState(
            state_id=state_id,
            phase=phase,
            potential=float(potential),
            entropy=float(entropy),
            urgency=float(urgency),
            provenance_weight=float(provenance_weight),
            sequence=self._sequence,
        )
        self._sequence += 1
        heapq.heappush(
            self._heap,
            (
                self.cost(
                    potential=item.potential,
                    entropy=item.entropy,
                    urgency=item.urgency,
                    provenance_weight=item.provenance_weight,
                ),
                item.sequence,
                item,
            ),
        )
        return item

    def pop(self) -> ScheduledState:
        if not self._heap:
            raise IndexError("scheduler is empty")
        return heapq.heappop(self._heap)[2]

    def __len__(self) -> int:
        return len(self._heap)
