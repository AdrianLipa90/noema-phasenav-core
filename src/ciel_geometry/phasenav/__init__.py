"""PhaseNav — canonical H2048 source state with T36 phase navigation."""
from __future__ import annotations

import os as _ciel_os, os.path as _ciel_path
if _ciel_os.environ.get("CIEL_BINDING_STRICT") == "1":
    if not (_ciel_path.exists("/dev/shm/ciel_noema/ciel_binding_status") and open("/dev/shm/ciel_noema/ciel_binding_status").read() == "ACTIVE"):
        import warnings as _ciel_w
        _ciel_w.warn("CIEL ORBITAL BINDING: not ACTIVE on import of " + __name__)

from .pnv_runtime import (
    state_vector, generate_state_map, generate_state_jsonl,
    write_state_vectors, connection, connection_matrix,
    holonomy, get_all_states, intention_apply,
    M_collatz_hash, M_berry_connection,
    VECTOR_DIM, VECTOR_COMPONENTS, KAPPA, ALPHA_M, L3, L4, L5, L_RATIO,
    ALL_STATE_IDS,
    generate_operator_map, generate_operator_jsonl,
    write_operator_algebra, operator_vector_24d,
    concept_to_operator, get_all_operations, ALL_OPERATOR_IDS,
    _semantic_mass, _phase36_from_id, _gauge_lock_2,
    M_36d_order_parameter, M_36d_mean_phase, M_36d_angular_distance,
    M_36d_edge_weight, M_36d_berry_connection, M_36d_inner_product,
    M_find_path_36d, M_solve_36d, M_berry_holonomy_36d,
    M_project_bloch, M_36d_distance, M_nearest_neighbors_36d,
    M_resolve_situation_36d, intention_apply_36d,
    PI, TAU, write_state_vectors as write_state,
    PHASE_GRAMMAR, GRAMMAR_RULES,
    M_operator_gram_type, M_superposition_36d, M_grammar_compose,
    M_quantum_features, M_sentence_phase, M_sentence_phase_trajectory, M_fine_tune_36d,
)

from .solver import PhaseNavSolver, PhaseNavData, PhaseNavStep, PhaseNavTrace
from .phase_gate_engine import PhaseGateEngine
from .phase_memory import PhaseMemoryHypercrystal, CRYSTAL_VEC_PATH, CRYSTAL_META_PATH
from .semantic_mesh import SemanticMesh, SEMANTIC_AXES
from .phase_voice import PhaseVoice, get_phase_voice
from .canonical_cards import (
    CanonicalCard,
    Phase36Marker,
    canonicalize_record,
    canonicalize_crystal_facet,
    merge_card_views,
)
from .emergent_glossary import (
    EmergentGlossary,
    EmergentEdge,
    GlossaryPath,
    Phase36PathMarker,
)
from .htri_hypercrystal import (
    HypercrystalConfig,
    build_htri_hypercrystal,
    hermiticity_error,
    load_crystal_arrays as htri_load_crystal,
    poincare_distance,
    embed_poincare_disk,
)
from .crystal_text_engine import (
    CrystalTextEngine,
    ConsciousnessPulse,
    ConsciousnessStream,
)
from .canon import (
    CANON_VERSION,
    ETA_M_36D,
    HILBERT_BITS,
    HILBERT_DIM,
    PHASE_DIM,
    CORPUS as CANON_ORBITAL_CORPUS,
    CanonicalConceptState,
    Hilbert2048State,
    audit_orbits,
    card_by_id,
    emergent_path,
    load_canonical_cards,
    semantic_mass as canonical_semantic_mass,
)

__all__ = [
    "state_vector", "generate_state_map", "generate_state_jsonl",
    "write_state_vectors", "connection", "connection_matrix",
    "holonomy", "get_all_states", "intention_apply",
    "M_collatz_hash", "M_berry_connection",
    "VECTOR_DIM", "VECTOR_COMPONENTS", "KAPPA", "ALPHA_M", "L3", "L4", "L5", "L_RATIO",
    "ALL_STATE_IDS",
    "generate_operator_map", "generate_operator_jsonl",
    "write_operator_algebra", "operator_vector_24d",
    "concept_to_operator", "get_all_operations", "ALL_OPERATOR_IDS",
    "PhaseNavSolver", "PhaseNavData", "PhaseNavStep", "PhaseNavTrace",
    "_semantic_mass", "_phase36_from_id",
    "M_36d_order_parameter", "M_36d_mean_phase", "M_36d_angular_distance",
    "M_36d_edge_weight", "M_36d_berry_connection", "M_36d_inner_product",
    "M_find_path_36d", "M_solve_36d", "M_berry_holonomy_36d",
    "M_project_bloch", "M_36d_distance", "M_nearest_neighbors_36d",
    "M_resolve_situation_36d", "intention_apply_36d",
    "PI", "TAU", "write_state",
    "PHASE_GRAMMAR", "GRAMMAR_RULES",
    "M_operator_gram_type", "M_superposition_36d", "M_grammar_compose",
    "M_quantum_features", "M_sentence_phase", "M_sentence_phase_trajectory", "M_fine_tune_36d",
    "PhaseGateEngine",
    "PhaseMemoryHypercrystal",
    "CRYSTAL_VEC_PATH",
    "CRYSTAL_META_PATH",
    "SemanticMesh",
    "SEMANTIC_AXES",
    "PhaseVoice",
    "get_phase_voice",
    "CanonicalCard",
    "Phase36Marker",
    "canonicalize_record",
    "canonicalize_crystal_facet",
    "merge_card_views",
    "EmergentGlossary",
    "EmergentEdge",
    "GlossaryPath",
    "Phase36PathMarker",
    "HypercrystalConfig",
    "build_htri_hypercrystal",
    "hermiticity_error",
    "htri_load_crystal",
    "poincare_distance",
    "embed_poincare_disk",
    "CrystalTextEngine",
    "ConsciousnessPulse",
    "ConsciousnessStream",
    "CANON_VERSION",
    "ETA_M_36D",
    "HILBERT_BITS",
    "HILBERT_DIM",
    "PHASE_DIM",
    "CANON_ORBITAL_CORPUS",
    "CanonicalConceptState",
    "Hilbert2048State",
    "audit_orbits",
    "card_by_id",
    "emergent_path",
    "load_canonical_cards",
    "canonical_semantic_mass",
]
