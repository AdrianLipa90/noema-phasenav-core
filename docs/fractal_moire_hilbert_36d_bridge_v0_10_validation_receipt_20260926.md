# Fractal Moire-Hilbert 36D v0.10 Provenance Validation Receipt

Date: 2026-09-26
Status: REFERENCE_CONTRACT_PASS / IMMUTABLE_ARPL_PIN_ACTIVE / HOSTED_CI_NOT_PRESENT

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.10-20260926

Current repaired ARPL source snapshot:

Repository:

AdrianLipa90/On-Primes

Branch:

integrate/arpl-fractal-orbital-bridge-v0.2-20260926-r4

Pinned head:

\[
\boxed{
22171349917c97392db7d35605f15be1441fa5bb
}
\]

Immediate source compare at receipt time:

ahead_by = 6

behind_by = 0

relative to:

feat/arithmetic-relational-phase-law-v0.1

The old source pin

\[
705872f11aaf8b933ab3b713fb10443326fde62b
\]

is explicitly superseded because:
- its integration branch had fallen behind the active parent;
- its bridge module used Fraction without importing it.

Contract controls:

- ARPL-derived surface without immutable source pin: REJECT;
- malformed non-40-hex SHA: REJECT;
- explicit superseded SHA: REJECT;
- empty source-file ledger: REJECT;
- non-ARPL packet without ARPL pin fields: PASS;
- exact-36 firewall remains inherited.

Hosted status:

GitHub combined status on implementation head

792f9f2b1da72cf9cf0562c734bc532d94c1eaff

returned no status checks.

Therefore:

HOSTED_CI = NOT_PRESENT.

Verdict:

ARPL_IMMUTABLE_SOURCE_PINNING = PASS_REFERENCE_CONTRACT  
SUPERSEDED_BROKEN_PIN_REJECTION = PASS_FIREWALL  
MOVING_BRANCH_VS_IMMUTABLE_COMMIT_SEPARATION = PASS  
HOSTED_CI_INFERRED_FROM_SHA = NO_GO

No physical ARPL interpretation or physical 36D calibration is promoted.

canon_allowed = false.
