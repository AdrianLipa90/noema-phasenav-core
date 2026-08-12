"""Whole-repository PhaseNav integrity audit.

Exit non-zero on structural placeholders, empty canonical/runtime surfaces,
non-36D vectors, crystal shape/count mismatches, or broken canonical fallback.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tempfile

import numpy as np


EXPECTED_EXECUTABLE_DIRS = {
    "concept_phases": {"README.md", "__init__.py", "catalog.py", "export.py"},
    "orbit_vectors": {"README.md", "__init__.py", "catalog.py", "export.py"},
    "kuramoto": {"README.md", "__init__.py", "synchronizer.py", "diagnostics.py"},
    "solver": {"README.md", "__init__.py", "runtime.py", "cli.py"},
    "encryption": {"README.md", "__init__.py", "runtime.py", "validation.py"},
}


def _check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def audit(root: Path) -> dict:
    failures: list[str] = []
    warnings: list[str] = []
    details: dict = {}

    for dirname, required in EXPECTED_EXECUTABLE_DIRS.items():
        directory = root / dirname
        present = {path.name for path in directory.iterdir()} if directory.exists() else set()
        missing = sorted(required - present)
        _check(directory.is_dir(), f"missing directory: {dirname}", failures)
        _check(not missing, f"{dirname}: missing executable files {missing}", failures)
        details[f"dir:{dirname}"] = {"present": sorted(present), "missing": missing}

    compile_failures = []
    for base in (root / "src", root / "scripts", *(root / name for name in EXPECTED_EXECUTABLE_DIRS)):
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except Exception as exc:
                compile_failures.append(f"{path.relative_to(root)}: {type(exc).__name__}: {exc}")
    _check(not compile_failures, f"python compile failures: {compile_failures[:8]}", failures)
    details["python_compile_failures"] = compile_failures

    vec_path = root / "src/ciel_geometry/phasenav/data/phase_crystal_36d.npy"
    meta_path = root / "src/ciel_geometry/phasenav/data/phase_crystal_meta.jsonl"
    _check(vec_path.exists(), "phase_crystal_36d.npy missing", failures)
    _check(meta_path.exists(), "phase_crystal_meta.jsonl missing", failures)
    if vec_path.exists() and meta_path.exists():
        arr = np.load(vec_path, mmap_mode="r")
        meta_count = sum(1 for line in meta_path.open(encoding="utf-8") if line.strip())
        _check(arr.ndim == 2 and arr.shape[1] == 36, f"crystal shape is {arr.shape}, expected N×36", failures)
        _check(arr.shape[0] >= 34770, f"crystal has only {arr.shape[0]} facets", failures)
        _check(meta_count == arr.shape[0], f"crystal vectors/meta mismatch {arr.shape[0]} vs {meta_count}", failures)
        details["crystal"] = {"shape": list(arr.shape), "metadata_records": meta_count}

    import sys
    sys.path.insert(0, str(root / "src"))
    from ciel_geometry.phasenav.artifact_registry import (
        build_canonical_runtime_bundle,
        validate_runtime_directory,
        write_runtime_artifacts,
    )
    from ciel_geometry.phasenav.canon.cards import load_canonical_cards
    from ciel_geometry.phasenav.loader import load_phasenav
    from ciel_geometry.phasenav.runtime_integrity import runtime_integrity_receipt
    from ciel_geometry.phasenav.solver import PhaseNavSolver
    from ciel_geometry.phasenav import pnv_runtime
    from ciel_geometry.phasenav import operator_algebra

    cards = load_canonical_cards()
    bundle = build_canonical_runtime_bundle()
    _check(len(cards) >= 120, f"canonical cards unexpectedly low: {len(cards)}", failures)
    _check(bundle.count("concept_phases") == len(cards), "concept phase count != canonical card count", failures)
    _check(bundle.count("orbit_vectors") == len(cards), "orbit count != canonical card count", failures)
    _check(bundle.count("operator_vectors") > 0, "operator vector catalogue empty", failures)
    _check(bundle.count("holonomic_edges") > 0, "holonomic edge catalogue empty", failures)

    for row in bundle.records["orbit_vectors"]:
        v = row["orbit_vector"]
        _check(len(v) == 36 and all(math.isfinite(float(x)) for x in v),
               f"bad orbit vector {row.get('card_id')}", failures)
    for row in bundle.records["operator_vectors"]:
        v = row["vector_36d"]
        _check(len(v) == 36 and all(math.isfinite(float(x)) for x in v),
               f"bad operator vector {row.get('operator_id')}", failures)

    receipt = runtime_integrity_receipt()
    _check(receipt.get("state_ids", 0) == len(cards), "runtime compatibility state count mismatch", failures)
    _check(len(pnv_runtime._load_glossary()) == len(cards), "pnv_runtime glossary compatibility is empty/mismatched", failures)

    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        data = load_phasenav(temp)
        _check(len(data.orbits) == len(cards), f"loader fallback orbit count {len(data.orbits)} != {len(cards)}", failures)
        _check(len(data.operator_vectors) > 0, "loader fallback operator vectors empty", failures)
        solver = PhaseNavSolver(data)
        orbit = solver.get_orbit("001")
        _check(len(orbit) == 36, f"solver orbit returned {len(orbit)}D", failures)

        write_runtime_artifacts(temp)
        runtime_report = validate_runtime_directory(temp)
        _check(bool(runtime_report["ok"]), f"materialized runtime validation failed: {runtime_report}", failures)
        details["materialized_runtime"] = runtime_report

        concept_map = operator_algebra.load_concept_phases(
            jsonl_path=temp / "missing-concepts.jsonl",
            force_reload=True,
        )
        _check(len(concept_map) >= len(cards), "operator_algebra concept fallback empty", failures)

    readme = (root / "README.md").read_text(encoding="utf-8")
    stale_active_claims = (
        "Memory Crystal (35 836 facets)",
        "Memory Crystal (35,836 facets)",
        "phase_crystal_36d.npy       35 836",
        "phase_crystal_36d.npy       35,836",
    )
    _check(
        not any(claim in readme for claim in stale_active_claims),
        "README still advertises stale 35,836 snapshot as active crystal",
        failures,
    )

    for rel in (
        "src/ciel_geometry/phasenav/pnv_runtime.py",
        "src/ciel_geometry/phasenav/operator_algebra.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        if "except Exception:\n        pass" in text:
            warnings.append(
                f"{rel}: legacy broad silent exception remains in source; public runtime is superseded by runtime_integrity v0.14"
            )

    details["canonical_cards"] = len(cards)
    details["runtime_counts"] = {key: bundle.count(key) for key in bundle.records}
    details["compat_receipt"] = receipt

    return {
        "schema": "phasenav.repo-integrity-audit/v0.14",
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.root.resolve())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("PASS" if report["ok"] else "FAIL")
        for item in report["failures"]:
            print(f"FAIL: {item}")
        for item in report["warnings"]:
            print(f"WARN: {item}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
