#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import time
from typing import Any

SCHEMA = "phasenav.independent-validator/v1"
VECTOR_DIM = 36
MIN_CARDS = 120
MIN_CRYSTAL_ROWS = 34770

SURFACES = {
    "concept_phases": {"README.md", "__init__.py", "catalog.py", "export.py"},
    "orbit_vectors": {"README.md", "__init__.py", "catalog.py", "export.py"},
    "kuramoto": {"README.md", "__init__.py", "synchronizer.py", "diagnostics.py"},
    "solver": {"README.md", "__init__.py", "runtime.py", "cli.py"},
    "encryption": {"README.md", "__init__.py", "runtime.py", "validation.py"},
}

REQUIRED = (
    "pyproject.toml",
    "README.md",
    "src/ciel_geometry/phasenav/pnv_runtime.py",
    "src/ciel_geometry/phasenav/operator_algebra.py",
    "src/ciel_geometry/phasenav/loader.py",
    "src/ciel_geometry/phasenav/solver.py",
    "src/ciel_geometry/phasenav/canon/seed_data.py",
    "src/ciel_geometry/phasenav/canon/canon_manifest.json",
    "src/ciel_geometry/phasenav/data/phase_crystal_36d.npy",
    "src/ciel_geometry/phasenav/data/phase_crystal_meta.jsonl",
)

CRITICAL = (
    "src/ciel_geometry/phasenav/pnv_runtime.py",
    "src/ciel_geometry/phasenav/operator_algebra.py",
    "src/ciel_geometry/phasenav/loader.py",
    "src/ciel_geometry/phasenav/solver.py",
)


class Report:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def add(self, name: str, status: str, detail: Any = None) -> None:
        self.checks.append({"name": name, "status": status, "detail": detail})

    def ok(self, name: str, detail: Any = None) -> None:
        self.add(name, "PASS", detail)

    def fail(self, name: str, detail: Any = None) -> None:
        self.add(name, "FAIL", detail)

    def skip(self, name: str, detail: Any = None) -> None:
        self.add(name, "SKIP", detail)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def root_from(start: Path) -> Path:
    start = start.resolve()
    for p in (start, *start.parents):
        if (p / "pyproject.toml").exists() and (p / "src/ciel_geometry/phasenav").is_dir():
            return p
    raise FileNotFoundError(f"cannot locate repository root from {start}")


def check_structure(root: Path, r: Report) -> None:
    missing = [p for p in REQUIRED if not (root / p).exists()]
    (r.fail if missing else r.ok)("repo.required_paths", missing or {"count": len(REQUIRED)})

    bad: dict[str, list[str]] = {}
    detail = {}
    for name, required in SURFACES.items():
        d = root / name
        present = {p.name for p in d.iterdir()} if d.is_dir() else set()
        absent = sorted(required - present)
        detail[name] = {"present": sorted(present), "missing": absent}
        if absent or not d.is_dir():
            bad[name] = absent or ["<directory missing>"]
    (r.fail if bad else r.ok)("repo.executable_surfaces", bad or detail)


def check_python_syntax(root: Path, r: Report) -> None:
    failures = []
    count = 0
    roots = [root / "src", root / "scripts", root / "tests"]
    roots += [root / name for name in SURFACES]
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            count += 1
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except Exception as exc:
                failures.append(f"{path.relative_to(root)}: {type(exc).__name__}: {exc}")
    (r.fail if failures else r.ok)("python.syntax", failures or {"files": count})


