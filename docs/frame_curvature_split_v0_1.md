# PhaseNav 36D Frame/Curvature Split v0.1

Status: CANDIDATE_ONLY / EXACT_REPRESENTATION_CROSSWALK / PHYSICAL_CURVATURE_BINDING_OPEN  
Date: 2026-09-24

This note corrects one interpretation in `moire_bivector_decoder_v0_1`.

The existing exact decomposition

\[
X=X_{\rm geom}+Q
\]

remains valid, but the 20-dimensional complement \(Q\) should not generically be called a "simplicity defect".

With the four-dimensional wedge pairing

\[
J=\begin{pmatrix}0&I_3\\I_3&0\end{pmatrix},
\]

the exact conditions

\[
JQ=Q^TJ,
\qquad
\operatorname{tr}Q=0
\]

imply that

\[
S=JQ
\]

is a symmetric bilinear form on \(\Lambda^2\) satisfying the single 4D algebraic Bianchi condition.

Thus the representation-level split is

\[
\boxed{
\operatorname{Mat}_6
=
\mathfrak{co}(3,3)_{16}
\oplus
\mathcal K(V)_{20},
}
\]

where \(\mathcal K(V)\) is the space of algebraic curvature tensors.

The runtime now exposes this interpretation through `split_frame_curvature()`.

Important firewall:

\[
Q_{\rm alg}(x)
\neq
R_{\rm physical}(x)
\]

unless an independent differential gate proves compatibility with the selected coframe/connection,

\[
Q_{\rm alg}
\stackrel?=
R[\omega_{LC}(e)].
\]

The old 20-snapshot small-defect runtime experiment is retained for provenance, but its use as a **geometry promotion criterion is deprecated**. It tested a hypothesis that the curvature sector should be small; the corrected representation theory does not require that.

For the exact canonical tetrahedral edge-transport overlap matrix supplied by TIR, the two Frobenius-energy fractions are

\[
\boxed{
f_{frame}=f_{curvature}=1/2.
}
\]

This is a witness-specific exact identity, not a universal physical law.
