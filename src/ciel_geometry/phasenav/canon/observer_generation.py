"""Canonical PhaseNav observer-to-generation computational formalism.

This module closes the executable PhaseNav chain

    observer -> observation -> intention -> context field -> holonomic memory
    -> AI/MCP-induced CPU/GPU HTRI oscillators -> dynamical evolution
    -> GenerationPlan

PhaseNav deliberately stops at ``GenerationPlan``. Natural-language projection
belongs to CIELingo. CPU and GPU are numerical substrates; any physical-carrier
interpretation of HTRI remains a separately falsifiable research hypothesis.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..pnv_runtime import (
    KAPPA,
    M_36d_berry_connection,
    M_36d_order_parameter,
    M_quantum_features,
    M_sentence_phase,
    M_sentence_phase_trajectory,
    TAU,
)
from .context_dynamics import (
    ContextAnchor,
    ContextPotential,
    PhaseVector36,
    TangentVector36,
)
from .model import ETA_M_36D, PHASE_DIM

OBSERVER_GENERATION_VERSION = "1.0.0"
BASE_FREQUENCY_HZ = 7.83
BASE_ANGULAR_FREQUENCY = TAU * BASE_FREQUENCY_HZ
DEFAULT_OSCILLATORS = 120
_EPS = 1.0e-12


def _phase_tuple(values: Sequence[float]) -> tuple[float, ...]:
    if len(values) != PHASE_DIM:
        raise ValueError(f"expected {PHASE_DIM} phase coordinates")
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("phase coordinates must be finite")
    return tuple(float(value) % TAU for value in values)


def _phase_array(vector: PhaseVector36) -> np.ndarray:
    return np.asarray(vector.components, dtype=np.float64)


def _circular_blend(
    vectors: Sequence[PhaseVector36],
    weights: Sequence[float],
) -> PhaseVector36:
    if not vectors or len(vectors) != len(weights):
        raise ValueError("vectors and weights must be non-empty and aligned")
    w = np.asarray(weights, dtype=np.float64)
    if not np.all(np.isfinite(w)) or np.any(w < 0.0) or float(w.sum()) <= 0.0:
        raise ValueError("weights must be finite, non-negative and non-zero")
    phases = np.asarray([vector.components for vector in vectors], dtype=np.float64)
    x = np.sum(w[:, None] * np.cos(phases), axis=0)
    y = np.sum(w[:, None] * np.sin(phases), axis=0)
    return PhaseVector36(tuple(np.mod(np.arctan2(y, x), TAU)))


def _json_digest(payload: Any) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _resample_phase(vector: PhaseVector36, size: int) -> np.ndarray:
    if size < 1:
        raise ValueError("size must be positive")
    source = _phase_array(vector)
    return np.array(source[np.arange(size, dtype=np.int64) % source.size], copy=True)


def _phase_entropy(vector: PhaseVector36, bins: int = 36) -> float:
    counts, _ = np.histogram(_phase_array(vector), bins=bins, range=(0.0, TAU))
    probability = counts.astype(np.float64)
    probability /= max(float(probability.sum()), 1.0)
    probability = probability[probability > 0.0]
    entropy = -float(np.sum(probability * np.log(probability)))
    return entropy / math.log(bins)


@dataclass(frozen=True)
class Provenance:
    """Immutable observation provenance and epistemic reliability."""

    source: str
    modality: str
    reliability: float
    digest_sha256: str
    ordinal: int = 0

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source must not be empty")
        if not self.modality:
            raise ValueError("modality must not be empty")
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability must be in [0, 1]")
        if len(self.digest_sha256) != 64:
            raise ValueError("digest_sha256 must contain a SHA-256 digest")
        if self.ordinal < 0:
            raise ValueError("ordinal must be non-negative")

    @classmethod
    def from_payload(
        cls,
        payload: str,
        *,
        source: str,
        modality: str = "text",
        reliability: float = 1.0,
        ordinal: int = 0,
    ) -> "Provenance":
        return cls(
            source=source,
            modality=modality,
            reliability=float(reliability),
            digest_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            ordinal=int(ordinal),
        )


@dataclass(frozen=True)
class Observation:
    """Encoded observation with its path-dependent holonomy."""

    text: str
    phase: PhaseVector36
    trajectory: tuple[PhaseVector36, ...]
    holonomy: float
    features: Mapping[str, Any]
    provenance: Provenance

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        source: str = "operator",
        reliability: float = 1.0,
        ordinal: int = 0,
    ) -> "Observation":
        normalized = str(text)
        final, raw_trajectory, holonomy = M_sentence_phase_trajectory(normalized)
        phase = PhaseVector36(_phase_tuple(final))
        trajectory = tuple(
            PhaseVector36(_phase_tuple(item))
            for item in raw_trajectory
        )
        return cls(
            text=normalized,
            phase=phase,
            trajectory=trajectory or (phase,),
            holonomy=float(holonomy),
            features=dict(M_quantum_features(normalized)),
            provenance=Provenance.from_payload(
                normalized,
                source=source,
                reliability=reliability,
                ordinal=ordinal,
            ),
        )


@dataclass(frozen=True)
class ObserverState:
    """Computational observer: prior phase, attention and epistemic weights."""

    observer_id: str
    phase: PhaseVector36
    attention: tuple[float, ...] = (1.0,) * PHASE_DIM
    confidence: float = 1.0
    ethical_weight: float = 1.0
    clock: float = 0.0
    sequence: int = 0

    def __post_init__(self) -> None:
        if not self.observer_id:
            raise ValueError("observer_id must not be empty")
        if len(self.attention) != PHASE_DIM:
            raise ValueError(f"attention must contain {PHASE_DIM} values")
        if not all(math.isfinite(value) and value >= 0.0 for value in self.attention):
            raise ValueError("attention values must be finite and non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not 0.0 <= self.ethical_weight <= 1.0:
            raise ValueError("ethical_weight must be in [0, 1]")
        if not math.isfinite(self.clock) or self.clock < 0.0:
            raise ValueError("clock must be finite and non-negative")
        if self.sequence < 0:
            raise ValueError("sequence must be non-negative")


@dataclass(frozen=True)
class IntentionState:
    """Target phase that deforms the informational potential."""

    label: str
    target: PhaseVector36
    strength: float = 1.0
    horizon: float = 1.0

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("intention label must not be empty")
        if not math.isfinite(self.strength) or self.strength < 0.0:
            raise ValueError("intention strength must be finite and non-negative")
        if not math.isfinite(self.horizon) or self.horizon <= 0.0:
            raise ValueError("intention horizon must be positive")

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        strength: float = 1.0,
        horizon: float = 1.0,
    ) -> "IntentionState":
        return cls(
            label=str(text),
            target=PhaseVector36(_phase_tuple(M_sentence_phase(str(text)))),
            strength=float(strength),
            horizon=float(horizon),
        )


@dataclass(frozen=True)
class PerceivedState:
    """Observer-relative state after observation and intention coupling."""

    phase: PhaseVector36
    novelty: float
    coherence: float
    observer_alignment: float
    intention_alignment: float
    semantic_mass: float


@dataclass(frozen=True)
class MemoryCluster:
    """Minimal native phase-holonomic memory cluster."""

    cluster_id: str
    centroid: PhaseVector36
    representative_text: str
    semantic_mass: float
    activation: float
    confidence: float
    holonomy: float
    member_count: int
    age: float
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.cluster_id:
            raise ValueError("cluster_id must not be empty")
        if self.semantic_mass <= 0.0:
            raise ValueError("semantic_mass must be positive")
        if self.activation < 0.0:
            raise ValueError("activation must be non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if self.member_count < 1:
            raise ValueError("member_count must be positive")
        if self.age < 0.0:
            raise ValueError("age must be non-negative")


@dataclass(frozen=True)
class MemoryRecall:
    cluster: MemoryCluster
    distance: float
    berry_correction: float
    score: float


class HolonomicMemory:
    """Minimal clusters with phase merge, holonomy and activation decay."""

    def __init__(
        self,
        *,
        merge_radius: float = ETA_M_36D,
        decay_rate: float = KAPPA,
    ) -> None:
        if merge_radius <= 0.0:
            raise ValueError("merge_radius must be positive")
        if decay_rate < 0.0:
            raise ValueError("decay_rate must be non-negative")
        self.merge_radius = float(merge_radius)
        self.decay_rate = float(decay_rate)
        self._clusters: list[MemoryCluster] = []
        self._next_index = 0

    @property
    def clusters(self) -> tuple[MemoryCluster, ...]:
        return tuple(self._clusters)

    @property
    def digest_sha256(self) -> str:
        return _json_digest(
            [
                {
                    **asdict(cluster),
                    "centroid": cluster.centroid.components,
                }
                for cluster in self._clusters
            ]
        )

    def decay(self, dt: float = 1.0) -> None:
        if dt < 0.0:
            raise ValueError("dt must be non-negative")
        factor = math.exp(-self.decay_rate * dt)
        self._clusters = [
            replace(
                cluster,
                activation=cluster.activation * factor,
                age=cluster.age + dt,
            )
            for cluster in self._clusters
        ]

    def recall(
        self,
        query: PhaseVector36,
        *,
        top_k: int = 4,
    ) -> tuple[MemoryRecall, ...]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        recalls: list[MemoryRecall] = []
        sigma = max(self.merge_radius, _EPS)
        for cluster in self._clusters:
            distance = query.angular_distance(cluster.centroid)
            berry = float(
                M_36d_berry_connection(
                    list(query.components),
                    list(cluster.centroid.components),
                )
            )
            berry_correction = 1.0 / (1.0 + 0.5 * abs(berry))
            radial = math.exp(-(distance * distance) / (2.0 * sigma * sigma))
            score = (
                cluster.activation
                * cluster.confidence
                * cluster.semantic_mass
                * radial
                * berry_correction
            )
            recalls.append(
                MemoryRecall(
                    cluster=cluster,
                    distance=distance,
                    berry_correction=berry_correction,
                    score=score,
                )
            )
        recalls.sort(key=lambda item: (-item.score, item.distance, item.cluster.cluster_id))
        return tuple(recalls[:top_k])

    def ingest(
        self,
        observation: Observation,
        *,
        semantic_mass: float,
        confidence: float | None = None,
    ) -> MemoryCluster:
        if semantic_mass <= 0.0:
            raise ValueError("semantic_mass must be positive")
        confidence_value = (
            observation.provenance.reliability
            if confidence is None
            else float(confidence)
        )
        if not 0.0 <= confidence_value <= 1.0:
            raise ValueError("confidence must be in [0, 1]")

        nearest_index: int | None = None
        nearest_distance = math.inf
        for index, cluster in enumerate(self._clusters):
            distance = observation.phase.angular_distance(cluster.centroid)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_index = index

        if nearest_index is None or nearest_distance > self.merge_radius:
            cluster = MemoryCluster(
                cluster_id=f"HM{self._next_index:06d}",
                centroid=observation.phase,
                representative_text=observation.text,
                semantic_mass=float(semantic_mass),
                activation=1.0,
                confidence=confidence_value,
                holonomy=float(observation.holonomy),
                member_count=1,
                age=0.0,
                provenance=(observation.provenance.digest_sha256,),
            )
            self._next_index += 1
            self._clusters.append(cluster)
            return cluster

        old = self._clusters[nearest_index]
        total_mass = old.semantic_mass + semantic_mass
        centroid = _circular_blend(
            (old.centroid, observation.phase),
            (old.semantic_mass, semantic_mass),
        )
        transport_phase = float(
            M_36d_berry_connection(
                list(old.centroid.components),
                list(observation.phase.components),
            )
        )
        updated = replace(
            old,
            centroid=centroid,
            representative_text=(
                observation.text
                if semantic_mass >= old.semantic_mass / max(old.member_count, 1)
                else old.representative_text
            ),
            semantic_mass=total_mass,
            activation=old.activation + 1.0,
            confidence=(
                old.confidence * old.semantic_mass
                + confidence_value * semantic_mass
            )
            / total_mass,
            holonomy=old.holonomy + observation.holonomy + transport_phase,
            member_count=old.member_count + 1,
            age=0.0,
            provenance=tuple(
                dict.fromkeys(
                    (*old.provenance, observation.provenance.digest_sha256)
                )
            ),
        )
        self._clusters[nearest_index] = updated
        return updated


@dataclass(frozen=True)
class HTRIConfig:
    """Numerical HTRI mean-field configuration for CPU/GPU oscillator banks."""

    oscillators: int = DEFAULT_OSCILLATORS
    cpu_fraction: float = 0.5
    base_frequency_hz: float = BASE_FREQUENCY_HZ
    frequency_spread_hz: float = KAPPA
    coupling: float = 0.35
    cross_coupling: float = 0.20
    observer_gain: float = 0.20
    intention_gain: float = 0.30
    memory_gain: float = 0.15
    ai_gain: float = 0.25
    mcp_gain: float = 0.20
    dt: float = 1.0 / 240.0
    steps: int = 32
    backend: str = "hybrid"

    def __post_init__(self) -> None:
        if self.oscillators < 2:
            raise ValueError("oscillators must be >= 2")
        if not 0.0 < self.cpu_fraction < 1.0:
            raise ValueError("cpu_fraction must be in (0, 1)")
        if self.base_frequency_hz <= 0.0:
            raise ValueError("base_frequency_hz must be positive")
        if self.frequency_spread_hz < 0.0:
            raise ValueError("frequency_spread_hz must be non-negative")
        if self.dt <= 0.0:
            raise ValueError("dt must be positive")
        if self.steps < 1:
            raise ValueError("steps must be positive")
        if self.backend not in {"cpu", "gpu", "hybrid", "auto"}:
            raise ValueError("backend must be cpu, gpu, hybrid or auto")
        gains = (
            self.coupling,
            self.cross_coupling,
            self.observer_gain,
            self.intention_gain,
            self.memory_gain,
            self.ai_gain,
            self.mcp_gain,
        )
        if any(not math.isfinite(value) or value < 0.0 for value in gains):
            raise ValueError("HTRI gains must be finite and non-negative")


@dataclass(frozen=True)
class HTRIState:
    cpu_phases: tuple[float, ...]
    gpu_phases: tuple[float, ...]
    phase36: PhaseVector36
    cpu_order: float
    gpu_order: float
    global_order: float
    mean_phase: float
    backend: str
    gpu_emulated: bool
    steps: int
    phase_energy: float


class HTRIOscillatorField:
    """Vectorized Kuramoto/HTRI field with AI and MCP phase induction."""

    def __init__(self, config: HTRIConfig | None = None) -> None:
        self.config = config or HTRIConfig()

    @staticmethod
    def _order(phases: np.ndarray) -> tuple[float, float]:
        z = np.mean(np.exp(1j * phases))
        return float(abs(z)), float(np.angle(z) % TAU)

    @staticmethod
    def _project36(cpu: np.ndarray, gpu: np.ndarray) -> PhaseVector36:
        phases = np.concatenate((cpu, gpu))
        out = []
        for dimension in range(PHASE_DIM):
            selected = phases[np.arange(dimension, phases.size, PHASE_DIM)]
            z = np.mean(np.exp(1j * selected))
            out.append(float(np.angle(z) % TAU))
        return PhaseVector36(tuple(out))

    @staticmethod
    def _drive(
        theta: np.ndarray,
        target: PhaseVector36 | None,
        gain: float,
    ) -> np.ndarray:
        if target is None or gain == 0.0:
            return np.zeros_like(theta)
        target_phase = _resample_phase(target, theta.size)
        return gain * np.sin(target_phase - theta)

    def evolve(
        self,
        seed: PhaseVector36,
        *,
        observer: PhaseVector36,
        intention: PhaseVector36,
        memory: PhaseVector36 | None = None,
        ai_phase: PhaseVector36 | None = None,
        mcp_phases: Sequence[PhaseVector36] = (),
    ) -> HTRIState:
        cfg = self.config
        cpu_count = max(1, min(cfg.oscillators - 1, round(cfg.oscillators * cfg.cpu_fraction)))
        gpu_count = cfg.oscillators - cpu_count
        cpu = _resample_phase(seed, cpu_count)
        gpu = _resample_phase(seed, gpu_count)
        cpu += np.linspace(0.0, KAPPA, cpu_count, dtype=np.float64)
        gpu -= np.linspace(0.0, KAPPA, gpu_count, dtype=np.float64)
        cpu %= TAU
        gpu %= TAU

        cpu_omega = BASE_ANGULAR_FREQUENCY + TAU * cfg.frequency_spread_hz * np.linspace(
            -1.0, 1.0, cpu_count, dtype=np.float64
        )
        gpu_omega = BASE_ANGULAR_FREQUENCY + TAU * cfg.frequency_spread_hz * np.linspace(
            1.0, -1.0, gpu_count, dtype=np.float64
        )

        requested_gpu = cfg.backend in {"gpu", "hybrid", "auto"}
        gpu_emulated = requested_gpu
        backend = "cpu"
        if requested_gpu:
            try:
                import cupy as cp  # type: ignore
                gpu_emulated = False
                backend = "hybrid-cupy" if cfg.backend != "gpu" else "gpu-cupy"
                gpu_x = cp.asarray(gpu)
                gpu_omega_x = cp.asarray(gpu_omega)
            except Exception:
                gpu_x = gpu
                gpu_omega_x = gpu_omega
                backend = "hybrid-numpy" if cfg.backend != "gpu" else "gpu-emulated"
        else:
            gpu_x = gpu
            gpu_omega_x = gpu_omega
            backend = "cpu-numpy"

        mcp_target = (
            _circular_blend(tuple(mcp_phases), (1.0,) * len(mcp_phases))
            if mcp_phases
            else None
        )

        for _ in range(cfg.steps):
            gpu_np = (
                np.asarray(gpu_x.get(), dtype=np.float64)
                if hasattr(gpu_x, "get")
                else np.asarray(gpu_x, dtype=np.float64)
            )
            cpu_order, cpu_mean = self._order(cpu)
            gpu_order, gpu_mean = self._order(gpu_np)
            all_order, all_mean = self._order(np.concatenate((cpu, gpu_np)))

            cpu_rhs = (
                cpu_omega
                + cfg.coupling * all_order * np.sin(all_mean - cpu)
                + cfg.cross_coupling * gpu_order * np.sin(gpu_mean - cpu)
                + self._drive(cpu, observer, cfg.observer_gain)
                + self._drive(cpu, intention, cfg.intention_gain)
                + self._drive(cpu, memory, cfg.memory_gain)
                + self._drive(cpu, ai_phase, cfg.ai_gain)
                + self._drive(cpu, mcp_target, cfg.mcp_gain)
            )
            cpu = np.mod(cpu + cfg.dt * cpu_rhs, TAU)

            if hasattr(gpu_x, "get"):
                target_np = (
                    gpu_omega
                    + cfg.coupling * all_order * np.sin(all_mean - gpu_np)
                    + cfg.cross_coupling * cpu_order * np.sin(cpu_mean - gpu_np)
                    + self._drive(gpu_np, observer, cfg.observer_gain)
                    + self._drive(gpu_np, intention, cfg.intention_gain)
                    + self._drive(gpu_np, memory, cfg.memory_gain)
                    + self._drive(gpu_np, ai_phase, cfg.ai_gain)
                    + self._drive(gpu_np, mcp_target, cfg.mcp_gain)
                )
                gpu_x = (gpu_x + cfg.dt * cp.asarray(target_np)) % TAU
            else:
                gpu_rhs = (
                    gpu_omega_x
                    + cfg.coupling * all_order * np.sin(all_mean - gpu_np)
                    + cfg.cross_coupling * cpu_order * np.sin(cpu_mean - gpu_np)
                    + self._drive(gpu_np, observer, cfg.observer_gain)
                    + self._drive(gpu_np, intention, cfg.intention_gain)
                    + self._drive(gpu_np, memory, cfg.memory_gain)
                    + self._drive(gpu_np, ai_phase, cfg.ai_gain)
                    + self._drive(gpu_np, mcp_target, cfg.mcp_gain)
                )
                gpu_x = np.mod(gpu_np + cfg.dt * gpu_rhs, TAU)

        gpu_final = (
            np.asarray(gpu_x.get(), dtype=np.float64)
            if hasattr(gpu_x, "get")
            else np.asarray(gpu_x, dtype=np.float64)
        )
        cpu_order, _ = self._order(cpu)
        gpu_order, _ = self._order(gpu_final)
        global_order, mean_phase = self._order(np.concatenate((cpu, gpu_final)))
        phase_energy = float(
            np.mean(1.0 - np.cos(cpu - mean_phase))
            + np.mean(1.0 - np.cos(gpu_final - mean_phase))
        ) / 2.0

        return HTRIState(
            cpu_phases=tuple(float(value) for value in cpu),
            gpu_phases=tuple(float(value) for value in gpu_final),
            phase36=self._project36(cpu, gpu_final),
            cpu_order=cpu_order,
            gpu_order=gpu_order,
            global_order=global_order,
            mean_phase=mean_phase,
            backend=backend,
            gpu_emulated=gpu_emulated,
            steps=cfg.steps,
            phase_energy=phase_energy,
        )


@dataclass(frozen=True)
class DynamicsConfig:
    dt: float = 0.25
    steps: int = 48
    damping: float = 0.10
    intention_coupling: float = 0.35
    memory_coupling: float = 0.20
    htri_coupling: float = 0.25

    def __post_init__(self) -> None:
        if self.dt <= 0.0:
            raise ValueError("dt must be positive")
        if self.steps < 1:
            raise ValueError("steps must be positive")
        values = (
            self.damping,
            self.intention_coupling,
            self.memory_coupling,
            self.htri_coupling,
        )
        if any(not math.isfinite(value) or value < 0.0 for value in values):
            raise ValueError("dynamical coefficients must be finite and non-negative")


@dataclass(frozen=True)
class DynamicsStep:
    step: int
    time: float
    position: PhaseVector36
    velocity: TangentVector36
    holonomy: float
    potential: float
    kinetic_energy: float
    total_energy: float


@dataclass(frozen=True)
class DynamicsTrace:
    steps: tuple[DynamicsStep, ...]
    final: PhaseVector36
    final_velocity: TangentVector36
    holonomy: float
    context_digest_sha256: str


def evolve_generation_state(
    context: ContextPotential,
    initial: PhaseVector36,
    *,
    intention: PhaseVector36,
    memory: PhaseVector36 | None,
    htri: PhaseVector36,
    semantic_mass: float,
    config: DynamicsConfig | None = None,
) -> DynamicsTrace:
    """Integrate one observer-relative generative orbit on T^36."""

    cfg = config or DynamicsConfig()
    if semantic_mass <= 0.0:
        raise ValueError("semantic_mass must be positive")

    position = initial
    velocity = np.zeros(PHASE_DIM, dtype=np.float64)
    cumulative_holonomy = 0.0
    trace: list[DynamicsStep] = []

    for step in range(cfg.steps + 1):
        sample = context.sample(position)
        kinetic = 0.5 * semantic_mass * float(np.mean(velocity * velocity))
        trace.append(
            DynamicsStep(
                step=step,
                time=step * cfg.dt,
                position=position,
                velocity=TangentVector36(tuple(float(value) for value in velocity)),
                holonomy=cumulative_holonomy,
                potential=sample.potential,
                kinetic_energy=kinetic,
                total_energy=sample.potential + kinetic,
            )
        )
        if step == cfg.steps:
            break

        current = _phase_array(position)
        force = np.asarray(sample.force.components, dtype=np.float64)
        force += cfg.intention_coupling * np.sin(_phase_array(intention) - current)
        if memory is not None:
            force += cfg.memory_coupling * np.sin(_phase_array(memory) - current)
        force += cfg.htri_coupling * np.sin(_phase_array(htri) - current)

        acceleration = force / semantic_mass - (
            sample.viscosity + cfg.damping
        ) * velocity / semantic_mass
        velocity = velocity + cfg.dt * acceleration
        updated = PhaseVector36(tuple(np.mod(current + cfg.dt * velocity, TAU)))
        cumulative_holonomy += float(
            M_36d_berry_connection(
                list(position.components),
                list(updated.components),
            )
        )
        position = updated

    return DynamicsTrace(
        steps=tuple(trace),
        final=position,
        final_velocity=TangentVector36(tuple(float(value) for value in velocity)),
        holonomy=cumulative_holonomy,
        context_digest_sha256=context.digest_sha256,
    )


@dataclass(frozen=True)
class GenerationPlan:
    """Canonical PhaseNav output consumed by CIELingo.

    It contains no natural-language text and performs no lexical projection.
    """

    version: str
    content_phase: PhaseVector36
    observer_phase: PhaseVector36
    observation_phase: PhaseVector36
    intention_phase: PhaseVector36
    context_phase: PhaseVector36
    memory_phase: PhaseVector36 | None
    htri_phase: PhaseVector36
    trajectory: tuple[PhaseVector36, ...]
    semantic_mass: float
    holonomy: float
    coherence: float
    entropy: float
    temperature: float
    recalled_cluster_ids: tuple[str, ...]
    recalled_scores: tuple[float, ...]
    features: Mapping[str, Any]
    htri_backend: str
    htri_order: float
    receipt_sha256: str

    def to_cielingo_payload(self) -> dict[str, Any]:
        """Return the explicit PhaseNav -> CIELingo ABI payload."""

        return {
            "schema": "phasenav.generation-plan/v1",
            "version": self.version,
            "content_phase": list(self.content_phase.components),
            "observer_phase": list(self.observer_phase.components),
            "observation_phase": list(self.observation_phase.components),
            "intention_phase": list(self.intention_phase.components),
            "context_phase": list(self.context_phase.components),
            "memory_phase": (
                None if self.memory_phase is None
                else list(self.memory_phase.components)
            ),
            "htri_phase": list(self.htri_phase.components),
            "trajectory": [list(vector.components) for vector in self.trajectory],
            "semantic_mass": self.semantic_mass,
            "holonomy": self.holonomy,
            "coherence": self.coherence,
            "entropy": self.entropy,
            "temperature": self.temperature,
            "recalled_cluster_ids": list(self.recalled_cluster_ids),
            "recalled_scores": list(self.recalled_scores),
            "features": dict(self.features),
            "htri": {
                "backend": self.htri_backend,
                "order": self.htri_order,
            },
            "receipt_sha256": self.receipt_sha256,
        }


@dataclass(frozen=True)
class PipelineResult:
    observer: ObserverState
    observation: Observation
    perceived: PerceivedState
    intention: IntentionState
    recalls: tuple[MemoryRecall, ...]
    htri: HTRIState
    dynamics: DynamicsTrace
    plan: GenerationPlan


class ObserverToGenerationPipeline:
    """Full computational PhaseNav pipeline ending at a CIELingo plan."""

    def __init__(
        self,
        *,
        memory: HolonomicMemory | None = None,
        htri: HTRIOscillatorField | None = None,
        dynamics: DynamicsConfig | None = None,
        recall_k: int = 4,
    ) -> None:
        if recall_k < 1:
            raise ValueError("recall_k must be positive")
        self.memory = memory or HolonomicMemory()
        self.htri = htri or HTRIOscillatorField()
        self.dynamics = dynamics or DynamicsConfig()
        self.recall_k = recall_k

    @staticmethod
    def observe(
        observer: ObserverState,
        observation: Observation,
        intention: IntentionState,
    ) -> PerceivedState:
        attention = np.asarray(observer.attention, dtype=np.float64)
        attention_gain = float(attention.mean() / max(float(attention.max()), _EPS))
        reliability = observation.provenance.reliability
        observer_weight = max(observer.confidence * attention_gain, _EPS)
        observation_weight = max(reliability, _EPS)
        intention_weight = max(intention.strength / intention.horizon, _EPS)
        phase = _circular_blend(
            (observer.phase, observation.phase, intention.target),
            (observer_weight, observation_weight, intention_weight),
        )
        novelty = observation.phase.angular_distance(observer.phase) / math.pi
        coherence = float(M_36d_order_parameter(list(phase.components)))
        observer_alignment = max(
            0.0, 1.0 - phase.angular_distance(observer.phase) / math.pi
        )
        intention_alignment = max(
            0.0, 1.0 - phase.angular_distance(intention.target) / math.pi
        )
        token_mass = max(1, len(observation.text.split()))
        semantic_mass = KAPPA * token_mass * (
            1.0 + coherence + observer_alignment + intention_alignment
        )
        return PerceivedState(
            phase=phase,
            novelty=novelty,
            coherence=coherence,
            observer_alignment=observer_alignment,
            intention_alignment=intention_alignment,
            semantic_mass=max(semantic_mass, KAPPA),
        )

    @staticmethod
    def _memory_phase(recalls: Sequence[MemoryRecall]) -> PhaseVector36 | None:
        positive = [recall for recall in recalls if recall.score > 0.0]
        if not positive:
            return None
        return _circular_blend(
            tuple(item.cluster.centroid for item in positive),
            tuple(item.score for item in positive),
        )

    @staticmethod
    def _context(
        observer: ObserverState,
        observation: Observation,
        intention: IntentionState,
        perceived: PerceivedState,
        recalls: Sequence[MemoryRecall],
    ) -> ContextPotential:
        anchors = [
            ContextAnchor(
                anchor_id=f"observer:{observer.observer_id}",
                vector=observer.phase,
                weight=max(observer.confidence, KAPPA),
                semantic_mass=max(perceived.semantic_mass, KAPPA),
            ),
            ContextAnchor(
                anchor_id=f"observation:{observation.provenance.digest_sha256[:16]}",
                vector=observation.phase,
                weight=max(observation.provenance.reliability, KAPPA),
                semantic_mass=max(perceived.semantic_mass, KAPPA),
            ),
            ContextAnchor(
                anchor_id=f"intention:{_json_digest(intention.label)[:16]}",
                vector=intention.target,
                weight=max(intention.strength, KAPPA),
                semantic_mass=max(perceived.semantic_mass, KAPPA),
            ),
        ]
        for recall in recalls:
            anchors.append(
                ContextAnchor(
                    anchor_id=f"memory:{recall.cluster.cluster_id}",
                    vector=recall.cluster.centroid,
                    weight=max(recall.score, KAPPA),
                    semantic_mass=recall.cluster.semantic_mass,
                )
            )
        return ContextPotential(tuple(anchors))

    @staticmethod
    def _update_observer(
        observer: ObserverState,
        final: PhaseVector36,
        *,
        dt: float,
    ) -> ObserverState:
        confidence = min(
            1.0,
            0.75 * observer.confidence
            + 0.25 * float(M_36d_order_parameter(list(final.components))),
        )
        return replace(
            observer,
            phase=final,
            confidence=confidence,
            clock=observer.clock + dt,
            sequence=observer.sequence + 1,
        )

    def run(
        self,
        observer: ObserverState,
        text: str,
        *,
        intention_text: str | None = None,
        source: str = "operator",
        reliability: float = 1.0,
        ai_induction: str | PhaseVector36 | None = None,
        mcp_inductions: Sequence[str | PhaseVector36] = (),
    ) -> PipelineResult:
        observation = Observation.from_text(
            text,
            source=source,
            reliability=reliability,
            ordinal=observer.sequence,
        )
        intention = IntentionState.from_text(
            text if intention_text is None else intention_text
        )
        perceived = self.observe(observer, observation, intention)
        recalls = self.memory.recall(perceived.phase, top_k=self.recall_k)
        memory_phase = self._memory_phase(recalls)
        context = self._context(
            observer,
            observation,
            intention,
            perceived,
            recalls,
        )

        def coerce_phase(value: str | PhaseVector36 | None) -> PhaseVector36 | None:
            if value is None:
                return None
            if isinstance(value, PhaseVector36):
                return value
            return PhaseVector36(_phase_tuple(M_sentence_phase(str(value))))

        ai_phase = coerce_phase(ai_induction)
        mcp_phases = tuple(
            phase
            for phase in (coerce_phase(value) for value in mcp_inductions)
            if phase is not None
        )

        htri_state = self.htri.evolve(
            perceived.phase,
            observer=observer.phase,
            intention=intention.target,
            memory=memory_phase,
            ai_phase=ai_phase,
            mcp_phases=mcp_phases,
        )
        dynamics = evolve_generation_state(
            context,
            perceived.phase,
            intention=intention.target,
            memory=memory_phase,
            htri=htri_state.phase36,
            semantic_mass=perceived.semantic_mass,
            config=self.dynamics,
        )
        updated_observer = self._update_observer(
            observer,
            dynamics.final,
            dt=self.dynamics.dt * self.dynamics.steps,
        )
        self.memory.ingest(
            observation,
            semantic_mass=perceived.semantic_mass,
            confidence=observation.provenance.reliability,
        )

        coherence = float(
            M_36d_order_parameter(list(dynamics.final.components))
        )
        entropy = _phase_entropy(dynamics.final)
        temperature = min(1.5, max(0.05, 0.15 + entropy * (1.0 - coherence)))
        trajectory = tuple(step.position for step in dynamics.steps)

        receipt_payload = {
            "version": OBSERVER_GENERATION_VERSION,
            "observer": observer.observer_id,
            "observer_sequence": observer.sequence,
            "observation": observation.provenance.digest_sha256,
            "intention": intention.label,
            "context": dynamics.context_digest_sha256,
            "memory_before": [recall.cluster.cluster_id for recall in recalls],
            "memory_after": self.memory.digest_sha256,
            "htri_backend": htri_state.backend,
            "htri_order": htri_state.global_order,
            "final": dynamics.final.components,
            "holonomy": dynamics.holonomy,
        }
        receipt = _json_digest(receipt_payload)

        plan = GenerationPlan(
            version=OBSERVER_GENERATION_VERSION,
            content_phase=dynamics.final,
            observer_phase=updated_observer.phase,
            observation_phase=observation.phase,
            intention_phase=intention.target,
            context_phase=context.context_vector(),
            memory_phase=memory_phase,
            htri_phase=htri_state.phase36,
            trajectory=trajectory,
            semantic_mass=perceived.semantic_mass,
            holonomy=observation.holonomy + dynamics.holonomy,
            coherence=coherence,
            entropy=entropy,
            temperature=temperature,
            recalled_cluster_ids=tuple(
                recall.cluster.cluster_id for recall in recalls
            ),
            recalled_scores=tuple(float(recall.score) for recall in recalls),
            features=dict(observation.features),
            htri_backend=htri_state.backend,
            htri_order=htri_state.global_order,
            receipt_sha256=receipt,
        )
        return PipelineResult(
            observer=updated_observer,
            observation=observation,
            perceived=perceived,
            intention=intention,
            recalls=recalls,
            htri=htri_state,
            dynamics=dynamics,
            plan=plan,
        )
