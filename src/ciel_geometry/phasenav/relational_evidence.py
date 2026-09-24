"""Read-only relational evidence sidecar for PhaseNav.

The canonical PhaseNav state remains exactly 36-dimensional. This module
validates PNCS/GREMLIN diagnostic provenance and conservative routing only.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping

EXPECTED_SCHEMA = "PNCS_RELATIONAL_EVIDENCE_PACKET_V0_1"
GREMLIN_SCHEMA = "GREMLIN_CROSS_MODAL_RELATIONAL_EVIDENCE_PACKET_V0_1"
_ALLOWED_STATES = {"CONSISTENT", "INCONSISTENT", "UNDERDETERMINED"}
_ALLOWED_ROUTES = {
    "STOP_DECLARED_MODEL",
    "REQUEST_MORE_CONSTRAINTS",
    "NO_SOURCE_ROUTE",
    "ALLOW_CANDIDATE_SOURCE_TESTS",
}


class RelationalEvidenceSidecarError(ValueError):
    pass


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _finite(name: str, value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RelationalEvidenceSidecarError(f"{name} must be finite") from exc
    if not math.isfinite(number):
        raise RelationalEvidenceSidecarError(f"{name} must be finite")
    return number


def _expected_route(state: str, admissible: bool) -> str:
    if state == "INCONSISTENT":
        return "STOP_DECLARED_MODEL"
    if state == "UNDERDETERMINED":
        return "REQUEST_MORE_CONSTRAINTS"
    if not admissible:
        return "NO_SOURCE_ROUTE"
    return "ALLOW_CANDIDATE_SOURCE_TESTS"


def _verify_embedded_gremlin(packet: Mapping[str, Any]) -> str:
    if packet.get("schema") != GREMLIN_SCHEMA:
        raise RelationalEvidenceSidecarError(
            "unexpected embedded GREMLIN evidence schema"
        )
    if packet.get("physical_source_selected") is not False:
        raise RelationalEvidenceSidecarError(
            "embedded physical_source_selected must be exactly false"
        )
    digest = packet.get("packet_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise RelationalEvidenceSidecarError(
            "embedded packet_sha256 must be a 64-character digest"
        )
    if any(ch not in "0123456789abcdef" for ch in digest.lower()):
        raise RelationalEvidenceSidecarError(
            "embedded packet_sha256 must be hexadecimal"
        )
    base = dict(packet)
    base.pop("packet_sha256", None)
    expected = hashlib.sha256(_canonical_json(base)).hexdigest()
    if expected != digest.lower():
        raise RelationalEvidenceSidecarError(
            "embedded GREMLIN evidence hash mismatch"
        )
    return digest.lower()


@dataclass(frozen=True)
class RelationalEvidenceSidecar:
    packet: Mapping[str, Any]

    def validate(self) -> None:
        packet = self.packet
        if packet.get("schema") != EXPECTED_SCHEMA:
            raise RelationalEvidenceSidecarError(
                "unexpected relational evidence packet schema"
            )
        if packet.get("physical_source_selected") is not False:
            raise RelationalEvidenceSidecarError(
                "physical_source_selected must be exactly false"
            )
        if packet.get("flatten_into_t36") is not False:
            raise RelationalEvidenceSidecarError(
                "relational evidence must not flatten into T36"
            )
        if packet.get("semantic_holonomy_equivalence") != "OPEN":
            raise RelationalEvidenceSidecarError(
                "semantic holonomy equivalence must remain OPEN"
            )

        state = packet.get("consistency_state")
        if state not in _ALLOWED_STATES:
            raise RelationalEvidenceSidecarError("invalid consistency_state")
        route = packet.get("route")
        if route not in _ALLOWED_ROUTES:
            raise RelationalEvidenceSidecarError("invalid route")

        admissible = packet.get("source_attribution_admissible")
        if not isinstance(admissible, bool):
            raise RelationalEvidenceSidecarError(
                "source_attribution_admissible must be boolean"
            )
        expected_route = _expected_route(state, admissible)
        if route != expected_route:
            raise RelationalEvidenceSidecarError(
                "route inconsistent with consistency/admissibility state"
            )

        upstream = packet.get("upstream")
        if not isinstance(upstream, Mapping):
            raise RelationalEvidenceSidecarError("upstream must be a mapping")
        for key in ("repository", "branch", "commit", "receipt", "schema", "packet_sha256"):
            if not str(upstream.get(key, "")).strip():
                raise RelationalEvidenceSidecarError(
                    f"upstream.{key} must be non-empty"
                )
        commit = str(upstream["commit"])
        if len(commit) != 40 or any(
            ch not in "0123456789abcdef" for ch in commit.lower()
        ):
            raise RelationalEvidenceSidecarError(
                "upstream.commit must be a 40-character hexadecimal SHA"
            )
        if upstream.get("schema") != GREMLIN_SCHEMA:
            raise RelationalEvidenceSidecarError(
                "upstream.schema must identify GREMLIN cross-modal evidence"
            )

        embedded = packet.get("gremlin_evidence")
        if not isinstance(embedded, Mapping):
            raise RelationalEvidenceSidecarError(
                "gremlin_evidence must be a mapping"
            )
        embedded_digest = _verify_embedded_gremlin(embedded)
        if upstream.get("packet_sha256") != embedded_digest:
            raise RelationalEvidenceSidecarError(
                "upstream packet hash does not match embedded GREMLIN evidence"
            )
        if embedded.get("consistency_state") != state:
            raise RelationalEvidenceSidecarError(
                "wrapper consistency_state differs from GREMLIN evidence"
            )
        if embedded.get("source_attribution_admissible") != admissible:
            raise RelationalEvidenceSidecarError(
                "wrapper source admissibility differs from GREMLIN evidence"
            )

        # Basic finite diagnostic sanity; detailed scientific validation remains
        # source-owned upstream.
        consistency = embedded.get("consistency")
        if not isinstance(consistency, Mapping):
            raise RelationalEvidenceSidecarError(
                "embedded consistency must be a mapping"
            )
        _finite("embedded consistency.chi_square", consistency.get("chi_square"))
        _finite(
            "embedded consistency.max_abs_normalized_residual",
            consistency.get("max_abs_normalized_residual"),
        )

    def runtime_metadata(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": "PHASENAV_RELATIONAL_EVIDENCE_SIDECAR_V0_1",
            "t36_dimension": 36,
            "t36_modified": False,
            "physical_source_selected": False,
            "semantic_holonomy_equivalence": "OPEN",
            "route": self.packet["route"],
            "consistency_state": self.packet["consistency_state"],
            "evidence_packet": dict(self.packet),
        }


def attach_relational_evidence(
    phase_vector,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate exact T36 plus evidence sidecar and return immutable metadata."""

    values = tuple(float(x) for x in phase_vector)
    if len(values) != 36:
        raise RelationalEvidenceSidecarError(
            "phase_vector must contain exactly 36 values"
        )
    if not all(math.isfinite(x) for x in values):
        raise RelationalEvidenceSidecarError(
            "phase_vector must contain only finite values"
        )

    sidecar = RelationalEvidenceSidecar(packet)
    metadata = sidecar.runtime_metadata()
    return {
        "phase_vector_36d": values,
        "relational_evidence": metadata,
    }
