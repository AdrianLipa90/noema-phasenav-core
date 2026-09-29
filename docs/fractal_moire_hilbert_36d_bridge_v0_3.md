# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.3

Status: CANDIDATE_ONLY / RECURSIVE_IFS_INTERTWINER_TYPED / 36D_BRANCH_COVARIANCE_GATE
Date: 2026-09-26

## 1. Purpose

v0.3 imports the exact Orbital-System-base v0.3 covariance theorem into the
finite PhaseNav 36D representation boundary.

The new distinction is:

COMPRESSION_ONLY

versus

FIXED_BRANCH_UNITARY_INTERTWINER.

A finite packet may claim a recursively unitary branch relation only in the
second mode.

## 2. Upstream theorem

For a Cuntz branch family \(V_i\) and local unitary relations \(R_i\),

\[
R=\sum_iV_iR_iV_i^*
\]

is unitary and satisfies

\[
\boxed{RV_i=V_iR_i},
\]

\[
\boxed{V_i^*RV_i=R_i},
\]

and

\[
\boxed{[R,P_i]=0},
\qquad
P_i=V_iV_i^*.
\]

Recursively, for a word \(w\),

\[
\boxed{RV_w=V_wR_w}.
\]

Therefore

\[
\boxed{
V_w^*\Delta V_w
=
(I-R_w)^*(I-R_w).
}
\]

This is the exact gate that upgrades a branch from generic compression to a
unitary local Moire relation.

## 3. COMPRESSION_ONLY mode

A packet in this mode may carry

\[
V_w^*\Delta V_w
\]

as a positive compressed mismatch.

It must not claim:
- local relative unitarity;
- a branch eigenphase law;
- exact local \(4\sin^2(\vartheta/2)\) spectrum;
- recursive unitary self-similarity.

This mode remains valid even when the cylinder is not reducing.

## 4. FIXED_BRANCH_UNITARY_INTERTWINER mode

A packet may enter this mode only if it supplies witnesses for:

\[
\|RV_w-V_wR_w\|
\le
\varepsilon,
\]

\[
\|R_w^*R_w-I\|
\le
\varepsilon,
\]

and

\[
\|[P_w,R]\|
\le
\varepsilon.
\]

The packet must also provide immutable witness references for:
- the IFS branch isometry;
- the orbital/IFS covariance test;
- the local branch relation.

When all three residuals pass, the finite representation may use

\[
\boxed{
\Delta_w
=
(I-R_w)^*(I-R_w)
}
\]

and, for a local eigenphase,

\[
\boxed{
\Delta_w
=
4\sin^2(\vartheta_w/2).
}
\]

## 5. Why commutator and intertwiner are both carried

At exact operator level, unitary fixed-branch intertwining implies the reducing
property.

At finite representation level, the two residuals probe different failure
surfaces:
- intertwiner residual tests the declared local relation;
- commutator residual tests cylinder invariance.

Both are retained as independent diagnostics.

## 6. Prefix-permutation firewall

A globally unitary orbital relation can permute cylinders:

\[
RV_i=V_{\sigma(i)}R_i.
\]

Such an operator is not a FIXED_BRANCH_UNITARY_INTERTWINER unless
\(\sigma(i)=i\).

Permutation covariance is mathematically valid but belongs to a different
future packet type.

A prefix swap must therefore fail the fixed-branch gate even though it is
globally unitary.

## 7. 36D phase observable

The projective phase coherence remains

\[
C_{ab}^{36}
=
\frac1{36}
\sum_j
e^{i(\theta_j^{(b)}-\theta_j^{(a)})},
\]

with numerically clamped nonnegative residual

\[
\boxed{
\delta_{ab}^2
=
\max\{0,2(1-|C_{ab}^{36}|)\}.
}
\]

This observable is representation-level.

A FIXED_BRANCH_UNITARY_INTERTWINER witness upgrades its branch interpretation
but does not make the 36D phase vector the full Hilbert state.

## 8. Packet fields

All v0.2 fields remain required.

For IFS_COMPRESSION add:

ifs_covariance_mode =
- COMPRESSION_ONLY, or
- FIXED_BRANCH_UNITARY_INTERTWINER.

For FIXED_BRANCH_UNITARY_INTERTWINER also require:
- orbital_ifs_covariance_witness_ref;
- local_relation_witness_ref;
- intertwiner_residual;
- local_unitarity_residual;
- reducing_commutator_residual.

All residuals must be finite, nonnegative and below the declared tolerance.

## 9. Information-loss firewall

Even a successful branch intertwiner does not reconstruct:
- the full direct-integral state;
- all other cylinder relations;
- infinite-depth recursion;
- amplitudes discarded by a phase-only projection;
- winding unless separately carried;
- coframe/bivector semantics unless separately typed.

The information-loss ledger remains mandatory.

## 10. Promotion ledger

PASS at representation-contract level:
- explicit COMPRESSION_ONLY mode;
- explicit FIXED_BRANCH_UNITARY_INTERTWINER mode;
- fail-closed residual witnesses;
- exact-36 coordinate gate;
- global-U(1)-blind phase residual;
- numerical residual positivity.

NO-GO:
- nonreducing branch claims local unitary relation;
- global unitarity alone promotes recursive branch unitarity;
- cylinder permutation silently passes as fixed-branch covariance.

OPEN:
- physical branch words;
- source-owned covariance witnesses;
- infinite-depth 36D truncation law;
- permutation-covariant 36D contract;
- physical calibration.

canon_allowed = false.
