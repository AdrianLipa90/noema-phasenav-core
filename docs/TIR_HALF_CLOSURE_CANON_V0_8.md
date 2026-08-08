# PhaseNav TIR × Secret-of-a-Half Cross-Repository Closure Canon v0.8

## Purpose

This layer closes the provenance identity of the already merged TIR × Secret-of-a-Half dependency programme. It does not add a second phase engine and it does not change any scientific claim status.

The canonical merged parents are:

- PhaseNav runtime parent: `54f65f2ca7d35cdd98f0ab8984cc1a8d74444a96`
- NOEMA dependency/provenance parent: `42a0a8916e81ca27f2213bf0f28538f046c2e89a`
- TIR merged formalism parent: `df8a6e1321ecf2e2c8819f4e9d5ec7d4f997d170`
- Secret-of-a-Half merged v0.7 parent: `a1b0aeba192766163893fab1468b8f9cd9b8853b`

A change to any of these parents changes the source-state digest and therefore changes every source/path routing identity derived from that state.

## Three vector layers

### 1. Source-anchor vectors

Each exact repository+commit anchor is routed by the existing native `CanonicalConceptState.from_id` mechanism into `T^36`.

These vectors identify executable/provenance states. They do not assert that the content of a source is mathematically or physically true.

### 2. Dependency-node vectors

The v0.7 typed dependency nodes keep their existing native PhaseNav vectors and epistemic statuses. No node is re-embedded by a separate algorithm.

In particular:

- `HALF`: `EXACT`
- `KAPPA`: `PROJECT_DERIVED_EXACT_ALGEBRA`
- `ROLE_ROUTER_HABC`: `STRUCTURAL_ROLE_ROUTING_PASS`
- `TIR_SLOT_BINDING`: `OPEN`
- `SOH_C004`: `OPEN`
- `SOH_C005`: `OPEN`
- `TIR_NEUTRON_EDM`: `PHYSICAL_FAIL`
- `COLLATZ_STOPPING_ORIENTATION`: `RETROSPECTIVE_CANDIDATE_NEEDS_PROSPECTIVE_TEST`

### 3. Path vectors

Every declared dependency edge receives a deterministic 36D routing identity bound to:

- source-state digest;
- source node;
- target node;
- relation label;
- edge status.

A path vector is explicitly `EDGE_METADATA_ONLY`. It is not a theorem, proof, causal law, or physical validation of the edge.

## Dimensional invariant

The intrinsic recovered TIR coefficient state remains

`(h,a,b,c) in Z^4`.

The PhaseNav routing envelope remains

`T^36`.

Therefore:

`intrinsic_state != routing_envelope`.

The 36D vector is forbidden as a hidden source of intrinsic coefficients.

## Proof firewall

Vectorization cannot promote a scientific status.

The closure receipt explicitly forbids:

- `vectorization -> scientific promotion`;
- `path vector -> edge truth`;
- `source vector -> source correctness`;
- measured mass as a derivation parent;
- measured Yukawa coupling as a derivation parent;
- coefficient-enriched vectors as parents of the coefficient derivation;
- OPEN/FAILED -> EXACT without an independent external receipt.

Consequently `SOH_C004`, `SOH_C005`, the physical TIR slot binding, the common-likelihood debt, the neutron-EDM failure, and the prospective Collatz validation remain exactly where their ledgers place them.

## Receipt

`TIR_HALF_CLOSURE.receipt()` emits:

- exact source repositories and commit SHA values;
- source-state SHA-256;
- all source-anchor 36D vectors and vector hashes;
- all dependency-node 36D vectors, hashes, statuses and open conditions;
- all path 36D vectors, hashes and edge metadata;
- blocked-node set;
- proof/vectorization firewall;
- one deterministic closure SHA-256.

`TIR_HALF_CLOSURE.noema_projection()` emits only the closure/provenance state required for append-only NOEMA writeback and explicitly declares both scientific promotion and memory mutation as `NOT_PERFORMED` by the reader.

## Promotion rule

This closure can be promoted as a software/provenance canon only after the exact-head PhaseNav test suite and explicit closure-vector gate pass. Scientific claims remain independently gated by their mathematical/physical receipts.
