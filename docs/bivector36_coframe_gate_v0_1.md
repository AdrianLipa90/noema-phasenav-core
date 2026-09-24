# PhaseNav Bivector-36 Coframe Gate v0.1

Status: CANDIDATE_ONLY / EXECUTABLE_NECESSARY_GATE / PHYSICAL_GRAVITY_NOT_CLAIMED
Date: 2026-09-24

PhaseNav now has a non-arbitrary 36D geometry target based on four-dimensional exterior algebra:

\[
\dim\Lambda^2(\mathbb R^4)=6,
\qquad
\dim\operatorname{End}(\Lambda^2(\mathbb R^4))=36.
\]

A raw 36-vector may therefore be reshaped as a 6x6 candidate bivector operator. It is **not** automatically a coframe or a gravitational field.

A 4x4 coframe matrix \(e\) induces

\[
B=C_2(e)=\Lambda^2 e,
\]

where \(C_2(e)\) is the second compound matrix of 2x2 minors. In the pair basis

\[
(01,02,03,23,31,12),
\]

the canonical wedge-pairing matrix is

\[
J=\begin{pmatrix}0&I_3\\I_3&0\end{pmatrix}.
\]

Every exact coframe lift obeys

\[
B^TJB=\det(e)J.
\]

The runtime candidate therefore exposes a normalized residual for

\[
M^TJM\approx\lambda J.
\]

Passing this is a **necessary** lift gate only. Global component, orientation, reality and full Plebanski simplicity conditions remain downstream responsibilities of TIR.

The same 6D two-form carrier admits the exact Euclidean Hodge half projectors

\[
P_\pm=\frac12(I\pm\star),
\qquad
6=3+3.
\]

Lorentzian signature requires the appropriate complex self-dual/anti-self-dual treatment; the Euclidean real formula is not silently reused.

This module does not duplicate canonical PhaseNav semantic U(1) holonomy. It only exposes the 36D-to-bivector structure and liftability test required by the TIR moire gravity branch.
