# Git Blob Identity × Native CIEL Semantic Observation Canon v0.11

## Why this layer exists

v0.9 and v0.10 remove arbitrariness from repository, tree and blob identity routing by using native Git object digests. That solves identity and provenance. It does **not** solve semantic locality: cryptographic digest geometry is deliberately avalanche-like, so proximity of two Git hashes cannot be interpreted as similarity of meaning.

Therefore the canon separates two independent layers:

1. **identity/provenance** — exact Git object digest and digest-native PhaseNav T^36 routing identity;
2. **meaning observation** — native CIELingo × Lingophysics × PhaseNav × MemoryFabric / ASIR state returned by the pinned semantic runtime and bound by receipts.

`Git identity vector != semantic embedding`.

## Native semantic parent

The semantic layer is not invented in this repository. It is pinned to the existing cross-repository runtime compatibility contract:

- `AdrianLipa90/Ciel-Semantic-Model-` release `0.8.1`;
- semantic runtime code commit `0a4a1b57217fc876ed0535829686cfed8ccd0d8f`;
- `AdrianLipa90/cielingo-canon` runtime commit `ab097f99d46eb446836833ac90b2bc3cf9d219e1`;
- AUX request `CIEL_AUX_PHASE_MEMORY_REQUEST_V2`;
- AUX packet `CIEL_AUX_PHASE_MEMORY_PACKET_V3`;
- native semantic state `CIEL_NATIVE_SEMANTIC_STATE_V1`;
- exactly 36 phase dimensions;
- native spinor `4pi` phase convention;
- exactly 12 MemoryFabric lanes.

The CIEL runtime already preserves independent ontic and epistemic statuses, semantic mass, context scalar, node/edge phase states, provenance, MemoryFabric membership/evidence and graph bindings. This v0.11 layer is only a binding boundary; it is not a second semantic engine.

## Exact-byte binding

A text semantic observation is admissible only when the supplied raw bytes reproduce the declared native Git blob object id using Git's own object-domain header:

`blob <byte_length>\0<raw_bytes>`.

The same raw bytes also receive a SHA-256 evidence digest in the semantic receipt.

The repository commit and blob must use the same Git object format (SHA-1 or SHA-256). Mixed object formats fail closed.

## Context is part of semantic provenance

A semantic observation is not assumed to be an intrinsic, context-free vector of a file. The receipt binds:

- exact repository head commit;
- exact blob digest and raw-byte SHA-256;
- declared text encoding and language;
- AUX request SHA-256;
- AUX packet receipt SHA-256;
- native semantic binding SHA-256;
- semantic graph / ASIR binding SHA-256;
- MemoryFabric read-set SHA-256;
- NOEMA receipt SHA-256;
- external-ACK state;
- exact semantic and CIELingo runtime commits.

Consequently the same blob may have multiple contextual semantic observations while preserving one immutable Git identity vector.

## No arbitrary file-semantic vector

This layer deliberately does **not** define a single `intrinsic_file_semantic_vector`.

It also forbids these fallbacks:

- Git identity vector used as semantic embedding;
- hash distance interpreted as semantic similarity;
- repository/file/path/extension labels used as semantic parents;
- averaging ASIR nodes into one vector without an upstream canonical operator;
- replacing a missing semantic receipt with filename heuristics;
- treating binary/non-text bytes as text merely to force semantic coverage.

If no valid native semantic observation exists, the correct status is unavailable/not-run rather than a fabricated semantic vector.

## Binary/non-text objects

v0.11 is a text-semantic binding contract. A blob that cannot be decoded in the declared encoding fails text-semantic binding. It retains its Git identity vector. It receives no invented text semantics.

A future binary semantic layer requires its own native engine and receipt contract; it must not be inferred from extension or MIME guesses.

## Validation

Focused validation: `PASS_8_OF_8`.

The tests verify:

- native Git blob-domain hashing;
- exact-byte/blob binding;
- modified bytes cannot reuse an observation identity;
- invalid text encoding has no semantic fallback;
- commit/blob Git object formats must match;
- changing semantic context receipts leaves identity vector unchanged but changes the observation receipt;
- pinned native CIEL runtime/schema/36D/4pi/12-lane contract;
- all semantic-arbitrariness firewalls remain closed.

## Execution state

The private repository-head identity snapshot is complete for 39 real heads. The complete 39-checkout tree/blob execution remains `NOT_RUN`. Accordingly, private blob semantic observations are also `NOT_RUN`: the exact blob inventory has not yet been executed, and those bytes have not been passed through the pinned native CIEL semantic runtime with frozen MemoryFabric/NOEMA provenance.

No missing execution is substituted with path/name/hash heuristics.

## Promotion boundary

A valid semantic observation proves only that one exact blob byte sequence was processed under one receipted native semantic context. It does not establish scientific truth, SOURCE/canon promotion, repository correctness or universal context-free meaning.