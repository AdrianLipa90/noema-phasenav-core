# Defect Density Transport Reference v0.1
Date: 2026-09-26
Status: CANDIDATE_KINEMATIC_TRANSPORT / CONSTITUTIVE_VELOCITY_OPEN

## 1. Separation from compatible elasticity

For a smooth compatible deformation,

    F=Grad y,

the row-wise incompatibility tensor

    alpha=Curl F

vanishes.

Therefore a nonzero defect field must not be silently generated while still
claiming F is globally compatible.

This gate treats alpha as an independently admitted defect-density state.

## 2. Source-free transport harness

For each admitted component alpha_c on a periodic 2D reference domain, use

    partial_tau alpha_c
      + div(v alpha_c)
      =0

for a prescribed velocity v.

This is a conservation harness. It is not claimed as the final constitutive
law for physical dislocation motion.

The periodic integral

    integral alpha_c dA

is preserved component by component.

## 3. Numerical update

Use conservative first-order upwind finite-volume fluxes.

Fail-closed CFL condition:

    |v_x| dt/dx
      + |v_y| dt/dy
      <=1.

Consequences at this reference level:
- exact component inventory conservation up to roundoff;
- positivity preservation for nonnegative scalar components;
- numerical L2 dissipation rather than artificial growth;
- exact one-cell translation when one-direction CFL=1.

## 4. Divergence-of-Curl consistency

Each row of a true Curl field obeys

    div alpha_i = 0

in the smooth continuum because div curl = 0.

For uniform prescribed advection on the periodic grid, the translation
operator commutes with the same constant-coefficient discrete derivatives.
The validation therefore checks that a divergence-free row constructed from a
streamfunction remains divergence-free to roundoff.

## 5. What remains constitutive

Not yet supplied:
- stress-driven defect velocity;
- Peach-Koehler force;
- Burgers-vector/line-direction resolved kinetics;
- creation/annihilation sources;
- multiplicative F=F_e F_p plastic decomposition;
- thermodynamic dissipation inequality coupling alpha to F.

Those are separate physics choices and must not be inferred from conservation
alone.

The next gate is a thermodynamically admissible stress-defect coupling.
