# Full repository integrity repair v0.14

## Status

`IMPLEMENTED_REPAIR_CANDIDATE / MASTER_NOT_TOUCHED / EXECUTABLE_AUDIT_ADDED`

Base: merged v0.13 state (`24c268fee3a1c364e9b478e80f512fbbfc2b7a74`).

## Confirmed defects addressed

1. `concept_phases/`, `orbit_vectors/`, `kuramoto/`, `solver/`, and `encryption/` were README-only top-level shells.
2. Historical runtime initialization depended on absent `glossary.pnv` / `glossarius/ciel_omega_glossary.json`, allowing a zero-card runtime surface.
3. `_write_state_jsonl()` serialized only `v36[:11]` into fields called `orbit_vector`.
4. `solver.ORBIT_DIMS` simultaneously described those 11 entries as `mass/sin/cos/...`, producing a schema collision: the stored values were phase coordinates, not those named features.
5. runtime loaders could accept missing/empty files as empty state.
6. existing crystal tests could skip/accept zero-data states.
7. README advertised the stale 35,836-facet distribution snapshot as the active crystal. The active repository array is 34,770 × 36.

## Repair

- canonical card registry is now the deterministic fallback parent for runtime concept/name-mass/orbit/edge tables;
- all public orbit/operator vectors are finite 36D;
- runtime JSONL materialization is atomic and emits a SHA-256 manifest;
- loader rejects malformed/non-36D data and reconstructs missing/empty required runtime tables instead of returning empty state;
- solver orbit contract is explicitly 36D and missing data no longer becomes zero padding;
- compatibility overlay repairs legacy `pnv_runtime` state IDs/glossary and operator aliases without promoting scientific claims;
- top-level domain directories now contain executable modules rather than README placeholders;
- a whole-repository audit and strict regression tests were added;
- CI is configured to run the repository audit after pytest.

## Epistemic boundary

This is a software integrity repair. It does not promote legacy CIEL source, scientific hypotheses, open TIR/Secret-of-a-Half claims, or candidate concepts.

## Merge boundary

No direct write to `master` is performed by this repair branch.
