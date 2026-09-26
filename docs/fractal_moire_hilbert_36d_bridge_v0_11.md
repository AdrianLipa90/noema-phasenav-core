# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.11

Status: CANDIDATE_ONLY / ARPL_HETEROGENEOUS_CLOCK_FIBRES / RECTANGULAR_MATRIX_GRAM / FINITE_NETWORK_VISIBILITY
Date: 2026-09-26

## 1. Purpose

v0.11 admits the exact source-owned ARPL clock-fibre matrix Gram without
forcing variable-dimensional arithmetic fibres into a square common-dimension
schema.

New subtype:

ARPL_CLOCK_FIBRE_MATRIX_GRAM.

It remains separate from:
- scalar ARPL hit-cylinder overlap;
- Cuntz refinement/carry cocycle;
- 36D routing coordinates.

## 2. Source theorem

For local ARPL periods

\[
e_p=\operatorname{ord}_p(4),
\]

define

\[
\mathcal H_{e_p}
=
\ell^2(\mathbb Z/e_p\mathbb Z).
\]

For a finite support with common clock \(L\), the canonical pullbacks \(J_e\)
give rectangular cross-Gram operators

\[
\boxed{
A_{ef}=J_e^*J_f.
}
\]

Their rank is

\[
\boxed{
\operatorname{rank}A_{ef}
=
\gcd(e,f).
}
\]

In residue bases,

\[
(A_{ef})_{ab}
=
\begin{cases}
\dfrac{\gcd(e,f)}{\sqrt{ef}},
&a\equiv b\pmod{\gcd(e,f)},\\
0,&\text{otherwise}.
\end{cases}
\]

## 3. Exact local orbital family

The source-owned local cyclic odometers satisfy

\[
\boxed{
A_{ef}U_f=U_eA_{ef}.
}
\]

The corresponding mismatch operators satisfy

\[
\boxed{
A_{ef}\Delta_f=\Delta_eA_{ef}.
}
\]

This is a genuine heterogeneous matrix intertwiner family with different local
dimensions.

## 4. Packet requirements

The subtype requires:

- matrix_overlap_source_subtype = ARPL_CLOCK_FIBRE_MATRIX_GRAM;
- ARPL immutable source pin;
- orbital heterogeneous-theorem witness;
- arpl_separation_h;
- arpl_prime_support;
- maximum pair odometer-intertwiner residual;
- maximum pair mismatch-intertwiner residual;
- heterogeneous fibre information-loss ledger;
- matrix_storage_contract = UPSTREAM_WITNESS_ONLY.

The validator computes rather than trusts:

- \(e_p=\operatorname{ord}_p(4)\);
- active pulse existence;
- common clock \(L\);
- pairwise gcd-rank matrix;
- left/right pairwise kernel dimensions;
- finite-support network-visible Fourier modes;
- finite-support network-hidden Fourier modes.

## 5. h=6 control

For

\[
P=\{5,7,11,13,19\},
\]

the exact periods are

\[
\boxed{
(2,3,5,6,9).
}
\]

The common clock is

\[
\boxed{
L=90.
}
\]

The finite-support hidden dimensions are

\[
\boxed{
(0,0,4,2,6).
}
\]

These dimensions are arithmetic source data relative to the selected finite
support.

## 6. 36D firewall

The local fibre dimensions, pairwise matrix shapes and common clock size are
not identified with 36.

The packet may route summaries/witnesses through PhaseNav 36D, but

\[
\boxed{
\text{36D routing dimension}
\neq
\sum_p e_p
\neq
L
}
\]

as a type identity.

For the h=6 control,

\[
\sum_p e_p=25,
\qquad
L=90,
\]

neither number is promoted as a new PhaseNav dimensionality.

## 7. Finite-support hidden firewall

A network-hidden mode means only that it lies outside every pairwise common
frequency subspace within the declared finite support.

Adding further ARPL channels may expose it.

Therefore v0.11 reports

finite_support_hidden = true

and

infinite_support_persistence = OPEN

unless a separate infinite-support theorem is supplied.

## 8. Relation to scalar pulse failure

The v0.8 scalar adapter FAIL remains valid.

The successful matrix source is not obtained by retuning the failed scalar
phase. It uses the complete local clock fibre and the canonical local odometer.

Thus:

ARITHMETIC_PULSE_AS_SCALAR_ORBITAL = FAIL_RETAINED.

ARPL_CLOCK_ODOMETER_AS_RECTANGULAR_MATRIX_INTERTWINER = PASS_SOURCE_THEOREM.

## 9. Provenance

Current source pin:

AdrianLipa90/On-Primes  
branch integrate/arpl-clock-fibre-matrix-gram-v0.1-20260926  
commit 8781f4a685257eced538daa7462ec4fc48093a6b

Orbital heterogeneous theorem receipt:

AdrianLipa90/Orbital-System-base  
branch formalism/fractal-orbital-moire-hilbert-v0.9-20260926  
commit cbf5d83a40ebe4e090ffad0749418dbac732f25b

## 10. Promotion ledger

PASS at representation-contract level:
- heterogeneous ARPL fibre dimensions;
- computed arithmetic periods;
- computed gcd-rank network;
- exact rectangular intertwiner witness slots;
- finite-support network visibility ledger;
- immutable source pinning;
- strict separation from 36D transport dimension.

OPEN:
- infinite-support persistence of hidden modes;
- unique finite 36D summary encoding;
- physical orbital meaning;
- empirical calibration.

canon_allowed = false.
