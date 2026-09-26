# Conservative Elastic Evolution Reference v0.1
Date: 2026-09-26
Status: CANDIDATE_NUMERICAL_DYNAMICS / ENERGY_LEDGER_REQUIRED

## 1. Purpose

This gate checks that the linearized second-gradient dynamics derived from the
GL(3) hyperelastic field can be evolved by a conservative time integrator
without hidden damping or forcing.

It is a verification integrator, not a production multiphysics solver.

## 2. Reduced equation

For one longitudinal or transverse periodic displacement component,

    u_tt
      = c_mode^2 u_xx
        - (eta/rho0) u_xxxx.

The finite-difference spatial operator is the exact gradient of the discrete
Hamiltonian used in the ledger.

## 3. Discrete energy

With periodic grid spacing dx,

    E
      = dx sum_i [
          rho0/2 v_i^2
          + rho0 c_mode^2/2 (D_+u_i)^2
          + eta/2 (D_2u_i)^2
        ].

The associated discrete acceleration is

    a
      = c_mode^2 D_2 u
        - (eta/rho0) D_2^2 u.

The total discrete momentum is

    P = rho0 dx sum_i v_i.

## 4. Integrator

Use velocity-Verlet / Störmer-Verlet:

    v_{n+1/2}=v_n+(dt/2)a(u_n),
    u_{n+1}=u_n+dt v_{n+1/2},
    v_{n+1}=v_{n+1/2}+(dt/2)a(u_{n+1}).

For the chosen spatial discretization,

    omega_max^2
      = c_mode^2 4/dx^2
        + (eta/rho0)16/dx^4.

The code fails closed unless

    dt < 2/omega_max.

## 5. Required ledger

Every evolution run exposes:
- kinetic energy;
- ordinary elastic energy;
- gradient energy;
- total energy;
- total momentum.

The numerical state is not accepted as a conservative reference evolution
without this ledger.

## 6. Validation targets

The reference suite checks:
- exact zero mode;
- uniform-velocity solution;
- exact discrete Fourier eigenvalue;
- nonnegative ledger components;
- bounded long-run symplectic energy error;
- momentum conservation;
- timestep stability rejection.

## 7. Boundary

This gate does not yet solve the full nonlinear 3D neo-Hookean field.
Its role is to verify:
- the sign and spectral content of the derived linearized operator;
- the energy functional paired with it;
- a conservative integration strategy.

The next numerical gate may lift the same ledger discipline to the full
nonlinear finite-strain field.
