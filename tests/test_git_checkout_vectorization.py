from __future__ import annotations

from pathlib import Path
import subprocess

from ciel_geometry.phasenav.canon.git_checkout_vectorization import scan_git_checkout


def run(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return p.stdout.strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run(repo, "init")
    run(repo, "config", "user.email", "vector-test@example.invalid")
    run(repo, "config", "user.name", "Vector Test")
    (repo / "nested").mkdir()
    (repo / "same-a.txt").write_text("same bytes\n", encoding="utf-8")
    (repo / "nested" / "same-b.txt").write_text("same bytes\n", encoding="utf-8")
    (repo / "nested" / "different.txt").write_text("different\n", encoding="utf-8")
    run(repo, "add", "-A")
    run(repo, "commit", "-m", "initial")
    return repo


def occurrence(graph, path: str):
    return next(item for item in graph.occurrences if item.path == path)


def test_scanner_discovers_git_database_not_manual_file_list(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    graph = scan_git_checkout(repo)
    paths = {item.path for item in graph.occurrences}
    assert {"nested", "same-a.txt", "nested/same-b.txt", "nested/different.txt"} <= paths
    receipt = graph.receipt()
    assert receipt["firewall"]["manual_file_selection"] is False
    assert receipt["firewall"]["untracked_files_included"] is False


def test_identical_blob_content_has_one_object_vector_despite_two_paths(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    graph = scan_git_checkout(repo)
    left = occurrence(graph, "same-a.txt")
    right = occurrence(graph, "nested/same-b.txt")
    assert left.object_type == right.object_type == "blob"
    assert left.digest == right.digest
    key = ("blob", left.digest)
    assert key in graph.object_vectors
    assert len([k for k in graph.object_vectors if k == key]) == 1


def test_rename_changes_path_and_tree_but_not_blob_vector(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    before = scan_git_checkout(repo)
    before_blob = occurrence(before, "same-a.txt")
    before_vector = before.object_vectors[("blob", before_blob.digest)].vector36

    run(repo, "mv", "same-a.txt", "renamed.txt")
    run(repo, "commit", "-m", "rename only")
    after = scan_git_checkout(repo)
    after_blob = occurrence(after, "renamed.txt")
    after_vector = after.object_vectors[("blob", after_blob.digest)].vector36

    assert before_blob.digest == after_blob.digest
    assert before_vector == after_vector
    assert before.root_tree != after.root_tree
    assert before.head_commit != after.head_commit


def test_one_byte_content_change_forces_blob_vector_change(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    before = scan_git_checkout(repo)
    old = occurrence(before, "same-a.txt")
    old_vector = before.object_vectors[("blob", old.digest)].vector36

    (repo / "same-a.txt").write_text("same bytes!\n", encoding="utf-8")
    run(repo, "add", "same-a.txt")
    run(repo, "commit", "-m", "content change")
    after = scan_git_checkout(repo)
    new = occurrence(after, "same-a.txt")
    new_vector = after.object_vectors[("blob", new.digest)].vector36

    assert old.digest != new.digest
    assert old_vector != new_vector


def test_untracked_file_has_no_vector_until_git_tracks_it(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "untracked.txt").write_text("not in Git\n", encoding="utf-8")
    graph = scan_git_checkout(repo)
    assert "untracked.txt" not in {item.path for item in graph.occurrences}


def test_git_commit_to_root_tree_and_tree_containment_are_explicit(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    graph = scan_git_checkout(repo)
    root = graph.containment_edges[0]
    assert root.parent_type == "commit"
    assert root.parent_digest == graph.head_commit
    assert root.child_type == "tree"
    assert root.child_digest == graph.root_tree
    assert root.relation == "git_commit_root_tree"
    assert any(edge.relation == "git_tree_contains" for edge in graph.containment_edges[1:])


def test_edges_use_endpoint_geometry_not_relation_label_vector(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    graph = scan_git_checkout(repo)
    receipt = graph.receipt()
    assert receipt["firewall"]["relation_label_as_vector_parent"] is False
    assert receipt["firewall"]["invented_edge_vector"] is False
    for row in receipt["containment_edges"]:
        assert row["relation_label_is_vector_parent"] is False
        assert row["child_path_is_vector_parent"] is False
        assert row["proves_semantics"] is False
        assert row["scientific_meaning"] == "GIT_GRAPH_GEOMETRY_ONLY"


def test_receipt_is_deterministic_for_same_git_state(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    left = scan_git_checkout(repo).receipt()
    right = scan_git_checkout(repo).receipt()
    assert left["receipt_sha256"] == right["receipt_sha256"]
    assert left == right
