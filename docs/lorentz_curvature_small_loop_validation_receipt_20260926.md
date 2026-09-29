# Lorentz Connection Curvature Small-Loop Validation Receipt
Date: 2026-09-26
Status: PASS / CONNECTION_CURVATURE_ONLY

Branch:

    formalism/lorentz-curvature-small-loop-v0.1-20260926

Field strength:

    F_mu_nu
      =partial_mu A_nu
       -partial_nu A_mu
       +[A_mu,A_nu].

For the declared constant-connection plaquette orientation,

    [H(h)-I]/h^2
      -> [A_mu,A_nu].

Independent shrinking-loop errors for h=
0.1, 0.05, 0.025, 0.0125:

    1.00252e-1
    5.00313e-2
    2.50039e-2
    1.25005e-2

showing the expected O(h) error after division by area for a first
group-commutator plaquette.

Additional controls:
- orientation reversal gives the opposite leading field-strength sign — PASS;
- commuting constant connection gives zero field strength and trivial loop — PASS;
- d(Lambda^2) preserves the curvature commutator exactly — PASS;
- constant Lorentz gauge conjugation carries F -> GFG^{-1} — PASS;
- constant-connection Bianchi reduces to the exact Jacobi identity — PASS;
- explicit derivative terms enter as d_mu A_nu-d_nu A_mu — PASS;
- pure-Python 4x4 expm agrees with scipy.linalg.expm to 4.86e-16 on an
  independent mixed-generator control; Lorentz metric residual 9.46e-16.

Verdict:

    LORENTZ_CONNECTION_CURVATURE = PASS_AS_GAUGE_FIELD_STRENGTH.

Not yet established:

    LORENTZ_CONNECTION_CURVATURE
      == PHYSICAL_SPACETIME_RIEMANN.

That requires a coframe/spin-connection/torsion binding.
