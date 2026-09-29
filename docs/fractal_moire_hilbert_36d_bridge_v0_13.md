# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.13

Status: CANDIDATE_ONLY / RELATIONAL_ZERO_PROJECTOR_OPERATOR_LAYER / EXACT_FINITE_HILBERT_SEMANTICS
Date: 2026-09-28

## 1. Purpose

v0.13 adds the ARPL relational-zero projector family as a typed operator layer
above the existing 36D routing representation.

The operators are exact mathematical Hilbert-space operators.

The 36D packet carries their verified finite invariants and immutable upstream
witnesses. It does not pretend to embed the complete operator matrix into 36
coordinates.

## 2. Canonical operator family

For a finite residue multiplicative group \(G_Q\), and nested calibrated
subgroups

\[
\Gamma_0
\le
\Gamma_h
\le
\Gamma_{h\zeta},
\]

define subgroup-averaging projections

\[
\Pi_0,\Pi_h,\Pi_{h\zeta}.
\]

The PhaseNav operator layer exposes:

\[
\boxed{
\Delta_h=\Pi_0-\Pi_h
}
\]

as ARPL_ACTIVITY_DEFECT_PROJECTOR,

\[
\boxed{
\Delta_\zeta=\Pi_h-\Pi_{h\zeta}
}
\]

as ARPL_DEPTH_DEFECT_PROJECTOR,

and

\[
\boxed{
\Delta=\Pi_0-\Pi_{h\zeta}
}
\]

as ARPL_TOTAL_RELATIONAL_ZERO_PROJECTOR.

They satisfy

\[
\boxed{
\Delta=\Delta_h+\Delta_\zeta
}
\]

and

\[
\boxed{
\Delta_h\Delta_\zeta=0.
}
\]

Each is self-adjoint, positive and idempotent.

Hence every finite operator has spectrum contained in

\[
\boxed{\{0,1\}}.
\]

## 3. Exact finite invariants

Let

\[
N=|G_Q|,
\]

\[
g_0=|\Gamma_0|,
\quad
g_h=|\Gamma_h|,
\quad
g_a=|\Gamma_{h\zeta}|.
\]

The packet requires

\[
g_0\mid g_h\mid g_a\mid N.
\]

The local projection indices are

\[
I_0=N/g_0,
\quad
I_h=N/g_h,
\quad
I_a=N/g_a.
\]

The validator computes

\[
\boxed{
r_h=I_0-I_h
}
\]

\[
\boxed{
r_\zeta=I_h-I_a
}
\]

and

\[
\boxed{
r=I_0-I_a.
}
\]

It also verifies

\[
\boxed{
r=r_h+r_\zeta.
}
\]

## 4. Relational zero

The packet reports

\[
\boxed{
\text{relational_zero}
\iff
r=0.
}
\]

This is equivalent to

\[
\Gamma_0=\Gamma_{h\zeta}.
\]

The normalized relational defect is

\[
\boxed{
\varepsilon_Q
=
\frac r{I_0}
=
1-\frac{g_0}{g_a}.
}
\]

The enlargement factor

\[
m_Q=g_a/g_0
\]

is integral and

\[
\boxed{
\varepsilon_Q=1-\frac1{m_Q}.
}
\]

Thus the scalar defect is quantized.

## 5. q=31 control

For the h=6, p=11, d=5 calibrated negative control,

\[
N=30,
\]

\[
(g_0,g_h,g_a)=(5,15,15).
\]

v0.13 must derive

\[
(I_0,I_h,I_a)=(6,2,2),
\]

\[
(r_h,r_\zeta,r)=(4,0,4),
\]

\[
\varepsilon_Q=2/3.
\]

Thus the failure is typed as pure activity defect.

## 6. q=61 control

For the positive control,

\[
N=60,
\]

\[
(g_0,g_h,g_a)=(30,30,30).
\]

The validator derives

\[
(r_h,r_\zeta,r)=(0,0,0).
\]

Hence

\[
\boxed{
\text{relational_zero}=true.
}
\]

## 7. Operator storage boundary

The packet must declare

RELATIONAL_OPERATOR_STORAGE = UPSTREAM_WITNESS_ONLY.

The complete finite matrices \(\Pi_H,\Delta_h,\Delta_\zeta,\Delta\) remain in
the source operator implementation.

The 36D packet carries:
- source pin;
- group/subgroup orders;
- exact ranks;
- normalized defect;
- zero/nonzero spectral gate;
- optional finite numerical residual witnesses.

It does not claim:

\[
36=\dim\mathcal H_Q.
\]

## 8. Quantum-language firewall

These are Hilbert-space projection operators and are therefore valid
operator-theoretic objects of the same mathematical class used in quantum
theory.

v0.13 does not infer from that fact alone that they are physical quantum
observables of a laboratory system.

Therefore

physical_quantum_observable_claim = true

is rejected unless a later physical binding contract explicitly supplies that
evidence.

## 9. Prime-fibre operator

The upstream theorem also defines

\[
\mu(Q)=\operatorname{rank}\Delta_Q
\]

and multiplication

\[
(M_\mu f)(Q)=\mu(Q)f(Q).
\]

The 36D contract may reference this as

ARPL_PRIME_FIBRE_DEFECT_MULTIPLICATION,

but does not embed the infinite operator.

The arithmetic exposure set is exactly its zero fibre.

## 10. Provenance

Current source:

AdrianLipa90/On-Primes

branch:

research/arpl-relational-zero-exposure-v0.1-20260928

validation receipt commit:

\[
\boxed{
605119b2b2e50ff6eb4cab550382b48630f14c67
}
\]

## 11. Promotion ledger

PASS EXACT / CONTRACT:
- subgroup-averaging projector surface;
- activity defect projector;
- depth defect projector;
- total relational-zero projector;
- orthogonal decomposition;
- exact rank ledger;
- quantized normalized defect;
- q31/q61 typed controls;
- separation of full operator dimension from 36D routing dimension.

OPEN:
- unconditional infinite zero multiplicity of the prime-fibre operator;
- physical observable binding;
- empirical calibration.

canon_allowed = false.
