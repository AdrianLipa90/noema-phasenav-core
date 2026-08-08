"""Frozen-head gate for private repository object scans.

The v0.9 private inventory freezes 39 real repository heads. A tree/blob scan is
canonical only when the checkout HEAD equals that frozen native Git commit.
Repository aliases are used solely to locate the frozen provenance record; they
never enter the object-vector calculation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from .git_checkout_vectorization import GitCheckoutObjectGraph, scan_git_checkout
from .private_repository_snapshot import PRIVATE_REPOSITORY_HEADS

FROZEN_PRIVATE_CHECKOUT_VERSION = "0.10.0"


def frozen_private_heads() -> dict[str, str]:
    return {
        record.repository: record.head_commit
        for record in PRIVATE_REPOSITORY_HEADS
        if record.head_commit is not None
    }


def scan_checkout_at_expected_head(
    checkout: str | Path,
    expected_head: str,
) -> GitCheckoutObjectGraph:
    graph = scan_git_checkout(checkout)
    if graph.head_commit != expected_head.lower():
        raise RuntimeError(
            f"checkout head drift: expected {expected_head.lower()}, got {graph.head_commit}"
        )
    return graph


def scan_frozen_private_checkout(
    repository_alias: str,
    checkout: str | Path,
) -> GitCheckoutObjectGraph:
    expected = frozen_private_heads().get(repository_alias)
    if expected is None:
        raise KeyError(f"no frozen real head for {repository_alias}")
    return scan_checkout_at_expected_head(checkout, expected)


def scan_all_frozen_private_checkouts(
    checkouts: Mapping[str, str | Path],
) -> dict[str, object]:
    """Scan the complete 39-head snapshot or fail closed.

    Partial execution can use `scan_frozen_private_checkout`; this aggregate
    receipt intentionally requires all frozen real heads so a partial scan cannot
    be mislabeled as a complete private-repository object graph.
    """
    expected = frozen_private_heads()
    supplied = set(checkouts)
    required = set(expected)
    missing = sorted(required - supplied)
    extra = sorted(supplied - required)
    if missing or extra:
        raise ValueError(f"checkout set mismatch: missing={missing}, extra={extra}")

    rows = []
    for alias in sorted(required):
        graph = scan_checkout_at_expected_head(checkouts[alias], expected[alias])
        receipt = graph.receipt()
        rows.append({
            "repository_alias": alias,
            "head_commit": graph.head_commit,
            "root_tree": graph.root_tree,
            "object_count": receipt["object_count"],
            "occurrence_count": receipt["occurrence_count"],
            "containment_edge_count": receipt["containment_edge_count"],
            "object_graph_receipt_sha256": receipt["receipt_sha256"],
            "repository_alias_is_vector_parent": False,
        })

    payload: dict[str, object] = {
        "schema": "phasenav.private-repository-object-graphs/v0.10",
        "version": FROZEN_PRIVATE_CHECKOUT_VERSION,
        "frozen_head_count": len(expected),
        "scanned_head_count": len(rows),
        "complete_snapshot": True,
        "repositories": rows,
        "firewall": {
            "moving_head_allowed": False,
            "partial_scan_can_claim_complete": False,
            "repository_alias_is_vector_parent": False,
            "manual_file_selection": False,
            "path_is_vector_parent": False,
            "scientific_promotion": "NOT_PERFORMED",
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    payload["receipt_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload
