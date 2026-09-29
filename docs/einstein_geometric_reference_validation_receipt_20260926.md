# Einstein Geometric Reference Validation Receipt
Date: 2026-09-26
Status: PASS / GEOMETRY_ONLY

Branch:

    formalism/einstein-geometric-reference-v0.1-20260926

Reference metric:

    g=diag(-1,e^(2sigma),e^(2sigma),1),
    sigma=a(x^2+y^2).

Independent SymPy calculation:
- Ricci:
      diag(0,-4a,-4a,0).
- scalar curvature:
      R=-8a exp[-2a(x^2+y^2)].
- Einstein tensor:
      G_cov
        =diag(
          -4a exp[-2sigma],
           0,
           0,
          +4a exp[-2sigma]
        ).
- mixed Einstein tensor:
      G^mu_nu
        =diag(q,0,0,q),
      q=4a exp[-2sigma].
- contracted Bianchi:
      nabla_mu G^mu_nu=0
  exactly for all four components.

Additional controls:
- G^mu_mu=-R — PASS;
- flat a=0 limit gives G=0 — PASS;
- G_mu_nu symmetric — PASS.

Verdict:

    EINSTEIN_GEOMETRIC_REFERENCE = PASS.

No source tensor, gravitational coupling or cosmological term is inferred or
fit in this receipt.
