# TIR × ½ Dependency Canon v0.7 — Validation Receipt

Date: 2026-08-08

## Source

- repository: `AdrianLipa90/noema-phasenav-core`
- base branch: `master`
- base commit: `7210e8c62ac7ae6516469ecf502bbb38df98f2fd`
- integration branch: `canon/tir-half-noema-v0.7`
- PR: `#11`
- pre-receipt validated head: `fb6d497f3cb3ccd914adbe9e44b68b885b0a7b4c`

## Result

`PASS_FOCUSED / FULL_CI_INFRA_BLOCKED`

The focused validation covers the new v0.7 dependency mechanism itself. The
repository-wide GitHub Actions suite is **not** recorded as PASS because the
current Actions jobs fail before a runner executes any step.

## Focused validation — PASS

The independent validation reproduced the current PhaseNav non-numeric-ID 36D
routing law from `pnv_runtime.py` and checked the v0.7 dependency invariants:

- 11 typed dependency nodes;
- every routing vector finite and exactly 36D;
- all node-vector SHA-256 identities distinct in the declared graph;
- intrinsic coefficient dimension remains 4 and is not identified with 36D;
- `(h,a,b,c)` role router remains `STRUCTURAL_ROLE_ROUTING_PASS`;
- TIR slot binding remains `OPEN` and blocked;
- `SOH_C004` and `SOH_C005` remain `OPEN` and blocked;
- retrospective Collatz orientation remains blocked pending prospective test;
- `KAPPA` retains `PROJECT_DERIVED_EXACT_ALGEBRA` rather than proof strength;
- `HALF` remains exact/proof-consumable;
- current TIR neutron-EDM relation remains `PHYSICAL_FAIL` and blocked;
- deterministic focused receipt digest reproduced identically across two builds.

Focused validation digest:

`905c8bfd826f68695f0a3c02fd34d78b779405e32961e939ad5ac6b39e07bb68`

This digest identifies the focused validation payload, not the runtime graph
receipt returned by `DependencyGraph.receipt()`.

## GitHub Actions — INFRA_BLOCKED / NOT A TEST PASS

Two workflows were attempted on exact head
`fb6d497f3cb3ccd914adbe9e44b68b885b0a7b4c`:

- existing `Tests`, run `31247826931`;
- new `PhaseNav canon validation`, run `31247826928`.

Both concluded `failure`, but their failed jobs reported zero executed steps;
retries reproduced the same failure-before-runner pattern. The connector could
not retrieve job logs (`BlobNotFound`). Therefore no traceback or failed test
assertion exists in the available evidence.

For comparison, the same repository's existing `Tests` workflow completed all
Python 3.10/3.11/3.12 jobs successfully on historical commit
`43e67e704194afd6cd59199f82cd26890c2ad93b` (workflow run
`30947198047`). That historical PASS is provenance only and is **not** treated as
a PASS for the v0.7 head.

## Review

CodeRabbit successfully parsed and summarized all eight pre-receipt PR files and
reported the commit range `7210e8c...fb6d497`. Its summary is a review signal,
not an execution test.

## Promotion boundary

This receipt canonizes the software dependency/firewall structure under explicit
owner authority while preserving the CI limitation. It does not promote any
OPEN, retrospective, or failed scientific claim.

Scientific promotion remains independently gated by prospective evidence and the
claim ledgers in TIR and Secret-of-a-Half.
