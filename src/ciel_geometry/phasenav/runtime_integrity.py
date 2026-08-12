"""Compatibility repair layer for legacy PhaseNav runtime entry points.

The historical runtime expected glossary.pnv files that are no longer present in
this repository. This module binds those entry points to the current canonical
card registry and removes silent-empty behavior without mutating scientific canon.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from .artifact_registry import (
    ArtifactIntegrityError,
    build_canonical_runtime_bundle,
    canonical_glossary,
    write_runtime_artifacts,
)

_INSTALL_RECEIPT: dict[str, Any] | None = None


def _binding_active(root: Path) -> bool:
    marker = root / "ciel_binding_status"
    if not marker.exists():
        return False
    try:
        return marker.read_text(encoding="utf-8").strip() == "ACTIVE"
    except OSError:
        return False


def _materialize_active_host(receipt: dict[str, Any]) -> None:
    root = Path("/dev/shm/ciel_noema")
    if not root.exists() or not _binding_active(root):
        receipt["host_materialization"] = "INACTIVE_OR_ABSENT"
        return
    try:
        written = write_runtime_artifacts(root / "phasenav")
    except (OSError, ArtifactIntegrityError) as exc:
        receipt["host_materialization"] = "FAILED"
        receipt["host_materialization_error"] = f"{type(exc).__name__}: {exc}"
    else:
        receipt["host_materialization"] = "WRITTEN"
        receipt["host_files"] = sorted(str(path) for path in written.values())


def install_runtime_compat(*, materialize_active_host: bool = True) -> dict[str, Any]:
    """Install canonical fallbacks and repair package-level legacy aliases.

    Installation is idempotent. A later call may still request host materialization
    even when the in-process compatibility bindings were installed earlier.
    """
    global _INSTALL_RECEIPT
    if _INSTALL_RECEIPT is not None:
        if (
            materialize_active_host
            and _INSTALL_RECEIPT.get("host_materialization") == "NOT_REQUESTED"
        ):
            _materialize_active_host(_INSTALL_RECEIPT)
        package = sys.modules.get("ciel_geometry.phasenav")
        if package is not None:
            setattr(package, "RUNTIME_INTEGRITY_RECEIPT", dict(_INSTALL_RECEIPT))
        return dict(_INSTALL_RECEIPT)

    from . import pnv_runtime as runtime
    from . import operator_algebra as algebra

    def glossary_with_bloch() -> dict[str, dict[str, Any]]:
        glossary = canonical_glossary()
        for entry in glossary.values():
            vector = entry["v36"]
            theta, phi = runtime.M_project_bloch(vector)
            entry["v2"] = [round(float(theta), 10), round(float(phi), 10)]
        return glossary

    from .canon.seed_data import SEED_ROWS

    ids = sorted(
        line.split("|", 1)[0].strip()
        for line in SEED_ROWS.splitlines()
        if line.strip()
    )

    runtime._load_glossary = glossary_with_bloch
    runtime.ALL_STATE_IDS = ids

    def write_state_surface(base_path: str = "/dev/shm/ciel_noema/phasenav"):
        return write_runtime_artifacts(base_path)

    def write_operator_surface(base_path: str | Path | None = None) -> str:
        base = Path(base_path) if base_path is not None else Path("/dev/shm/ciel_noema/phasenav")
        base.mkdir(parents=True, exist_ok=True)
        path = base / "CIELINGO_PHASENAV_OPERATOR_VECTORS.noema.jsonl"
        algebra.generate_operator_jsonl(str(path))
        return str(path)

    runtime._write_state_jsonl = write_state_surface

    # Correct legacy aliases that previously pointed operator APIs at state JSONL text.
    runtime.generate_operator_map = algebra.generate_operator_map
    runtime.generate_operator_jsonl = algebra.generate_operator_jsonl
    runtime.write_operator_algebra = write_operator_surface
    runtime.operator_vector_24d = algebra.operator_vector_36d
    runtime.operator_vector_36d = algebra.operator_vector_36d
    runtime.concept_to_operator = algebra.concept_to_operator
    runtime.get_all_operations = algebra.get_all_operations
    runtime.ALL_OPERATOR_IDS = list(algebra.ALL_OPERATOR_IDS)
    algebra.write_operator_algebra = write_operator_surface

    original_operator_loader = algebra.load_runtime_operators

    def load_runtime_operators_strict(
        jsonl_path=None,
        noema_root=None,
        force_reload: bool = False,
    ):
        if jsonl_path is None and noema_root is None:
            return {
                key: __import__("numpy").asarray(vector, dtype=float)
                for key, vector in algebra.generate_operator_map().items()
            }
        result = original_operator_loader(
            jsonl_path=jsonl_path,
            noema_root=noema_root,
            force_reload=force_reload,
        )
        if not result:
            raise ArtifactIntegrityError("operator runtime resolved to zero vectors")
        bad = [key for key, value in result.items() if len(value) != 36]
        if bad:
            raise ArtifactIntegrityError(f"non-36D runtime operators: {bad[:8]}")
        return result

    def load_concept_phases_strict(
        jsonl_path=None,
        noema_root=None,
        force_reload: bool = False,
    ):
        import numpy as np

        # Explicit files stay supported, but missing/empty files fall back to canon.
        path = None
        if jsonl_path is not None:
            path = Path(jsonl_path)
        elif noema_root is not None:
            path = (
                Path(noema_root)
                / "runtime"
                / "phasenav"
                / "latest"
                / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl"
            )

        concepts: dict[str, Any] = {}
        if path is not None and path.exists():
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ArtifactIntegrityError(
                        f"invalid concept JSONL {path}:{line_number}: {exc}"
                    ) from exc
                cid = str(rec.get("concept_card_id", ""))
                raw = rec.get("phase_vector_36d") or rec.get("vector_36d")
                if cid and raw is not None:
                    arr = np.asarray(raw, dtype=np.float64)
                    if arr.shape != (36,) or not np.all(np.isfinite(arr)):
                        raise ArtifactIntegrityError(
                            f"{path}:{line_number}: concept vector is not finite 36D"
                        )
                    key = cid.removeprefix("concept:")
                    concepts[key] = arr
                    concepts[cid] = arr

        if not concepts:
            bundle = build_canonical_runtime_bundle()
            for rec in bundle.records["concept_phases"]:
                arr = np.asarray(rec["phase_vector_36d"], dtype=np.float64)
                cid = str(rec["concept_card_id"])
                key = cid.removeprefix("concept:")
                concepts[key] = arr
                concepts[cid] = arr

        algebra.CONCEPT_PHASES = concepts
        return concepts

    algebra.load_runtime_operators = load_runtime_operators_strict
    algebra.load_concept_phases = load_concept_phases_strict

    # The package imported several old pnv_runtime aliases before solver->loader
    # installed this layer. Rebind those public attributes in-place so explicit
    # package-level imports cannot retain the stale empty/string-returning callables.
    package = sys.modules.get("ciel_geometry.phasenav")
    if package is not None:
        public_rebindings = {
            "ALL_STATE_IDS": runtime.ALL_STATE_IDS,
            "ALL_OPERATOR_IDS": algebra.ALL_OPERATOR_IDS,
            "generate_operator_map": algebra.generate_operator_map,
            "generate_operator_jsonl": algebra.generate_operator_jsonl,
            "write_operator_algebra": write_operator_surface,
            "operator_vector_24d": algebra.operator_vector_36d,
            "operator_vector_36d": algebra.operator_vector_36d,
            "concept_to_operator": algebra.concept_to_operator,
            "get_all_operations": algebra.get_all_operations,
        }
        for name, value in public_rebindings.items():
            setattr(package, name, value)

    receipt: dict[str, Any] = {
        "schema": "phasenav.runtime-compat-install/v0.14",
        "status": "ACTIVE",
        "glossary_source": "CANONICAL_CARD_REGISTRY",
        "state_ids": len(ids),
        "operator_vectors": len(algebra.ALL_OPERATOR_IDS),
        "orbit_vectors": len(ids),
        "vector_dim": 36,
        "public_abi_rebound": True,
        "silent_empty_fallback": False,
        "host_materialization": "NOT_REQUESTED",
    }

    if materialize_active_host:
        _materialize_active_host(receipt)

    _INSTALL_RECEIPT = receipt
    if package is not None:
        setattr(package, "RUNTIME_INTEGRITY_RECEIPT", dict(receipt))
    return dict(receipt)


def runtime_integrity_receipt() -> dict[str, Any]:
    return install_runtime_compat()


__all__ = ["install_runtime_compat", "runtime_integrity_receipt"]
