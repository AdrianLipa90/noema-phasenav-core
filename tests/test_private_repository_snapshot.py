from __future__ import annotations

from ciel_geometry.phasenav.canon.private_repository_snapshot import (
    EXPECTED_HEAD_PRESENT_COUNT,
    EXPECTED_INVENTORY_SHA256,
    EXPECTED_REPOSITORY_COUNT,
    EXPECTED_VECTOR_SET_SHA256,
    PRIVATE_REPOSITORY_HEADS,
    PRIVATE_REPOSITORY_SNAPSHOT,
    build_private_repository_snapshot,
)


def test_private_scope_is_complete_and_mechanical() -> None:
    snapshot = build_private_repository_snapshot()
    assert snapshot["repository_count"] == EXPECTED_REPOSITORY_COUNT == 40
    assert snapshot["head_present_count"] == EXPECTED_HEAD_PRESENT_COUNT == 39
    assert snapshot["scope"]["visibility"] == "private"
    assert len({row.repository_id for row in PRIVATE_REPOSITORY_HEADS}) == 40
    assert len({row.repository for row in PRIVATE_REPOSITORY_HEADS}) == 40


def test_snapshot_hashes_reproduce() -> None:
    snapshot = build_private_repository_snapshot()
    assert snapshot["inventory_sha256"] == EXPECTED_INVENTORY_SHA256
    assert snapshot["vector_set_sha256"] == EXPECTED_VECTOR_SET_SHA256
    assert snapshot == PRIVATE_REPOSITORY_SNAPSHOT


def test_all_real_heads_have_unique_native_vectors() -> None:
    rows = PRIVATE_REPOSITORY_SNAPSHOT["repositories"]
    hashes = [row["vector_sha256"] for row in rows if row["head_commit"] is not None]
    assert len(hashes) == 39
    assert len(set(hashes)) == 39
    assert all(len(value) == 64 for value in hashes)


def test_archived_empty_repository_is_not_given_an_invented_vector() -> None:
    rows = PRIVATE_REPOSITORY_SNAPSHOT["repositories"]
    empty = [row for row in rows if row["head_commit"] is None]
    assert empty == [
        {
            "repository": "AdrianLipa90/noema-poincyre-cymatix",
            "repository_id": 1287238577,
            "default_branch": "main",
            "archived": True,
            "head_commit": None,
            "status": "ARCHIVED_EMPTY_SOURCE",
            "vector_sha256": None,
        }
    ]


def test_no_repository_metadata_is_a_vector_parent() -> None:
    policy = PRIVATE_REPOSITORY_SNAPSHOT["vectorization"]
    assert policy["parent"] == "native_git_object_digest_only"
    assert policy["repository_name_vector_parent"] is False
    assert policy["repository_id_vector_parent"] is False
    assert policy["default_branch_vector_parent"] is False
    assert policy["path_label_vector_parent"] is False
    assert policy["size_vector_parent"] is False
    assert policy["collatz_string_hash_used"] is False
    assert policy["scientific_promotion"] == "NOT_PERFORMED"
