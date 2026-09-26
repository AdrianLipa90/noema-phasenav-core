# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.8

Status: CANDIDATE_ONLY / ARPL_HIT_OVERLAP_GRAM_TYPED / SCALAR_PULSE_PROMOTION_FIREWALL
Date: 2026-09-26

## 1. Purpose

v0.8 adds a typed ARPL source subtype to the existing
OVERLAP_GRAM_COVARIANT mode.

The subtype is

ARPL_HIT_OVERLAP_GRAM.

Its purpose is to admit the exact arithmetic overlap geometry already proved
in On-Primes while preserving the reverse-test result that an arithmetic pulse
angle is not automatically a scalar orbital phase.

No new prime-distribution theorem is introduced here.

## 2. ARPL source object

For a fixed admissible separation

\[
h\ge6,
\qquad
6\mid h,
\]

and active prime channels \(p\), ARPL defines hit cylinders

\[
C_p
\subset
K_h.
\]

Their exact finite Gram kernel is

\[
G_{pq}^{ARPL}
=
m(C_p\cap C_q).
\]

The cylinder density is

\[
d_p
=
m(C_p)
=
\frac1{e_p}.
\]

Normalize the indicator embedding by

\[
W_p z
=
z\frac{\mathbf1_{C_p}}{\sqrt{d_p}}.
\]

Then every \(W_p\) is an isometry and the normalized overlap Gram is

\[
\boxed{
\widetilde G_{pq}
=
\frac{
m(C_p\cap C_q)
}{
\sqrt{m(C_p)m(C_q)}
}.
}
\]

This is a lawful source-owned overlap Gram witness for the finite ARPL hit
cylinder family.

## 3. Exact arithmetic entry

If generalized-CRT phase constraints for \(p,q\) are incompatible,

\[
\widetilde G_{pq}=0.
\]

If they are compatible,

\[
m(C_p\cap C_q)
=
\frac1{\operatorname{lcm}(e_p,e_q)},
\]

hence

\[
\boxed{
\widetilde G_{pq}
=
\frac{
\gcd(e_p,e_q)
}{
\sqrt{e_pe_q}
}.
}
\]

The overlap geometry is therefore determined by arithmetic clock periods and
phase compatibility.

## 4. Packet subtype

A packet using

ARPL_HIT_OVERLAP_GRAM

must already satisfy the generic v0.4 overlap contract and must additionally
declare:

- arpl_bridge_witness_ref;
- arpl_gram_witness_ref;
- arpl_normalized_gram_witness_ref;
- arpl_separation_h;
- arpl_prime_support;
- arpl_gram_normalization_residual;
- arithmetic_pulse_scalar_adapter_status.

The prime support must contain distinct primes \(p\ge5\).

The separation must satisfy

\[
h\ge6,
\qquad
6\mid h.
\]

## 5. Scalar arithmetic pulse adapter statuses

The packet must use exactly one of:

NOT_CLAIMED

PASS_STABILIZER

FAIL_STABILIZER.

### NOT_CLAIMED

The arithmetic pulse coordinates remain arithmetic coordinates/observables.
No scalar orbital interpretation is asserted.

### PASS_STABILIZER

A declared scalar phase family has passed

\[
\boxed{
\|D^*\widetilde G D-\widetilde G\|
\le
\varepsilon.
}
\]

Only then may

scalar_orbital_pulse_promotion = true.

### FAIL_STABILIZER

The proposed scalar phase family has a residual above tolerance.

The ARPL overlap source remains valid, but

\[
\boxed{
scalar\_orbital\_pulse\_promotion=false.
}
\]

This is a failed adapter, not a failed arithmetic theorem.

## 6. h=6 reverse-test control

For

\[
P=\{5,7,11,13,19\},
\qquad
h=6,
\]

the exact arithmetic pulse rendering is

\[
\theta
=
\left(
\pi,
\frac{2\pi}{3},
\frac{4\pi}{5},
\frac{2\pi}{3},
\frac{10\pi}{9}
\right).
\]

The independent On-Primes bridge receipt reports

\[
\boxed{
\|D^*\widetilde G D-\widetilde G\|_F
=
1.0236181222825256.
}
\]

Therefore this particular naive scalar-orbital adapter is

FAIL_STABILIZER.

It must not be promoted by PhaseNav.

## 7. Distinction from ARPL refinement cocycle

ARPL now supplies two exact but different branch geometries.

### Refinement-clock channel

Finite lift labels at

\[
L_N\mid L_{N+1}
\]

are mutually exclusive branch sectors and use

CUNTZ_BLOCK_COCYCLE_UNITARY

with the exact odometer carry cocycle.

### Hit-cylinder channel

The arithmetic events \(C_p\) may overlap and use

OVERLAP_GRAM_COVARIANT

with the exact normalized Gram kernel.

Therefore:

\[
\boxed{
ARPL\_REFINEMENT\_COCYCLE
\neq
ARPL\_HIT\_OVERLAP\_GRAM.
}
\]

Mixing these source objects without an explicit adapter is rejected.

## 8. Why the FAIL is structurally useful

The failed scalar-pulse adapter eliminates a tempting shortcut.

It shows that exact arithmetic pulse characters cannot simply be copied into
the overlap representation as independent one-dimensional orbital blocks when
the Gram stabilizer forbids them.

Lawful future routes include:

- arithmetic phase as coordinate only;
- a larger internal matrix representation in the Gram stabilizer;
- the exact odometer carry-cocycle channel;
- a different branch embedding with an independently proved covariance law.

## 9. 36D boundary

Even when ARPL_HIT_OVERLAP_GRAM passes, the 36D packet remains a finite
projection.

It does not reconstruct:

- the complete ARPL inverse-limit hull;
- all active prime channels;
- the full overlap kernel;
- all arithmetic pulse coordinates;
- the full operator stabilizer;
- a physical prime-generated state.

The existing information-loss ledger remains mandatory.

## 10. Fail-closed rules

Reject:

- ARPL overlap subtype outside OVERLAP_GRAM_COVARIANT;
- duplicate/non-prime support entries;
- \(h<6\) or \(6\nmid h\);
- missing arithmetic Gram witness;
- Gram normalization residual above tolerance;
- PASS_STABILIZER with residual above tolerance;
- FAIL_STABILIZER with residual at or below tolerance;
- unknown adapter status;
- exact-36 violation.

## 11. Promotion ledger

PASS at contract level:

- exact ARPL hit-cylinder source typing;
- exact normalized overlap Gram witness surface;
- explicit scalar-pulse adapter status;
- failed adapter preserved as FAIL without invalidating source mathematics;
- separation from ARPL carry-cocycle semantics;
- inherited overlap, inductive, noisy-depth and exact-36 firewalls.

OPEN:

- non-scalar Gram-stabilizer orbital representation;
- source-owned physical ARPL orbital meaning;
- physical 36D packing;
- empirical calibration.

Pinned On-Primes receipt:

AdrianLipa90/On-Primes
branch integrate/arpl-fractal-orbital-bridge-v0.2-20260926
commit 705872f11aaf8b933ab3b713fb10443326fde62b

canon_allowed = false.
