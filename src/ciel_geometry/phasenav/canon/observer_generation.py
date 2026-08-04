"""Canonical PhaseNav observer-to-generation computational formalism.

Pipeline:
observer -> observation -> intention -> context -> holonomic memory ->
AI/MCP-induced CPU/GPU HTRI -> dynamics -> GenerationPlan.

PhaseNav ends at GenerationPlan. CIELingo owns language projection.
The HTRI implementation is a finite numerical model; physical-carrier claims
remain separate falsifiable bridge obligations.
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
from .context_dynamics import ContextAnchor, ContextPotential, PhaseVector36, TangentVector36
from .model import ETA_M_36D, PHASE_DIM

OBSERVER_GENERATION_VERSION = "1.0.1"
BASE_FREQUENCY_HZ = 7.83
BASE_ANGULAR_FREQUENCY = TAU * BASE_FREQUENCY_HZ
DEFAULT_OSCILLATORS = 120
_EPS = 1.0e-12


def _phase(values: Sequence[float]) -> PhaseVector36:
    if len(values) != PHASE_DIM:
        raise ValueError(f"expected {PHASE_DIM} phase coordinates")
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("phase coordinates must be finite")
    return PhaseVector36(tuple(float(v) % TAU for v in values))


def _array(vector: PhaseVector36) -> np.ndarray:
    return np.asarray(vector.components, dtype=np.float64)


def _blend(vectors: Sequence[PhaseVector36], weights: Sequence[float]) -> PhaseVector36:
    if not vectors or len(vectors) != len(weights):
        raise ValueError("vectors and weights must be non-empty and aligned")
    w = np.asarray(weights, dtype=np.float64)
    if np.any(w < 0.0) or not np.all(np.isfinite(w)) or float(w.sum()) <= 0.0:
        raise ValueError("weights must be finite, non-negative and non-zero")
    phases = np.asarray([v.components for v in vectors], dtype=np.float64)
    return _phase(np.mod(np.arctan2(
        np.sum(w[:, None] * np.sin(phases), axis=0),
        np.sum(w[:, None] * np.cos(phases), axis=0),
    ), TAU))


def _digest(payload: Any) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _resample(vector: PhaseVector36, size: int) -> np.ndarray:
    if size < 1:
        raise ValueError("size must be positive")
    source = _array(vector)
    return np.array(source[np.arange(size) % PHASE_DIM], dtype=np.float64, copy=True)


def _entropy(vector: PhaseVector36) -> float:
    counts, _ = np.histogram(_array(vector), bins=PHASE_DIM, range=(0.0, TAU))
    p = counts.astype(np.float64)
    p /= max(float(p.sum()), 1.0)
    p = p[p > 0.0]
    return -float(np.sum(p * np.log(p))) / math.log(PHASE_DIM)


@dataclass(frozen=True)
class Provenance:
    source: str
    modality: str
    reliability: float
    digest_sha256: str
    ordinal: int = 0

    def __post_init__(self) -> None:
        if not self.source or not self.modality:
            raise ValueError("source and modality must not be empty")
        if not 0.0 <= self.reliability <= 1.0:
            raise ValueError("reliability must be in [0,1]")
        if len(self.digest_sha256) != 64 or self.ordinal < 0:
            raise ValueError("invalid provenance receipt")

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        source: str,
        reliability: float,
        ordinal: int,
    ) -> "Provenance":
        return cls(
            source=source,
            modality="text",
            reliability=float(reliability),
            digest_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            ordinal=int(ordinal),
        )


@dataclass(frozen=True)
class Observation:
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
        text = str(text)
        final, trajectory, holonomy = M_sentence_phase_trajectory(text)
        terminal = _phase(final)
        return cls(
            text=text,
            phase=terminal,
            trajectory=tuple(_phase(v) for v in trajectory) or (terminal,),
            holonomy=float(holonomy),
            features=dict(M_quantum_features(text)),
            provenance=Provenance.from_text(
                text, source=source, reliability=reliability, ordinal=ordinal
            ),
        )


@dataclass(frozen=True)
class ObserverState:
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
        if len(self.attention) != PHASE_DIM or any(v < 0.0 for v in self.attention):
            raise ValueError("attention must be a non-negative 36D vector")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0,1]")
        if not 0.0 <= self.ethical_weight <= 1.0:
            raise ValueError("ethical_weight must be in [0,1]")
        if self.clock < 0.0 or self.sequence < 0:
            raise ValueError("clock and sequence must be non-negative")


@dataclass(frozen=True)
class IntentionState:
    label: str
    target: PhaseVector36
    strength: float = 1.0
    horizon: float = 1.0

    def __post_init__(self) -> None:
        if not self.label or self.strength < 0.0 or self.horizon <= 0.0:
            raise ValueError("invalid intention")

    @classmethod
    def from_text(cls, text: str, *, strength: float = 1.0, horizon: float = 1.0) -> "IntentionState":
        text = str(text)
        return cls(text, _phase(M_sentence_phase(text)), float(strength), float(horizon))


@dataclass(frozen=True)
class PerceivedState:
    phase: PhaseVector36
    novelty: float
    coherence: float
    observer_alignment: float
    intention_alignment: float
    semantic_mass: float


@dataclass(frozen=True)
class MemoryCluster:
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


@dataclass(frozen=True)
class MemoryRecall:
    cluster: MemoryCluster
    distance: float
    berry_correction: float
    score: float


class HolonomicMemory:
    def __init__(self, *, merge_radius: float = ETA_M_36D, decay_rate: float = KAPPA) -> None:
        if merge_radius <= 0.0 or decay_rate < 0.0:
            raise ValueError("invalid memory parameters")
        self.merge_radius = float(merge_radius)
        self.decay_rate = float(decay_rate)
        self._clusters: list[MemoryCluster] = []
        self._next = 0

    @property
    def clusters(self) -> tuple[MemoryCluster, ...]:
        return tuple(self._clusters)

    @property
    def digest_sha256(self) -> str:
        return _digest([
            {**asdict(c), "centroid": c.centroid.components} for c in self._clusters
        ])

    def decay(self, dt: float = 1.0) -> None:
        if dt < 0.0:
            raise ValueError("dt must be non-negative")
        factor = math.exp(-self.decay_rate * dt)
        self._clusters = [
            replace(c, activation=c.activation * factor, age=c.age + dt)
            for c in self._clusters
        ]

    def recall(self, query: PhaseVector36, *, top_k: int = 4) -> tuple[MemoryRecall, ...]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        out = []
        sigma = max(self.merge_radius, _EPS)
        for c in self._clusters:
            distance = query.angular_distance(c.centroid)
            berry = float(M_36d_berry_connection(
                list(query.components), list(c.centroid.components)
            ))
            correction = 1.0 / (1.0 + 0.5 * abs(berry))
            radial = math.exp(-(distance ** 2) / (2.0 * sigma ** 2))
            out.append(MemoryRecall(
                c, distance, correction,
                c.activation * c.confidence * c.semantic_mass * radial * correction,
            ))
        out.sort(key=lambda r: (-r.score, r.distance, r.cluster.cluster_id))
        return tuple(out[:top_k])

    def ingest(
        self,
        observation: Observation,
        *,
        semantic_mass: float,
        confidence: float | None = None,
    ) -> MemoryCluster:
        if semantic_mass <= 0.0:
            raise ValueError("semantic_mass must be positive")
        confidence = observation.provenance.reliability if confidence is None else float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be in [0,1]")
        nearest = min(
            enumerate(self._clusters),
            key=lambda item: observation.phase.angular_distance(item[1].centroid),
            default=None,
        )
        if nearest is None or observation.phase.angular_distance(nearest[1].centroid) > self.merge_radius:
            cluster = MemoryCluster(
                f"HM{self._next:06d}", observation.phase, observation.text,
                float(semantic_mass), 1.0, confidence, observation.holonomy,
                1, 0.0, (observation.provenance.digest_sha256,),
            )
            self._next += 1
            self._clusters.append(cluster)
            return cluster

        index, old = nearest
        total = old.semantic_mass + semantic_mass
        transport = float(M_36d_berry_connection(
            list(old.centroid.components), list(observation.phase.components)
        ))
        updated = replace(
            old,
            centroid=_blend(
                (old.centroid, observation.phase), (old.semantic_mass, semantic_mass)
            ),
            representative_text=(
                observation.text
                if semantic_mass >= old.semantic_mass / old.member_count
                else old.representative_text
            ),
            semantic_mass=total,
            activation=old.activation + 1.0,
            confidence=(old.confidence * old.semantic_mass + confidence * semantic_mass) / total,
            holonomy=old.holonomy + observation.holonomy + transport,
            member_count=old.member_count + 1,
            age=0.0,
            provenance=tuple(dict.fromkeys(
                (*old.provenance, observation.provenance.digest_sha256)
            )),
        )
        self._clusters[index] = updated
        return updated


@dataclass(frozen=True)
class HTRIConfig:
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
        if self.oscillators < 2 or not 0.0 < self.cpu_fraction < 1.0:
            raise ValueError("invalid oscillator partition")
        if self.base_frequency_hz <= 0.0 or self.frequency_spread_hz < 0.0:
            raise ValueError("invalid frequency")
        if self.dt <= 0.0 or self.steps < 1:
            raise ValueError("invalid integration parameters")
        if self.backend not in {"cpu", "gpu", "hybrid", "auto"}:
            raise ValueError("invalid backend")
        if any(v < 0.0 for v in (
            self.coupling, self.cross_coupling, self.observer_gain,
            self.intention_gain, self.memory_gain, self.ai_gain, self.mcp_gain,
        )):
            raise ValueError("HTRI gains must be non-negative")


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
    def __init__(self, config: HTRIConfig | None = None) -> None:
        self.config = config or HTRIConfig()

    @staticmethod
    def _order(phases: np.ndarray) -> tuple[float, float]:
        z = np.mean(np.exp(1j * phases))
        return float(abs(z)), float(np.angle(z) % TAU)

    @staticmethod
    def _drive(theta: np.ndarray, target: PhaseVector36 | None, gain: float) -> np.ndarray:
        return (
            np.zeros_like(theta)
            if target is None or gain == 0.0
            else gain * np.sin(_resample(target, theta.size) - theta)
        )

    @staticmethod
    def _project36(cpu: np.ndarray, gpu: np.ndarray) -> PhaseVector36:
        phases = np.concatenate((cpu, gpu))
        return _phase([
            float(np.angle(np.mean(np.exp(
                1j * phases[np.arange(d, phases.size, PHASE_DIM)]
            ))) % TAU)
            for d in range(PHASE_DIM)
        ])

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
        c = self.config
        nc = max(1, min(c.oscillators - 1, round(c.oscillators * c.cpu_fraction)))
        ng = c.oscillators - nc
        cpu = (_resample(seed, nc) + np.linspace(0.0, KAPPA, nc)) % TAU
        gpu = (_resample(seed, ng) - np.linspace(0.0, KAPPA, ng)) % TAU
        omega0 = TAU * c.base_frequency_hz
        cpu_omega = omega0 + TAU * c.frequency_spread_hz * np.linspace(-1.0, 1.0, nc)
        gpu_omega = omega0 + TAU * c.frequency_spread_hz * np.linspace(1.0, -1.0, ng)
        mcp = _blend(tuple(mcp_phases), (1.0,) * len(mcp_phases)) if mcp_phases else None

        requested_gpu = c.backend in {"gpu", "hybrid", "auto"}
        gpu_emulated = requested_gpu
        cp = None
        if requested_gpu:
            try:
                import cupy as cp_module  # type: ignore
                cp = cp_module
                gpu_x = cp.asarray(gpu)
                backend = "gpu-cupy" if c.backend == "gpu" else "hybrid-cupy"
                gpu_emulated = False
            except Exception:
                gpu_x = gpu
                backend = "gpu-emulated" if c.backend == "gpu" else "hybrid-numpy"
        else:
            gpu_x = gpu
            backend = "cpu-numpy"

        for _ in range(c.steps):
            gpu_np = np.asarray(gpu_x.get() if hasattr(gpu_x, "get") else gpu_x)
            rc, pc = self._order(cpu)
            rg, pg = self._order(gpu_np)
            r, p = self._order(np.concatenate((cpu, gpu_np)))
            cpu_rhs = (
                cpu_omega + c.coupling * r * np.sin(p - cpu)
                + c.cross_coupling * rg * np.sin(pg - cpu)
                + self._drive(cpu, observer, c.observer_gain)
                + self._drive(cpu, intention, c.intention_gain)
                + self._drive(cpu, memory, c.memory_gain)
                + self._drive(cpu, ai_phase, c.ai_gain)
                + self._drive(cpu, mcp, c.mcp_gain)
            )
            cpu = (cpu + c.dt * cpu_rhs) % TAU
            gpu_rhs = (
                gpu_omega + c.coupling * r * np.sin(p - gpu_np)
                + c.cross_coupling * rc * np.sin(pc - gpu_np)
                + self._drive(gpu_np, observer, c.observer_gain)
                + self._drive(gpu_np, intention, c.intention_gain)
                + self._drive(gpu_np, memory, c.memory_gain)
                + self._drive(gpu_np, ai_phase, c.ai_gain)
                + self._drive(gpu_np, mcp, c.mcp_gain)
            )
            gpu_x = (
                (gpu_x + c.dt * cp.asarray(gpu_rhs)) % TAU
                if cp is not None
                else (gpu_np + c.dt * gpu_rhs) % TAU
            )

        gpu = np.asarray(gpu_x.get() if hasattr(gpu_x, "get") else gpu_x)
        rc, _ = self._order(cpu)
        rg, _ = self._order(gpu)
        r, p = self._order(np.concatenate((cpu, gpu)))
        energy = float(
            np.mean(1.0 - np.cos(cpu - p)) + np.mean(1.0 - np.cos(gpu - p))
        ) / 2.0
        return HTRIState(
            tuple(map(float, cpu)), tuple(map(float, gpu)), self._project36(cpu, gpu),
            rc, rg, r, p, backend, gpu_emulated, c.steps, energy,
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
        if self.dt <= 0.0 or self.steps < 1 or any(v < 0.0 for v in (
            self.damping, self.intention_coupling,
            self.memory_coupling, self.htri_coupling,
        )):
            raise ValueError("invalid dynamics configuration")


@dataclass(frozen=True)
class DynamicsStep:
    step: int
    time: float
    position: PhaseVector36
    velocity: TangentVector36
    holonomy: float
    context_potential: float
    drive_potential: float
    potential: float
    kinetic_energy: float
    lagrangian: float
    hamiltonian: float


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
    c = config or DynamicsConfig()
    if semantic_mass <= 0.0:
        raise ValueError("semantic_mass must be positive")
    position = initial
    velocity = np.zeros(PHASE_DIM)
    holonomy = 0.0
    steps = []
    for index in range(c.steps + 1):
        sample = context.sample(position)
        current = _array(position)
        drive = c.intention_coupling * float(np.mean(
            1.0 - np.cos(_array(intention) - current)
        ))
        if memory is not None:
            drive += c.memory_coupling * float(np.mean(
                1.0 - np.cos(_array(memory) - current)
            ))
        drive += c.htri_coupling * float(np.mean(
            1.0 - np.cos(_array(htri) - current)
        ))
        potential = sample.potential + drive
        kinetic = 0.5 * semantic_mass * float(np.mean(velocity ** 2))
        steps.append(DynamicsStep(
            index, index * c.dt, position, TangentVector36(tuple(velocity)),
            holonomy, sample.potential, drive, potential, kinetic,
            kinetic - potential, kinetic + potential,
        ))
        if index == c.steps:
            break
        force = np.asarray(sample.force.components)
        force += c.intention_coupling * np.sin(_array(intention) - current)
        if memory is not None:
            force += c.memory_coupling * np.sin(_array(memory) - current)
        force += c.htri_coupling * np.sin(_array(htri) - current)
        acceleration = force / semantic_mass - (
            sample.viscosity + c.damping
        ) * velocity / semantic_mass
        velocity += c.dt * acceleration
        updated = _phase((current + c.dt * velocity) % TAU)
        holonomy += float(M_36d_berry_connection(
            list(position.components), list(updated.components)
        ))
        position = updated
    return DynamicsTrace(
        tuple(steps), position, TangentVector36(tuple(velocity)),
        holonomy, context.digest_sha256,
    )


@dataclass(frozen=True)
class GenerationPlan:
    """Terminal PhaseNav state consumed by CIELingo; contains no text output."""

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
        return {
            "schema": "phasenav.generation-plan/v1",
            "version": self.version,
            "content_phase": list(self.content_phase.components),
            "observer_phase": list(self.observer_phase.components),
            "observation_phase": list(self.observation_phase.components),
            "intention_phase": list(self.intention_phase.components),
            "context_phase": list(self.context_phase.components),
            "memory_phase": None if self.memory_phase is None else list(self.memory_phase.components),
            "htri_phase": list(self.htri_phase.components),
            "trajectory": [list(v.components) for v in self.trajectory],
            "semantic_mass": self.semantic_mass,
            "holonomy": self.holonomy,
            "coherence": self.coherence,
            "entropy": self.entropy,
            "temperature": self.temperature,
            "recalled_cluster_ids": list(self.recalled_cluster_ids),
            "recalled_scores": list(self.recalled_scores),
            "features": dict(self.features),
            "htri": {"backend": self.htri_backend, "order": self.htri_order},
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
        observer: ObserverState, observation: Observation, intention: IntentionState
    ) -> PerceivedState:
        attention = np.asarray(observer.attention)
        attention_gain = float(attention.mean() / max(float(attention.max()), _EPS))
        observer_weight = max(
            observer.confidence * attention_gain * max(observer.ethical_weight, KAPPA),
            _EPS,
        )
        perceived = _blend(
            (observer.phase, observation.phase, intention.target),
            (observer_weight, max(observation.provenance.reliability, _EPS),
             max(intention.strength / intention.horizon, _EPS)),
        )
        observer_alignment = max(
            0.0, 1.0 - perceived.angular_distance(observer.phase) / math.pi
        )
        intention_alignment = max(
            0.0, 1.0 - perceived.angular_distance(intention.target) / math.pi
        )
        coherence = float(M_36d_order_parameter(list(perceived.components)))
        mass = KAPPA * max(1, len(observation.text.split())) * (
            1.0 + coherence + observer_alignment + intention_alignment
        ) * (0.5 + 0.5 * observer.ethical_weight)
        return PerceivedState(
            perceived,
            observation.phase.angular_distance(observer.phase) / math.pi,
            coherence,
            observer_alignment,
            intention_alignment,
            max(mass, KAPPA),
        )

    @staticmethod
    def _memory_phase(recalls: Sequence[MemoryRecall]) -> PhaseVector36 | None:
        positive = [r for r in recalls if r.score > 0.0]
        return (
            None if not positive
            else _blend(
                tuple(r.cluster.centroid for r in positive),
                tuple(r.score for r in positive),
            )
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
                f"observer:{observer.observer_id}", observer.phase,
                max(observer.confidence * observer.ethical_weight, KAPPA),
                perceived.semantic_mass,
            ),
            ContextAnchor(
                f"observation:{observation.provenance.digest_sha256[:16]}",
                observation.phase, max(observation.provenance.reliability, KAPPA),
                perceived.semantic_mass,
            ),
            ContextAnchor(
                f"intention:{_digest(intention.label)[:16]}", intention.target,
                max(intention.strength, KAPPA), perceived.semantic_mass,
            ),
        ]
        anchors.extend(
            ContextAnchor(
                f"memory:{r.cluster.cluster_id}", r.cluster.centroid,
                max(r.score, KAPPA), r.cluster.semantic_mass,
            )
            for r in recalls
        )
        return ContextPotential(tuple(anchors))

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
            text, source=source, reliability=reliability, ordinal=observer.sequence
        )
        intention = IntentionState.from_text(
            text if intention_text is None else intention_text
        )
        perceived = self.observe(observer, observation, intention)
        recalls = self.memory.recall(perceived.phase, top_k=self.recall_k)
        memory_phase = self._memory_phase(recalls)
        context = self._context(observer, observation, intention, perceived, recalls)

        def coerce(value: str | PhaseVector36 | None) -> PhaseVector36 | None:
            return (
                None if value is None
                else value if isinstance(value, PhaseVector36)
                else _phase(M_sentence_phase(str(value)))
            )

        ai_phase = coerce(ai_induction)
        mcp = tuple(v for v in (coerce(x) for x in mcp_inductions) if v is not None)
        htri = self.htri.evolve(
            perceived.phase, observer=observer.phase, intention=intention.target,
            memory=memory_phase, ai_phase=ai_phase, mcp_phases=mcp,
        )
        dynamics = evolve_generation_state(
            context, perceived.phase, intention=intention.target,
            memory=memory_phase, htri=htri.phase36,
            semantic_mass=perceived.semantic_mass, config=self.dynamics,
        )
        coherence = float(M_36d_order_parameter(list(dynamics.final.components)))
        updated_observer = replace(
            observer,
            phase=dynamics.final,
            confidence=min(1.0, 0.75 * observer.confidence + 0.25 * coherence),
            clock=observer.clock + self.dynamics.dt * self.dynamics.steps,
            sequence=observer.sequence + 1,
        )
        self.memory.ingest(
            observation, semantic_mass=perceived.semantic_mass,
            confidence=observation.provenance.reliability,
        )
        receipt = _digest({
            "version": OBSERVER_GENERATION_VERSION,
            "observer": observer.observer_id,
            "sequence": observer.sequence,
            "observation": observation.provenance.digest_sha256,
            "intention": intention.label,
            "context": dynamics.context_digest_sha256,
            "memory_before": [r.cluster.cluster_id for r in recalls],
            "memory_after": self.memory.digest_sha256,
            "htri": [htri.backend, htri.global_order],
            "final": dynamics.final.components,
            "holonomy": dynamics.holonomy,
        })
        entropy = _entropy(dynamics.final)
        plan = GenerationPlan(
            OBSERVER_GENERATION_VERSION,
            dynamics.final, updated_observer.phase, observation.phase,
            intention.target, context.context_vector(), memory_phase, htri.phase36,
            tuple(step.position for step in dynamics.steps),
            perceived.semantic_mass, observation.holonomy + dynamics.holonomy,
            coherence, entropy,
            min(1.5, max(0.05, 0.15 + entropy * (1.0 - coherence))),
            tuple(r.cluster.cluster_id for r in recalls),
            tuple(float(r.score) for r in recalls),
            dict(observation.features), htri.backend, htri.global_order, receipt,
        )
        return PipelineResult(
            updated_observer, observation, perceived, intention,
            recalls, htri, dynamics, plan,
        )
