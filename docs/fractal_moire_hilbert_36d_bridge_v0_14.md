# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.14

Status: CANDIDATE_ONLY / RELATIONAL_UMEGAKI_INFORMATION_LAYER / KAPPA_NORMALIZATION_TYPED
Date: 2026-09-28

v0.14 adds a quantum-information invariant above the exact relational projector
layer of v0.13.

For a nested subgroup step

\[
H\le K,
\]

let

\[
m=[K:H].
\]

The normalized projector states satisfy the exact Umegaki theorem

\[
\boxed{
D(\rho_K\|\rho_H)=\ln m.
}
\]

The PhaseNav receipt therefore carries:

\[
\boxed{s=1/m}
\]

as relational survival,

\[
\boxed{\varepsilon=1-1/m}
\]

as normalized relational defect,

\[
\boxed{D=\ln m}
\]

as relational quantum information in nats, and

\[
\boxed{
\mathcal I_{24\pi}
=
\frac{\ln m}{24\pi}
}
\]

as the canonical phase-normalized information.

For a chain

\[
H_0\le H_1\le H_2,
\]

with factors

\[
m_{01}=[H_1:H_0],
\qquad
m_{12}=[H_2:H_1],
\]

the validator verifies

\[
m_{02}=m_{01}m_{12},
\]

\[
D_{02}=D_{01}+D_{12},
\]

\[
s_{02}=s_{01}s_{12},
\]

and

\[
\varepsilon_{02}
=
\varepsilon_{01}
+
\varepsilon_{12}
-
\varepsilon_{01}\varepsilon_{12}.
\]

The project canonical normalization is

\[
\kappa=\frac{\ln2}{24\pi}.
\]

Therefore for every binary relational enlargement

\[
m=2,
\]

v0.14 returns

\[
\boxed{
\mathcal I_{24\pi}=\kappa.
}
\]

This statement is exact given the declared \(24\pi\) normalization.

The theorem does not independently derive the \(24\pi\) factor.

Source theorem:

AdrianLipa90/Orbital-System-base  
formalism/fractal-orbital-moire-hilbert-v0.11-20260928  
validation receipt commit

\[
\boxed{
c96531e0816dba01f3ade8a849f67494d064727a
}
\]

Physical thermodynamic entropy and physical measurement semantics remain OPEN.

canon_allowed = false.
