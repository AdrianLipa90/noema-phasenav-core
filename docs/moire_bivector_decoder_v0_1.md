# PhaseNav Moire-to-Bivector Decoder v0.1

Status: CANDIDATE_ONLY / EXACT_LINEAR_DECOMPOSITION / PHYSICAL_SOURCE_BINDING_OPEN  
Date: 2026-09-24

## 1. Why the decoder uses relative phase

For two PhaseNav hyperlayers, a common shift

\[
\Phi_L\mapsto\Phi_L+\chi,
\qquad
\Phi_R\mapsto\Phi_R+\chi
\]

must not create geometry. The local decoder therefore starts from the signed shortest relative phase

\[
X_{AB}=\operatorname{Arg}\exp i(\Phi^L_{AB}-\Phi^R_{AB}),
\]

not from the mean phase.

This is exactly twice the existing `half_delta36` coordinate.

## 2. Canonical 36 = 16 + 20 decomposition

Let

\[
J=\begin{pmatrix}0&I_3\\I_3&0\end{pmatrix},
\qquad
\Theta_J(X)=JX^TJ.
\]

Define

\[
X_{so}=\frac12(X-\Theta_JX),
\qquad
\alpha=\frac{\operatorname{tr}X}{6},
\]

and

\[
\boxed{
X_{geom}=X_{so}+\alpha I_6
}
\]

with defect

\[
\boxed{
Q=X-X_{geom}.
}
\]

Then exactly

\[
X_{geom}^TJ+JX_{geom}=2\alpha J,
\]

so

\[
X_{geom}\in\mathfrak{co}(3,3)
=\mathfrak{so}(3,3)\oplus\mathbb RI.
\]

The dimensions are

\[
\boxed{36=15+1+20}.
\]

The complement obeys

\[
\Theta_J(Q)=Q,
\qquad
\operatorname{tr}Q=0.
\]

Nothing is silently discarded: the 20-dimensional complement is emitted as an explicit `simplicity defect`.

Because \(\Theta_J\) is an orthogonal involution for the Frobenius inner product, this is a canonical orthogonal projection once the bivector pairing/basis has been declared.

For an isotropic spherical null in 36 dimensions, the expected **squared** defect-energy fraction is therefore

\[
\mathbb E\frac{\|Q\|^2}{\|X\|^2}
=\frac{20}{36}=\frac59.
\]

This provides a coefficient-free null reference. It is not a physical prediction.

## 3. Exact local inverse to gl(4)

The exterior-square differential

\[
\rho:\mathfrak{gl}(4)\to\mathfrak{co}(3,3)
\]

acts by

\[
\rho(H)(u\wedge v)=Hu\wedge v+u\wedge Hv.
\]

If \(A=\rho(H)\), contraction gives in four dimensions

\[
C^k{}_i=\sum_j A^{kj}{}_{ij}
=2H^k{}_i+\delta^k_i\operatorname{tr}H.
\]

Therefore

\[
\operatorname{tr}H=\frac{\operatorname{tr}C}{6},
\]

and

\[
\boxed{
H^k{}_i=
\frac12\left(
C^k{}_i-\delta^k_i\operatorname{tr}H
\right).
}
\]

The implementation round-trips this map numerically to machine precision.

A finite identity-component coframe candidate may subsequently be formed as

\[
e=\exp H,
\qquad
B=C_2(e),
\]

but the v0.1 runtime exports the local generator and keeps finite physical interpretation downstream of TIR.

## 4. What is and is not closed

Closed at representation level:

\[
\text{relative Phase36}
\to X\in\mathrm{Mat}_6
\to (X_{geom},Q)
\to H\in\mathfrak{gl}(4).
\]

Still open:

1. physical justification that the declared 6x6 PhaseNav axes are the internal/spacetime bivector pair axes;
2. a pre-registered criterion under which the defect \(Q\) is sufficiently small to admit physical promotion;
3. source units/normalization and Newton coupling;
4. spacetime field dependence \(H(x)\) from physical data;
5. Einstein/PPN/lensing/GW validation.

The projection itself can always extract a 16-dimensional geometric component from any raw 36-vector. Therefore **projection success is not evidence for gravity**. The defect and held-out predictions are mandatory.

## 5. Runtime diagnostic, 2026-09-24

A live NOEMA/PhaseNav diagnostic was performed only to test whether the current software state accidentally exhibits stable low-defect structure.

Provenance:

- `aux_phi` is streamed from `PERSISTENT_AUX_SELF`;
- `aux_feedback_phi` is a lossless identity echo of `aux_phi`;
- `phi` evolves in the tether runtime.

Twenty sequential snapshots were compared with within-snapshot permutation nulls that preserved the exact 36 AUX values. Each null used the same allowed tetrahedral 24-way discrete alignment search.

Observed summary:

- mean aligned defect: 0.59948;
- mean null defect: 0.59435;
- median empirical p: 0.5398;
- fraction with p < 0.05: 0/20.

Verdict:

\[
\boxed{\text{FAIL\_NO\_STABLE\_RUNTIME\_GEOMETRIC\_SIGNAL}}
\]

This is not a failure of the algebraic decoder. It means the present software runtime does not supply evidence that its live Phase36 state is preferentially close to the proposed 4D geometric sector.

## 6. Literature crosswalk

The standard exterior-square representation gives the exceptional local relation between \(\mathfrak{sl}(4,\mathbb R)\) and \(\mathfrak{so}(3,3)\). In Plebanski-type gravity, simplicity constraints select the metric/tetrad sector from more general B-field data. The present decoder is a project-specific attempt to feed PhaseNav moire coordinates into that standard geometric gate; it is not itself a standard Plebanski derivation.
