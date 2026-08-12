"""Current native PhaseNav executable algorithms mapped onto concept cards.

Unlike ``ciel_executable_map`` (cross-repository provenance), this module maps
algorithms that are already part of the current PhaseNav runtime.  Recognition
of a concept still never executes an algorithm; the mapping is declarative and
execution requires explicit dispatch by a caller.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable, Literal


NATIVE_EXECUTABLE_MAP_VERSION = "0.13.0"
NATIVE_EXECUTABLE_MAP_STATUS = "CURRENT_NATIVE_TYPED_BINDING_NO_AUTO_EXECUTION"
PHASENAV_NATIVE_REPO = "AdrianLipa90/noema-phasenav-core"
PHASENAV_NATIVE_COMMIT = "3be5df43492ef011ad0847ba3b9891aa86de994f"

NativeSideEffect = Literal["PURE", "READ", "STATEFUL", "VERIFY", "ORCHESTRATE"]


@dataclass(frozen=True)
class NativeExecutableBinding:
    binding_id: str
    family: str
    source_repo: str
    source_commit: str
    source_blob_sha: str
    source_path: str
    symbol: str
    provenance_class: str
    side_effect: NativeSideEffect
    concept_ids: tuple[str, ...]
    priority: int
    semantic_role: str
    execution_activation: str = "EXPLICIT_RUNTIME_DISPATCH"
    scientific_promotion: str = "NOT_PERFORMED"

    def __post_init__(self) -> None:
        if self.provenance_class != "PHASENAV_NATIVE_CURRENT":
            raise ValueError("native binding must retain PHASENAV_NATIVE_CURRENT provenance")
        if not self.concept_ids:
            raise ValueError("native binding needs at least one concept")
        if any(len(cid) != 3 or not cid.isdigit() for cid in self.concept_ids):
            raise ValueError("concept ids must be zero-padded 3-digit strings")
        if self.execution_activation != "EXPLICIT_RUNTIME_DISPATCH":
            raise ValueError("concept recognition must not auto-execute algorithms")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_BLOB = {
    "observer_generation": "24a2965c42ecedfd27555f055643c3e0c7671fda",
    "operator_calculus": "557689f8e207ba4537397b3bae591379f211ef32",
    "context_dynamics": "1a8e82faaf6dcfeae2b56853bc289f6215ed65c7",
    "numerical_guards": "22acc82bd88a408d04f34ddd8c0c31f4940727a5",
}


def _n(
    binding_id: str,
    family: str,
    *,
    blob: str,
    path: str,
    symbol: str,
    side_effect: NativeSideEffect,
    concepts: Iterable[str],
    priority: int,
    role: str,
) -> NativeExecutableBinding:
    return NativeExecutableBinding(
        binding_id=binding_id,
        family=family,
        source_repo=PHASENAV_NATIVE_REPO,
        source_commit=PHASENAV_NATIVE_COMMIT,
        source_blob_sha=blob,
        source_path=path,
        symbol=symbol,
        provenance_class="PHASENAV_NATIVE_CURRENT",
        side_effect=side_effect,
        concept_ids=tuple(str(x).zfill(3) for x in concepts),
        priority=priority,
        semantic_role=role,
    )


_BINDINGS: tuple[NativeExecutableBinding, ...] = (
    # --------------------------------------------------------------- memory
    _n(
        "PNV.MEMORY.HOLONOMIC_RECALL.NATIVE", "memory",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="HolonomicMemory.recall", side_effect="READ",
        concepts=("090", "089"), priority=5,
        role="Berry-corrected retrieval from phase-holonomic memory clusters",
    ),
    _n(
        "PNV.MEMORY.HOLONOMIC_INGEST.NATIVE", "memory",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="HolonomicMemory.ingest", side_effect="STATEFUL",
        concepts=("090", "071", "080"), priority=10,
        role="merge-or-create holonomic memory cluster with provenance preservation",
    ),
    _n(
        "PNV.MEMORY.DECAY.NATIVE", "memory",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="HolonomicMemory.decay", side_effect="STATEFUL",
        concepts=("090", "018", "114"), priority=20,
        role="time-parameterized activation decay and memory-cluster ageing",
    ),
    _n(
        "PNV.MEMORY.HOLONOMY_CACHE_GET.NATIVE", "memory",
        blob=_BLOB["operator_calculus"],
        path="src/ciel_geometry/phasenav/canon/operator_calculus.py",
        symbol="HolonomyCache.get", side_effect="READ",
        concepts=("090", "089"), priority=25,
        role="deterministic holonomy-result lookup by semantic CRC and operator identity",
    ),
    _n(
        "PNV.MEMORY.HOLONOMY_CACHE_PUT.NATIVE", "memory",
        blob=_BLOB["operator_calculus"],
        path="src/ciel_geometry/phasenav/canon/operator_calculus.py",
        symbol="HolonomyCache.put", side_effect="STATEFUL",
        concepts=("090", "080"), priority=30,
        role="cache a provenance-addressable holonomy result",
    ),

    # ----------------------------------------------------------- perception
    _n(
        "PNV.PERCEPTION.OBSERVATION_FROM_TEXT.NATIVE", "perception",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="Observation.from_text", side_effect="PURE",
        concepts=("077", "071", "092"), priority=5,
        role="text -> phase trajectory, holonomy, quantum features, provenance receipt",
    ),
    _n(
        "PNV.INTENTION.FROM_TEXT.NATIVE", "intention",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="IntentionState.from_text", side_effect="PURE",
        concepts=("002", "040"), priority=5,
        role="text -> typed intention target on T^36",
    ),
    _n(
        "PNV.OBSERVER.PERCEIVE.NATIVE", "perception",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="ObserverToGenerationPipeline.observe", side_effect="PURE",
        concepts=("077", "074", "031"), priority=10,
        role="observer/observation/intention weighted phase perception",
    ),

    # --------------------------------------------------------------- context
    _n(
        "PNV.CONTEXT.FROM_CONCEPTS.NATIVE", "context",
        blob=_BLOB["context_dynamics"],
        path="src/ciel_geometry/phasenav/canon/context_dynamics.py",
        symbol="ContextPotential.from_concepts", side_effect="PURE",
        concepts=("073", "083"), priority=5,
        role="concept set -> weighted smooth context potential on T^36",
    ),
    _n(
        "PNV.CONTEXT.VECTOR.NATIVE", "context",
        blob=_BLOB["context_dynamics"],
        path="src/ciel_geometry/phasenav/canon/context_dynamics.py",
        symbol="ContextPotential.context_vector", side_effect="PURE",
        concepts=("073",), priority=10,
        role="weighted circular resultant of context anchors",
    ),
    _n(
        "PNV.CONTEXT.SAMPLE.NATIVE", "context",
        blob=_BLOB["context_dynamics"],
        path="src/ciel_geometry/phasenav/canon/context_dynamics.py",
        symbol="ContextPotential.sample", side_effect="PURE",
        concepts=("073", "083", "067"), priority=15,
        role="density, potential, viscosity, variance, gradient and force at a T^36 point",
    ),
    _n(
        "PNV.CONTEXT.FIND_ATTRACTORS.NATIVE", "context",
        blob=_BLOB["context_dynamics"],
        path="src/ciel_geometry/phasenav/canon/context_dynamics.py",
        symbol="find_attractors", side_effect="PURE",
        concepts=("073", "080", "094"), priority=20,
        role="deterministic circular mean-shift context attractor search",
    ),
    _n(
        "PNV.CONTEXT.TRACE_ORBIT.NATIVE", "context",
        blob=_BLOB["context_dynamics"],
        path="src/ciel_geometry/phasenav/canon/context_dynamics.py",
        symbol="trace_orbit", side_effect="PURE",
        concepts=("073", "036", "080"), priority=25,
        role="semi-implicit integration of damped semantic orbit in context potential",
    ),

    # -------------------------------------------------------------- temporal
    _n(
        "PNV.TIME.GENERATION_DYNAMICS.NATIVE", "temporal",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="evolve_generation_state", side_effect="PURE",
        concepts=("018", "080", "114", "115"), priority=5,
        role="finite dt evolution of context/intention/memory/HTRI coupled phase state",
    ),
    _n(
        "PNV.TIME.TRAJECTORY_CURVATURE.NATIVE", "temporal",
        blob=_BLOB["numerical_guards"],
        path="src/ciel_geometry/phasenav/canon/numerical_guards.py",
        symbol="stable_trajectory_curvature", side_effect="PURE",
        concepts=("018", "080", "067"), priority=10,
        role="finite stabilized RMS turning curvature of a phase trajectory",
    ),

    # ------------------------------------------------------------ scheduling
    _n(
        "PNV.SCHEDULER.COST.NATIVE", "scheduler",
        blob=_BLOB["operator_calculus"],
        path="src/ciel_geometry/phasenav/canon/operator_calculus.py",
        symbol="SemanticScheduler.cost", side_effect="PURE",
        concepts=("035", "067", "115"), priority=5,
        role="semantic scheduling cost from potential, entropy, urgency and provenance weight",
    ),
    _n(
        "PNV.SCHEDULER.PUSH.NATIVE", "scheduler",
        blob=_BLOB["operator_calculus"],
        path="src/ciel_geometry/phasenav/canon/operator_calculus.py",
        symbol="SemanticScheduler.push", side_effect="STATEFUL",
        concepts=("035", "115", "080"), priority=10,
        role="enqueue semantic state with deterministic priority and sequence tie-break",
    ),
    _n(
        "PNV.SCHEDULER.POP.NATIVE", "scheduler",
        blob=_BLOB["operator_calculus"],
        path="src/ciel_geometry/phasenav/canon/operator_calculus.py",
        symbol="SemanticScheduler.pop", side_effect="STATEFUL",
        concepts=("035", "115", "105"), priority=15,
        role="select next lowest-cost semantic state for execution",
    ),

    # --------------------------------------------------------- constraints
    _n(
        "PNV.CONSTRAINT.PROJECT_FORBIDDEN.NATIVE", "constraint",
        blob=_BLOB["operator_calculus"],
        path="src/ciel_geometry/phasenav/canon/operator_calculus.py",
        symbol="project_forbidden_directions", side_effect="PURE",
        concepts=("013", "067", "088"), priority=5,
        role="orthogonally remove explicitly forbidden tangent directions",
    ),

    # ----------------------------------------------------------- full pipeline
    _n(
        "PNV.PIPELINE.OBSERVER_TO_GENERATION.NATIVE", "pipeline",
        blob=_BLOB["observer_generation"],
        path="src/ciel_geometry/phasenav/canon/observer_generation.py",
        symbol="ObserverToGenerationPipeline.run", side_effect="ORCHESTRATE",
        concepts=("031", "077", "002", "073", "090", "105"), priority=50,
        role="observer -> observation -> intention -> memory -> context -> HTRI -> GenerationPlan",
    ),
)


def native_executable_bindings() -> tuple[NativeExecutableBinding, ...]:
    return _BINDINGS


def native_binding_by_id(binding_id: str) -> NativeExecutableBinding:
    for binding in _BINDINGS:
        if binding.binding_id == binding_id:
            return binding
    raise KeyError(binding_id)


def native_bindings_for_concept(concept_id: str | int) -> tuple[NativeExecutableBinding, ...]:
    key = str(concept_id).zfill(3)
    return tuple(sorted(
        (binding for binding in _BINDINGS if key in binding.concept_ids),
        key=lambda row: (row.priority, row.binding_id),
    ))


def native_bindings_for_family(family: str) -> tuple[NativeExecutableBinding, ...]:
    key = str(family).strip().lower()
    return tuple(sorted(
        (binding for binding in _BINDINGS if binding.family == key),
        key=lambda row: (row.priority, row.binding_id),
    ))


def native_executable_map_receipt() -> dict[str, object]:
    rows = [binding.to_dict() for binding in _BINDINGS]
    payload: dict[str, object] = {
        "schema": "phasenav.native-executable-concept-map/v0.13",
        "version": NATIVE_EXECUTABLE_MAP_VERSION,
        "status": NATIVE_EXECUTABLE_MAP_STATUS,
        "source_anchor": {"repo": PHASENAV_NATIVE_REPO, "commit": PHASENAV_NATIVE_COMMIT},
        "bindings": rows,
        "binding_count": len(rows),
        "families": sorted({binding.family for binding in _BINDINGS}),
        "policy": {
            "auto_execute_from_concept_match": False,
            "source_is_current_native_runtime": True,
            "scientific_promotion": "NOT_PERFORMED",
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    payload["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
