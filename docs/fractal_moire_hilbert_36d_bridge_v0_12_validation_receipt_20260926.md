# Fractal Moire-Hilbert 36D v0.12 GRH Infinite-Visibility Validation Receipt

Date: 2026-09-26
Status: REFERENCE_CONTRACT_PASS / GRH_CONDITIONAL_VISIBILITY / HOSTED_CI_NOT_PRESENT

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.12-20260926

Parent:

formalism/fractal-moire-hilbert-36d-bridge-v0.11-20260926

Immediate compare before receipt:

ahead_by = 3  
behind_by = 0

## Provenance surfaces

Exact matrix source:

AdrianLipa90/On-Primes  
integrate/arpl-clock-fibre-matrix-gram-v0.1-20260926  
8781f4a685257eced538daa7462ec4fc48093a6b

GRH visibility frontier source:

AdrianLipa90/On-Primes  
research/arpl-infinite-clock-visibility-frontier-v0.1-20260926  
deac8af3ae12ac80f0cfab21b440b6e727c0b342

The pins are intentionally separate.

## h=6 P5 reference replay

For

\[
P=\{5,7,11,13,19\},
\]

the local periods are

\[
(2,3,5,6,9).
\]

The complete nonconstant reduced-denominator sets are

\[
\boxed{
(\{2\},\{3\},\{5\},\{2,3,6\},\{3,9\}).
}
\]

Therefore exactly eight source-prime replication certificates are required.

Independent arithmetic replay produced:

\[
(p,e_p,d,\operatorname{ord}_p(36),I_4,I_h,M_{p,d})
\]

equal to

\[
(5,2,2,1,2,4,8),
\]

\[
(7,3,3,1,2,6,9),
\]

\[
(11,5,5,5,2,2,25),
\]

\[
(13,6,2,6,2,2,8),
\]

\[
(13,6,3,6,2,2,9),
\]

\[
(13,6,6,6,2,2,72),
\]

\[
(19,9,3,9,2,2,27),
\]

\[
(19,9,9,9,2,2,27).
\]

## Finite versus infinite hidden dimensions

The exact finite P5 hidden-dimension vector remains

\[
\boxed{
(0,0,4,2,6).
}
\]

Under the GRH source-prime replication theorem, every fixed local denominator
has a positive-density replication subclass of exposure channels.

Therefore v0.12 reports the conditional complete-support vector

\[
\boxed{
(0,0,0,0,0)
}
\]

with status

ZERO_FOR_EACH_FIXED_LOCAL_FIBRE_UNDER_GRH.

The unconditional generic value is not promoted.

## Density semantics

The theorem supplies a positive-natural-density subclass

\[
S_{C,H}
\subseteq
\mathcal E_{h,d}.
\]

Therefore

\[
\underline{\delta}(\mathcal E_{h,d})>0.
\]

The contract explicitly does not claim that the natural density of the full
exposure set has independently been proved to exist.

## Fail-closed controls

The v0.12 contract rejects:

- missing GRH declaration;
- unconditional generic infinite-exposure promotion;
- physical-observability promotion;
- wrong/missing independent frontier provenance pin;
- missing v0.11 matrix-source surface;
- exact-36 violation.

## Hosted status

GitHub combined status on implementation head

68bcb2d62f6718c306efc03b25bb16bff59e3e75

returned no status checks.

Therefore:

HOSTED_CI = NOT_PRESENT.

## Verdict

PHASENAV_36D_GRH_SOURCE_PRIME_REPLICATION = PASS_REFERENCE_CONTRACT  
COMPLETE_LOCAL_DENOMINATOR_COVERAGE = PASS_EXACT_STRUCTURE  
FINITE_HIDDEN_VECTOR_P5 = RETAINED_EXACT  
INFINITE_HIDDEN_VECTOR_P5_UNDER_GRH = ZERO  
UNCONDITIONAL_GENERIC_INFINITE_EXPOSURE = OPEN  
PHYSICAL_OBSERVABILITY = NOT_PROMOTED

canon_allowed = false.
