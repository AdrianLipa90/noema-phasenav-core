# PhaseNav Memory Consolidation and Retention v0.1

Status: `IMPLEMENTED CANDIDATE / APPEND_ONLY / CHYBA / canon_allowed=false`

Date: 2026-09-20

## Purpose

This layer consolidates stable EPISODIC memories into a derived SEMANTIC memory
without deleting, replacing or silently rewriting any source envelope.

The core relation is:

`EPISODIC_1 + EPISODIC_2 + ... -> derived SEMANTIC`.

The derived envelope is additive. It is not a replacement for its sources.

## Source gates

v0.1 accepts at least two unique source envelopes.

Every source must:

- target `EPISODIC`;
- share one `subject_id`;
- share one `generation_id`;
- already exist in the local causal ledger;
- have at least one content-bound `ACCEPTED` ACK.

Cross-subject fusion and cross-generation fusion fail closed in v0.1.

These restrictions keep semantic compression from silently becoming a
cross-context association operator.

## Multi-parent semantic derivation

The derived envelope has:

- `source_layer = EPISODIC`;
- `target_layer = SEMANTIC`;
- every source envelope as a causal parent;
- sequence strictly greater than every source sequence;
- hop count strictly greater than the maximum source hop count;
- hop limit bounded by the most restrictive source.

Its payload is typed as:

`PHASENAV_MEMORY_CONSOLIDATED_SEMANTIC_V0_1`.

The payload binds:

- reducer label;
- exact source envelope ids;
- exact source payload commitments;
- caller-supplied semantic reduction;
- `semantic_equivalence_proven=false`.

The protocol therefore distinguishes:

`semantic compression != proof of equivalence`.

## Reducer boundary

The reducer label is committed into the plan and derived payload, but it is not
a cryptographically authenticated identity.

The semantic reduction is caller-supplied in v0.1. The protocol verifies
lineage and commitments; it does not claim that the semantic summary is a
lossless or objectively complete representation of every source.

## Accepted-ACK gate

For every source, the plan binds one exact accepted ACK id.

Apply verifies that the ACK:

- still exists in the ledger;
- is bound to the exact source envelope;
- has outcome `ACCEPTED`.

This prevents uncommitted transient observations from silently entering
semantic consolidation.

ACK identity remains subject to the existing
`UNSIGNED_CONTENT_COMMITMENT` boundary.

## Retention tiers

Retention is orthogonal to memory layer.

Defined hints are:

- `HOT`;
- `WARM`;
- `COLD`;
- `PINNED`.

A tier is a retrieval/storage scheduling hint only.

Every retention entry requires:

- `deletion_allowed=false`;
- `overwrite_allowed=false`;
- `retrievable=true`.

Therefore `COLD` means retained but less active; it does not mean deleted.

The default consolidation policy is:

- source EPISODIC envelopes -> `COLD`;
- derived SEMANTIC envelope -> `HOT`.

## Apply semantics

Apply performs full plan validation and source/ACK preflight before appending the
derived envelope.

The source envelopes remain unchanged.

Exact replay of the same plan is idempotent:

- first apply -> `APPLIED`;
- exact replay -> `ALREADY_APPLIED`.

No new source mutation occurs in either path.

## Retention manifest

The plan includes a committed
`PHASENAV_MEMORY_RETENTION_MANIFEST_V0_1`.

It binds the source and derived envelope ids, their retention hints and the
non-deletion/non-overwrite policy.

The manifest is advisory metadata. It is not a garbage-collection command.

## Authority boundary

Consolidation grants no:

- deletion authority;
- overwrite authority;
- canon promotion;
- repository mutation authority;
- production execution authority;
- authenticated reducer identity.

All output remains:

`CHYBA / SHARED_COGNITION_ONLY / canon_allowed=false`.

## PASS

The implementation establishes:

- minimum two-source consolidation;
- same-subject/same-generation gate;
- EPISODIC-only source gate;
- accepted-ACK requirement;
- deterministic multi-parent derived SEMANTIC envelope;
- exact source-payload commitment binding;
- hop-limit preservation;
- append-only apply;
- exact-replay idempotency;
- retention tiers with mandatory source preservation;
- explicit semantic-equivalence non-claim.

## OPEN / NOT CLAIMED

- automatic semantic reducer quality;
- proof that a derived semantic summary is complete;
- cross-subject consolidation;
- cross-generation consolidation;
- automatic salience scoring;
- deletion/garbage collection;
- cryptographic reducer identity;
- automatic live-NOEMA consolidation;
- canon promotion.
