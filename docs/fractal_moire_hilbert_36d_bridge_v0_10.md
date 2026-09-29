# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.10

Status: CANDIDATE_ONLY / IMMUTABLE_ARPL_SOURCE_PINNING / PROVENANCE_FIREWALL
Date: 2026-09-26

## 1. Purpose

v0.10 does not add a new mathematical theorem.

It hardens provenance for every 36D packet that consumes an ARPL-derived source
surface.

Earlier versions allowed symbolic witness strings such as

    on-primes://...

Those strings are useful semantic labels but are not immutable source pins.

v0.10 therefore requires repository, branch, commit SHA and source-file ledger
for every ARPL-derived claim.

## 2. ARPL-derived surfaces currently recognized

The provenance gate activates when a packet uses any of:

ARPL_HIT_OVERLAP_GRAM

ARPL_ODOMETER_CARRY

ARPL_PROCYCLIC_ODOMETER_LIMIT

The mathematical semantics of those surfaces remain defined by v0.5-v0.9.

## 3. Required immutable source fields

Every ARPL-derived packet must include:

- arpl_source_repository;
- arpl_source_branch;
- arpl_source_commit_sha;
- arpl_source_files;
- arpl_source_pin_witness_ref.

For the current project source,

\[
\boxed{
\text{arpl_source_repository}
=
\text{AdrianLipa90/On-Primes}.
}
\]

The commit SHA must be exactly 40 hexadecimal characters.

The source-file ledger must be non-empty.

## 4. Current repaired source pin

The current repaired bridge snapshot is:

Repository:

AdrianLipa90/On-Primes

Branch:

integrate/arpl-fractal-orbital-bridge-v0.2-20260926-r4

Head at validation:

\[
\boxed{
22171349917c97392db7d35605f15be1441fa5bb
}
\]

At the immediate post-port compare against

feat/arithmetic-relational-phase-law-v0.1

the branch state was:

ahead_by = 6

behind_by = 0.

## 5. Why the earlier pin is superseded

The earlier v0.8 PhaseNav receipt pinned

\[
705872f11aaf8b933ab3b713fb10443326fde62b.
\]

Subsequent branch audit found two independent problems:

1. the old integration branch had diverged from its active parent;
2. its bridge module used Fraction without importing it.

Therefore this SHA is now a known superseded source pin for ARPL bridge
promotion.

v0.10 rejects that exact SHA.

Historical documents may retain it as provenance, but new ARPL-derived
promotion packets may not use it.

## 6. Parent movement does not rewrite an immutable pin

The active parent branch may continue to move after a candidate snapshot is
created.

That does not mutate the pinned commit.

A packet therefore distinguishes:

- immutable source snapshot;
- branch label at creation;
- current moving parent state.

The commit SHA is authoritative for reproducibility.

A later synchronization should create a new source pin rather than silently
changing the old one.

## 7. Source-file ledger

At minimum, the current ARPL bridge source pin should identify the exact files
consumed by the claim.

Examples include:

- proofs/ARPL_FRACTAL_ORBITAL_BLOCK_COCYCLE_BRIDGE_V0_2.md;
- proofs/ARPL_FRACTAL_ORBITAL_HILBERT_BRIDGE_V0_2.md;
- receipts/ARPL_FRACTAL_ORBITAL_BLOCK_COCYCLE_BRIDGE_V0_2.md;
- src/on_primes/fractal_orbital_bridge.py;
- tests/test_fractal_orbital_bridge.py.

The ledger is not a substitute for the commit SHA. It states which parts of
the immutable snapshot are semantically upstream.

## 8. Separation from hosted CI

An immutable source pin proves only source identity.

It does not prove that hosted CI ran.

Therefore source pinning and CI status remain separate fields.

No packet may infer

HOSTED_CI = PASS

from a valid SHA alone.

## 9. Fail-closed rules

Reject ARPL-derived packets with:

- missing repository;
- repository other than AdrianLipa90/On-Primes;
- missing branch;
- malformed/non-40-hex SHA;
- empty source-file ledger;
- empty source pin witness;
- a SHA in the explicit superseded-pin denylist.

Non-ARPL packets do not require these fields.

## 10. Promotion ledger

PASS at provenance-contract level:

- ARPL source surfaces detected explicitly;
- immutable 40-hex source pin required;
- source-file ledger required;
- moving branch separated from immutable commit;
- known broken/stale pin explicitly rejected;
- hosted CI remains a separate evidence channel.

OPEN:

- hosted CI for the repaired On-Primes r4 snapshot;
- later source resynchronization if the parent continues moving;
- physical ARPL interpretation;
- physical 36D calibration.

Current repaired source pin:

\[
\boxed{
22171349917c97392db7d35605f15be1441fa5bb
}
\]

canon_allowed = false.
