"""ciel_geometry — Poincaré disk geometry engine for CIEL orbital system.

CIEL ORBITAL BINDING — HARDCODED CHECK przy każdym imporcie.
Jeśli binding_status nie jest ACTIVE → system działa w trybie degradowanym.

Exports are loaded lazily so module CLIs like
``python -m ciel_geometry.noema_surface_mmap`` do not trigger duplicate-import
warnings via eager package side effects.
"""

from __future__ import annotations
import os as _os
import logging as _noema_quiet_logging
_NOEMA_QUIET_EXCEPT_LOGGER = _noema_quiet_logging.getLogger(__name__)


from importlib import import_module
from pathlib import Path

_CIEL_BINDING_STATUS_PATH = Path("/dev/shm/ciel_noema") / "ciel_binding_status"
if _os.environ.get("CIEL_BINDING_STRICT") == "1":
    if _CIEL_BINDING_STATUS_PATH.exists():
        _binding_status = _CIEL_BINDING_STATUS_PATH.read_text().strip()
        if _binding_status != "ACTIVE":
            import warnings
            warnings.warn(f"CIEL ORBITAL BINDING: status={_binding_status} — degraded mode")
    else:
        import warnings
        warnings.warn("CIEL ORBITAL BINDING: status file missing — degraded mode")

try:
    # Two files are named noema_bootstrap.py (NOEMA/src/ and NOEMA/scripts/,
    # different purposes). A plain `from noema_bootstrap import ...` resolves
    # via sys.path search order, and running a script auto-prepends its own
    # directory — so launching e.g. NOEMA/scripts/noema_portal_daemon.py
    # silently shadows this src/ file with the scripts/ one, which has no
    # activate_local_packages(). Load this exact file by path instead.
    import importlib.util as _ilu
    _bootstrap_path = Path(__file__).resolve().parent.parent / "noema_bootstrap.py"
    _spec = _ilu.spec_from_file_location("noema_src_bootstrap", _bootstrap_path)
    _bootstrap_mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_bootstrap_mod)
    _bootstrap_mod.activate_local_packages()
except Exception as exc:
    _NOEMA_QUIET_EXCEPT_LOGGER.debug("noema_bootstrap.activate_local_packages unavailable: %s", exc)

__all__ = [
    "DEFAULT_SURFACE_ROOT",
    "DEFAULT_MEMORY_ROOT",
    "DEFAULT_IMAGINAL_SURFACE_ROOT",
    "DEFAULT_IMAGINAL_MEMORY_ROOT",
    "DiskLayout",
    "DiskNode",
    "DiskEdge",
    "SurfaceArraySpec",
    "PhaseMemoryRecord",
    "bind_phase_memory",
    "build_layout",
    "ensure_surface",
    "ensure_phase_memory",
    "evolve_surface",
    "initialize_coupling_from_memory_channels",
    "initialize_surface",
    "open_surface",
    "oscillator_id_for_concept",
    "query_phase_memory",
    "read_surface_state",
    "update_coupling_from_concepts",
    "update_coupling_hebbian",
    "update_coupling_weight",
    "update_surface_from_ciel_state",
    "write_concepts_to_surface",
    "apply_resonance_bridge",
    "balanced_ternary",
    "dual_surface_step",
    "encode_phi",
    "ensure_dual_surfaces",
    "full_report",
    "harmonic_signature",
    "imaginalize_state",
    "kuramoto_order_from_ternary",
    "canonical_weighting",
    "canonical_weighting_from_phase_metadata",
    "OrbitalHierarchy",
    "OrbitalHierarchyNode",
    "build_orbital_hierarchy",
    "layer_name_for_depth",
    "orbit_load_order",
    "read_phi_from_surface",
    "resonance_snapshot",
    "render_orbital_mermaid",
    "supergroup_consensi",
    "supergroup_operators",
    "superpair_dominance",
    "su3_coherence",
    "sync_surface_geometry",
    "trits_to_operators",
]

