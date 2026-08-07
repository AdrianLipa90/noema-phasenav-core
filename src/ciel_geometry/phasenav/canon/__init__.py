"""PhaseNav hard canon v1."""
from .model import (
    ALPHA_M,
    CANON_VERSION,
    ETA_M_36D,
    HILBERT_BITS,
    HILBERT_DIM,
    KAPPA,
    L3,
    L4,
    L5,
    PHASE_DIM,
    CanonicalConceptState,
    Hilbert2048State,
    semantic_mass,
)
from .orbital import OrbitalRecord, architectural_role, audit_orbits
from .corpus import CORPUS
from .cards import card_by_id, emergent_path, load_canonical_cards
from .context_dynamics import (
    CONTEXT_BANDWIDTH,
    Attractor,
    ContextAnchor,
    ContextPotential,
    FieldSample,
    OrbitStep,
    OrbitTrace,
    PhaseVector36,
    TangentVector36,
    find_attractors,
    trace_orbit,
)
from .observer_generation import (
    BASE_ANGULAR_FREQUENCY,
    BASE_FREQUENCY_HZ,
    DEFAULT_OSCILLATORS,
    OBSERVER_GENERATION_VERSION,
    DynamicsConfig,
    DynamicsStep,
    DynamicsTrace,
    GenerationPlan,
    HolonomicMemory,
    HTRIConfig,
    HTRIOscillatorField,
    HTRIState,
    IntentionState,
    MemoryCluster,
    MemoryRecall,
    Observation,
    ObserverState,
    ObserverToGenerationPipeline,
    PerceivedState,
    PipelineResult,
    Provenance,
    evolve_generation_state,
)
from .operator_calculus import (
    OPERATOR_CALCULUS_VERSION,
    CompressedPhase,
    HolonomyCache,
    HolonomyCacheEntry,
    LinearPhaseOperator,
    MergeResult,
    ProjectionResult,
    ScheduledState,
    SemanticDelta,
    SemanticScheduler,
    compress_phase,
    decompress_phase,
    gauge_transform,
    project_forbidden_directions,
    semantic_crc,
    semantic_diff,
    semantic_merge,
    trajectory_curvature,
)
from .identity_cycle import (
    FLAVOUR_COUNT,
    IDENTITY_CYCLE_VERSION,
    INFORMATION_PER_PROJECTIVE_CYCLE,
    INFORMATION_QUANTUM,
    MIX_COUNT,
    PROJECTIVE_CYCLES_PER_INFORMATION_CYCLE,
    PROJECTIVE_HALF_TURNS,
    SIGMA_AXIS,
    SPINOR_CYCLES_PER_INFORMATION_CYCLE,
    SPINOR_HALF_TURNS,
    CrossDerivation24,
    CycleCoordinate,
    IdentityAxis,
    cycle_from_phase,
    information_from_projective_cycles,
    information_rate,
    phase_from_cycle,
    phase_information_density,
    projective_cycles_from_information,
    spinor_parity,
    verify_runtime_identity,
    winding_frequency,
)
from . import observer_generation as _observer_generation_module
from . import operator_calculus as _operator_calculus_module
from .numerical_guards import (
    project_oscillator_banks_36,
    stable_trajectory_curvature,
)

# Canonical numerical repairs are installed on the original runtime objects so
# direct submodule imports and package-level exports use the same implementation.
HTRIOscillatorField._project36 = staticmethod(project_oscillator_banks_36)
_observer_generation_module.HTRIOscillatorField._project36 = staticmethod(
    project_oscillator_banks_36
)
_operator_calculus_module.trajectory_curvature = stable_trajectory_curvature
trajectory_curvature = stable_trajectory_curvature

__all__ = [
    "ALPHA_M", "CANON_VERSION", "ETA_M_36D", "HILBERT_BITS", "HILBERT_DIM",
    "KAPPA", "L3", "L4", "L5", "PHASE_DIM", "CanonicalConceptState",
    "Hilbert2048State", "semantic_mass", "OrbitalRecord", "architectural_role",
    "audit_orbits", "CORPUS", "card_by_id", "emergent_path", "load_canonical_cards",
    "CONTEXT_BANDWIDTH", "Attractor", "ContextAnchor", "ContextPotential",
    "FieldSample", "OrbitStep", "OrbitTrace", "PhaseVector36", "TangentVector36",
    "find_attractors", "trace_orbit",
    "BASE_ANGULAR_FREQUENCY", "BASE_FREQUENCY_HZ", "DEFAULT_OSCILLATORS",
    "OBSERVER_GENERATION_VERSION", "DynamicsConfig", "DynamicsStep",
    "DynamicsTrace", "GenerationPlan", "HolonomicMemory", "HTRIConfig",
    "HTRIOscillatorField", "HTRIState", "IntentionState", "MemoryCluster",
    "MemoryRecall", "Observation", "ObserverState", "ObserverToGenerationPipeline",
    "PerceivedState", "PipelineResult", "Provenance", "evolve_generation_state",
    "OPERATOR_CALCULUS_VERSION", "CompressedPhase", "HolonomyCache",
    "HolonomyCacheEntry", "LinearPhaseOperator", "MergeResult", "ProjectionResult",
    "ScheduledState", "SemanticDelta", "SemanticScheduler", "compress_phase",
    "decompress_phase", "gauge_transform", "project_forbidden_directions",
    "semantic_crc", "semantic_diff", "semantic_merge", "trajectory_curvature",
    "project_oscillator_banks_36", "stable_trajectory_curvature",
    "FLAVOUR_COUNT", "IDENTITY_CYCLE_VERSION", "INFORMATION_PER_PROJECTIVE_CYCLE",
    "INFORMATION_QUANTUM", "MIX_COUNT", "PROJECTIVE_CYCLES_PER_INFORMATION_CYCLE",
    "PROJECTIVE_HALF_TURNS", "SIGMA_AXIS", "SPINOR_CYCLES_PER_INFORMATION_CYCLE",
    "SPINOR_HALF_TURNS", "CrossDerivation24", "CycleCoordinate", "IdentityAxis",
    "cycle_from_phase", "information_from_projective_cycles", "information_rate",
    "phase_from_cycle", "phase_information_density",
    "projective_cycles_from_information", "spinor_parity",
    "verify_runtime_identity", "winding_frequency",
]
