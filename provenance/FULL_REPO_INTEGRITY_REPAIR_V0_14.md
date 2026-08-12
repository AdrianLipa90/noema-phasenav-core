# Full Repository Integrity Repair v0.14

## Status

`IMPLEMENTED / STATIC_AND_CONTRACT_AUDITED / CI_INFRA_BLOCKED / NOT_MERGED`

## Scope

This repair follows a whole-repository audit of `AdrianLipa90/noema-phasenav-core` after empty/placeholder executable surfaces and silent runtime degradation were discovered.

## Repaired defects

1. `concept_phases/`, `orbit_vectors/`, `kuramoto/`, `solver/`, and `encryption/` are executable surfaces, not README-only placeholders.
2. Runtime artifact construction is backed by canonical cards and cannot resolve required tables to zero records.
3. Orbit and operator vectors are finite 36D values; the historical `v36[:11]` truncation is prohibited.
4. The solver separates legacy 11-feature semantics from the canonical 36D phase-orbit vector contract.
5. Missing runtime JSONLs use explicit canonical fallback; malformed existing runtime data fails closed.
6. Solver lookups no longer fabricate zero-padded missing orbit/operator vectors.
7. The active crystal is documented and audited as 34,770 × 36 float64 with metadata-count alignment; 35,836 is historical/stale only.
8. `pnv_runtime` import initialization is side-effect free: it does not write `/dev/shm` or any runtime artifacts. Explicit `_write_state_jsonl()` delegates to the validated artifact registry.
9. `operator_algebra` no longer swallows broad exceptions, silently accepts non-36D records, expands malformed 24D runtime vectors, or substitutes `UNCERTAINTY` for unknown operator names.
10. Repository integrity CI fails on silent-exception patterns, `v36[:11]`, zero-padding fallbacks, malformed runtime records, stale active-crystal claims, placeholder directories, compile failures, and dimension/count mismatch.

## New integrity architecture

- `src/ciel_geometry/phasenav/artifact_registry.py`
- `src/ciel_geometry/phasenav/runtime_integrity.py`
- strict `loader.py`
- strict `solver.py`
- side-effect-free `pnv_runtime.py`
- fail-closed `operator_algebra.py`
- `scripts/repo_integrity_audit.py`
- `tests/test_repo_integrity_v014.py`

Runtime materialization is explicit and atomic, with SHA-256 manifest output.

## Validation evidence

The modified `pnv_runtime.py` and `operator_algebra.py` replacements were syntax-compiled during construction. Repository tests and the whole-repository audit are wired into GitHub Actions.

GitHub Actions on the exact repair heads continue to fail before a runner executes any workflow step (`steps=null` / runner unavailable). This is classified as `CI_INFRA_BLOCKED`; it is not represented as either code PASS or code FAIL.

No executable full-suite PASS is claimed until a runner or equivalent exact-checkout environment actually runs the suite.

## Merge boundary

Repair branch: `repair/full-repo-integrity-v0.14`

PR: `#23`

No direct write to `master` was performed by this repair workflow. Owner merge remains explicit.

## Scientific boundary

This is software integrity and compatibility work. It does not promote legacy algorithms or scientific claims to canon.
