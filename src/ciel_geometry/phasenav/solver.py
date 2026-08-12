"""Target-aware PhaseNav solver over explicit and emergent 36D paths.

v0.14 removes the historical 11D/36D schema collision. ``get_orbit`` now means
exactly one thing: a finite 36D phase-orbit vector. The former 11 labels are
retained only as legacy feature names and are never attached to phi[0:11].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .loader import ArtifactIntegrityError, PhaseNavData, load_phasenav

VECTOR_DIM = 36
PHASE_ORBIT_DIMS = [f"phi_{i}" for i in range(VECTOR_DIM)]
LEGACY_ORBIT_FEATURE_DIMS = [
    "mass",
    "sin",
    "cos",
    "align",
    "tension",
    "j_bus",
    "visc",
    "afford",
    "word_int",
    "file_int",
    "tele_ctrl",
]
ORBIT_DIMS = PHASE_ORBIT_DIMS


@dataclass
class PhaseNavStep:
    source_card_id: str
    target_card_id: str
    operator_hook: str
    operator_card_id: str
    phase_start: float
    phase_end: float
    phase_delta: float
    holonomic_viscosity: float
    phasenav_affordance: float
    transition_lane: str
    path_integral: float = 0.0
    epistemic_status: str = "artifact_grounded"
    canon_allowed: bool = False
    phase36_path_marker: dict[str, Any] | None = None
    edge_source: str = "runtime"


@dataclass
class PhaseNavTrace:
    steps: list[PhaseNavStep] = field(default_factory=list)
    total_path_integral: float = 0.0
    mean_viscosity: float = 0.0
    mean_affordance: float = 0.0
    card_sequence: list[str] = field(default_factory=list)
    epistemic_status: str = "artifact_grounded"


@dataclass
class PhaseNavSolver:
    data: PhaseNavData
    glossary: Any | None = None

    @classmethod
    def load(cls, base_path=None, *, glossary: Any | None = None) -> "PhaseNavSolver":
        return cls(data=load_phasenav(base_path), glossary=glossary)

    def get_phase(self, card_id: str) -> float:
        resolved = self.data.resolve_card_id(card_id)
        concept = (
            self.data.concept_phases.get(resolved)
            or self.data.concept_phases.get(card_id)
        )
        if concept:
            return float(concept.get("geometric_phase_rad", 0.0))
        name_mass = (
            self.data.name_mass_by_card_id.get(resolved)
            or self.data.name_mass_by_card_id.get(card_id)
        )
        if name_mass:
            return float(name_mass.get("geometric_phase_rad", 0.0))
        card = self.data.canonical_cards.get(resolved) or self.data.canonical_cards.get(card_id)
        if card:
            marker = card.get("phase_marker_36d") or card.get("phase36_marker") or {}
            return float(marker.get("mean_phase", marker.get("mean_phase_rad", 0.0)))
        raise KeyError(f"no phase record for {card_id!r}")

    def get_orbit(self, card_id: str) -> list[float]:
        """Return a validated 36D phase-orbit vector; never synthesize zero padding."""
        resolved = self.data.resolve_card_id(card_id)
        candidates = (
            card_id,
            resolved,
            str(card_id).removeprefix("concept:"),
            str(resolved).removeprefix("concept:"),
        )
        orbit = None
        for key in candidates:
            if key in self.data.orbits:
                orbit = self.data.orbits[key]
                break
        if orbit is None:
            raise KeyError(f"no orbit vector for {card_id!r}")
        vector = [float(x) for x in orbit]
        if len(vector) != VECTOR_DIM:
            raise ArtifactIntegrityError(
                f"orbit {card_id!r}: expected {VECTOR_DIM}D, got {len(vector)}D"
            )
        return vector

    def get_operator_vector(self, operator_id: str) -> list[float]:
        vector = self.data.operator_vectors.get(operator_id)
        if vector is None:
            vector = self.data.operator_vectors.get(operator_id.upper())
        if vector is None:
            raise KeyError(f"no operator vector for {operator_id!r}")
        result = [float(x) for x in vector]
        if len(result) != VECTOR_DIM:
            raise ArtifactIntegrityError(
                f"operator {operator_id!r}: expected {VECTOR_DIM}D, got {len(result)}D"
            )
        return result

    def best_edge_from(self, concept_id: str) -> dict[str, Any] | None:
        edges = (
            self.data.edges_by_concept.get(concept_id)
            or self.data.edges_by_concept.get(self.data.resolve_card_id(concept_id))
        )
        if not edges:
            return None
        return max(edges, key=lambda edge: float(edge.get("phasenav_affordance", 0.0)))

    def edge_between(self, source_card_id: str, target_card_id: str) -> Any | None:
        source_card_id = self.data.resolve_card_id(source_card_id)
        target_card_id = self.data.resolve_card_id(target_card_id)
        explicit = self.data.edge_between(source_card_id, target_card_id)
        if explicit is not None:
            return explicit
        explicit = self.data.edge_between(
            source_card_id.removeprefix("concept:"),
            target_card_id.removeprefix("concept:"),
        )
        if explicit is not None:
            return explicit
        if self.glossary is not None:
            return self.glossary.edge_between(source_card_id, target_card_id)
        return None

    def trace(self, card_ids: list[str]) -> PhaseNavTrace:
        trace = PhaseNavTrace(card_sequence=list(card_ids))
        for source, target in zip(card_ids, card_ids[1:]):
            step = self._step_between(source, target)
            if step is not None:
                trace.steps.append(step)
        if trace.steps:
            trace.total_path_integral = sum(step.path_integral for step in trace.steps)
            trace.mean_viscosity = sum(
                step.holonomic_viscosity for step in trace.steps
            ) / len(trace.steps)
            trace.mean_affordance = sum(
                step.phasenav_affordance for step in trace.steps
            ) / len(trace.steps)
            if any(step.epistemic_status == "chyba" for step in trace.steps):
                trace.epistemic_status = "chyba"
        return trace

    def trace_emergent(self, source_card_id: str, target_card_id: str) -> PhaseNavTrace:
        if self.glossary is None:
            return PhaseNavTrace(
                card_sequence=[source_card_id, target_card_id],
                epistemic_status="chyba",
            )
        path = self.glossary.trace(source_card_id, target_card_id)
        if path is None:
            return PhaseNavTrace(
                card_sequence=[source_card_id, target_card_id],
                epistemic_status="chyba",
            )
        return self.trace(list(path.card_sequence))

    def _step_between(self, source_card_id: str, target_card_id: str) -> PhaseNavStep | None:
        resolved_source = self.data.resolve_card_id(source_card_id)
        resolved_target = self.data.resolve_card_id(target_card_id)
        edge = self.edge_between(source_card_id, target_card_id)
        if edge is None:
            return None

        source_phase = self.get_phase(source_card_id)
        target_phase = self.get_phase(target_card_id)

        if hasattr(edge, "to_dict"):
            edge_data = edge.to_dict()
            edge_source = "emergent_36d"
        else:
            edge_data = dict(edge)
            edge_source = "runtime"

        viscosity = float(edge_data.get("holonomic_viscosity", 0.0))
        affordance = float(edge_data.get("phasenav_affordance", 0.0))
        phase_delta = target_phase - source_phase
        path_integral = edge_data.get("path_integral")
        if path_integral is None:
            path_integral = viscosity * abs(phase_delta)

        return PhaseNavStep(
            source_card_id=resolved_source,
            target_card_id=resolved_target,
            operator_hook=str(edge_data.get("operator_hook", "")),
            operator_card_id=str(edge_data.get("operator_card_id", "")),
            phase_start=source_phase,
            phase_end=target_phase,
            phase_delta=phase_delta,
            holonomic_viscosity=viscosity,
            phasenav_affordance=affordance,
            transition_lane=str(edge_data.get("transition_lane", "unknown")),
            path_integral=float(path_integral),
            epistemic_status=str(edge_data.get("epistemic_status", "artifact_grounded")),
            canon_allowed=bool(edge_data.get("canon_allowed", False)),
            phase36_path_marker=edge_data.get("phase36_path_marker"),
            edge_source=edge_source,
        )


__all__ = [
    "LEGACY_ORBIT_FEATURE_DIMS",
    "ORBIT_DIMS",
    "PHASE_ORBIT_DIMS",
    "PhaseNavStep",
    "PhaseNavTrace",
    "PhaseNavSolver",
    "PhaseNavData",
]
