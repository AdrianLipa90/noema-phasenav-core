# Bivector36 Orbital Rotation Calibration v0.1
Date: 2026-09-26
Status: TYPED_BIVECTOR36_SO2_BINDING_PASS / GENERIC_PHASENAV36_BINDING_OPEN

## 1. Physical orbital group

Use ordinary relative rotation in the physical x-y plane:

    R_xy(theta) in SO(2) subset SO(3).

Embed it in four coordinates (t,x,y,z) by leaving t and z fixed.

The typed six-dimensional bivector carrier is Lambda^2 R^4 with basis

    (01,02,03,23,31,12).

The induced representation is

    rho_36(theta) = Lambda^2 R_xy(theta),

stored as a 6x6 operator, i.e. exactly 36 real coefficients.

This supplies an explicit physical orbital representation

    rho_36 : SO(2) -> GL(6)

for the typed BIVECTOR_OPERATOR_36 carrier.

## 2. Generator

The generator

    J_36 = d/dtheta rho_36(theta)|_(theta=0)

has only four non-zero entries in the declared basis:

    J[01,02] = -1
    J[02,01] = +1
    J[23,31] = -1
    J[31,23] = +1.

Thus two bivector planes rotate while 03 and 12 are fixed.

## 3. Exact trace calibration

The representation has

    tr rho_36(theta) = 2 + 4 cos(theta).

Therefore

    d_36(theta)
      = [6 - tr rho_36(theta)]/2
      = 2 - 2 cos(theta)
      = 4 sin^2(theta/2).

Combining with homobilayer Moire geometry,

    L_M = a/[2 sin(|theta|/2)],

gives the exact typed physical calibration

    [6 - tr rho_36(theta)]/2 = (a/L_M)^2.

No fitted coefficient is required.

## 4. Inverse calibration

For an admitted matrix known to lie on this SO(2) representation orbit,

    cos(theta) = [tr rho_36 - 2]/4,

so the principal twist is

    |theta| = arccos([tr rho_36 - 2]/4).

The Moire period then follows as

    L_M = a / sqrt(d_36).

## 5. Scope

PASS:
- physical SO(2) orbital group;
- explicit J_36;
- exact 36-coefficient representation;
- group law;
- forward/inverse twist mapping;
- exact match to the scalar Moire residual;
- direct physical length calibration after declaring lattice constant a.

OPEN:
- identification of arbitrary legacy PhaseNav phi vectors with this carrier;
- claim that every 36D PhaseNav vector is a bivector operator;
- physical meaning of the historical 6x6 phase-coordinate factorization;
- gravity/curvature interpretation.

The calibration therefore closes the physical orbital axis for a typed
BIVECTOR_OPERATOR_36 representation while preserving the firewall around
generic PhaseNav 36D state.
