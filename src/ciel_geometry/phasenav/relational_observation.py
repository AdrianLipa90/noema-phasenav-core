"""Read-only relational observation sidecar for PhaseNav.

The canonical PhaseNav state remains exactly 36-dimensional. This module only
validates and carries external observation metadata.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

EXPECTED_SCHEMA = "PNCS_RELATIONAL_OBSERVATION_PACKET_V0_1"


class RelationalObservationSidecarError(ValueError):
    pass


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise RelationalObservationSidecarError(f"{name} must be finite")
    return value


@dataclass(frozen=True)
class RelationalObservationSidecar:
    packet: Mapping[str, Any]

    def validate(self) -> None:
        packet = self.packet
        if packet.get("schema") != EXPECTED_SCHEMA:
            raise RelationalObservationSidecarError("unexpected observation packet schema")
        if packet.get("flatten_into_t36") is not False:
            raise RelationalObservationSidecarError(
                "observation sidecars must not flatten into T36"
            )
        if packet.get("semantic_holonomy_equivalence") != "OPEN":
            raise RelationalObservationSidecarError(
                "semantic holonomy equivalence must remain OPEN"
            )

        obs = packet.get("observables")
        ident = packet.get("identifiability")
        prov = packet.get("provenance")
        if not isinstance(obs, Mapping):
            raise RelationalObservationSidecarError("observables must be a mapping")
        if not isinstance(ident, Mapping):
            raise RelationalObservationSidecarError("identifiability must be a mapping")
        if not isinstance(prov, Mapping):
            raise RelationalObservationSidecarError("provenance must be a mapping")

        intensity = _finite("intensity", obs.get("intensity"))
        linewidth = _finite("linewidth", obs.get("linewidth"))
        coherence = _finite("coherence", obs.get("coherence"))
        _finite("frequency", obs.get("frequency"))
        _finite("phase", obs.get("phase"))

        if intensity < 0.0:
            raise RelationalObservationSidecarError("intensity must be >= 0")
        if linewidth < 0.0:
            raise RelationalObservationSidecarError("linewidth must be >= 0")
        if not 0.0 <= coherence <= 1.0:
            raise RelationalObservationSidecarError("coherence must lie in [0,1]")

        phase_count = ident.get("phase_count")
        cycle_rank = ident.get("cycle_rank")
        jacobian_rank = ident.get("jacobian_rank")
        fisher_rank = ident.get("fisher_rank")
        for name, value in (
            ("phase_count", phase_count),
            ("cycle_rank", cycle_rank),
            ("jacobian_rank", jacobian_rank),
            ("fisher_rank", fisher_rank),
        ):
            if not isinstance(value, int) or value < 0:
                raise RelationalObservationSidecarError(
                    f"{name} must be a non-negative integer"
                )
        if cycle_rank > phase_count:
            raise RelationalObservationSidecarError("cycle_rank cannot exceed phase_count")
        if jacobian_rank > phase_count or fisher_rank > phase_count:
            raise RelationalObservationSidecarError("rank cannot exceed phase_count")

        full = bool(ident.get("fully_identifiable"))
        expected = jacobian_rank >= cycle_rank and fisher_rank >= cycle_rank
        if full != expected:
            raise RelationalObservationSidecarError(
                "fully_identifiable inconsistent with declared ranks"
            )

        commit = str(prov.get("commit", ""))
        if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit.lower()):
            raise RelationalObservationSidecarError(
                "provenance commit must be a 40-character hexadecimal SHA"
            )
        for key in ("repository", "branch", "schema", "receipt"):
            if not str(prov.get(key, "")).strip():
                raise RelationalObservationSidecarError(
                    f"provenance.{key} must be non-empty"
                )

    def runtime_metadata(self) -> dict[str, Any]:
        self.validate()
        packet = self.packet
        return {
            "schema": "PHASENAV_RELATIONAL_OBSERVATION_SIDECAR_V0_1",
            "t36_dimension": 36,
            "t36_modified": False,
            "physical_source_inferred": False,
            "semantic_holonomy_equivalence": "OPEN",
            "observation_packet": dict(packet),
        }


def attach_relational_observation(
    phase_vector,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a 36D phase vector and return it with immutable sidecar metadata."""

    values = tuple(float(x) for x in phase_vector)
    if len(values) != 36:
        raise RelationalObservationSidecarError("phase_vector must contain exactly 36 values")
    if not all(math.isfinite(x) for x in values):
        raise RelationalObservationSidecarError("phase_vector must contain only finite values")

    sidecar = RelationalObservationSidecar(packet)
    metadata = sidecar.runtime_metadata()
    return {
        "phase_vector_36d": values,
        "relational_observation": metadata,
    }
