# Independent PhaseNav Validator v1

This directory contains an external repository validator for `noema-phasenav-core`.

Its purpose is to answer a different question from the package's own tests:

> Can an observer that does **not trust PhaseNav's internal validation helpers** verify the repository's structural and runtime integrity?

## Independence boundary

`independent_validator.py` does not use pytest, GitHub Actions, `artifact_registry` validation routines, or PhaseNav health/doctor functions for its primary checks.

The first validation layer uses only the Python standard library and reads repository files directly. It independently verifies:

- required repository paths;
- the five executable top-level surfaces (`concept_phases`, `orbit_vectors`, `kuramoto`, `solver`, `encryption`);
- syntax of Python sources/tests/scripts via built-in `compile()`;
- the literal canonical `SEED_ROWS` ledger via Python AST without importing it;
- unique, contiguous `001..N` canonical IDs and at least 120 canonical cards;
- `canon_manifest.json` parseability;
- the `.npy` magic/version/header/shape/dtype-derived file size without NumPy;
- full JSON parsing of every non-empty crystal metadata JSONL record;
- exact equality between NPY row count and metadata record count;
- the 36D orbit-schema contract;
- absence of silent broad `except: pass` in critical runtime paths;
- absence of known regressions such as `v36[:11]`, orbit zero-padding, 36D zero-padding and unknown-operator→`UNCERTAINTY` placeholders;
- absence of import-time writer/materializer calls from `pnv_runtime._init`;
- stale active-crystal documentation claims.

A second layer runs an **isolated subprocess** and performs a minimal runtime probe. It checks package import, `VECTOR_DIM == 36`, at least 120 states, a non-empty all-36D operator map and a 36D solver orbit from an empty temporary runtime directory. A crash in this subprocess cannot erase the static audit results.

## Usage

Normal independent validation:

```text
python3 validator/independent_validator.py
```

Machine-readable report:

```text
python3 validator/independent_validator.py --json
```

Write an immutable-style receipt file chosen by the operator:

```text
python3 validator/independent_validator.py --json --receipt provenance/independent-validation.json
```

Run only the standard-library forensic layer, with no PhaseNav import:

```text
python3 validator/independent_validator.py --no-runtime
```

Require the runtime probe to execute successfully; missing external Python dependencies become a hard failure:

```text
python3 validator/independent_validator.py --require-runtime
```

## Verdict semantics

Each check emits one of:

- `PASS` — this check was executed and its invariant held;
- `FAIL` — the check was executed and detected a violation;
- `SKIP` — only permitted for the isolated runtime probe when an external dependency is unavailable, unless `--require-runtime` is used.

The overall process exits `0` only when there are zero `FAIL` checks. Otherwise it exits `1`.

The JSON report includes the SHA-256 of the validator itself, hashes of critical source/data artifacts, Python version, per-check evidence, elapsed time, and PASS/FAIL/SKIP totals.

## Epistemic boundary

This validator checks software/data integrity contracts. It does not validate scientific interpretations, physical claims, theorem status, or promotion to canon.

It is intentionally separate from GitHub billing/runner availability. It can be executed locally, in another CI provider, in a container, or on an offline checkout.
