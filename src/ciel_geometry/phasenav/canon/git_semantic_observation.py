"""Bind native Git blob identity to contextual CIEL/ASIR semantic observations.

A cryptographic Git object id is an identity/provenance coordinate, not a
semantic embedding. Conversely, a native CIEL semantic state is contextual: it
is bound to an AUX request, MemoryFabric read set, NOEMA receipt, runtime code
state and 4pi PhaseNav convention.

This module refuses to invent one file-level semantic vector from a Git hash,
path, file name, extension, or arbitrary reduction of an ASIR graph. It only
binds exact blob bytes to externally receipted native semantic observations.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal

from .git_object_vectorization import GitObjectVector, normalize_git_digest

GIT_SEMANTIC_OBSERVATION_VERSION = "0.11.0"
GIT_SEMANTIC_OBSERVATION_SCHEMA = "phasenav.git-blob-semantic-observation/v0.11"

CIEL_SEMANTIC_MODEL_RUNTIME_COMMIT = "0a4a1b57217fc876ed0535829686cfed8ccd0d8f"
CIELINGO_RUNTIME_COMMIT = "ab097f99d46eb446836833ac90b2bc3cf9d219e1"
NATIVE_SEMANTIC_SCHEMA = "CIEL_NATIVE_SEMANTIC_STATE_V1"
AUX_REQUEST_SCHEMA = "CIEL_AUX_PHASE_MEMORY_REQUEST_V2"
AUX_PACKET_SCHEMA = "CIEL_AUX_PHASE_MEMORY_PACKET_V3"
PHASE_CONVENTION = "native_spinor_4pi"
PHASE_DIMENSION = 36
MEMORY_LANES = 12
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def git_blob_digest(raw: bytes, algorithm: Literal["sha1", "sha256"] = "sha1") -> str:
    """Compute the native Git blob id from exact bytes, including Git domain header."""
    body = f"blob {len(raw)}\0".encode("ascii") + raw
    if algorithm == "sha1":
        return hashlib.sha1(body).hexdigest()
    if algorithm == "sha256":
        return hashlib.sha256(body).hexdigest()
    raise ValueError(algorithm)


def raw_bytes_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256(value: str, name: str) -> str:
    canonical = value.strip().lower()
    if _HEX64.fullmatch(canonical) is None:
        raise ValueError(f"{name} must be canonical SHA-256")
    return canonical


@dataclass(frozen=True)
class GitBlobSemanticObservation:
    repository_head_commit: str
    blob_digest: str
    git_hash_algorithm: Literal["sha1", "sha256"]
    raw_bytes_sha256: str
    text_encoding: str
    language_id: str
    aux_request_sha256: str
    aux_packet_receipt_sha256: str
    native_semantic_binding_sha256: str
    semantic_graph_binding_sha256: str
    memory_read_set_sha256: str
    noema_receipt_sha256: str
    external_ack: bool
    semantic_runtime_commit: str = CIEL_SEMANTIC_MODEL_RUNTIME_COMMIT
    cielingo_runtime_commit: str = CIELINGO_RUNTIME_COMMIT
    phase_convention: str = PHASE_CONVENTION
    phase_dimension: int = PHASE_DIMENSION
    memory_lane_count: int = MEMORY_LANES

    @classmethod
    def bind(
        cls,
        raw: bytes,
        *,
        repository_head_commit: str,
        blob_digest: str,
        git_hash_algorithm: Literal["sha1", "sha256"],
        text_encoding: str,
        language_id: str,
        aux_request_sha256: str,
        aux_packet_receipt_sha256: str,
        native_semantic_binding_sha256: str,
        semantic_graph_binding_sha256: str,
        memory_read_set_sha256: str,
        noema_receipt_sha256: str,
        external_ack: bool,
    ) -> "GitBlobSemanticObservation":
        alg, canonical_blob = normalize_git_digest(blob_digest, git_hash_algorithm)
        if alg != git_hash_algorithm:
            raise ValueError("Git hash algorithm mismatch")
        actual_blob = git_blob_digest(raw, git_hash_algorithm)
        if actual_blob != canonical_blob:
            raise ValueError("raw bytes do not reproduce the declared Git blob digest")
        try:
            raw.decode(text_encoding)
        except (LookupError, UnicodeDecodeError) as exc:
            raise ValueError("blob is not valid text in the declared encoding") from exc
        if not language_id:
            raise ValueError("language_id is required for a semantic observation")
        commit_alg, commit = normalize_git_digest(repository_head_commit)
        if commit_alg not in {"sha1", "sha256"}:
            raise AssertionError(commit_alg)
        return cls(
            repository_head_commit=commit,
            blob_digest=canonical_blob,
            git_hash_algorithm=git_hash_algorithm,
            raw_bytes_sha256=raw_bytes_sha256(raw),
            text_encoding=text_encoding,
            language_id=language_id,
            aux_request_sha256=_sha256(aux_request_sha256, "aux_request_sha256"),
            aux_packet_receipt_sha256=_sha256(aux_packet_receipt_sha256, "aux_packet_receipt_sha256"),
            native_semantic_binding_sha256=_sha256(native_semantic_binding_sha256, "native_semantic_binding_sha256"),
            semantic_graph_binding_sha256=_sha256(semantic_graph_binding_sha256, "semantic_graph_binding_sha256"),
            memory_read_set_sha256=_sha256(memory_read_set_sha256, "memory_read_set_sha256"),
            noema_receipt_sha256=_sha256(noema_receipt_sha256, "noema_receipt_sha256"),
            external_ack=bool(external_ack),
        )

    @property
    def identity_vector(self) -> GitObjectVector:
        return GitObjectVector.from_digest("blob", self.blob_digest, self.git_hash_algorithm)

    def receipt(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": GIT_SEMANTIC_OBSERVATION_SCHEMA,
            "version": GIT_SEMANTIC_OBSERVATION_VERSION,
            "git_identity": {
                "repository_head_commit": self.repository_head_commit,
                "blob_digest": self.blob_digest,
                "git_hash_algorithm": self.git_hash_algorithm,
                "raw_bytes_sha256": self.raw_bytes_sha256,
                "identity_vector_sha256": self.identity_vector.vector_sha256,
                "routing_dimension": 36,
            },
            "semantic_observation": {
                "text_encoding": self.text_encoding,
                "language_id": self.language_id,
                "semantic_runtime_commit": self.semantic_runtime_commit,
                "cielingo_runtime_commit": self.cielingo_runtime_commit,
                "aux_request_schema": AUX_REQUEST_SCHEMA,
                "aux_packet_schema": AUX_PACKET_SCHEMA,
                "native_semantic_schema": NATIVE_SEMANTIC_SCHEMA,
                "aux_request_sha256": self.aux_request_sha256,
                "aux_packet_receipt_sha256": self.aux_packet_receipt_sha256,
                "native_semantic_binding_sha256": self.native_semantic_binding_sha256,
                "semantic_graph_binding_sha256": self.semantic_graph_binding_sha256,
                "memory_read_set_sha256": self.memory_read_set_sha256,
                "noema_receipt_sha256": self.noema_receipt_sha256,
                "phase_convention": self.phase_convention,
                "phase_dimension": self.phase_dimension,
                "memory_lane_count": self.memory_lane_count,
                "external_ack": self.external_ack,
            },
            "firewall": {
                "git_identity_vector_is_semantic_embedding": False,
                "file_path_is_semantic_parent": False,
                "file_name_is_semantic_parent": False,
                "extension_is_semantic_parent": False,
                "repository_name_is_semantic_parent": False,
                "hash_distance_implies_semantic_similarity": False,
                "semantic_graph_collapsed_to_one_vector": False,
                "missing_semantic_receipt_fallback_allowed": False,
                "semantic_observation_implies_scientific_truth": False,
            },
            "semantic_status": "CONTEXTUAL_RECEIPTED_OBSERVATION",
            "intrinsic_file_semantic_vector": "NOT_DEFINED_BY_THIS_LAYER",
            "scientific_promotion": "NOT_PERFORMED",
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        payload["receipt_sha256"] = hashlib.sha256(encoded).hexdigest()
        return payload
