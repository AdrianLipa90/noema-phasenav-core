# PhaseNav 36D v0.14 relational-information validation

Date: 2026-09-28
Status: REFERENCE_CONTRACT_PASS / HOSTED_CI_NOT_PRESENT

Source theorem:
AdrianLipa90/Orbital-System-base
formalism/fractal-orbital-moire-hilbert-v0.11-20260928
receipt c96531e0816dba01f3ade8a849f67494d064727a

For subgroup enlargement factor m, the v0.14 contract computes

D = ln(m),
s = 1/m,
epsilon = 1 - 1/m,
I_24pi = ln(m)/(24*pi).

For a chain, it validates

m_total = m_1*m_2,
D_total = D_1 + D_2,
s_total = s_1*s_2,
epsilon_total = epsilon_1 + epsilon_2 - epsilon_1*epsilon_2.

Controls:
- q31-like chain 5 -> 15 -> 15 gives (ln 3, 0, ln 3).
- q61-like chain 30 -> 30 -> 30 gives zero information.
- binary enlargement m=2 gives I_24pi = ln(2)/(24*pi) = kappa.

The ln(m) law is derived by the projector-state relative-entropy theorem.
The factor 24*pi is the project's pre-existing canonical normalization.

No hosted GitHub status checks were present on implementation head
6db514858a1d191c29c7ed05c0047e7ab76ea1a5.

canon_allowed = false.
