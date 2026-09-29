# Typed T36 -> Bivector36 SO(2) Adapter v0.1
Date: 2026-09-26
Status: TYPED_ADAPTER_PASS / GENERIC_LEGACY_T36_FAIL_CLOSED

## 1. Why the generic adapter is forbidden

The canonical PNCS contracts state that the generic PhaseNav phase object is

    theta in T^36,
    basis_id = PNV_T36_PHASE_ANGLES_RADIANS_V1,

while the identities/physical meanings of coordinates 0..35 remain explicitly
unassigned.

Therefore the current project state does not select a canonical map

    generic T^36 -> BIVECTOR_OPERATOR_36.

There are infinitely many possible projections/relabelings, and choosing one
would invent axis semantics. The adapter therefore rejects the generic legacy
basis.

## 2. New typed source basis

The admitted source basis is

    PNV_MOIRE_RELATIVE_PHASE_MATRIX6_ROW_MAJOR_V1.

Its 36 coordinates are not generic semantic phases. They are the row-major
wrapped coefficients of a 6x6 Lie-generator matrix on Lambda^2(R^4).

For the calibrated x-y orbital axis,

    X(theta) = theta J_36.

The phase representation is

    phase_ij = X_ij mod 2pi.

For |theta|<pi, principal phase unwrapping recovers X exactly.

## 3. Adapter

For two typed records A and B,

    X_BA = wrap(B-A)

entry-wise.

Project onto the calibrated generator:

    theta_hat = <X_BA,J_36>_F / <J_36,J_36>_F.

Admission requires

    ||X_BA - theta_hat J_36||_F <= epsilon

with an explicit tolerance.

After admission,

    rho_36(theta_hat) = Lambda^2 R_xy(theta_hat),

and

    D_biv36
      = [6-tr rho_36]/2
      = 4 sin^2(theta_hat/2).

For a declared homobilayer lattice constant a,

    L_M = a/sqrt(D_biv36).

## 4. What this closes

The full typed chain is now

    physical relative twist
      <-> typed Moire log-phase T36
      <-> theta J_36
      <-> BIVECTOR_OPERATOR_36
      <-> Lambda^2 R_xy(theta)
      <-> scalar residual
      <-> Moire period.

The inverse is exact inside the principal branch and admitted SO(2) subspace.

## 5. What remains blocked

This does NOT authorize

    PNV_T36_PHASE_ANGLES_RADIANS_V1
      -> BIVECTOR_OPERATOR_36.

A generic legacy/live phi vector requires an upstream basis/derivation receipt
showing that its coordinates are actually in the typed Moire matrix basis.
Without that receipt the conversion remains fail-closed.

This is a provenance boundary, not a numerical limitation.
