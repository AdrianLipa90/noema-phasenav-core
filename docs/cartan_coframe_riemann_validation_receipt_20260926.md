# Cartan Coframe -> Riemann Reference Validation Receipt
Date: 2026-09-26
Status: PASS / ANALYTIC_NONFLAT_REFERENCE

Branch:

    formalism/cartan-coframe-riemann-reference-v0.1-20260926

Reference:

    e^0=dt,
    e^1=e^sigma dx,
    e^2=e^sigma dy,
    e^3=dz,

    sigma=a(x^2+y^2).

Metric:

    g=diag(-1,e^(2sigma),e^(2sigma),1).

Torsion-free spin connection:

    omega^1_2=sigma_y dx-sigma_x dy,
    omega^2_1=-omega^1_2.

Independent checks:
- Cartan torsion T^a_xy=0 exactly on control points — PASS.
- spin curvature:
      Omega^1_2=-(Delta sigma) dx^dy
  with Delta sigma=4a — PASS.
- Cartan-to-coordinate conversion:
      R^x_{ yxy}=-4a,
      R^y_{ xxy}=+4a
  — PASS.
- independent SymPy Christoffel/Riemann calculation gives exactly the same
  components — PASS.
- independent SymPy scalar curvature:
      R=-8a exp[-2a(x^2+y^2)]
  matching 2K — PASS.
- flat a=0 limit gives zero torsion and zero curvature — PASS.
- exact rectangle SO(2) spin holonomy obeys the shrinking-area curvature
  limit; observed errors for h=0.2,0.1,0.05,0.025:
      1.81014e-2,
      4.52548e-3,
      1.13137e-3,
      2.82843e-4
  — PASS.
- induced Bivector36 curvature remains in so(3,3) — PASS.

Verdict:

    CARTAN_SPIN_CURVATURE_TO_RIEMANN_REFERENCE = PASS.

This validates the mathematical binding for the declared nonflat torsion-free
reference. It does not establish a physical spacetime/coframe identification
for PhaseNav or Moire.
