# PhaseNav Memory Anti-Entropy Synchronization v0.1

Status: `IMPLEMENTED CANDIDATE / APPEND_ONLY / CHYBA / canon_allowed=false`

Date: 2026-09-20

## Purpose

The memory-exchange protocol already defines immutable envelopes, ACKs, causal
lineage and portable lineage bundles. Anti-entropy adds peer synchronization
without introducing last-writer-wins semantics.

The protocol is set reconciliation:

`local committed items <-> remote committed items`.

It does not synchronize by replacing a remote database image.

## Four-stage exchange

The protocol deliberately separates discovery from payload transfer.

1. **Inventory summary**
   - envelope/ACK counts;
   - ledger commitment;
   - 256 two-hex-digit bucket roots;
   - no payloads.

2. **Divergent bucket manifests**
   - only buckets whose roots/counts differ;
   - content-addressed envelope/ACK descriptors;
   - still no payloads.

3. **Delta plan**
   - sender-only envelope ids;
   - sender-only ACK ids;
   - receiver-only ids retained explicitly;
   - exact sender/receiver inventory commitments.

4. **Delta apply**
   - only missing envelope/ACK packets are transferred;
   - causal preflight occurs on a cloned ledger;
   - receiver inventory commitment is rechecked before mutation;
   - append-only apply follows only after preflight succeeds.

## Bucket geometry

Envelope and ACK commitments already contain 64 hexadecimal digest characters.
The first two digest characters select one of 256 buckets.

For bucket `b`:

`R_b = SHA256(canonical(sorted envelope descriptors, sorted ACK descriptors))`.

Peers compare `R_b` and counts first. Equal buckets require no manifest and no
payload traffic.

This is a deterministic content partition, not a semantic partition. It does
not infer meaning from hash locality.

## Inventory commitments

Two commitments are separated:

- `content_root_sha256`: depends only on committed ledger content;
- `inventory_sha256`: additionally binds the declared peer/node label.

Therefore two peers with identical memory have equal content roots even though
their inventory packet commitments differ.

Node labels remain unsigned protocol labels:

`authentication = UNSIGNED_CONTENT_COMMITMENT`.

## No last-writer-wins

A remote-only item is never deleted merely because the sender lacks it.

The delta plan explicitly carries:

- `receiver_only_envelope_ids`;
- `receiver_only_ack_ids`.

Claims remain:

`delete_receiver_only_items = false`

and

`overwrite_receiver_items = false`.

A content-addressed id collision with different metadata fails closed.

## Causal apply

Envelope packets are transferred in parent-friendly sequence/id order.

Before mutation the receiver:

1. validates every packet commitment;
2. rebuilds every envelope from its canonical fields;
3. verifies ACK structure;
4. clones the current ledger;
5. stages the full delta into the clone;
6. rejects orphan parents, generation discontinuity, bad sequence or ACK
   mismatch;
7. only then appends to the real ledger.

This prevents a malformed batch from partially mutating the receiver.

## Stale-plan protection

The delta binds the exact receiver inventory used during planning.

If the receiver changed independently before apply:

`current_inventory_sha256 != planned_receiver_inventory_sha256`

then the delta is rejected and must be replanned.

The one exception is exact network replay after successful application. If every
delta item is already present with identical content, apply returns
`ALREADY_APPLIED` and creates nothing.

## Directionality

One delta is directional:

`sender -> receiver`.

Bidirectional convergence is two independent append-only reconciliations:

`A -> B`

followed by

`B -> A`.

This prevents a hidden symmetric merge operator from acquiring overwrite
authority.

## Security and authority boundary

Anti-entropy grants no:

- deletion authority;
- overwrite authority;
- canon promotion;
- production execution authority;
- repository mutation authority;
- authenticated node identity.

The protocol transports committed shared cognition only.

## PASS

The implementation establishes:

- deterministic bucketed inventory summaries;
- payload-free divergence discovery;
- manifest-to-inventory binding;
- minimal sender-only delta planning;
- explicit receiver-only preservation;
- causal preflight before mutation;
- stale-plan rejection;
- exact-retry idempotency;
- no deletion or overwrite;
- deterministic content convergence when the receiver has no independent extra
  state.

## OPEN / NOT CLAIMED

- cryptographic peer identity authentication;
- encrypted transport;
- Byzantine quorum/consensus;
- concurrent transactional persistence across processes;
- garbage collection/tombstone semantics;
- automatic live-NOEMA synchronization;
- physical nonlocal signalling;
- canon promotion.
