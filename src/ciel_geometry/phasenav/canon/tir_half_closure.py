"""Provenance-bound TIR × Secret-of-a-Half closure canon v0.8.

The v0.7 dependency graph already vectorizes typed scientific/dependency nodes
into the native PhaseNav T^36 routing envelope.  This module adds the missing
cross-repository closure layer: exact merged source commits become vectorized
source anchors, dependency edges receive deterministic routing identities, and
one receipt binds sources, nodes, paths, epistemic statuses, and firewalls.

Vectorization is an identity/routing operation only.  It does not prove an edge,
promote an OPEN claim, repair a PHYSICAL_FAIL claim, or identify a 36D routing
vector with an intrinsic scientific state.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping

from .model import CanonicalConceptState, PHASE_DIM
from .tir_half_dependencies import (
    INTRINSIC_COEFFICIENT_DIM,
    TIR_HALF_DEPENDENCY_GRAPH,
    DependencyEdge,
    DependencyGraph,
)

TIR_HALF_CLOSURE_VERSION = "0.8.0"
TIR_HALF_CLOSURE_SCHEMA = "phasenav.tir-half-closure/v0.8"

PHASENAV_RUNTIME_PARENT = "54f65f2ca7d35cdd98f0ab8984cc1a8d74444a96"
NOEMA_PARENT = "42a0a8916e81ca27f2213bf0f28538f046c2e89a"
TIR_PARENT = "df8a6e1321ecf2e2c8819f4e9d5ec7d4f997d170"
SECRET_HALF_PARENT = "a1b0aeba192766163893fab1468b8f9cd9b8853b"


def _vector_sha256(vector: tuple[float, ...]) -> str:
    payload = json.dumps(
        [round(float(value), 15) for value in vector],
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _routing_vector(identity: str) -> tuple[float, ...]:
    vector = tuple(CanonicalConceptState.from_id(identity).phase36)
    if len(vector) != PHASE_DIM or not all(math.isfinite(value) for value in vector):
        raise ValueError(f"invalid PhaseNav routing vector for {identity!r}")
    return vector


@dataclass(frozen=True)
class SourceAnchor:
    source_id: str
    repository: str
    commit_sha: str
    role: str
    vector36: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.commit_sha) != 40 or any(c not in "0123456789abcdef" for c in self.commit_sha):
            raise ValueError(f"{self.source_id}: commit SHA must be canonical lowercase SHA-1")
        if len(self.vector36) != PHASE_DIM or not all(math.isfinite(v) for v in self.vector36):
            raise ValueError(f"{self.source_id}: invalid routing vector")

    @property
    def vector_sha256(self) -> str:
        return _vector_sha256(self.vector36)


@dataclass(frozen=True)
class PathVector:
    source: str
    target: str
    relation: str
    status: str
    routing_identity: str
    vector36: tuple[float, ...]

    @property
    def vector_sha256(self) -> str:
        return _vector_sha256(self.vector36)


@dataclass(frozen=True)
class TIRHalfClosure:
    graph: DependencyGraph
    sources: Mapping[str, SourceAnchor]
    paths: tuple[PathVector, ...]
    source_state_sha256: str

    def receipt(self) -> dict[str, object]:
        source_rows = {
            key: {
                "repository": source.repository,
                "commit_sha": source.commit_sha,
                "role": source.role,
                "routing_dimension": PHASE_DIM,
                "vector_36d": list(source.vector36),
                "vector_sha256": source.vector_sha256,
            }
            for key, source in sorted(self.sources.items())
        }
        node_rows = {
            node_id: {
                "status": node.status.value,
                "relation": node.relation,
                "provenance": list(node.provenance),
                "intrinsic_dimension": node.intrinsic_dimension,
                "routing_dimension": PHASE_DIM,
                "vector_36d": list(node.vector36),
                "vector_sha256": node.vector_sha256,
                "proof_consumable": node.proof_consumable,
                "canon_blocked": node.canon_blocked,
                "open_condition": node.falsification_or_open_condition,
            }
            for node_id, node in sorted(self.graph.nodes.items())
        }
        path_rows = [
            {
                "source": path.source,
                "target": path.target,
                "relation": path.relation,
                "status": path.status,
                "routing_identity": path.routing_identity,
                "routing_dimension": PHASE_DIM,
                "vector_36d": list(path.vector36),
                "vector_sha256": path.vector_sha256,
                "scientific_meaning": "EDGE_METADATA_ONLY",
            }
            for path in self.paths
        ]
        payload: dict[str, object] = {
            "schema": TIR_HALF_CLOSURE_SCHEMA,
            "version": TIR_HALF_CLOSURE_VERSION,
            "source_state_sha256": self.source_state_sha256,
            "routing_dimension": PHASE_DIM,
            "intrinsic_coefficient_dimension": INTRINSIC_COEFFICIENT_DIM,
            "intrinsic_state_equals_routing_envelope": False,
            "sources": source_rows,
            "nodes": node_rows,
            "paths": path_rows,
            "blocked_nodes": list(self.graph.blocked_nodes()),
            "firewall": {
                "vectorization_implies_scientific_promotion": False,
                "path_vector_implies_edge_truth": False,
                "source_vector_implies_source_correctness": False,
                "mass_as_derivation_input": "FORBIDDEN",
                "yukawa_as_derivation_input": "FORBIDDEN",
                "coefficient_enriched_vector_as_parent": "FORBIDDEN",
                "open_or_failed_to_exact_without_external_receipt": "FORBIDDEN",
            },
            "scientific_promotion": "NOT_PERFORMED",
        }
        digest_source = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        payload["closure_sha256"] = hashlib.sha256(digest_source).hexdigest()
        return payload

    def noema_projection(self) -> dict[str, object]:
        receipt = self.receipt()
        return {
            "schema": "noema.phasenav-tir-half-closure/v0.8",
            "closure_sha256": receipt["closure_sha256"],
            "source_state_sha256": self.source_state_sha256,
            "source_commits": {
                key: source.commit_sha for key, source in sorted(self.sources.items())
            },
            "routing_dimension": PHASE_DIM,
            "intrinsic_coefficient_dimension": INTRINSIC_COEFFICIENT_DIM,
            "blocked_nodes": receipt["blocked_nodes"],
            "scientific_promotion": "NOT_PERFORMED",
            "memory_mutation": "NOT_PERFORMED",
        }


def _source_specs() -> tuple[tuple[str, str, str, str], ...]:
    return (
        (
            "PHASENAV_RUNTIME",
            "AdrianLipa90/noema-phasenav-core",
            PHASENAV_RUNTIME_PARENT,
            "canonical_vector_runtime_parent",
        ),
        (
            "NOEMA",
            "AdrianLipa90/NOEMA-vectorised-full",
            NOEMA_PARENT,
            "provenance_and_dependency_state_parent",
        ),
        (
            "TIR",
            "AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations",
            TIR_PARENT,
            "merged_formalism_parent",
        ),
        (
            "SECRET_OF_A_HALF",
            "AdrianLipa90/secret-of-a-half",
            SECRET_HALF_PARENT,
            "merged_half_axis_and_weil_parent",
        ),
    )


def _source_state_digest() -> str:
    payload = [
        {"source_id": sid, "repository": repo, "commit_sha": sha, "role": role}
        for sid, repo, sha, role in _source_specs()
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_anchors(source_digest: str) -> dict[str, SourceAnchor]:
    anchors: dict[str, SourceAnchor] = {}
    for source_id, repository, commit_sha, role in _source_specs():
        identity = (
            f"TIR_HALF_CLOSURE_V08::SOURCE::{source_digest}::"
            f"{source_id}::{commit_sha}"
        )
        anchors[source_id] = SourceAnchor(
            source_id=source_id,
            repository=repository,
            commit_sha=commit_sha,
            role=role,
            vector36=_routing_vector(identity),
        )
    return anchors


def _path_vector(edge: DependencyEdge, source_digest: str) -> PathVector:
    identity = (
        f"TIR_HALF_CLOSURE_V08::PATH::{source_digest}::"
        f"{edge.source}->{edge.target}::{edge.relation}::{edge.status}"
    )
    return PathVector(
        source=edge.source,
        target=edge.target,
        relation=edge.relation,
        status=edge.status,
        routing_identity=identity,
        vector36=_routing_vector(identity),
    )


def build_tir_half_closure() -> TIRHalfClosure:
    source_digest = _source_state_digest()
    graph = TIR_HALF_DEPENDENCY_GRAPH
    return TIRHalfClosure(
        graph=graph,
        sources=_source_anchors(source_digest),
        paths=tuple(_path_vector(edge, source_digest) for edge in graph.edges),
        source_state_sha256=source_digest,
    )


TIR_HALF_CLOSURE = build_tir_half_closure()
