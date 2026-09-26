# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.1

Status: CANDIDATE_ONLY / REPRESENTATION_BRIDGE / CALIBRATION_SPLIT_ADDED
Date: 2026-09-26

## Why this branch exists

The earlier branch `formalism/moire-hyperlayer-36d-v0-1-20260924` contains a useful Moire/coframe/bivector candidate, but it is divergent from current `master`.

This branch keeps the current-head bridge separate and adds the calibration distinction discovered on 2026-09-26.

## Upstream mathematical object

Let

    H_MF = integral_F^oplus H_x d mu_F(x)

and

    A_FO = C(F) rtimes_(alpha,omega) G_orb.

For admitted orbital layers a,b:

    R_ab = U_a^* U_b,
    D_ab = (I-R_ab)^*(I-R_ab).

If R_ab v = exp(i theta) v, then

    D_ab v = 4 sin^2(theta/2) v.

For an identical-lattice homobilayer with lattice constant a and Moire period L_M,

    4 sin^2(theta/2) = (a/L_M)^2.

This is the scalar physical calibration. It does not yet assign physical meaning to the 36D coordinate basis.

## 36D representation contract

A PhaseNav 36D carrier is a representation/projection, not the full Hilbert space:

    Pi_36 : A_FO -> V_36,
    dim(V_36)=36.

The bridge must explicitly declare:
- coordinate ordering;
- carrier type;
- information discarded by Pi_36;
- reconstruction contract;
- whether common global U(1) is quotiented;
- the physical orbital-group representation, if any.

For phase-coordinate carriers theta^(a), theta^(b), define

    delta_j = wrap(theta_j^(b)-theta_j^(a))

and

    C_ab = (1/36) sum_j exp(i delta_j).

Three different observables must not be conflated.

### Raw relational residual

    D_raw = (1/36) sum_j 4 sin^2(delta_j/2)
          = 2 - 2 Re(C_ab).

### Projective/shape residual

    D_shape = 2(1-|C_ab|).

This is global-U(1)-blind.

### Coherent-phase residual

    D_coh = 2(|C_ab|-Re(C_ab)) >= 0.

Exact decomposition:

    D_raw = D_shape + D_coh.

Calibration consequence:
if every channel is shifted by the same theta, then

    D_raw = 4 sin^2(theta/2),
    D_shape = 0.

Therefore the old projective residual cannot be used by itself as a physical
uniform-twist observable. Quotienting common phase before establishing the
physical orbital representation can erase the signal one is trying to
calibrate.

## Physical orbital representation gate

A physical 36D twist binding requires an explicit representation such as

    rho_36 : SO(2) -> End(V_36)

with a typed generator J_36:

    rho_36(theta) = exp(theta J_36).

A coordinate-wise common quantum phase is not automatically the same object as
a physical lattice rotation. Until rho_36/J_36 is identified and calibrated,
live PhaseNav 36D values remain dimensionless computational state.

## Relation to historical Moire hyperlayer candidate

The historical candidate uses signed shortest relative phases in a 6x6 phase
matrix and decomposes Mat(6) into co(3,3) plus a 20D complement.

That branch remains useful as a candidate representation because it retains
channelwise relative phase instead of immediately quotienting it away.
However it is not automatically the unique physical rho_36 and must be
forward-ported and calibrated before promotion.

## Arithmetic phase input

The On-Primes Arithmetic Relational Phase Law supplies exact cyclic characters

    chi_(q,a)(n)=exp(2 pi i a n/q).

These may enter a typed representation layer. Arithmetic exactness does not
establish a physical prime interaction.

## Fractal covariance

For a unitary scale action D_r require

    D_r U_g D_r^(-1) = U_(alpha_r(g)).

For a scale word w,

    R_ab^(w) = D_w^(-1) R_ab D_w.

A 36D implementation must test whether Pi_36 intertwines this action.

## Mandatory promotion tests

1. exactly 36 finite coordinates;
2. fail-closed validation;
3. raw residual identity D_raw = 2 - 2 Re(C);
4. projective residual identity D_shape = 2(1-|C|);
5. exact split D_raw = D_shape + D_coh;
6. common-phase blind-spot control;
7. layer-exchange symmetry;
8. relational zero for identical inputs;
9. information-loss ledger;
10. explicit rho_36/J_36 physical orbital binding before dimensional conversion;
11. historical Moire-hyperlayer replay only after clean forward-port.

## Firewall

Not established here:
- unique physical 36D realization;
- physical gravity from Moire;
- prime-driven physical dynamics;
- equivalence of winding and local residual;
- conversion of live phi/aux_phi to a physical length before rho_36/J_36 calibration.
