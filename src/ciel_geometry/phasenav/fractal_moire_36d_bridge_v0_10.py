from __future__ import annotations

import re
from typing import Any, Mapping

from .fractal_moire_36d_bridge_v0_2 import FractalMoire36Error
from .fractal_moire_36d_bridge_v0_9 import (
    SCHEMA as SCHEMA_V09,
    validate_bridge_packet_v09,
)


SCHEMA = "phasenav.fractal-moire-36d-bridge/v0.10"

ARPL_OVERLAP = "ARPL_HIT_OVERLAP_GRAM"
ARPL_CARRY = "ARPL_ODOMETER_CARRY"
ARPL_LIMIT = "ARPL_PROCYCLIC_ODOMETER_LIMIT"

ARPL_REPOSITORY = "AdrianLipa90/On-Primes"

SUPERSEDED_ARPL_SOURCE_SHAS = {
    "705872f11aaf8b933ab3b713fb10443326fde62b",
}

_SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")


def _text(x: Any, name: str) -> str:
    if not isinstance(x, str) or not x.strip():
        raise FractalMoire36Error(f"{name} must be non-empty")
    return x.strip()


def arpl_source_usage(packet: Mapping[str, Any]) -> tuple[str, ...]:
    uses: list[str] = []
    if packet.get("overlap_source_subtype") == ARPL_OVERLAP:
        uses.append(ARPL_OVERLAP)
    if packet.get("cocycle_subtype") == ARPL_CARRY:
        uses.append(ARPL_CARRY)
    if packet.get("infinite_depth_subtype") == ARPL_LIMIT:
        uses.append(ARPL_LIMIT)
    return tuple(uses)


def _validate_arpl_source_pin(packet: Mapping[str, Any]) -> dict[str, Any]:
    repo = _text(packet.get("arpl_source_repository"), "arpl_source_repository")
    if repo != ARPL_REPOSITORY:
        raise FractalMoire36Error(
            f"arpl_source_repository must be {ARPL_REPOSITORY}"
        )

    branch = _text(packet.get("arpl_source_branch"), "arpl_source_branch")
    sha = _text(packet.get("arpl_source_commit_sha"), "arpl_source_commit_sha")
    if not _SHA40.fullmatch(sha):
        raise FractalMoire36Error(
            "arpl_source_commit_sha must be exactly 40 hexadecimal characters"
        )
    sha = sha.lower()

    if sha in SUPERSEDED_ARPL_SOURCE_SHAS:
        raise FractalMoire36Error(
            "arpl_source_commit_sha is explicitly superseded"
        )

    files = packet.get("arpl_source_files")
    if not isinstance(files, list) or not files:
        raise FractalMoire36Error("arpl_source_files must be a non-empty list")
    normalized_files = tuple(
        _text(item, f"arpl_source_files[{i}]")
        for i, item in enumerate(files)
    )

    witness = _text(
        packet.get("arpl_source_pin_witness_ref"),
        "arpl_source_pin_witness_ref",
    )

    return {
        "repository": repo,
        "branch": branch,
        "commit_sha": sha,
        "source_files": normalized_files,
        "pin_witness_ref": witness,
        "immutable_pin": True,
    }


def validate_bridge_packet_v10(
    packet: Mapping[str, Any],
    *,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    if packet.get("schema") != SCHEMA:
        raise FractalMoire36Error(f"schema must be {SCHEMA}")

    p9 = dict(packet)
    p9["schema"] = SCHEMA_V09

    usage = arpl_source_usage(packet)
    pin_receipt = None

    if usage:
        pin_receipt = _validate_arpl_source_pin(packet)
        pin_receipt["arpl_surfaces"] = usage

    out = validate_bridge_packet_v09(p9, tolerance=tolerance)
    out["schema"] = SCHEMA
    out["arpl_source_pin_receipt"] = pin_receipt
    out["canon_allowed"] = False
    return out
