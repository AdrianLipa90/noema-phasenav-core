# GL(3) Deformation / Moire Bivector36 Calibration v0.1
Date: 2026-09-26
Status: TYPED_GL3_BINDING / ROTATION_STRAIN_SHEAR_GEOMETRY

## 1. Exterior-square representation

Let F be an invertible spatial deformation in GL(3) and embed it as

    E(F)=diag(1,F).

In the ordered bivector basis

    (01,02,03,23,31,12),

the exterior-square representation is exactly

    rho_36(F)
      =Lambda^2 E(F)
      =diag(F,cof(F)),

where

    cof(F)=det(F) F^{-T}.

The 36 coefficients therefore contain:
- the direct action F on time-space bivectors;
- the induced cofactor action on spatial bivectors.

The lower block is a consistency witness, not an independent arbitrary matrix.

## 2. Recovery and admission

F is read from the upper-left 3x3 block.

Admission requires:
- invertible F;
- zero off-diagonal 3x3 blocks;
- lower-right block equal to cof(F) within explicit tolerance.

Thus the typed representation is exactly recoverable and fail-closed.

## 3. Rotation specialization

If F=R in SO(3),

    det(R)=1,
    cof(R)=R,

so

    rho_36(R)=diag(R,R),

recovering the previously calibrated SO(3) carrier exactly.

## 4. Planar general Moire geometry

Let A be the 2x2 direct-lattice primitive matrix whose columns are the primitive
vectors of layer 1.

Its reciprocal basis is

    B=2pi A^{-T}.

For layer 2 obtained by an in-plane deformation F_2,

    A_2=F_2 A,

hence

    B_2=F_2^{-T} B.

The reciprocal mismatch is

    Delta B=(F_2^{-T}-I)B.

When Delta B is invertible, the real-space Moire primitive matrix is

    A_M=2pi (Delta B)^{-T}.

This handles rotation, isotropic lattice mismatch, anisotropic strain and shear
within one linear geometric formula.

## 5. Checks

For a hexagonal lattice with lattice constant a and pure rotation theta, both
primitive Moire lengths reduce exactly to

    L_M=a/[2sin(|theta|/2)].

For pure isotropic scale mismatch F=sI,

    A_M=-(s/(s-1)) A

up to orientation sign, so primitive lengths scale as

    L_M=|s/(s-1)| a.

For s=1+epsilon and small epsilon,

    L_M ~ a/|epsilon|.

## 6. Scope

This closes the geometric rotation/strain/shear carrier.

It does not yet supply:
- elastic energy or constitutive laws;
- nonlinear spatially varying strain fields;
- dislocations/defects beyond local affine patches;
- full GL(4) spacetime/coframe dynamics;
- curvature.

Those require additional dynamics, not a new coordinate-space guess.
