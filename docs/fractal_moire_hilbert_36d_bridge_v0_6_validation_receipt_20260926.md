# Fractal Moire-Hilbert 36D v0.6 Inductive-Limit Validation Receipt

Date: 2026-09-26
Status: REFERENCE_PASS / HOSTED_CI_NOT_PRESENT / REPRESENTATION_CONTRACT_ONLY

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.6-20260926

Independent contract controls:

- FINITE_LEVEL_ONLY without infinite claim: PASS;
- INDUCTIVE_STEP_COVARIANT with residuals
  2e-13, 3e-13, 4e-13, 5e-13: PASS;
- INDUCTIVE_LIMIT_COVARIANT without family witness: REJECT as designed;
- ARPL procyclic limit control:
      current L_N=30,
      next L_{N+1}=90,
      branching=3,
      first positive mismatch
        4 sin^2(pi/30)
        = 0.04370479853238871
  — PASS;
- non-divisible ARPL transition 30 -> 91: REJECT;
- cross-level residual 1e-3 above tolerance: REJECT;
- exact-36 firewall inherited.

The ARPL limit subtype may reference the theorem-level results

    sigma(U_infinity)=S^1,

    sigma(Delta_infinity)=[0,4],

only when family/cofinality/theorem witnesses are explicitly supplied.

A single finite packet never establishes the infinite limit by itself.

GitHub combined status on the current implementation head returned no status
checks. Hosted CI PASS is therefore not claimed.

canon_allowed = false.
