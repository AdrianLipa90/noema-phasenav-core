"""Native Git object-database scanner for non-arbitrary repository vectorization.

Discovery is delegated to Git itself. The scanner calls `git rev-parse` and
`git ls-tree -r -t -z --full-tree HEAD`; it does not maintain a list of
"important" files, infer importance from paths, or use paths as numerical
vector parents.

A path is only an occurrence/localizer inside a Git tree. Object routing is
content-addressed by the native Git object digest through
`GitObjectVector.from_digest`.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from typing import Iterable

from ..pnv_runtime import M_36d_angular_distance, M_36d_berry_connection, M_36d_edge_weight
from .git_object_vectorization import GitObjectVector

GIT_CHECKOUT_VECTORIZATION_VERSION = "0.10.0"
GIT_CHECKOUT_VECTORIZATION_SCHEMA = "phasenav.git-checkout-object-graph/v0.10"


@dataclass(frozen=True)
class GitOccurrence:
    path: str
    mode: str
    object_type: str
    digest: str


@dataclass(frozen=True)
class GitContainmentEdge:
    parent_type: str
    parent_digest: str
    child_type: str
    child_digest: str
    relation: str
    child_path: str

    def geometry(self) -> dict[str, float | str | bool]:
        parent = GitObjectVector.from_digest(self.parent_type, self.parent_digest)  # type: ignore[arg-type]
        child = GitObjectVector.from_digest(self.child_type, self.child_digest)  # type: ignore[arg-type]
        return {
            "angular_distance": M_36d_angular_distance(parent.vector36, child.vector36),
            "berry_connection": M_36d_berry_connection(parent.vector36, child.vector36),
            "edge_weight": M_36d_edge_weight(parent.vector36, child.vector36),
            "scientific_meaning": "GIT_GRAPH_GEOMETRY_ONLY",
            "proves_semantics": False,
        }


@dataclass(frozen=True)
class GitCheckoutObjectGraph:
    head_commit: str
    root_tree: str
    occurrences: tuple[GitOccurrence, ...]
    containment_edges: tuple[GitContainmentEdge, ...]

    @property
    def object_vectors(self) -> dict[tuple[str, str], GitObjectVector]:
        objects: dict[tuple[str, str], GitObjectVector] = {
            ("commit", self.head_commit): GitObjectVector.from_digest("commit", self.head_commit),
            ("tree", self.root_tree): GitObjectVector.from_digest("tree", self.root_tree),
        }
        for occurrence in self.occurrences:
            key = (occurrence.object_type, occurrence.digest)
            if key not in objects:
                objects[key] = GitObjectVector.from_digest(occurrence.object_type, occurrence.digest)  # type: ignore[arg-type]
        return objects

    def receipt(self) -> dict[str, object]:
        vectors = self.object_vectors
        object_rows = [
            {
                "object_type": object_type,
                "object_digest": digest,
                "routing_dimension": 36,
                "vector_sha256": vector.vector_sha256,
            }
            for (object_type, digest), vector in sorted(vectors.items())
        ]
        occurrence_rows = [
            {
                "path": item.path,
                "mode": item.mode,
                "object_type": item.object_type,
                "object_digest": item.digest,
                "path_is_vector_parent": False,
            }
            for item in self.occurrences
        ]
        edge_rows = []
        for edge in self.containment_edges:
            row = {
                "parent_type": edge.parent_type,
                "parent_digest": edge.parent_digest,
                "child_type": edge.child_type,
                "child_digest": edge.child_digest,
                "relation": edge.relation,
                "child_path": edge.child_path,
                "relation_label_is_vector_parent": False,
                "child_path_is_vector_parent": False,
            }
            row.update(edge.geometry())
            edge_rows.append(row)
        payload: dict[str, object] = {
            "schema": GIT_CHECKOUT_VECTORIZATION_SCHEMA,
            "version": GIT_CHECKOUT_VECTORIZATION_VERSION,
            "head_commit": self.head_commit,
            "root_tree": self.root_tree,
            "object_count": len(object_rows),
            "occurrence_count": len(occurrence_rows),
            "containment_edge_count": len(edge_rows),
            "objects": object_rows,
            "occurrences": occurrence_rows,
            "containment_edges": edge_rows,
            "firewall": {
                "manual_file_selection": False,
                "path_as_vector_parent": False,
                "file_name_as_vector_parent": False,
                "extension_as_vector_parent": False,
                "size_as_vector_parent": False,
                "relation_label_as_vector_parent": False,
                "invented_edge_vector": False,
                "untracked_files_included": False,
                "vectorization_implies_semantic_truth": False,
            },
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload["receipt_sha256"] = hashlib.sha256(encoded).hexdigest()
        return payload


def _git(repo: Path, *args: str) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({process.returncode}): "
            + process.stderr.decode("utf-8", errors="replace").strip()
        )
    return process.stdout


def _parse_ls_tree(raw: bytes) -> tuple[GitOccurrence, ...]:
    occurrences: list[GitOccurrence] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_raw = record.split(b"\t", 1)
        mode_raw, type_raw, digest_raw = metadata.split(b" ", 2)
        object_type = type_raw.decode("ascii")
        if object_type not in {"blob", "tree", "commit"}:
            raise ValueError(f"unsupported ls-tree object type: {object_type}")
        occurrences.append(
            GitOccurrence(
                path=path_raw.decode("utf-8", errors="surrogateescape"),
                mode=mode_raw.decode("ascii"),
                object_type=object_type,
                digest=digest_raw.decode("ascii").lower(),
            )
        )
    return tuple(occurrences)


def _parent_directory(path: str) -> str:
    parent = PurePosixPath(path).parent.as_posix()
    return "" if parent == "." else parent


def _tree_containment_edges(
    root_tree: str,
    occurrences: Iterable[GitOccurrence],
) -> tuple[GitContainmentEdge, ...]:
    items = tuple(occurrences)
    tree_by_path = {item.path: item.digest for item in items if item.object_type == "tree"}
    edges: list[GitContainmentEdge] = []
    for item in items:
        parent_path = _parent_directory(item.path)
        parent_digest = root_tree if parent_path == "" else tree_by_path.get(parent_path)
        if parent_digest is None:
            raise ValueError(f"missing parent tree for Git occurrence: {item.path}")
        edges.append(
            GitContainmentEdge(
                parent_type="tree",
                parent_digest=parent_digest,
                child_type=item.object_type,
                child_digest=item.digest,
                relation="git_tree_contains",
                child_path=item.path,
            )
        )
    return tuple(edges)


def scan_git_checkout(repo: str | Path, revision: str = "HEAD") -> GitCheckoutObjectGraph:
    """Scan every tracked object reachable through the selected revision tree."""
    root = Path(repo).resolve()
    head = _git(root, "rev-parse", f"{revision}^{{commit}}").decode("ascii").strip().lower()
    root_tree = _git(root, "rev-parse", f"{revision}^{{tree}}").decode("ascii").strip().lower()
    raw = _git(root, "ls-tree", "-r", "-t", "-z", "--full-tree", revision)
    occurrences = _parse_ls_tree(raw)
    root_edge = GitContainmentEdge(
        parent_type="commit",
        parent_digest=head,
        child_type="tree",
        child_digest=root_tree,
        relation="git_commit_root_tree",
        child_path="",
    )
    edges = (root_edge,) + _tree_containment_edges(root_tree, occurrences)
    return GitCheckoutObjectGraph(
        head_commit=head,
        root_tree=root_tree,
        occurrences=occurrences,
        containment_edges=edges,
    )
