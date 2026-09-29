# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.5

Status: CANDIDATE_ONLY / CUNTZ_BLOCK_COCYCLE_TYPED / ARPL_ODOMETER_SUBTYPE
Date: 2026-09-26

## 1. Purpose

v0.5 imports the exact Cuntz block-matrix theorem and the exact ARPL odometer
carry-cocycle into the PhaseNav 36D contract.

The IFS covariance modes are now:

- COMPRESSION_ONLY;
- FIXED_BRANCH_UNITARY_INTERTWINER;
- OVERLAP_GRAM_COVARIANT;
- BRANCH_PERMUTATION_UNITARY;
- CUNTZ_BLOCK_COCYCLE_UNITARY.

UNITARY_DILATION remains a separate scale semantics.

## 2. Cuntz block theorem

For a strong-separation Cuntz family \(V_i\), define synthesis

\[
W(\psi_i)_i=\sum_iV_i\psi_i.
\]

For every global unitary \(R\),

\[
\boxed{
\mathcal R=W^*RW
}
\]

is a unitary block operator on the branch direct sum with blocks

\[
\boxed{
\mathcal R_{ji}=V_j^*RV_i.
}
\]

Conversely,

\[
\boxed{
R=W\mathcal RW^*
=
\sum_{i,j}V_j\mathcal R_{ji}V_i^*.
}
\]

Hence:
- fixed branch = block diagonal;
- branch permutation = block monomial;
- general state-dependent branch transport = unitary block/cocycle matrix.

## 3. BRANCH_PERMUTATION_UNITARY mode

This mode requires:
- branch_count;
- branch_permutation;
- block_covariance_witness_ref;
- block_unitarity_residual;
- block_reconstruction_residual;
- block_mismatch_residual.

The permutation must be a bijection of

\[
\{0,\dots,N-1\}.
\]

The mode certifies branch transport

\[
RV_i
=
V_{\sigma(i)}R_i.
\]

It does not certify fixed-branch recursion.

## 4. CUNTZ_BLOCK_COCYCLE_UNITARY mode

This mode requires:
- branch_count;
- block_covariance_witness_ref;
- block_unitarity_residual;
- block_reconstruction_residual;
- block_mismatch_residual;
- offdiagonal_transition_ledger;
- cocycle_witness_ref.

The off-diagonal ledger must be non-empty.

The semantics are

\[
\boxed{
RV_i
=
\sum_jV_j\mathcal R_{ji}
}
\]

with a unitary block matrix \(\mathcal R\).

Individual nonzero blocks may be partial isometries.

## 5. ARPL_ODOMETER_CARRY subtype

A block-cocycle packet may declare

ARPL_ODOMETER_CARRY

only with an immutable ARPL refinement witness.

Required:
- arpl_refinement_witness_ref;
- coarse_clock_size \(L_N\ge1\);
- refinement_branching \(b_N\ge2\);
- carry_cocycle_residual.

The exact parent law is

\[
L_{N+1}=b_NL_N.
\]

For child \(c\),

\[
\boxed{
U_{N+1}V_c
=
V_cU_N(I-Q_N)
+
V_{c+1\bmod b_N}U_NQ_N.
}
\]

The two nonzero block families are

\[
\mathcal U_{cc}=U_N(I-Q_N)
\]

and

\[
\mathcal U_{c+1,c}=U_NQ_N.
\]

This is a deterministic arithmetic carry cocycle.

## 6. ARPL typing firewall

The ARPL subtype does not mean that any 36D state is prime-generated.

The packet must separately state:
- finite ARPL refinement level;
- source branch/channel witness;
- omitted arithmetic channels;
- 36D projection loss.

The full inverse-limit phase hull

\[
K_h
\]

is not a 36-dimensional vector.

## 7. Moire mismatch preservation

For the exact Cuntz block synthesis,

\[
W^*\Delta W
=
(I-\mathcal R)^*(I-\mathcal R).
\]

Therefore the global mismatch is preserved by the complete block matrix.

In cocycle/permutation modes, a single diagonal block is insufficient.

The 36D packet must retain an off-diagonal transition witness whenever its
interpretation depends on block transport.

## 8. Relation to overlap mode

CUNTZ_BLOCK_COCYCLE_UNITARY assumes orthogonal branch ranges.

OVERLAP_GRAM_COVARIANT instead uses

\[
D^*GD=G.
\]

A packet cannot claim both modes for the same branch family unless it provides
a separate theorem proving that the overlap Gram reduces to the identity.

## 9. Fail-closed conditions

Reject:
- invalid/non-bijective branch permutation;
- branch_count < 2 for permutation/cocycle modes;
- missing block witness;
- block unitarity residual above tolerance;
- block reconstruction residual above tolerance;
- block mismatch residual above tolerance;
- empty cocycle transition ledger;
- ARPL subtype without \(L_N,b_N\) and carry residual;
- ARPL subtype with \(b_N<2\);
- mixing UNITARY_DILATION with IFS block modes;
- exact-36 violation.

## 10. Promotion ledger

PASS at representation-contract level:
- fixed-branch, permutation, generic block-cocycle and overlap modes separated;
- exact block-unitarity witness fields;
- exact ARPL carry-cocycle subtype;
- global mismatch preservation witness;
- inherited numerical positivity and exact-36 firewall.

OPEN:
- production branch-transition matrices;
- physical ARPL-to-PhaseNav projection;
- source-owned 36D arithmetic state;
- infinite-depth truncation law;
- physical calibration.

canon_allowed = false.
