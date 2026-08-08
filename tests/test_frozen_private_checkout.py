from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from ciel_geometry.phasenav.canon.frozen_private_checkout import (
    frozen_private_heads,
    scan_all_frozen_private_checkouts,
    scan_checkout_at_expected_head,
    scan_frozen_private_checkout,
)


def run(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def make_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    run(repo, "init")
    run(repo, "config", "user.email", "frozen@example.invalid")
    run(repo, "config", "user.name", "Frozen Test")
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    run(repo, "add", "-A")
    run(repo, "commit", "-m", "one")
    return repo, run(repo, "rev-parse", "HEAD")


def test_generic_expected_head_gate_passes_exact_state(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    graph = scan_checkout_at_expected_head(repo, head)
    assert graph.head_commit == head


def test_generic_expected_head_gate_rejects_moving_head(tmp_path: Path) -> None:
    repo, head = make_repo(tmp_path)
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    run(repo, "add", "-A")
    run(repo, "commit", "-m", "two")
    with pytest.raises(RuntimeError, match="checkout head drift"):
        scan_checkout_at_expected_head(repo, head)


def test_frozen_inventory_contains_39_real_heads() -> None:
    heads = frozen_private_heads()
    assert len(heads) == 39
    assert heads["AdrianLipa90/NOEMA-vectorised-full"] == "205ea2937dce04124753feb46f91266d228564d9"
    assert "AdrianLipa90/noema-poincyre-cymatix" not in heads


def test_unknown_or_empty_inventory_alias_fails_closed(tmp_path: Path) -> None:
    repo, _ = make_repo(tmp_path)
    with pytest.raises(KeyError):
        scan_frozen_private_checkout("unknown/repo", repo)
    with pytest.raises(KeyError):
        scan_frozen_private_checkout("AdrianLipa90/noema-poincyre-cymatix", repo)


def test_complete_aggregate_rejects_partial_checkout_set() -> None:
    with pytest.raises(ValueError, match="checkout set mismatch"):
        scan_all_frozen_private_checkouts({})
