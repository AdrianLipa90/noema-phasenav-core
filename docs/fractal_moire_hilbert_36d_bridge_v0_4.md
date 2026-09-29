# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.4

Status: CANDIDATE_ONLY / OVERLAP_GRAM_COVARIANCE_TYPED / THREE_SCALE_SEMANTICS_SEPARATED
Date: 2026-09-26

## 1. Purpose

v0.4 adds the finite-overlap Gram covariance theorem to the PhaseNav 36D
representation contract.

The scale/orbital stack now has three distinct admissible surfaces:

1. IFS_COMPRESSION + COMPRESSION_ONLY;
2. IFS_COMPRESSION + FIXED_BRANCH_UNITARY_INTERTWINER;
3. IFS_COMPRESSION + OVERLAP_GRAM_COVARIANT;

plus the already separate UNITARY_DILATION path.

These surfaces must not be silently interchanged.

## 2. Overlap theorem imported from Orbital-System-base v0.4

For branch embeddings \(W_i\), define synthesis

\[
W(\psi_1,\ldots,\psi_N)
=
\sum_iW_i\psi_i
\]

and Gram operator

\[
G=W^*W,
\qquad
G_{ij}=W_i^*W_j.
\]

For local unitary orbital relations

\[
D=\bigoplus_iR_i,
\]

the branch action descends to a unitary operator on the synthesized overlap
quotient iff

\[
\boxed{
D^*GD=G.
}
\]

Equivalently,

\[
\boxed{
R_i^*G_{ij}R_j=G_{ij}
\quad
\forall i,j.
}
\]

This replaces independent Cuntz-branch unitarity when branch ranges overlap.

## 3. OVERLAP_GRAM_COVARIANT mode

A 36D packet may use this mode only when it supplies:

- overlap_gram_witness_ref;
- overlap_level;
- local_relation_family_witness_ref;
- gram_compatibility_residual;
- overlap_intertwiner_residual;
- local_relation_unitarity_residual;
- overlap_kernel_ledger;
- quotient_reconstruction_contract.

All residuals must be finite, nonnegative and below tolerance.

The overlap kernel ledger must be non-empty because branch coefficients may
have nontrivial null combinations under synthesis.

## 4. Meaning of the overlap witnesses

The Gram residual tests

\[
\boxed{
\|D^*GD-G\|.
}
\]

The intertwiner residual tests the synthesized relation

\[
\boxed{
RW-WD.
}
\]

The local-unitarity residual tests the declared block family \(R_i\).

All three are needed because:
- local unity alone does not preserve overlap identifications;
- Gram preservation alone does not identify the claimed global operator;
- an intertwiner alone may be compatible with a nonunitary local block.

## 5. Quotient semantics

The coefficient space is not interpreted directly as the physical branch
Hilbert space.

Instead it carries the semidefinite inner product

\[
\langle\xi,\eta\rangle_G
=
\langle\xi,G\eta\rangle,
\]

and one must quotient by

\[
\ker G.
\]

Therefore the 36D packet must state what information is lost when distinct
branch coefficient vectors represent the same synthesized state.

This is separate from the existing finite-36D information-loss ledger.

## 6. Strong-separation recovery

If

\[
G=I,
\]

then

\[
D^*GD=I
\]

for every block unitary \(D\).

The packet should then use FIXED_BRANCH_UNITARY_INTERTWINER rather than
OVERLAP_GRAM_COVARIANT unless a nontrivial overlap witness is intentionally
being tested.

Thus v0.3 is recovered as the orthogonal-Gram special case.

## 7. Scalar phase-lock consequence

For one-dimensional branch fibres and nonzero overlap

\[
G_{ij}\neq0,
\]

local scalar phases must satisfy

\[
e^{i(\theta_j-\theta_i)}G_{ij}
=
G_{ij}.
\]

Therefore

\[
\boxed{
\theta_i=\theta_j\pmod{2\pi}
}
\]

on connected nonzero-overlap components.

A 36D overlap packet that claims independent scalar phase labels on maximally
overlapping branches must fail unless an additional internal matrix structure
changes the stabilizer.

## 8. Moire mismatch semantics

When the overlap Gram gate passes, the induced global relation \(R\) is unitary
on the quotient/synthesized Hilbert space.

The global mismatch

\[
\Delta=(I-R)^*(I-R)
\]

is therefore positive.

However, independent branch mismatch spectra are not free data: they are
coupled by the cross-Gram compatibility equations.

The packet may report branch features, but it must not interpret them as
independent local unitaries unless the overlap stabilizer permits that claim.

## 9. 36D projection boundary

A successful OVERLAP_GRAM_COVARIANT packet still does not reconstruct:

- the full Gram kernel;
- the infinite-depth overlap correspondence;
- the universal Cuntz-Pimsner algebra;
- the full operator spectrum;
- discarded amplitudes;
- physical source realization.

The 36D vector remains a finite projection.

## 10. Fail-closed cases

Reject:
- missing overlap Gram witness;
- empty overlap kernel ledger;
- zero or negative overlap level;
- Gram compatibility residual above tolerance;
- overlap intertwiner residual above tolerance;
- local relation unitarity residual above tolerance;
- simultaneous UNITARY_DILATION and overlap mode;
- exact-36 coordinate violation.

## 11. Promotion ledger

PASS at contract level:
- explicit overlap Gram semantics;
- explicit quotient/kernel loss;
- independent Gram/intertwiner/unitarity residuals;
- strong-separation recovery;
- separation from unitary dilation.

NO-GO:
- local branch unitarity is sufficient under overlap;
- overlap is silently treated as orthogonal Cuntz branching;
- branch phase labels remain independent under maximal scalar overlap.

OPEN:
- source-owned physical Gram operator;
- physical overlap depth;
- physical local orbital stabilizer;
- infinite-depth correspondence;
- physical 36D calibration.

canon_allowed = false.
