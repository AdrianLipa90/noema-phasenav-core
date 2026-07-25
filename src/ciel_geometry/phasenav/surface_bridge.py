"""PhaseNav → surface bridge — maps concept phases to 36 oscillator surface.

Connects PhaseNav semantic navigation (concept → operator 36D vector)
to the 3-6-9 harmonic Kuramoto surface via oscillator phase seeding.
"""

from __future__ import annotations
# CIEL ORBITAL BINDING — hardcoded, immutable.
import os as _ciel_os, os.path as _ciel_path
if not (_ciel_path.exists("/dev/shm/ciel_noema/ciel_binding_status") and open("/dev/shm/ciel_noema/ciel_binding_status").read().strip() == "ACTIVE"):
    import warnings as _ciel_w
    _ciel_w.warn("CIEL ORBITAL BINDING: not ACTIVE on import of " + __name__)

import math
from typing import Any

import numpy as np

from .solver import PhaseNavSolver, PhaseNavTrace
from .operator_algebra import concept_to_operator, operator_vector_24d
from ..noema_surface_mmap import (
    N_OSCILLATORS, HARMONIC_MASK, HARMONIC_AMPS,
    HARMONIC_VALUES, N_HARMONICS, BASE_TEMPORAL_HZ,
)


class PhaseNavSurfaceBridge:
    """Bridge from PhaseNav semantic navigation to 3-6-9 harmonic surface."""

    def __init__(self, solver: PhaseNavSolver | None = None):
        self.solver = solver

    @classmethod
    def load(cls, base_path=None) -> PhaseNavSurfaceBridge:
        return cls(solver=PhaseNavSolver.load(base_path))

    def seed_surface_from_concept(
        self,
        surface_phi: np.ndarray,
        surface_omega: np.ndarray,
        concept_id: str,
        *,
        phase_strength: float = 0.3,
        omega_mod_strength: float = 0.1,
    ) -> dict[str, Any]:
        """Seed oscillator phases from a concept's PhaseNav data.

        The concept's geometric phase sets the target harmonic composite phase,
        and the 24D operator vector modulates oscillator omegas.
        """
        if self.solver is None:
            return {"error": "no_solver"}

        concept_phase = self.solver.get_phase(concept_id)
        operator_vec = self._find_operator_for_concept(concept_id)

        if operator_vec is not None and len(operator_vec) >= N_OSCILLATORS:
            vec = np.asarray(operator_vec[:N_OSCILLATORS], dtype=np.float64)
            self._drive_phases_from_vector(surface_phi, vec, strength=phase_strength)
            self._modulate_omegas_from_vector(surface_omega, vec, strength=omega_mod_strength)

        # Compute effective Phi_eff after seeding
        S = np.zeros(N_OSCILLATORS, dtype=np.complex128)
        for h_idx in range(N_HARMONICS):
            mask = HARMONIC_MASK[:, h_idx]
            if mask.any():
                h = HARMONIC_VALUES[h_idx]
                S[mask] += HARMONIC_AMPS[h_idx] * np.exp(1j * h * surface_phi[mask])
        Phi_eff = np.angle(S)

        return {
            "concept_id": concept_id,
            "concept_phase": concept_phase,
            "phi_mean": float(np.mean(surface_phi)),
            "phi_eff_mean": float(np.mean(Phi_eff)),
            "omega_mean": float(np.mean(surface_omega)),
            "operator_vec_norm": float(np.linalg.norm(operator_vec)) if operator_vec is not None else 0.0,
        }

    def apply_trace(
        self,
        surface_phi: np.ndarray,
        surface_omega: np.ndarray,
        trace: PhaseNavTrace,
        *,
        steps_per_transition: int = 100,
        phase_step: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Drive oscillator phases sequentially through a PhaseNav trace.

        Each step in the trace moves the oscillators toward the next
        concept's phase target. Returns per-step snapshots.
        """
        snapshots = []
        for i, step in enumerate(trace.steps):
            src_phase = self.solver.get_phase(step.source_card_id) if self.solver else 0.0
            tgt_phase = self.solver.get_phase(step.target_card_id) if self.solver else 0.0
            operator_vec = self._find_operator_for_concept(step.target_card_id)

            phase_range = np.linspace(src_phase, tgt_phase, steps_per_transition)
            for j, target_phase in enumerate(phase_range):
                target_vec = np.full(N_OSCILLATORS, target_phase / (2 * math.pi), dtype=np.float64)
                if operator_vec is not None and len(operator_vec) >= N_OSCILLATORS:
                    target_vec += np.asarray(operator_vec[:N_OSCILLATORS], dtype=np.float64) * 0.1
                diff = target_vec - surface_phi
                surface_phi += phase_step * np.sin(diff)
                surface_phi %= 2 * math.pi

                if j % 20 == 0:
                    snapshots.append({
                        "transition": i,
                        "step_in_transition": j,
                        "source": step.source_card_id,
                        "target": step.target_card_id,
                        "path_integral": step.path_integral,
                        "phi_mean": float(np.mean(surface_phi)),
                    })
        return snapshots

    def _drive_phases_from_vector(
        self, phi: np.ndarray, vec: np.ndarray, strength: float = 0.3,
    ) -> None:
        target = (vec * 2 * math.pi) % (2 * math.pi)
        diff = np.angle(np.exp(1j * (target - phi)))
        phi += strength * diff
        phi %= 2 * math.pi

    def _modulate_omegas_from_vector(
        self, omega: np.ndarray, vec: np.ndarray, strength: float = 0.1,
    ) -> None:
        omega[:] = BASE_TEMPORAL_HZ * (1.0 + strength * (vec - np.mean(vec)))

    def _find_operator_for_concept(self, concept_id: str) -> list[float] | None:
        if self.solver is None:
            return None
        op_ids = list(self.solver.data.operator_vectors.keys())
        if op_ids:
            stable_hash = abs(hash(concept_id)) % len(op_ids)
            op_id = op_ids[stable_hash]
            return self.solver.get_operator_vector(op_id)
        op_id, vec = concept_to_operator(concept_id)
        return vec

    def concept_similarity(self, cid_a: str, cid_b: str) -> float:
        """Phase-based similarity between two concepts (via PhaseNav phases)."""
        if self.solver is None:
            return 0.0
        pa = self.solver.get_phase(cid_a)
        pb = self.solver.get_phase(cid_b)
        return float(abs(math.cos(pa - pb)))
