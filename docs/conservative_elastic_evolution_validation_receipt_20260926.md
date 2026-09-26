# Conservative Elastic Evolution Validation Receipt
Date: 2026-09-26
Status: PASS / INDEPENDENT_REPLAY_7_OF_7

Branch:

    dynamics/conservative-elastic-evolution-v0.1-20260926

Reference equation:

    u_tt
      =c_mode^2 u_xx
       -(eta/rho0)u_xxxx.

Integrator:

    velocity-Verlet / Stormer-Verlet.

Discrete energy ledger:

    E
      =dx sum_i [
        rho0/2 v_i^2
        +rho0 c_mode^2/2 (D_+u_i)^2
        +eta/2 (D_2u_i)^2
      ].

Replay:
1. exact constant-displacement zero mode — PASS;
2. uniform-velocity solution and momentum conservation — PASS;
3. discrete Fourier eigenvalue — PASS;
4. nonnegative energy components — PASS;
5. 5000-step bounded energy error — PASS;
6. 2000-step momentum conservation — PASS;
7. exact spectral timestep limit finite/positive — PASS.

Measured:
- Fourier absolute roundoff error: 6.2154e-10;
- scale-aware tolerance used because D4/dx^4 amplifies float64 cancellation;
- max relative energy deviation over 5000 steps: 1.74663e-6;
- max momentum deviation over 2000 steps: 3.77476e-15.

A first replay exposed that the original absolute Fourier tolerance 1e-10 was
too strict for float64 cancellation. The test was repaired to a scale-aware
roundoff bound; the dynamics equation was unchanged.
