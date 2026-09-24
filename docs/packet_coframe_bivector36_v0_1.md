# PhaseNav Four-Packet Coframe / Bivector36 Bridge v0.1

Status: CANDIDATE_ONLY / EXECUTABLE_TYPED_BRIDGE / PHYSICAL_GRAVITY_NOT_CLAIMED  
Date: 2026-09-24

The bridge consumes four explicit TIR x IDT elapsed-state packets

\[
x_a=\frac{\ell_a}{2}(1,\mathbf r_a),
\qquad
\ell_a>0,
\quad
|\mathbf r_a|\le1,
\]

and forms

\[
E=[x_0\;x_1\;x_2\;x_3].
\]

The frame is admitted only if \(\det E\neq0\).

For two admitted frames,

\[
e_{BA}=E_BE_A^{-1}
\]

is their relative coframe/layer operator and

\[
B_{BA}=C_2(e_{BA})
\]

is the generated 6x6 / 36-coefficient bivector representation.

This makes the typed direction explicit:

\[
\boxed{
\text{elapsed/Bloch packets}
\to
4D\ \text{frame}
\to
\text{relative coframe}
\to
36D\ \text{bivector operator}.
}
\]

The legacy PhaseNav vector \(\phi_0,\ldots,\phi_{35}\) is not accepted by this module as a gravitational coframe source.

For the canonical tetrahedral pure-state frame, all four columns are future null and the frame is nondegenerate. Its antipodal companion obeys

\[
E_{-T}=PE_T,
\qquad
P=\operatorname{diag}(1,-1,-1,-1).
\]

Therefore

\[
C_2(P)=\operatorname{diag}(-I_3,+I_3)
\]

in the ordered pair basis \((01,02,03,23,31,12)\).

A spatially constant relative coframe is not physical curvature. TIR owns the downstream field/dynamics/Levi-Civita curvature gate.
