from __future__ import annotations

import math
import pytest

from ciel_geometry.phasenav.canon.git_object_vectorization import (
    GitObjectVector,
    GitRepositorySnapshot,
    git_digest_phase36,
    normalize_git_digest,
)

SHA_A = "205ea2937dce04124753feb46f91266d228564d9"
SHA_B = "205ea2937dce04124753feb46f91266d228564d8"
SHA256 = "f" * 64


def test_sha1_and_sha256_are_native_inputs() -> None:
    assert normalize_git_digest(SHA_A) == ("sha1", SHA_A)
    assert normalize_git_digest(SHA256) == ("sha256", SHA256)


def test_vector_is_exactly_finite_36d() -> None:
    vector = git_digest_phase36(SHA_A)
    assert len(vector) == 36
    assert all(math.isfinite(x) for x in vector)


def test_digest_change_forces_vector_change() -> None:
    assert git_digest_phase36(SHA_A) != git_digest_phase36(SHA_B)


def test_aliases_and_repo_ids_cannot_change_vector() -> None:
    left = GitRepositorySnapshot.from_head("owner/a", 1, "main", SHA_A)
    right = GitRepositorySnapshot.from_head("other/renamed", 999999, "dev", SHA_A)
    assert left.head.vector36 == right.head.vector36
    assert left.head.vector_sha256 == right.head.vector_sha256


def test_same_git_object_has_same_vector_across_object_alias_context() -> None:
    # Git object digests are already type-domain-separated by Git object hashing;
    # local file/repository names are not additional vector parents.
    a = GitObjectVector.from_digest("blob", SHA_A)
    b = GitObjectVector.from_digest("blob", SHA_A.upper())
    assert a.vector36 == b.vector36
    assert a.vector_sha256 == b.vector_sha256


def test_receipt_declares_no_label_or_path_seed() -> None:
    receipt = GitObjectVector.from_digest("commit", SHA_A).receipt()
    assert receipt["label_seed_used"] is False
    assert receipt["path_seed_used"] is False
    assert receipt["manual_id_seed_used"] is False
    assert receipt["collatz_string_hash_used"] is False
    assert receipt["semantic_promotion"] == "NOT_PERFORMED"


def test_repository_receipt_declares_only_head_digest_as_vector_parent() -> None:
    receipt = GitRepositorySnapshot.from_head("owner/name", 123, "main", SHA_A).receipt()
    assert receipt["vector_parent"] == "native_git_head_commit_digest_only"
    assert receipt["repository_name_is_vector_parent"] is False
    assert receipt["repository_id_is_vector_parent"] is False
    assert receipt["branch_name_is_vector_parent"] is False


def test_invalid_or_mismatched_hashes_fail_closed() -> None:
    with pytest.raises(ValueError):
        normalize_git_digest("xyz")
    with pytest.raises(ValueError):
        normalize_git_digest(SHA_A, "sha256")
    with pytest.raises(ValueError):
        GitObjectVector.from_digest("not-an-object", SHA_A)  # type: ignore[arg-type]
