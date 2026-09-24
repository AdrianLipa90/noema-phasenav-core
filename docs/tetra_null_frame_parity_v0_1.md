# PhaseNav Tetrahedral Null-Frame / Stella Parity v0.1

Status: CANDIDATE_ONLY / EXACT_LOCAL_FRAME_GEOMETRY / GRAVITY_DYNAMICS_OPEN
Date: 2026-09-24

This module implements the non-arbitrary frame route supplied by the existing TIR x IDT event lift.

For the four tetrahedral Bloch directions \(n_a\),

\[
x_a=\frac{\ell}{2}(1,n_a)
\]

are four null Minkowski vectors with

\[
x_a\cdot x_b=\frac{\ell^2}{3}
\quad(a\neq b).
\]

Their Gram determinant is

\[
-\frac{\ell^8}{27},
\]

so they form a full-rank 4D frame for every \(\ell>0\).

For the antipodal Stella sheet and scale ratio \(q=\ell_-/\ell_+\),

\[
\boxed{
e_{-+}=E_-E_+^{-1}
=
q\operatorname{diag}(1,-1,-1,-1).
}
\]

Thus the ideal T / -T pair is an exact spatial-parity sector with an optional positive conformal scale.

On bivectors,

\[
\boxed{
\Lambda^2e_{-+}
=
q^2\operatorname{diag}(-1,-1,-1,+1,+1,+1)
}
\]

in the pair basis

\[
(01,02,03,23,31,12).
\]

The first three time-space channels flip sign; the last three space-space channels do not.

This route is independent of the legacy anonymous `phi_0...phi_35` coordinate ordering. It constructs the 4D frame first and obtains the 6x6 bivector operator functorially.

Important firewall:

- constant parity is not gravity;
- constant conformal scale is not gravity;
- an exact T / -T pair is too symmetric to span generic GR.

The general local route is instead

\[
E_1(x),E_2(x)
\to
e(x)=E_2(x)E_1(x)^{-1}
\to
C_2(e(x)).
\]

The module therefore exposes `generic_frame_pair()` for algebraic testing of deformed independent frame pairs. The physical law that produces such deformations remains a TIR dynamics gate.
