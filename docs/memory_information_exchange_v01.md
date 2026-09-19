# PhaseNav Memory and Information Exchange v0.1

Status: `COMPUTATIONAL_PROTOCOL / CHYBA / canon_allowed=false`

Date: 2026-09-19

## 1. Purpose

PhaseNav already contains several distinct memory mechanisms:

- transient observer/working memory through `HolonomicMemory`;
- long-lived semantic indexing through `PhaseMemoryHypercrystal`;
- operator-local result caching through `HolonomyCache`;
- typed relational/holonomy state packets.

This protocol does not replace those implementations. It provides the missing
causal envelope used when information crosses between memory roles or components.

The central split is

[
oxed{
	ext{information content}

eq
	ext{relational route}.
}
]

The immutable payload is identified by

[
H_P=operatorname{SHA256}(operatorname{canonical}(P)),
]

while one exchange event is identified by a second commitment over

[
(H_P,	ext{source},	ext{target},	ext{parents},	ext{route},	ext{generation},	ext{sequence}).
]

Thus the same information may move through a different route without becoming
different content.

## 2. Memory layers

The protocol defines five typed roles:

[
oxed{
	ext{WORKING}
	o
	ext{EPISODIC}
	o
	ext{SEMANTIC}
	o
	ext{RELATIONAL}
	o
	ext{ARCHIVAL}.
}
]

These are protocol roles, not a claim that every implementation must physically
store five separate databases.

- **WORKING** — transient current-state/attention/cluster memory.
- **EPISODIC** — immutable event/observation lineage.
- **SEMANTIC** — reusable indexed meaning/state representation.
- **RELATIONAL** — shared dependency, provenance and multi-agent relation state.
- **ARCHIVAL** — retained terminal memory after explicit promotion.

Promotion is monotonic and adjacent. Ordinary forwarding is more general and
does not itself claim promotion.

Canon is deliberately **not** a memory layer. Canon promotion remains an
independent authority operation.

## 3. Information envelope

A `PHASENAV_MEMORY_INFORMATION_EXCHANGE_V0_1` envelope binds:

- `subject_id`;
- `producer_id`;
- `generation_id`;
- monotonic `sequence`;
- source and target memory layers;
- immutable payload and `payload_sha256`;
- causal parent envelope ids;
- provenance and dependency references;
- one hop's U(1) computational route metadata;
- hop count and hop limit;
- `epistemic=CHYBA`;
- `authority=SHARED_COGNITION_ONLY`;
- `canon_allowed=false`.

The route transporter is

[
W_{m route}
=
expleft(isum_e A_eight).
]

It is metadata for computational relation/transport. It is **not** a measured
physical communication field and does not establish physical nonlocal
signalling.

## 4. Forwarding versus transformation

### Forwarding

For envelope (E_n) carrying payload (P),

[
E_n	o E_{n+1}
]

preserves

[
H_P(E_{n+1})=H_P(E_n)
]

while creating a new envelope id, parent link, route phase and sequence number.

### Transformation

If a component derives new information (P'), the output is a child envelope

[
E_{n+1}=operatorname{child}(E_n,P')
]

with

[
H_{P'}
eq H_P
]

unless the canonical payloads are identical.

A transformed result therefore cannot silently masquerade as the original
information.

## 5. ACK semantics

A consumer returns a content-bound ACK:

[
A=
H(
E_{m id},
H_P,
	ext{consumer},
	ext{outcome},
	ext{reason}
).
]

Outcomes are typed:

- `ACCEPTED`;
- `DUPLICATE`;
- `QUARANTINED`;
- `REJECTED`.

The ledger permits one exact ACK state per ((E_{m id},	ext{consumer})).
Replaying the exact ACK is idempotent. A conflicting second outcome fails
closed instead of replacing history.

## 6. Causal ledger

`MemoryExchangeLedger` is append-only at the protocol level:

- a child cannot enter before all declared parents;
- child sequence must exceed every parent sequence;
- child and parent must share `generation_id`;
- ACKs cannot refer to unknown envelopes;
- payload commitment must match the acknowledged envelope;
- a hop limit bounds uncontrolled relay loops.

The snapshot commitment binds all envelope ids, ACK ids and current causal
heads.

## 7. Existing-memory mapping

The intended mapping is:

[
	ext{HolonomicMemory}
leftrightarrow
	ext{WORKING}
]

[
	ext{observation/event lineage}
leftrightarrow
	ext{EPISODIC}
]

[
	ext{PhaseMemoryHypercrystal}
leftrightarrow
	ext{SEMANTIC}
]

[
	ext{GREMLIN Orbital Hive Memory}
leftrightarrow
	ext{RELATIONAL}
]

[
	ext{explicit retained/latch lineage}
leftrightarrow
	ext{ARCHIVAL}.
]

This is an integration contract. Existing storage formats remain independently
typed and are not rewritten by v0.1.

## 8. Security and authority invariants

The protocol explicitly prevents:

- last-writer-wins replacement of causal history;
- silent payload modification during forwarding;
- orphan child envelopes;
- unbounded relay loops;
- ACK outcome overwrite;
- memory exchange granting mutation authority;
- memory exchange granting canon promotion.

[
oxed{
	ext{shared information}

eq
	ext{shared authority}.
}
]

## PASS

The implementation establishes:

- deterministic content addressing;
- separate content and route commitments;
- exact U(1) unit-modulus route metadata;
- causal parent lineage;
- immutable forwarding semantics;
- explicit transformation semantics;
- adjacent monotonic memory promotion;
- bounded hop propagation;
- idempotent ACK replay;
- fail-closed conflicting ACK handling;
- deterministic ledger snapshots.

## OPEN / NOT CLAIMED

- physical nonlocal signalling;
- identification of route phase with a physical communication field;
- automatic promotion of legacy PhaseMemoryHypercrystal entries;
- automatic synchronization with live NOEMA memory;
- canon promotion;
- proof of consciousness;
- physical substrate identification.