_EXPORTS = {
    "DiskLayout": ("ciel_geometry.layout", "DiskLayout"),
    "DiskNode": ("ciel_geometry.layout", "DiskNode"),
    "DiskEdge": ("ciel_geometry.layout", "DiskEdge"),
    "build_layout": ("ciel_geometry.layout", "build_layout"),
    "DEFAULT_SURFACE_ROOT": ("ciel_geometry.noema_surface_mmap", "DEFAULT_SURFACE_ROOT"),
    "SurfaceArraySpec": ("ciel_geometry.noema_surface_mmap", "SurfaceArraySpec"),
    "ensure_surface": ("ciel_geometry.noema_surface_mmap", "ensure_surface"),
    "initialize_surface": ("ciel_geometry.noema_surface_mmap", "initialize_surface"),
    "open_surface": ("ciel_geometry.noema_surface_mmap", "open_surface"),
    "sync_surface_geometry": ("ciel_geometry.noema_surface_mmap", "sync_surface_geometry"),
    "update_surface_from_ciel_state": ("ciel_geometry.noema_surface_mmap", "update_surface_from_ciel_state"),
    "evolve_surface": ("ciel_geometry.noema_surface_mmap", "evolve_surface"),
    "evolve_surface_cps": ("ciel_geometry.noema_surface_mmap", "evolve_surface_cps"),
    "initialize_coupling_from_memory_channels": ("ciel_geometry.noema_surface_mmap", "initialize_coupling_from_memory_channels"),
    "oscillator_id_for_concept": ("ciel_geometry.noema_surface_mmap", "oscillator_id_for_concept"),
    "read_surface_state": ("ciel_geometry.noema_surface_mmap", "read_surface_state"),
    "update_coupling_from_concepts": ("ciel_geometry.noema_surface_mmap", "update_coupling_from_concepts"),
    "update_coupling_hebbian": ("ciel_geometry.noema_surface_mmap", "update_coupling_hebbian"),
    "update_coupling_weight": ("ciel_geometry.noema_surface_mmap", "update_coupling_weight"),
    "write_concepts_to_surface": ("ciel_geometry.noema_surface_mmap", "write_concepts_to_surface"),
    "PhaseNavData": ("ciel_geometry.phasenav", "PhaseNavData"),
    "PhaseNavSolver": ("ciel_geometry.phasenav", "PhaseNavSolver"),
    "PhaseNavSurfaceBridge": ("ciel_geometry.phasenav", "PhaseNavSurfaceBridge"),
    "generate_operator_map": ("ciel_geometry.phasenav", "generate_operator_map"),
    "get_all_operations": ("ciel_geometry.phasenav", "get_all_operations"),
    "write_operator_algebra": ("ciel_geometry.phasenav", "write_operator_algebra"),
    "ContinuousPhaseSync": ("ciel_geometry.continuous_phase_sync", "ContinuousPhaseSync"),
    "DEFAULT_MEMORY_ROOT": ("ciel_geometry.phase_memory_adapter", "DEFAULT_MEMORY_ROOT"),
    "PhaseMemoryRecord": ("ciel_geometry.phase_memory_adapter", "PhaseMemoryRecord"),
    "bind_phase_memory": ("ciel_geometry.phase_memory_adapter", "bind_phase_memory"),
    "ensure_phase_memory": ("ciel_geometry.phase_memory_adapter", "ensure_phase_memory"),
    "query_phase_memory": ("ciel_geometry.phase_memory_adapter", "query_phase_memory"),
    "DEFAULT_IMAGINAL_SURFACE_ROOT": ("ciel_geometry.resonance_bridge", "DEFAULT_IMAGINAL_SURFACE_ROOT"),
    "DEFAULT_IMAGINAL_MEMORY_ROOT": ("ciel_geometry.resonance_bridge", "DEFAULT_IMAGINAL_MEMORY_ROOT"),
    "Subconscious": ("ciel_geometry.subconscious", "Subconscious"),
    "ZetaSchrodinger": ("ciel_geometry.subconscious", "ZetaSchrodinger"),
    "BerryPhaseTracker": ("ciel_geometry.subconscious", "BerryPhaseTracker"),
    "WakeSignalGenerator": ("ciel_geometry.subconscious", "WakeSignalGenerator"),
    "PhaseLaneBank": ("ciel_geometry.subconscious", "PhaseLaneBank"),
    "apply_resonance_bridge": ("ciel_geometry.resonance_bridge", "apply_resonance_bridge"),
    "balanced_ternary": ("ciel_geometry.ternary_decoder", "balanced_ternary"),
    "dual_surface_step": ("ciel_geometry.resonance_bridge", "dual_surface_step"),
    "encode_phi": ("ciel_geometry.ternary_decoder", "encode_phi"),
    "ensure_dual_surfaces": ("ciel_geometry.resonance_bridge", "ensure_dual_surfaces"),
    "full_report": ("ciel_geometry.ternary_decoder", "full_report"),
    "harmonic_signature": ("ciel_geometry.ternary_decoder", "harmonic_signature"),
    "imaginalize_state": ("ciel_geometry.resonance_bridge", "imaginalize_state"),
    "kuramoto_order_from_ternary": ("ciel_geometry.ternary_decoder", "kuramoto_order_from_ternary"),
    "canonical_weighting": ("ciel_geometry.weighting", "canonical_weighting"),
    "canonical_weighting_from_phase_metadata": ("ciel_geometry.weighting", "canonical_weighting_from_phase_metadata"),
    "OrbitalHierarchy": ("ciel_geometry.orbital_hierarchy", "OrbitalHierarchy"),
    "OrbitalHierarchyNode": ("ciel_geometry.orbital_hierarchy", "OrbitalHierarchyNode"),
    "build_orbital_hierarchy": ("ciel_geometry.orbital_hierarchy", "build_orbital_hierarchy"),
    "layer_name_for_depth": ("ciel_geometry.orbital_hierarchy", "layer_name_for_depth"),
    "orbit_load_order": ("ciel_geometry.orbital_hierarchy", "orbit_load_order"),
    "read_phi_from_surface": ("ciel_geometry.ternary_decoder", "read_phi_from_surface"),
    "resonance_snapshot": ("ciel_geometry.resonance_bridge", "resonance_snapshot"),
    "render_orbital_mermaid": ("ciel_geometry.orbital_hierarchy", "render_orbital_mermaid"),
    "supergroup_consensi": ("ciel_geometry.ternary_decoder", "supergroup_consensi"),
    "supergroup_operators": ("ciel_geometry.ternary_decoder", "supergroup_operators"),
    "superpair_dominance": ("ciel_geometry.ternary_decoder", "superpair_dominance"),
    "su3_coherence": ("ciel_geometry.ternary_decoder", "su3_coherence"),
    "sync_surface_geometry": ("ciel_geometry.noema_surface_mmap", "sync_surface_geometry"),
    "trits_to_operators": ("ciel_geometry.ternary_decoder", "trits_to_operators"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value
