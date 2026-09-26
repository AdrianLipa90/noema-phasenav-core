# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.9

Status: CANDIDATE_ONLY / MATRIX_OVERLAP_STABILIZER_TYPED / INTERNAL_DIMENSION_FIREWALL
Date: 2026-09-26

## 1. Purpose

v0.9 imports the exact overlap-stabilizer theorem from Orbital-System-base
v0.8 into the PhaseNav 36D representation contract.

The central correction is:

\[
\boxed{
\text{larger internal dimension}
\not\Rightarrow
\text{independent local orbital freedom}.
}
\]

The packet must state how its internal overlap representation avoids or obeys
the cross-Gram stabilizer.

## 2. Parent stabilizer equation

For branch cross-Gram operator

\[
A_{pq}=W_p^*W_q
\]

and local unitaries \(R_p,R_q\), consistency requires

\[
\boxed{
R_p^*A_{pq}R_q=A_{pq}.
}
\]

Equivalently,

\[
\boxed{
A_{pq}R_q=R_pA_{pq}.
}
\]

Thus every nonzero cross-Gram block is an intertwiner between local orbital
representations.

## 3. Internal overlap modes

v0.9 defines four typed modes:

TRIVIAL_INTERNAL_TENSOR

FULL_RANK_FRAME_CONJUGACY

RANK_DEFICIENT_STABILIZER

GENERAL_MATRIX_GRAM_STABILIZER

These modes are only legal under

OVERLAP_GRAM_COVARIANT.

## 4. TRIVIAL_INTERNAL_TENSOR

This mode represents

\[
A_{pq}=g_{pq}I_d.
\]

For \(g_{pq}\neq0\),

\[
R_p=R_q.
\]

Therefore the packet must not claim channel-dependent internal orbital matrices
inside one connected nonzero-overlap component.

Required:
- internal_dimension;
- internal_overlap_witness_ref;
- internal_stabilizer_residual;
- local_unitary_equality_residual;
- overlap_component_count;
- channel_dependent_internal_claim = false.

This mode may increase the size of the common internal operator, but not the
number of independent local operators per connected component.

## 5. FULL_RANK_FRAME_CONJUGACY

For square unitary channel frames \(J_p\),

\[
A_{pq}
=
g_{pq}J_p^*J_q.
\]

The local matrices may differ by frame conjugation:

\[
R_p
=
(J_p^*J_q)R_q(J_q^*J_p).
\]

But the external operators

\[
S_p=J_pR_pJ_p^*
\]

must agree across the overlap edge.

Required:
- internal_dimension;
- internal_overlap_witness_ref;
- internal_stabilizer_residual;
- frame_unitarity_residual;
- external_operator_equality_residual;
- independent_external_dynamics_claim = false.

This mode certifies coordinate/frame variation, not independent external
dynamics.

## 6. RANK_DEFICIENT_STABILIZER

For rank-deficient \(A_{pq}\), the stabilizer constrains only the visible
support.

Degrees of freedom may remain on the kernel/complement.

Required:
- internal_dimension;
- cross_gram_rank;
- internal_overlap_witness_ref;
- internal_stabilizer_residual;
- hidden_freedom_witness_ref;
- visible_support_consistency_residual.

The rank must satisfy

\[
0\le \operatorname{rank}(A_{pq})<d.
\]

This mode is the first v0.9 mode that can support genuine local freedom not
visible to the overlap edge.

It still does not establish a physical interpretation of that hidden sector.

## 7. GENERAL_MATRIX_GRAM_STABILIZER

This mode permits a source-owned matrix-valued Gram family without assuming
trivial tensor, full-rank frame, or a particular rank-deficient normal form.

Required:
- internal_dimension;
- matrix_gram_witness_ref;
- matrix_stabilizer_witness_ref;
- internal_stabilizer_residual;
- matrix_gram_rank_lower_bound;
- matrix_gram_rank_upper_bound.

The contract validates only the declared residual/rank bounds.

It does not infer the stabilizer group automatically.

## 8. ARPL consequence

For the normalized ARPL hit-cylinder embedding with a trivial common internal
factor,

\[
W_p
=
\frac{\mathbf1_{C_p}}{\sqrt{m(C_p)}}\otimes I_d,
\]

the cross-Gram is

\[
A_{pq}
=
\widetilde G_{pq}I_d.
\]

Therefore the h=6 scalar adapter failure recorded in v0.8 cannot be repaired by
simply replacing every scalar phase with an arbitrary \(d\times d\) unitary on
the same trivial tensor embedding.

If the nonzero-overlap graph is connected,

\[
\boxed{
R_p=R_q
\quad
\forall p,q
}
\]

inside that component.

A lawful ARPL matrix escape therefore needs a genuinely nontrivial matrix Gram,
frame/intertwiner structure, rank-deficient overlap, or a different branch
representation.

## 9. Promotion firewall

A packet with

TRIVIAL_INTERNAL_TENSOR

must not set

channel_dependent_internal_claim = true.

A packet with

FULL_RANK_FRAME_CONJUGACY

must not set

independent_external_dynamics_claim = true.

A packet with

RANK_DEFICIENT_STABILIZER

must provide a strict rank defect and an explicit hidden-freedom witness.

Thus internal dimension is never used as an untyped escape hatch.

## 10. Relation to 36D

The internal Hilbert dimension and the PhaseNav transport dimension are
different types.

A 36-coordinate routing vector does not imply

\[
d=36
\]

for the overlap internal fibre.

Likewise an internal \(d\times d\) unitary is not automatically a 36D state.

The packet must keep:
- PhaseNav representation dimension;
- overlap internal dimension;
- branch count;
- refinement depth

as separately typed quantities.

## 11. Fail-closed rules

Reject:
- matrix-overlap mode outside OVERLAP_GRAM_COVARIANT;
- internal_dimension < 1;
- stabilizer residual above tolerance;
- trivial tensor with channel-dependent claim;
- full-rank frame mode with independent-external-dynamics claim;
- rank-deficient mode with rank >= internal_dimension;
- rank-deficient mode with missing hidden-freedom witness;
- inconsistent general rank bounds;
- exact-36 violation.

## 12. Promotion ledger

PASS at representation-contract level:
- matrix-valued overlap modes separated;
- trivial internal tensor no-go encoded;
- frame conjugacy separated from independent dynamics;
- rank-deficient hidden freedom typed explicitly;
- generic matrix Gram surface retained;
- inherited ARPL overlap, cocycle, inductive, noisy and exact-36 firewalls.

OPEN:
- source-owned physical matrix Gram;
- physical internal frame selection;
- physical hidden-sector interpretation;
- ARPL nontrivial stabilizer construction;
- empirical calibration.

Pinned Orbital-System-base receipt:

AdrianLipa90/Orbital-System-base
branch formalism/fractal-orbital-moire-hilbert-v0.8-20260926
commit 074f04328f7a615928d24b33474acb056e151985

canon_allowed = false.
