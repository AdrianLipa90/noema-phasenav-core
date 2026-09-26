# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.1

Status: CANDIDATE_ONLY / REPRESENTATION_BRIDGE / TYPED_BIVECTOR36_SO2_CALIBRATED
Date: 2026-09-26

## Why this branch exists

The earlier branch `formalism/moire-hyperlayer-36d-v0-1-20260924` contains a useful Moire/coframe/bivector candidate, but it is divergent from current `master`.

This branch keeps the current-head bridge separate and records the calibrated distinction between:
- generic PhaseNav 36D state;
- phase-coordinate 36D carriers;
- the physically typed BIVECTOR_OPERATOR_36 carrier.

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

For an identical-lattice homobilayer,

    L_M = a/[2 sin(|theta|/2)],

so

    4 sin^2(theta/2) = (a/L_M)^2.

## Generic phase-coordinate 36D split

For phase-coordinate carriers theta^(a), theta^(b), define

    delta_j = wrap(theta_j^(b)-theta_j^(a)),
    C_ab = (1/36) sum_j exp(i delta_j).

Then

    D_raw   = 2 - 2 Re(C_ab),
    D_shape = 2(1-|C_ab|),
    D_coh   = 2(|C_ab|-Re(C_ab)),

with the exact identity

    D_raw = D_shape + D_coh.

A uniform common phase is visible in D_raw but erased by D_shape. Therefore a
global-U(1)-blind quotient cannot be used by itself as a physical uniform-twist
observable.

## Typed physical Bivector36 orbital representation

For the typed carrier BIVECTOR_OPERATOR_36, physical x-y rotation is represented by

    rho_36(theta) = Lambda^2 R_xy(theta),

where R_xy(theta) is the ordinary spatial SO(2) rotation embedded in
(t,x,y,z), and rho_36 is stored as a 6x6 operator (36 real coefficients) in the
basis

    (01,02,03,23,31,12).

This gives an explicit physical orbital generator

    J_36 = d/dtheta rho_36(theta)|_(theta=0).

Its only nonzero entries are

    J[01,02] = -1,
    J[02,01] = +1,
    J[23,31] = -1,
    J[31,23] = +1.

The exact representation trace is

    tr rho_36(theta) = 2 + 4 cos(theta).

Hence the calibrated typed 36D residual is

    D_biv36
      = [6 - tr rho_36(theta)]/2
      = 4 sin^2(theta/2)
      = (a/L_M)^2.

Thus the physical orbital-axis calibration is CLOSED for this typed carrier.

The principal inverse is

    |theta| = arccos([tr rho_36 - 2]/4),

and

    L_M = a/sqrt(D_biv36).

## Scope boundary

PASS:
- scalar homobilayer Moire calibration;
- generic 36D raw/shape/coherent split;
- typed BIVECTOR_OPERATOR_36 SO(2) representation;
- explicit J_36;
- exact group law;
- exact trace-to-twist map;
- exact twist-to-Moire-length map after declaring lattice constant a.

OPEN:
- identifying arbitrary legacy PhaseNav phi vectors with BIVECTOR_OPERATOR_36;
- unique physical semantics for every generic 36D carrier;
- historical 6x6 phase-coordinate carrier promotion;
- curvature/gravity interpretation.

Live phi/aux_phi remain dimensionless generic computational state unless they
are explicitly and verifiably admitted into the typed bivector carrier.

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

A 36D implementation must test whether its typed projection intertwines this
action.

## Promotion tests

1. exact carrier type declaration;
2. exactly 36 finite coefficients where a 36-coefficient representation is used;
3. fail-closed validation;
4. generic residual split identities;
5. common-phase blind-spot control;
6. Bivector36 SO(2) group law;
7. J_36 generator structure;
8. tr rho_36(theta)=2+4cos(theta);
9. D_biv36=(a/L_M)^2;
10. inverse trace-to-angle mapping;
11. explicit information-loss ledger for any projection from H_MF;
12. historical Moire-hyperlayer replay only after clean forward-port.

## Firewall

Not established:
- generic PhaseNav 36D = physical bivector operator;
- physical gravity from Moire;
- prime-driven physical dynamics;
- winding = local residual;
- physical-unit conversion for untyped live phi/aux_phi.
