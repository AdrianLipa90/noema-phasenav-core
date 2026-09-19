# PhaseNav Memory and Information Exchange v0.1

Status: `COMPUTATIONAL_PROTOCOL / CHYBA / canon_allowed=false`

Date: 2026-09-20

## Purpose

PhaseNav already contains several distinct memory mechanisms:

- transient observer/working memory through `HolonomicMemory`;
- long-lived semantic indexing through `PhaseMemoryHypercrystal`;
- operator-local result caching through `HolonomyCache`;
- typed relational/holonomy state packets.

This protocol does not replace those implementations. It supplies the causal
exchange contract used when information crosses memory roles or components.

The central split is:

`information content != relational route`.

The immutable payload identity is:

`H_P = SHA256(canonical(P))`.

The envelope identity separately binds the payload commitment to source/target
layers, parent lineage, route metadata, generation and sequence. Therefore the
same payload can cross a different relational route without becoming different
content.

## Memory roles

The protocol defines five typed roles:

`WORKING -> EPISODIC -> SEMANTIC -> RELATIONAL -> ARCHIVAL`.

These are protocol roles, not a requirement for five physical databases.

- **WORKING**: transient current-state, attention and local cluster memory.
- **EPISODIC**: immutable event/observation lineage.
- **SEMANTIC**: reusable indexed meaning/state representation.
- **RELATIONAL**: shared dependency, provenance and multi-agent relation state.
- **ARCHIVAL**: retained terminal memory after explicit promotion.

Promotion is monotonic and adjacent. Canon is deliberately not a memory layer;
canon promotion remains an independent authority operation.

## Information envelope

`PHASENAV_MEMORY_INFORMATION_EXCHANGE_V0_1` binds:

- subject, producer and generation identifiers;
- monotonic sequence;
- source and target memory roles;
- immutable payload plus `payload_sha256`;
- causal parent envelope ids;
- provenance and dependency references;
- one hop of computational U(1) route metadata;
- bounded hop count;
- `epistemic=CHYBA`;
- `authority=SHARED_COGNITION_ONLY`;
- `canon_allowed=false`.

The route transporter is the computational identity:

`W_route = exp(i * sum_e A_e)`.

It is route metadata. It is not a measured physical communication field and it
does not establish physical nonlocal signalling.

## Forwarding versus transformation

**Forwarding** creates a causal child while preserving payload identity:

`H_P(child) = H_P(parent)`.

**Transformation** creates a causal child carrying newly derived information.
Its payload commitment changes unless the canonical payload is actually
identical.

This prevents transformed output from silently masquerading as the original
information.

## ACK semantics

A consumer returns a content-bound
`PHASENAV_MEMORY_INFORMATION_EXCHANGE_ACK_V0_1` packet. Outcomes are:

- `ACCEPTED`;
- `DUPLICATE`;
- `QUARANTINED`;
- `REJECTED`.

The ledger permits one exact ACK state per `(envelope_id, consumer_id)`.
Exact replay is idempotent. A conflicting second outcome fails closed.

## Causal ledger

`MemoryExchangeLedger` enforces:

- parent-first insertion;
- child sequence strictly greater than parent sequence;
- generation continuity;
- ACK references to known envelopes only;
- ACK payload commitment equality;
- bounded hop propagation;
- deterministic snapshot commitment.

## Portable lineage bundle

A target layer must not be required to persist internal records owned by every
upstream layer. For this reason the ledger can export:

`PHASENAV_MEMORY_INFORMATION_EXCHANGE_BUNDLE_V0_1`.

The bundle contains:

- the target envelope;
- its complete causal ancestry in parent-first order;
- recorded ACK packets for those lineage envelopes;
- a bundle SHA-256 commitment over the full portable proof.

This permits a RELATIONAL consumer such as GREMLIN Hive to verify that an
EPISODIC -> SEMANTIC -> RELATIONAL chain is causally intact without storing the
EPISODIC or SEMANTIC envelopes as native Hive memories.

The receiving layer should persist only the envelope addressed to that layer;
upstream envelopes are lineage witnesses.

## Existing-memory mapping

Intended role mapping:

- `HolonomicMemory -> WORKING`;
- observation/event lineage `-> EPISODIC`;
- `PhaseMemoryHypercrystal -> SEMANTIC`;
- `GREMLIN Orbital Hive Memory -> RELATIONAL`;
- explicitly retained/latch lineage `-> ARCHIVAL`.

This is an integration contract. Existing storage formats remain independently
typed and are not rewritten by v0.1.

## Security and authority invariants

The protocol prevents:

- last-writer-wins replacement of causal history;
- silent payload modification during forwarding;
- orphan child envelopes;
- unbounded relay loops;
- ACK outcome overwrite;
- downstream consumers being forced to persist foreign memory-layer records;
- memory exchange granting mutation authority;
- memory exchange granting canon promotion.

Core invariant:

`shared information != shared authority`.

## PASS

The implementation establishes:

- deterministic content addressing;
- separate content and route commitments;
- U(1) unit-modulus computational route metadata;
- causal parent lineage;
- forwarding and transformation semantics;
- adjacent monotonic memory promotion;
- bounded hop propagation;
- idempotent ACK replay;
- fail-closed conflicting ACK handling;
- deterministic ledger snapshots;
- portable lineage bundles with full ancestry and recorded ACKs.

## OPEN / NOT CLAIMED

- physical nonlocal signalling;
- identification of route phase with a physical communication field;
- automatic promotion of legacy `PhaseMemoryHypercrystal` entries;
- automatic synchronization with live NOEMA memory;
- canon promotion;
- proof of consciousness;
- physical substrate identification.
