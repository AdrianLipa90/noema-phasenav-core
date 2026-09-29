# Finite-Strain Multiplicative Plasticity Validation Receipt
Date: 2026-09-26
Status: PASS / INDEPENDENT_CROSSCHECK

Branch:

    dynamics/finite-strain-multiplicative-plasticity-v0.1-20260926

Validated kinematics:

    F=F_e F_p,
    F_e=F F_p^{-1},

with all admitted factors in GL+(3).

Elastic energy:

    psi(F_e)
      =mu/2[tr(F_e^T F_e)-3-2ln det F_e]
       +lambda/2[ln det F_e]^2.

Mandel-driven flow:

    M=F_e^T P_e,

    L_p
      =m_dev dev(sym M)
       +m_vol mean(M) I.

At fixed F:

    psi_dot=-M:L_p<=0.

Update:

    F_p^{n+1}=exp(dt L_p)F_p^n.

Independent numerical/algebraic crosschecks:
- factorization F_e F_p=F — PASS;
- objectivity under F->QF — PASS;
- rigid rotation gives M=0 and L_p=0 — PASS;
- isotropic-energy Mandel stress is symmetric — PASS;
- M:L_p is nonnegative — PASS;
- multiplicative step keeps det(F_p)>0 — PASS;
- m_vol=0 preserves det(F_p) to ~1e-15 over 20 steps — PASS;
- finite-difference psi_dot agrees with -M:L_p to relative error 2.22e-7 — PASS;
- central finite difference of psi with respect to total F agrees with
  P=P_e F_p^{-T}; tested component errors were ~5.7e-12 to 2.7e-10 — PASS;
- pure-Python scaling/squaring expm agrees with scipy.linalg.expm to
  Frobenius error 2.54e-16 on the control matrix — PASS;
- det(exp A)=exp(tr A) error 2.22e-16 on the control matrix — PASS.

Verdict:

    FINITE_STRAIN_MULTIPLICATIVE_REFERENCE = PASS.

Boundary:
- no finite-strain dislocation-density convention promoted;
- no yield surface/rate-independent flow;
- no empirical material calibration;
- no spacetime/gravity interpretation.
