# Stress–Plastic–Defect Gradient Flow Validation Receipt
Date: 2026-09-26
Status: PASS / INDEPENDENT_REPLAY_8_OF_8

Branch:

    dynamics/stress-plastic-defect-flow-v0.1-20260926

Free energy:

    psi
      =mu |sym(Grad u-beta_p)|^2
       +lambda/2 [tr sym(Grad u-beta_p)]^2
       +H/2 |beta_p|^2.

Stress:

    sigma
      =2mu eps_e
       +lambda tr(eps_e)I.

Driving force:

    Y=sigma-H beta_p.

Onsager flow:

    beta_p_dot=M Y,

with exact fixed-total-strain sectorwise solution.

Replay:
1. equilibrium driving force zero — PASS;
2. exact relaxation lowers energy for multiple dt scales — PASS;
3. exact semigroup property — PASS;
4. dpsi/dtau=-M|Y|^2 finite-difference check — PASS;
5. infinitesimal rigid rotation gives zero stress — PASS;
6. skew beta_p does not enter stress and hardening relaxes it — PASS;
7. H=0 relaxes symmetric stress to zero while preserving skew beta_p — PASS;
8. Curl beta_p vanishes for a compatible plastic-gradient field — PASS.

Measured:
- equilibrium force norm: 2.68204e-16;
- semigroup residual norm: 9.96523e-18;
- dissipation identity relative finite-difference error: 1.27538e-6.

Boundary:
- small-strain viscous plasticity only;
- no yield surface or crystal slip;
- no finite-strain multiplicative decomposition;
- no Peach-Koehler line law.
