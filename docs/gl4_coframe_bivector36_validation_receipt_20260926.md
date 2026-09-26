# GL(4) Coframe / Bivector36 Kinematics Validation Receipt
Date: 2026-09-26
Status: PASS / INDEPENDENT_CROSSCHECK_9_GATES

Branch:

    formalism/gl4-coframe-bivector36-v0.1-20260926

Core representation:

    rho_36(A)=Lambda^2 A,
    A in GL(4).

Independent checks:
1. Lambda^2(AB)=Lambda^2(A)Lambda^2(B):
   Frobenius residual 5.88e-16 — PASS.
2. det(Lambda^2 A)=det(A)^3:
   absolute discrepancy ~1.3e-15 on control matrix — PASS.
3. spatial GL(3) embedding recovers diag(F,cof(F)):
   residual 5.16e-16 — PASS.
4. proper Lorentz boost preserves eta:
   residual 6.17e-16; det=1+2.2e-16 — PASS.
5. induced bivector Lorentz transform preserves G_(3,3):
   residual 1.13e-15; det=1+2.2e-16 — PASS.
6. declared bivector metric signature:
   diag(-1,-1,-1,+1,+1,+1) — PASS.
7. spatial SO(3) restriction recovers previous Bivector36 rotation carrier:
   residual <=1.76e-16 on controls — PASS.
8. coframe metric g=e^T eta e is invariant under left Lorentz action:
   residual 6.60e-16 — PASS.
9. exact Z2 kernel:
   Lambda^2(A)-Lambda^2(-A)=0 exactly on control — PASS.

A generic GL(4) deformation is explicitly rejected as a Lorentz
transformation unless it satisfies the Lorentz metric/determinant/time
orientation gates.

Verdict:

    GL4_COFRAME_BIVECTOR36_KINEMATICS = PASS.

Boundary:
- no connection/curvature claim in this receipt;
- no Einstein dynamics;
- Bivector36 -> coframe inverse has an unavoidable A ~ -A ambiguity.