def read_seed_rows(path: Path) -> list[tuple[str, str, str, str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    text = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "SEED_ROWS" for t in node.targets):
                text = ast.literal_eval(node.value)
                break
    if not isinstance(text, str):
        raise ValueError("literal SEED_ROWS string not found")
    rows = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = tuple(x.strip() for x in line.split("|"))
        if len(parts) != 5:
            raise ValueError(f"SEED_ROWS line {n}: expected 5 fields")
        rows.append(parts)
    return rows  # type: ignore[return-value]


def check_canon(root: Path, r: Report) -> None:
    seed = root / "src/ciel_geometry/phasenav/canon/seed_data.py"
    manifest = root / "src/ciel_geometry/phasenav/canon/canon_manifest.json"
    try:
        rows = read_seed_rows(seed)
        ids = [x[0] for x in rows]
        nums = [int(x) for x in ids]
        problems = []
        if len(rows) < MIN_CARDS:
            problems.append(f"only {len(rows)} cards; expected >= {MIN_CARDS}")
        if len(set(ids)) != len(ids):
            problems.append("duplicate IDs")
        if nums != list(range(1, max(nums) + 1)):
            problems.append("IDs are not contiguous 001..N")
        if any(len(x) != 3 or not x.isdigit() for x in ids):
            problems.append("IDs must be zero-padded 3-digit strings")
        names = [x[1] for x in rows]
        if len(set(names)) != len(names):
            problems.append("duplicate names")
        detail = {"records": len(rows), "first": ids[0], "last": ids[-1], "sha256": sha256(seed)}
        (r.fail if problems else r.ok)("canon.seed_ledger", {"problems": problems, **detail} if problems else detail)
    except Exception as exc:
        r.fail("canon.seed_ledger", f"{type(exc).__name__}: {exc}")

    try:
        obj = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            raise ValueError("manifest must be a JSON object")
        r.ok("canon.manifest_json", {"keys": sorted(obj), "sha256": sha256(manifest)})
    except Exception as exc:
        r.fail("canon.manifest_json", f"{type(exc).__name__}: {exc}")


def npy_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as fh:
        if fh.read(6) != b"\x93NUMPY":
            raise ValueError("bad NPY magic")
        version = tuple(fh.read(2))
        if version == (1, 0):
            hlen = struct.unpack("<H", fh.read(2))[0]
            offset = 10 + hlen
        elif version in {(2, 0), (3, 0)}:
            hlen = struct.unpack("<I", fh.read(4))[0]
            offset = 12 + hlen
        else:
            raise ValueError(f"unsupported NPY version {version}")
        encoding = "utf-8" if version == (3, 0) else "latin1"
        header = ast.literal_eval(fh.read(hlen).decode(encoding).strip())
        if not isinstance(header, dict):
            raise ValueError("NPY header is not a dict")
        header["_offset"] = offset
        header["_version"] = version
        return header


def dtype_itemsize(descr: str) -> int:
    digits = ""
    for ch in reversed(descr):
        if ch.isdigit():
            digits = ch + digits
        else:
            break
    if not digits:
        raise ValueError(f"cannot parse dtype itemsize from {descr!r}")
    return int(digits)


def check_crystal(root: Path, r: Report) -> None:
    vec = root / "src/ciel_geometry/phasenav/data/phase_crystal_36d.npy"
    meta = root / "src/ciel_geometry/phasenav/data/phase_crystal_meta.jsonl"
    try:
        h = npy_header(vec)
        shape = tuple(h.get("shape", ()))
        if len(shape) != 2 or int(shape[1]) != VECTOR_DIM:
            raise ValueError(f"expected N×{VECTOR_DIM}, got {shape}")
        rows = int(shape[0])
        if rows < MIN_CRYSTAL_ROWS:
            raise ValueError(f"crystal has {rows} rows, expected >= {MIN_CRYSTAL_ROWS}")
        if bool(h.get("fortran_order")):
            raise ValueError("Fortran-order crystal rejected by baseline")
        itemsize = dtype_itemsize(str(h.get("descr", "")))
        expected_size = int(h["_offset"]) + rows * VECTOR_DIM * itemsize
        if vec.stat().st_size != expected_size:
            raise ValueError(f"NPY size {vec.stat().st_size} != expected {expected_size}")

        count = 0
        bad = []
        with meta.open(encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                count += 1
                try:
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError("record is not an object")
                except Exception as exc:
                    bad.append(f"line {line_no}: {type(exc).__name__}: {exc}")
                    if len(bad) >= 8:
                        break
        if bad:
            raise ValueError(f"malformed metadata: {bad}")
        if count != rows:
            raise ValueError(f"metadata records {count} != NPY rows {rows}")
        r.ok("crystal.dataset", {
            "shape": [rows, VECTOR_DIM],
            "dtype": h.get("descr"),
            "metadata_records": count,
            "npy_sha256": sha256(vec),
            "meta_sha256": sha256(meta),
        })
    except Exception as exc:
        r.fail("crystal.dataset", f"{type(exc).__name__}: {exc}")


class SilentExcept(ast.NodeVisitor):
    def __init__(self) -> None:
        self.lines: list[int] = []

    def visit_Try(self, node: ast.Try) -> Any:
        for h in node.handlers:
            broad = h.type is None or (
                isinstance(h.type, ast.Name) and h.type.id in {"Exception", "BaseException"}
            )
            silent = bool(h.body) and all(isinstance(x, ast.Pass) for x in h.body)
            if broad and silent:
                self.lines.append(h.lineno)
        self.generic_visit(node)


def check_source_regressions(root: Path, r: Report) -> None:
    failures = []
    detail = {}
    forbidden = {
        "v36[:11]": "36D->11D truncation",
        "[0.0] * len(ORBIT_DIMS)": "orbit zero-padding",
        "[0.0] * 36": "36D zero-padding",
        'return operator_signature("UNCERTAINTY")': "unknown-operator placeholder",
    }
    for rel in CRITICAL:
        p = root / rel
        text = p.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(p))
        visitor = SilentExcept()
        visitor.visit(tree)
        if visitor.lines:
            failures.append(f"{rel}: silent broad except at {visitor.lines}")
        hits = {k: v for k, v in forbidden.items() if k in text}
        if hits:
            failures.append(f"{rel}: forbidden patterns {hits}")
        detail[rel] = {"sha256": sha256(p), "silent_except_lines": visitor.lines}

    solver = (root / "src/ciel_geometry/phasenav/solver.py").read_text(encoding="utf-8")
    if "PHASE_ORBIT_DIMS = [f\"phi_{i}\" for i in range(VECTOR_DIM)]" not in solver:
        failures.append("solver: canonical PHASE_ORBIT_DIMS definition missing")
    if "ORBIT_DIMS = PHASE_ORBIT_DIMS" not in solver:
        failures.append("solver: ORBIT_DIMS is not bound to 36D PHASE_ORBIT_DIMS")

    pnv = ast.parse((root / "src/ciel_geometry/phasenav/pnv_runtime.py").read_text(encoding="utf-8"))
    init_calls = []
    for node in pnv.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_init":
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    fn = child.func
                    name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
                    if name:
                        init_calls.append(name)
    dangerous = [x for x in init_calls if "write" in x.lower() or "material" in x.lower()]
    if dangerous:
        failures.append(f"pnv_runtime._init mutating calls: {sorted(set(dangerous))}")
    detail["pnv_runtime._init_calls"] = sorted(set(init_calls))

    (r.fail if failures else r.ok)("source.anti_regression", {"failures": failures, "details": detail} if failures else detail)


def check_docs(root: Path, r: Report) -> None:
    text = (root / "README.md").read_text(encoding="utf-8")
    stale = [x for x in (
        "Memory Crystal (35 836 facets)",
        "Memory Crystal (35,836 facets)",
        "phase_crystal_36d.npy       35 836",
        "phase_crystal_36d.npy       35,836",
    ) if x in text]
    (r.fail if stale else r.ok)("docs.active_crystal_claim", stale or "no stale active-dataset claim")


RUNTIME_CODE = r"""
import json, pathlib, sys, tempfile
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / "src"))
result = {"status": "PASS"}
try:
    import ciel_geometry.phasenav as p
    if p.VECTOR_DIM != 36:
        raise AssertionError(f"VECTOR_DIM={p.VECTOR_DIM}")
    states = p.get_all_states()
    if len(states) < 120:
        raise AssertionError(f"states={len(states)}")
    ops = p.generate_operator_map()
    if not ops or any(len(v) != 36 for v in ops.values()):
        raise AssertionError("operator map empty or non-36D")
    with tempfile.TemporaryDirectory() as td:
        s = p.PhaseNavSolver.load(pathlib.Path(td))
        if len(s.get_orbit("001")) != 36:
            raise AssertionError("solver orbit is not 36D")
    result.update(states=len(states), operators=len(ops))
except ImportError as exc:
    result = {"status": "IMPORT_ERROR", "error": f"{type(exc).__name__}: {exc}"}
except Exception as exc:
    result = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS" else 3)
"""


def check_runtime(root: Path, r: Report, require: bool) -> None:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CIEL_BINDING_STRICT"] = "0"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", RUNTIME_CODE, str(root)],
            cwd=root, env=env, text=True, capture_output=True, timeout=120, check=False
        )
    except Exception as exc:
        r.fail("runtime.isolated_probe", f"{type(exc).__name__}: {exc}")
        return
    lines = [x for x in proc.stdout.splitlines() if x.strip()]
    parsed = None
    if lines:
        try:
            parsed = json.loads(lines[-1])
        except json.JSONDecodeError:
            pass
    detail = {
        "returncode": proc.returncode,
        "result": parsed,
        "stdout_tail": "\n".join(lines[-5:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-12:]),
    }
    if proc.returncode == 0 and parsed and parsed.get("status") == "PASS":
        r.ok("runtime.isolated_probe", detail)
    elif parsed and parsed.get("status") == "IMPORT_ERROR" and not require:
        r.skip("runtime.isolated_probe", {**detail, "reason": "dependency unavailable; use --require-runtime to make fatal"})
    else:
        r.fail("runtime.isolated_probe", detail)


