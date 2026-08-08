from __future__ import annotations

import hashlib
import pytest

from ciel_geometry.phasenav.canon.git_semantic_observation import (
    AUX_PACKET_SCHEMA,
    AUX_REQUEST_SCHEMA,
    CIELINGO_RUNTIME_COMMIT,
    CIEL_SEMANTIC_MODEL_RUNTIME_COMMIT,
    GIT_SEMANTIC_OBSERVATION_SCHEMA,
    GitBlobSemanticObservation,
    git_blob_digest,
)

SHA64_A = "a" * 64
SHA64_B = "b" * 64
SHA64_C = "c" * 64
SHA64_D = "d" * 64
SHA64_E = "e" * 64
SHA64_F = "f" * 64
HEAD_SHA1 = "205ea2937dce04124753feb46f91266d228564d9"


def bind(raw: bytes, **overrides):
    values = {
        "repository_head_commit": HEAD_SHA1,
        "blob_digest": git_blob_digest(raw, "sha1"),
        "git_hash_algorithm": "sha1",
        "text_encoding": "utf-8",
        "language_id": "en",
        "aux_request_sha256": SHA64_A,
        "aux_packet_receipt_sha256": SHA64_B,
        "native_semantic_binding_sha256": SHA64_C,
        "semantic_graph_binding_sha256": SHA64_D,
        "memory_read_set_sha256": SHA64_E,
        "noema_receipt_sha256": SHA64_F,
        "external_ack": False,
    }
    values.update(overrides)
    return GitBlobSemanticObservation.bind(raw, **values)


def test_git_blob_digest_uses_native_git_object_header() -> None:
    raw = b"hello\n"
    expected = hashlib.sha1(b"blob 6\0hello\n").hexdigest()
    assert git_blob_digest(raw, "sha1") == expected
    assert len(git_blob_digest(raw, "sha256")) == 64


def test_exact_bytes_are_bound_to_declared_blob() -> None:
    raw = b"print('hello')\n"
    observation = bind(raw)
    assert observation.blob_digest == git_blob_digest(raw)
    assert observation.raw_bytes_sha256 == hashlib.sha256(raw).hexdigest()
    assert len(observation.identity_vector.vector36) == 36


def test_modified_bytes_cannot_reuse_semantic_observation_blob_identity() -> None:
    raw = b"alpha\n"
    digest = git_blob_digest(raw)
    with pytest.raises(ValueError, match="do not reproduce"):
        bind(b"beta\n", blob_digest=digest)


def test_binary_or_wrongly_encoded_blob_has_no_text_semantic_fallback() -> None:
    raw = b"\xff\xfe\xfd"
    with pytest.raises(ValueError, match="not valid text"):
        bind(raw, blob_digest=git_blob_digest(raw), text_encoding="utf-8")


def test_commit_and_blob_object_formats_must_match() -> None:
    raw = b"text\n"
    blob_sha256 = git_blob_digest(raw, "sha256")
    with pytest.raises(ValueError, match="different Git object formats"):
        bind(raw, blob_digest=blob_sha256, git_hash_algorithm="sha256")


def test_context_receipts_can_change_without_changing_blob_identity() -> None:
    raw = b"same source bytes\n"
    left = bind(raw, aux_request_sha256=SHA64_A, memory_read_set_sha256=SHA64_E)
    right = bind(raw, aux_request_sha256=SHA64_B, memory_read_set_sha256=SHA64_F)
    assert left.identity_vector.vector36 == right.identity_vector.vector36
    assert left.blob_digest == right.blob_digest
    assert left.receipt()["receipt_sha256"] != right.receipt()["receipt_sha256"]


def test_receipt_preserves_native_ciel_contract_without_collapsing_graph() -> None:
    receipt = bind(b"semantic source\n").receipt()
    assert receipt["schema"] == GIT_SEMANTIC_OBSERVATION_SCHEMA
    semantic = receipt["semantic_observation"]
    assert semantic["semantic_runtime_commit"] == CIEL_SEMANTIC_MODEL_RUNTIME_COMMIT
    assert semantic["cielingo_runtime_commit"] == CIELINGO_RUNTIME_COMMIT
    assert semantic["aux_request_schema"] == AUX_REQUEST_SCHEMA
    assert semantic["aux_packet_schema"] == AUX_PACKET_SCHEMA
    assert semantic["phase_convention"] == "native_spinor_4pi"
    assert semantic["phase_dimension"] == 36
    assert semantic["memory_lane_count"] == 12
    assert receipt["intrinsic_file_semantic_vector"] == "NOT_DEFINED_BY_THIS_LAYER"


def test_no_arbitrary_semantic_fallbacks_are_permitted() -> None:
    firewall = bind(b"semantic source\n").receipt()["firewall"]
    assert firewall["git_identity_vector_is_semantic_embedding"] is False
    assert firewall["file_path_is_semantic_parent"] is False
    assert firewall["file_name_is_semantic_parent"] is False
    assert firewall["extension_is_semantic_parent"] is False
    assert firewall["repository_name_is_semantic_parent"] is False
    assert firewall["hash_distance_implies_semantic_similarity"] is False
    assert firewall["semantic_graph_collapsed_to_one_vector"] is False
    assert firewall["missing_semantic_receipt_fallback_allowed"] is False
    assert firewall["semantic_observation_implies_scientific_truth"] is False
