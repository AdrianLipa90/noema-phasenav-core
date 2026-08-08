"""Digest-native Git object vectorization for PhaseNav.

This module removes label-derived routing from repository vectorization.
A Git object's *native object digest* is the only numerical parent of its T^36
routing identity. Repository names, file names, paths, manually assigned IDs,
and relation labels are provenance/graph metadata only and never seed vectors.

For SHA-1 repositories the 40-hex Git object id is used directly. The module
also accepts 64-hex SHA-256 object ids for Git's SHA-256 object format. No
secondary Collatz/string hash is inserted between the Git object identity and
the information-phase law.

The routing vector is an identity representation, not evidence of semantic,
mathematical, or physical equivalence.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
import hashlib
import json
import math
import re
from typing import Literal

from .model import PHASE_DIM

GIT_OBJECT_VECTORIZATION_VERSION = "0.9.0"
GIT_OBJECT_VECTORIZATION_SCHEMA = "phasenav.git-object-vector/v0.9"

# Same exact algebraic phase increment used by the canonical non-numeric
# PhaseNav route: kappa * 2pi = ln(2)/12. Here the parent integer is the native
# Git object digest itself rather than a hash of a human label.
_LN2_OVER_12 = Decimal("0.05776226504666210911810267678818141")
_TAU = Decimal("6.2831853071795864769252867665590057")
_HEX = re.compile(r"^[0-9a-f]+$")
_HASH_LENGTH = {"sha1": 40, "sha256": 64}
GitObjectType = Literal["blob", "tree", "commit", "tag"]


def normalize_git_digest(digest: str, algorithm: str | None = None) -> tuple[str, str]:
    value = digest.strip().lower()
    if not _HEX.fullmatch(value):
        raise ValueError("Git object digest must be lowercase/uppercase hexadecimal")
    inferred = {40: "sha1", 64: "sha256"}.get(len(value))
    if inferred is None:
        raise ValueError("Git object digest must contain exactly 40 or 64 hex characters")
    if algorithm is not None and algorithm.lower() != inferred:
        raise ValueError(f"digest length implies {inferred}, not {algorithm}")
    return inferred, value


def git_digest_phase36(digest: str, algorithm: str | None = None) -> tuple[float, ...]:
    """Project one native Git object identity to the PhaseNav T^36 envelope.

    The mapping contains no repository-name/path/manual-ID input. Coordinate i
    follows the same information-phase progression used by PhaseNav:

        phi_i = (N_git * (i+1) * ln(2)/12) mod 2pi

    where N_git is the exact integer represented by the native Git object id.
    """
    _, value = normalize_git_digest(digest, algorithm)
    parent = int(value, 16)
    with localcontext() as ctx:
        # Enough precision to preserve the complete SHA-1/SHA-256 parent before
        # modular reduction, with guard digits for the phase constants.
        ctx.prec = max(96, len(value) * 2 + 32)
        phases = tuple(
            round(float((Decimal(parent * (i + 1)) * _LN2_OVER_12) % _TAU), 10)
            for i in range(PHASE_DIM)
        )
    if len(phases) != PHASE_DIM or not all(math.isfinite(x) for x in phases):
        raise AssertionError("invalid Git-object PhaseNav projection")
    return phases


def vector_sha256(vector36: tuple[float, ...]) -> str:
    payload = json.dumps(
        [round(float(x), 15) for x in vector36], separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class GitObjectVector:
    object_type: GitObjectType
    algorithm: str
    digest: str
    vector36: tuple[float, ...]

    @classmethod
    def from_digest(
        cls,
        object_type: GitObjectType,
        digest: str,
        algorithm: str | None = None,
    ) -> "GitObjectVector":
        alg, canonical = normalize_git_digest(digest, algorithm)
        if object_type not in {"blob", "tree", "commit", "tag"}:
            raise ValueError(f"unsupported Git object type: {object_type}")
        return cls(
            object_type=object_type,
            algorithm=alg,
            digest=canonical,
            vector36=git_digest_phase36(canonical, alg),
        )

    @property
    def vector_sha256(self) -> str:
        return vector_sha256(self.vector36)

    def receipt(self) -> dict[str, object]:
        return {
            "schema": GIT_OBJECT_VECTORIZATION_SCHEMA,
            "version": GIT_OBJECT_VECTORIZATION_VERSION,
            "object_type": self.object_type,
            "object_hash_algorithm": self.algorithm,
            "object_digest": self.digest,
            "routing_dimension": PHASE_DIM,
            "vector_36d": list(self.vector36),
            "vector_sha256": self.vector_sha256,
            "label_seed_used": False,
            "path_seed_used": False,
            "manual_id_seed_used": False,
            "collatz_string_hash_used": False,
            "semantic_promotion": "NOT_PERFORMED",
        }


@dataclass(frozen=True)
class GitRepositorySnapshot:
    """Repository metadata bound to a content/history state.

    `repository_full_name`, repository id, and branch are aliases/provenance.
    The routing vector depends *only* on `head_commit_digest`.
    """

    repository_full_name: str
    repository_id: int
    default_branch: str
    head_commit_digest: str
    head: GitObjectVector

    @classmethod
    def from_head(
        cls,
        repository_full_name: str,
        repository_id: int,
        default_branch: str,
        head_commit_digest: str,
        algorithm: str | None = None,
    ) -> "GitRepositorySnapshot":
        head = GitObjectVector.from_digest("commit", head_commit_digest, algorithm)
        return cls(
            repository_full_name=repository_full_name,
            repository_id=int(repository_id),
            default_branch=default_branch,
            head_commit_digest=head.digest,
            head=head,
        )

    def receipt(self) -> dict[str, object]:
        return {
            "schema": "phasenav.git-repository-snapshot/v0.9",
            "repository_alias": self.repository_full_name,
            "repository_id_provenance": self.repository_id,
            "default_branch_provenance": self.default_branch,
            "head_commit_digest": self.head_commit_digest,
            "head_vector_sha256": self.head.vector_sha256,
            "vector_36d": list(self.head.vector36),
            "vector_parent": "native_git_head_commit_digest_only",
            "repository_name_is_vector_parent": False,
            "repository_id_is_vector_parent": False,
            "branch_name_is_vector_parent": False,
        }
