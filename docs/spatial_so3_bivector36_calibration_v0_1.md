# Spatial SO(3) Bivector36 Calibration v0.1
Date: 2026-09-26
Status: TYPED_SPATIAL_SO3_BINDING_PASS / GENERIC_T36_UNCHANGED

## 1. Representation

Let R be an ordinary physical spatial rotation in SO(3), embedded in four
coordinates as

    E(R)=diag(1,R).

In the bivector basis

    (01,02,03,23,31,12),

the exterior-square representation satisfies exactly

    Lambda^2 E(R) = diag(R,R).

Thus one physical spatial rotation is represented by a 6x6 operator, i.e.
36 real coefficients, without inventing 36 independent physical axes.

## 2. Lie algebra

For rotation vector omega=(omega_x,omega_y,omega_z), let

    [omega]_x

be the usual 3x3 cross-product generator.

Then

    J_36(omega)=diag([omega]_x,[omega]_x).

For unit-axis generators J_x,J_y,J_z,

    [J_x,J_y]=J_z,
    [J_y,J_z]=J_x,
    [J_z,J_x]=J_y.

The previously calibrated x-y planar rotation is exactly the z-axis subgroup.

## 3. Trace invariant

For any rotation axis and principal angle theta,

    tr(R)=1+2cos(theta),

so

    tr(rho_36)=2+4cos(theta),

and therefore

    D_rot=[6-tr(rho_36)]/2
         =4sin^2(theta/2).

The scalar residual is axis-independent; axis information resides in the
off-diagonal structure of the two R blocks.

## 4. Typed log-phase carrier

Candidate source basis:

    PNV_SPATIAL_SO3_LOG_PHASE_MATRIX6_ROW_MAJOR_V1.

It stores the wrapped entries of

    J_36(omega)

as 36 phase coordinates.

For ||omega||<pi, principal unwrapping plus projection onto
span{J_x,J_y,J_z} recovers the full rotation vector.

Admission is fail-closed on:
- generic T36 basis;
- branch-cut proximity;
- components outside the so(3) generator subspace.

## 5. Relation to Moire calibration

For a planar homobilayer, the standard Moire period formula applies when the
relative rotation axis is the common layer normal. In that case the full SO(3)
carrier reduces to the previously calibrated SO(2) subgroup and

    D_rot=(a/L_M)^2.

For arbitrary 3D relative orientation, D_rot remains a rotation invariant but
must not be interpreted as a planar Moire period unless the common-normal
condition is separately satisfied.

## 6. Scope

PASS:
- full physical SO(3) spatial orbital representation;
- exact 36-coefficient bivector operator;
- so(3) commutator algebra;
- axis-independent trace residual;
- axis-angle inverse away from 0/pi singular branches;
- typed 3-component rotation-vector T36 log carrier;
- exact compatibility with prior z-axis SO(2) calibration.

OPEN:
- Lorentz boosts / full SO(1,3);
- strain/shear and general GL(3)/GL(4);
- generic legacy T36 physical binding;
- physical interpretation of untyped live phi.
