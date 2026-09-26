# Defect Density Transport Validation Receipt
Date: 2026-09-26
Status: PASS / INDEPENDENT_REPLAY_7_OF_7

Branch:

    dynamics/defect-transport-v0.1-20260926

Reference transport:

    partial_tau alpha_c + div(v alpha_c)=0

componentwise on a periodic 2D grid with prescribed constant velocity.

Numerics:
- conservative upwind finite volume;
- fail-closed CFL |vx|dt/dx+|vy|dt/dy<=1.

Replay:
1. zero velocity identity — PASS;
2. exact one-cell shift at one-direction CFL=1 — PASS;
3. per-component inventory conservation — PASS;
4. positivity under admissible CFL — PASS;
5. CFL violation rejection logic — PASS;
6. discrete div-alpha=0 preservation under uniform advection — PASS;
7. scalar L2 does not increase under upwind transport — PASS.

Measured:
- max component-inventory drift after 100 steps: 7.10543e-15;
- min value in positive-field test after 50 steps: 1.68260e-5;
- max discrete divergence after 80 steps: 4.23273e-16;
- example L2: 640.0 -> 597.69464 (numerical upwind diffusion).

Boundary:
this is source-free conservation transport, not a final stress-driven
dislocation mobility law.
