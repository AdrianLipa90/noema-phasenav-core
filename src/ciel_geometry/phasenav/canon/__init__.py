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

__all__ = [
    "ALPHA_M", "CANON_VERSION", "ETA_M_36D", "HILBERT_BITS", "HILBERT_DIM",
    "KAPPA", "L3", "L4", "L5", "PHASE_DIM", "CanonicalConceptState",
    "Hilbert2048State", "semantic_mass", "OrbitalRecord", "architectural_role",
    "audit_orbits", "CORPUS", "card_by_id", "emergent_path", "load_canonical_cards",
    "CONTEXT_BANDWIDTH", "Attractor", "ContextAnchor", "ContextPotential",
    "FieldSample", "OrbitStep", "OrbitTrace", "PhaseVector36", "TangentVector36",
    "find_attractors", "trace_orbit",
]