def validate(root: Path, no_runtime: bool, require_runtime: bool) -> dict[str, Any]:
    started = time.time()
    r = Report()
    check_structure(root, r)
    check_python_syntax(root, r)
    check_canon(root, r)
    check_crystal(root, r)
    check_source_regressions(root, r)
    check_docs(root, r)
    if no_runtime:
        r.skip("runtime.isolated_probe", "disabled by --no-runtime")
    else:
        check_runtime(root, r, require_runtime)
    fail_count = sum(1 for x in r.checks if x["status"] == "FAIL")
    return {
        "schema": SCHEMA,
        "status": "FAIL" if fail_count else "PASS",
        "root": str(root),
        "python": sys.version.split()[0],
        "validator_sha256": sha256(Path(__file__).resolve()),
        "duration_s": round(time.time() - started, 6),
        "summary": {
            "pass": sum(1 for x in r.checks if x["status"] == "PASS"),
            "fail": fail_count,
            "skip": sum(1 for x in r.checks if x["status"] == "SKIP"),
        },
        "checks": r.checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Independent noema-phasenav-core validator")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--no-runtime", action="store_true")
    ap.add_argument("--require-runtime", action="store_true")
    args = ap.parse_args()
    try:
        root = root_from(args.root)
        result = validate(root, args.no_runtime, args.require_runtime)
    except Exception as exc:
        result = {
            "schema": SCHEMA, "status": "FAIL", "root": str(args.root),
            "python": sys.version.split()[0],
            "summary": {"pass": 0, "fail": 1, "skip": 0},
            "checks": [{"name": "validator.internal", "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"}],
        }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"INDEPENDENT_VALIDATOR {result['status']} schema={result['schema']}")
        for item in result["checks"]:
            print(f"{item['status']:4} {item['name']}")
            if item["status"] != "PASS":
                print("     " + json.dumps(item.get("detail"), ensure_ascii=False, sort_keys=True))
        s = result["summary"]
        print(f"SUMMARY pass={s['pass']} fail={s['fail']} skip={s['skip']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
