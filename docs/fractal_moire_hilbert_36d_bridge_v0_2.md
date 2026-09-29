# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.2

Status: CANDIDATE_ONLY / IFS_SCALE_SEMANTICS_CORRECTED / TYPED_36D_PACKET / NO_PHYSICAL_PROMOTION
Date: 2026-09-26

## 1. Purpose

v0.2 corrects the scale semantics inherited by v0.1.

The upstream Fractal-Orbital Moire-Hilbert v0.2 distinguishes:

- reversible orbital unitary transport \(R\);
- one-sided IFS branch isometries \(V_w\);
- optional independently proved global unitary dilations \(D_r\).

A PhaseNav 36D representation must now declare which scale semantics it uses.

The two legal values are:

IFS_COMPRESSION

or

UNITARY_DILATION.

No implicit conversion is allowed.

## 2. Global relative relation

For admitted orbital layers \(a,b\),

\[
R_{ab}=U_a^*U_b
\]

is unitary and the global mismatch is

\[
\Delta_{ab}
=
(I-R_{ab})^*(I-R_{ab}).
\]

For a 36-phase representation,

\[
C_{ab}^{36}
=
\frac1{36}
\sum_{j=1}^{36}
e^{i(\theta_j^{(b)}-\theta_j^{(a)})},
\]

and the projective residual is

\[
\boxed{
\delta_{ab}^2
=
2(1-|C_{ab}^{36}|).
}
\]

This is invariant under one common global U(1) shift.

It remains a finite representation observable, not the full Hilbert operator.

## 3. IFS_COMPRESSION semantics

For a fractal cylinder word \(w\), the upstream exact object is

\[
\boxed{
\Delta_{ab}^{[w]}
=
V_w^*\Delta_{ab}V_w.
}
\]

This is positive.

The compressed relative relation

\[
R_{ab}^{[w]}
=
V_w^*R_{ab}V_w
\]

is generally only a contraction.

Therefore a 36D packet using IFS_COMPRESSION must declare:

- branch_word;
- branch_isometry_witness_ref;
- compressed_mismatch_source =
  GLOBAL_POSITIVE_OPERATOR_COMPRESSION;
- whether the branch cylinder is reducing for \(R_{ab}\);
- the tested commutator residual for \([P_w,R_{ab}]\) when a reducing claim is
  made.

The packet may claim a local unitary relation only if

\[
[P_w,R_{ab}]=0
\]

has passed its declared tolerance.

Without that gate,

\[
V_w^*\Delta V_w
\]

must not be replaced by

\[
(I-V_w^*RV_w)^*
(I-V_w^*RV_w).
\]

## 4. UNITARY_DILATION semantics

A packet may instead use an independently defined global unitary scale symmetry

\[
D_r.
\]

Then it must provide:

- unitary_scale_witness_ref;
- a unitarity residual;
- an intertwining residual for the claimed scale covariance.

Only on that typed surface may it use

\[
D_w^{-1}AD_w.
\]

The existence of an IFS does not establish this surface.

## 5. 36D representation boundary

The packet must always declare:

- exactly 36 finite coordinates per phase state;
- representation_type;
- coordinate_ordering;
- global_u1_quotiented;
- information_loss_ledger;
- reconstruction_contract;
- scale_semantics.

A 36D vector is a finite representation/projection.

It is not the full direct-integral Hilbert state and not a substitute for the
branch operator algebra.

## 6. IFS branch reduction firewall

If scale_semantics = IFS_COMPRESSION and

branch_reducing_for_relation = false,

then

local_relative_unitary_claim = true

is rejected.

If branch_reducing_for_relation = true, the packet must also supply

\[
\|[P_w,R]\|
\le
\varepsilon_{red}.
\]

The validator treats the reducing statement as a tested witness, not a name.

## 7. Projective 36D observable

The phase-only residual remains legal under either scale semantics:

\[
\delta^2
=
2(1-|C|).
\]

But its interpretation differs.

Under UNITARY_DILATION it may represent the projected residual of a unitary
scale-transformed relation if the intertwining test passes.

Under IFS_COMPRESSION it is only a branch-level finite feature unless the
upstream compression/reduction witness establishes the stronger operator
meaning.

## 8. Information-loss ledger

At minimum the packet must state whether it loses:

- cylinder-depth information;
- full branch address;
- fibre state;
- operator spectrum;
- global U(1);
- winding;
- non-phase amplitudes;
- coframe/bivector semantics.

An empty information-loss ledger is rejected.

## 9. Mandatory validator outcomes

PASS examples:
- projective 36-phase packet with explicit IFS compression witness;
- reducing branch with tested commutator residual;
- independently proved global unitary dilation with unitarity/intertwining
  residuals below tolerance.

FAIL examples:
- 35 or 37 phase coordinates;
- nonfinite phase coordinate;
- IFS packet with no branch witness;
- nonreducing branch advertised as a local unitary relation;
- unitary-dilation semantics with no unitary witness;
- empty information-loss ledger.

## 10. v0.1 correction ledger

Retained from v0.1:
- 36D is a projection/representation, not the full Hilbert space;
- projective coherence residual;
- global-U(1) firewall;
- arithmetic phase inputs remain typed;
- physical gravity/prime dynamics remain unestablished.

Corrected:
- generic IFS refinement is not represented by unitary \(D_r\);
- branch scale uses isometries \(V_w\);
- generic branch relation compression is not unitary;
- scale covariance must state IFS compression or unitary dilation explicitly.

canon_allowed = false.
