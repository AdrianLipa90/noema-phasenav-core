# Fractal Moire-Hilbert 36D v0.11 ARPL Heterogeneous Matrix Validation Receipt

Date: 2026-09-26
Status: REFERENCE_CONTRACT_PASS / SOURCE_OWNED_RECTANGULAR_GRAM / HOSTED_CI_NOT_PRESENT

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.11-20260926

Pinned ARPL source:

Repository:
AdrianLipa90/On-Primes

Branch:
integrate/arpl-clock-fibre-matrix-gram-v0.1-20260926

Commit:

\[
\boxed{
8781f4a685257eced538daa7462ec4fc48093a6b
}
\]

Immediate compare against its repaired r4 base:

ahead_by = 11  
behind_by = 0

Pinned Orbital heterogeneous theorem receipt:

\[
\boxed{
cbf5d83a40ebe4e090ffad0749418dbac732f25b
}
\]

## h=6 contract control

For

\[
P=\{5,7,11,13,19\},
\]

the validator-derived periods are

\[
\boxed{
(2,3,5,6,9).
}
\]

The common finite clock is

\[
\boxed{
L=90.
}
\]

The sum of local fibre dimensions is

\[
\boxed{
25.
}
\]

Neither \(90\) nor \(25\) is identified with the PhaseNav routing dimension
\(36\).

## Pairwise rank network

The exact rank rule is

\[
r_{ij}
=
\gcd(e_i,e_j).
\]

For the control support this gives

\[
\boxed{
R=
\begin{pmatrix}
2&1&1&2&1\\
1&3&1&3&3\\
1&1&5&1&1\\
2&3&1&6&3\\
1&3&1&3&9
\end{pmatrix}.
}
\]

These are ranks of rectangular source-owned cross-Gram maps.

## Finite-support network visibility

The validator-derived hidden dimensions are

\[
\boxed{
(0,0,4,2,6).
}
\]

The upstream source reverse control also shows that after extending to the first
15 active h=6 channels through p=79, the original P5 hidden dimensions become

\[
\boxed{
(0,0,0,0,0).
}
\]

Therefore:

FINITE_SUPPORT_HIDDEN = EXACT_SOURCE_PROPERTY.

PERSISTENT_INFINITE_SUPPORT_HIDDEN = NOT_ESTABLISHED.

## Intertwiner contract

The subtype requires independently supplied source residuals for

\[
A_{ef}U_f-U_eA_{ef}
\]

and

\[
A_{ef}\Delta_f-\Delta_eA_{ef}.
\]

Residuals above tolerance are rejected.

Full rectangular matrices remain upstream under

UPSTREAM_WITNESS_ONLY.

## Hosted status

GitHub combined status on implementation head

21b0c4cd611f0d8056fea4ac9d70fcddd234ffbc

returned no status checks.

Therefore:

HOSTED_CI = NOT_PRESENT.

## Verdict

ARPL_CLOCK_FIBRE_MATRIX_GRAM_36D_SOURCE_SUBTYPE = PASS_REFERENCE_CONTRACT  
ARPL_RECTANGULAR_GCD_RANK_LEDGER = PASS_EXACT_STRUCTURE  
ARPL_FINITE_NETWORK_HIDDEN_LEDGER = PASS_EXACT_STRUCTURE  
FIBRE_DIMENSION_SUM_EQUALS_36D = NO_GO  
COMMON_CLOCK_SIZE_EQUALS_36D = NO_GO  
FINITE_HIDDEN_IMPLIES_INFINITE_HIDDEN = NO_GO

Physical orbital meaning and empirical calibration remain OPEN.

canon_allowed = false.
