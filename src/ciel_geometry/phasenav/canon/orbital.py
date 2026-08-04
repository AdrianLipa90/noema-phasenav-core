"""Canonical orbital audit over H2048 source states and T36 projections."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .model import CanonicalConceptState, ETA_M_36D


@dataclass(frozen=True)
class OrbitalRecord:
    concept: str
    current_path: str
    architectural_role: str
    semantic_mass: float
    order_parameter: float
    p_plus: float
    p_minus: float
    q_ratio: float
    log_radius: float
    half_deficit: float
    self_dual_shell: int
    distance_from_mass_attractor: float
    geometric_shell: int
    berry_from_mass_attractor: float

    def to_dict(self) -> dict:
        return asdict(self)


def architectural_role(path: str, concept: str) -> str:
    p = path.strip("/")
    if p == "mmap" or concept.endswith("_mmap") or concept in {
        "phi", "aux_phi", "flavor", "g", "omega", "gravity", "holonomy",
        "psi_geom", "R_geom", "Z_geom", "sensor_raw", "tau", "tick", "registry",
    }:
        return "mmap"
    if p.startswith("scripts"):
        return "script"
    if p.startswith("integration"):
        return "registry"
    return "library"


def audit_orbits(corpus: Mapping[str, str]) -> dict:
    if not corpus:
        raise ValueError("corpus must not be empty")

    states = {name: CanonicalConceptState.from_id(name) for name in corpus}
    mass_attractor = max(
        states,
        key=lambda name: (states[name].semantic_mass, name),
    )
    coherence_peak = max(
        states,
        key=lambda name: (states[name].order_parameter, name),
    )
    self_dual_nearest = min(
        states,
        key=lambda name: (states[name].log_radius, name),
    )
    anchor = states[mass_attractor]

    records: list[OrbitalRecord] = []
    for name in sorted(corpus):
        state = states[name]
        distance = state.angular_distance(anchor)
        records.append(
            OrbitalRecord(
                concept=name,
                current_path=corpus[name],
                architectural_role=architectural_role(corpus[name], name),
                semantic_mass=state.semantic_mass,
                order_parameter=state.order_parameter,
                p_plus=state.p_plus,
                p_minus=state.p_minus,
                q_ratio=state.q_ratio,
                log_radius=state.log_radius,
                half_deficit=state.half_deficit,
                self_dual_shell=state.orbital_shell,
                distance_from_mass_attractor=distance,
                geometric_shell=int(distance // ETA_M_36D),
                berry_from_mass_attractor=anchor.berry_connection(state),
            )
        )

    return {
        "canon_version": "1.0.0",
        "mass_attractor": mass_attractor,
        "coherence_peak": coherence_peak,
        "self_dual_nearest": self_dual_nearest,
        "eta_m_36d": ETA_M_36D,
        "mutation_policy": "READ_ONLY",
        "directory_policy": "architectural role is independent of orbital shell",
        "records": [record.to_dict() for record in records],
    }
