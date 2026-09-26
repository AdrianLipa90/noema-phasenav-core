# Saint-Venant / Linearized Einstein Validation Receipt
Date: 2026-09-26
Status: PASS / EXACT_LINEAR_IDENTITY

Branch:

    formalism/saint-venant-linearized-einstein-v0.1-20260926

Conventions:

    (Curl A)_ij=epsilon_jkl partial_k A_il,

    inc(epsilon)=Curl[(Curl epsilon)^T].

For

    h_ij=delta_ij+2epsilon_ij,

the independent replay verifies

    inc(epsilon)=G_ij^(1)

to Frobenius residual 4.58e-16 on a generic symmetric second-derivative
control.

Additional controls:
- compatible cubic-displacement strain:
      ||inc epsilon||=2.08e-16,
      ||G^(1)||=5.09e-16;
- Kröner identity
      inc(sym beta_p)=sym Curl[(Curl beta_p)^T]
  residual 7.08e-17;
- with compatible total distortion and alpha=Curl beta_p:
      inc(epsilon_e)=-sym Curl(alpha^T)
  residual 2.70e-16;
- conformal quadratic strain
      epsilon=diag(sigma,sigma,0),
      sigma=a(x^2+y^2)
  gives
      G^(1)=diag(0,0,4a)
  exactly at float64 control precision.

Verdict:

    SAINT_VENANT_LINEARIZED_EINSTEIN_BRIDGE = PASS.

This is a geometric/continuum identity. It is not a physical identification of
defects with gravity.
