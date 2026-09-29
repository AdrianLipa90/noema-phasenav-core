# GL(3) Hyperelastic Field Dynamics Validation Receipt
Date: 2026-09-26
Status: PASS / INDEPENDENT_ALGEBRAIC_REPLAY_7_OF_7

Branch:

    dynamics/gl3-hyperelastic-field-v0.1-20260926

Validated model:

    F=I+Grad u,
    J=det F>0,

    W(F)
      =mu/2[tr(F^T F)-3-2ln J]
       +lambda/2(ln J)^2,

    P(F)
      =mu(F-F^{-T})
       +lambda ln(J)F^{-T},

    W_grad=eta/2|Grad F|^2,

    rho0 u_tt
      =Div P
       -Div Div H,
    H=eta Grad F.

Independent replay:
1. W(R)=0 and P(R)=0 for rigid rotations — PASS;
2. W(RF)=W(F) frame indifference — PASS;
3. small-strain limit converges to Lamé energy — PASS;
4. longitudinal/transverse dispersions positive — PASS;
5. discrete Fourier check confirms the -eta Delta^2 u sign — PASS;
6. Curl F=0 for compatible Hessian fields — PASS;
7. incompatible Grad F produces nonzero defect diagnostic — PASS.

Observed small-strain relative errors for scale factors
1e-3, 5e-4, 2.5e-4:

    1.4687e-4
    7.3443e-5
    3.6725e-5

consistent with cubic nonlinear correction relative to quadratic energy.

Boundary:
- this validates the continuum reference equations;
- no empirical material constants are claimed;
- no gravity interpretation is introduced.
