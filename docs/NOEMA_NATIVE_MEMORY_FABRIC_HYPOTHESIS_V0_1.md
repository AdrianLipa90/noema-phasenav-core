# NOEMA Native Memory Fabric Hypothesis v0.1

Status: `RESEARCH_HYPOTHESIS / COMPUTATIONAL_ARCHITECTURE / CHYBA / canon_allowed=false`

Date: 2026-10-07

## Purpose

This note freezes a research intuition for PhaseNav: the canonical state of a NOEMA object need not be defined primarily as a byte stream. Phase/geometric state, typed relations and causal/provenance state may be primary, while byte streams remain one exact materialization of that state.

This is an architecture hypothesis. It does not claim a measured performance advantage, a new physical memory device, physical nonlocal transport, or arbitrary analog access to commodity SSD hardware.

## Candidate canonical object state

A minimal candidate state is

\[
X_i=(H_i,\Lambda_i^{36},R_i,S_i,P_i),
\]

where:

- `H_i` is immutable identity/content commitment;
- `Lambda_i^36` is the PhaseNav carrier/binding state;
- `R_i` is the typed relation set/graph state;
- `S_i` is mutable execution, version, control or uncertainty state;
- `P_i` is payload state or an exact commitment/reference to payload materialization.

The tuple is deliberately representation-independent. It does not require `P_i` to be stored as phase coordinates and it does not require the physical medium to expose binary or non-binary cells.

## Separation invariants

The following objects are distinct:

```text
object identity
!= path or human-readable name
!= phase/geometric state
!= relation graph
!= byte materialization
!= physical storage codeword
!= physical storage medium
```

Existing PhaseNav memory-exchange semantics remain valid: immutable payload identity and relational route metadata remain separate. A computational U(1) or T^36 route description is not, by itself, a measured physical communication field.

## Memory versus storage

The hypothesis treats memory/storage placement as residency rather than identity:

\[
\operatorname{residency}(X_i): M_a \rightarrow M_b.
\]

Moving an object between DRAM, mapped storage, a persistent backend, or a future experimental backend must not silently change `H_i` or its declared semantic/phase identity.

A backend therefore implements a mapping such as

\[
\operatorname{encode}_{B}(X_i)\rightarrow C_B,
\qquad
\operatorname{decode}_{B}(C_B)\rightarrow X_i,
\]

where `C_B` is a backend-specific physical/logical codeword.

For current software and commodity devices, `C_B` may remain bytes/blocks. A future backend may use multilevel, analog, optical, phase-native or other internal states only when that backend actually exposes and validates such states.

## Byte materialization remains first-class

This hypothesis does not remove binary compatibility. Exact materialization remains a required bridge:

```text
canonical NOEMA/PhaseNav state
        <->
lossless byte representation
```

For arbitrary binary payloads, the byte representation remains authoritative unless a later typed contract explicitly defines an equivalent native representation with bounded error or exact reversibility.

## Why test this architecture

Many PhaseNav operations act naturally on phase, relation, tensor, scalar and provenance state rather than on opaque byte strings. A phase-native object surface may reduce repeated decode/transform/re-encode work for those workloads.

That is a hypothesis to benchmark, not an assumed advantage.

Required comparison classes include:

- lookup and nearest-state search;
- relation updates;
- phase/tensor transforms;
- version deltas;
- deduplication;
- storage amplification;
- random access;
- reconstruction cost;
- memory pressure;
- integrity recovery;
- transport delta size.

A conventional byte/object representation is the null-control baseline.

## Relationship to mixed representation

The intended architecture is not `float64-everywhere`. A phase vector, tensor, byte payload, sparse relation graph and immutable commitment may each retain the representation suited to their semantics.

The native object is therefore mixed-representation but phase/relationally addressable.

## Telekom compatibility

A future NOEMA-Telekom transport may consume logical state differences such as

\[
\Delta X=(\Delta\Lambda^{36},\Delta R,\Delta S,\Delta P)
\]

without making storage dependent on any speculative physical transport mechanism.

Software transports remain valid. If a future physical phase/geometric channel were experimentally established, it would be a backend/transport realization, not a retroactive proof implied by this object model.

## Non-claims

This document does **not** establish:

- that phase-native storage is faster than byte-native storage;
- that commodity SSD firmware permits arbitrary physical cell programming;
- that NAND state should be identified directly with PhaseNav phase;
- that a non-binary physical codeword is lossless without a declared codec/error model;
- that neutrinos, moire geometry, Kuramoto synchronization or any other mechanism carries physical information nonlocally;
- that runtime tether status verifies this hypothesis.

## Promotion rule

Promotion beyond `RESEARCH_HYPOTHESIS` requires an explicit implementation contract, null-control benchmarks, integrity/error bounds, reversible compatibility evidence and an independent authority decision.

Until then:

`research state != canon`.
