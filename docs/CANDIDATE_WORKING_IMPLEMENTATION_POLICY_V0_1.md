# Candidate Working Implementation Policy v0.1

Status: `CANONICAL_PROCESS_POLICY`

Date: 2026-09-11

`CANDIDATE` is an active working state. Candidate implementations are expected to execute, participate in benchmarks and integration tests, and emit provenance receipts while remaining visibly candidate-labelled.

```text
CANONICAL   = promoted/default-capable validated contract.
CANDIDATE   = active executable working implementation; explicit admission required.
QUARANTINED = isolated except diagnostics.
FAILED      = known failing implementation; not a working route.
```

The reference runtime contract is implemented by:

`src/ciel_geometry/phasenav/working_implementation_registry.py`

Rules:

1. A candidate may execute only after explicit candidate admission (`allow_candidate=True`).
2. A candidate execution receipt must preserve `status=CANDIDATE`.
3. A candidate may depend on canonical components and may feed other candidate-labelled components.
4. Candidate execution success does not silently promote it to canonical.
5. `FAILED` and `QUARANTINED` are distinct from `CANDIDATE` and require diagnostic override.
6. A candidate cannot silently become the default route.

This policy is intended to keep research implementations alive and usable while retaining exact epistemic and operational status.
