# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.1

Status: CANDIDATE_ONLY / REPRESENTATION_BRIDGE / CURRENT-HEAD SAFE
Date: 2026-09-26

## Why this branch exists

The earlier branch `formalism/moire-hyperlayer-36d-v0-1-20260924` contains a useful Moire/coframe/bivector candidate, but it is currently divergent from `master` (ahead 10, behind 69 at audit time).

This file does not overwrite or silently port that branch. It records the minimal current-head contract required to connect the newer Fractal-Orbital Moire-Hilbert formalism to PhaseNav 36D.

## Upstream mathematical object

Let

    H_MF = integral_F^oplus H_x d mu_F(x)

and let the fractal-orbital algebra be

    A_FO = C(F) rtimes_(alpha,omega) G_orb.

For admitted orbital layers a,b:

    R_ab = U_a^* U_b,
    D_ab = (I-R_ab)^*(I-R_ab).

If R_ab v = exp(i theta) v, then

    D_ab v = 4 sin^2(theta/2) v.

Thus ker(D_ab) is the relational-zero sector on the tested subspace.

## 36D representation contract

A PhaseNav 36D carrier is a representation/projection, not the full Hilbert space:

    Pi_36 : A_FO -> V_36,

with dim(V_36)=36.

The bridge must explicitly declare:
- coordinate ordering;
- whether the carrier is phase-only, bivector, semantic or another typed 36D object;
- information discarded by Pi_36;
- whether a reconstruction map exists;
- whether common global U(1) is quotiented.

For phase-coordinate carriers theta^(a), theta^(b) in R^36, define

    C_ab^(36) = (1/36) sum_j exp(i(theta_j^(b)-theta_j^(a)))

and the global-U(1)-blind projective residual

    delta_ab^2 = 2(1-|C_ab^(36)|).

This residual is a representation-level observable. It is not automatically a metric on spacetime and is not curvature.

## Relation to the historical Moire hyperlayer candidate

The older candidate uses a signed shortest relative phase in each 6x6 channel and then decomposes Mat(6) into a co(3,3) geometric sector plus a 20D complement.

That construction may be reintroduced only through a forward-port/rebase with its tests. This current-head bridge does not claim that every 36D PhaseNav state is a bivector matrix.

## Arithmetic phase input

The On-Primes branch `feat/arithmetic-relational-phase-law-v0.1` supplies exact finite cyclic characters

    chi_(q,a)(n)=exp(2 pi i a n/q)

and exact separation signatures.

Such characters may populate or modulate an admitted PhaseNav representation only through a typed adapter. Their arithmetic exactness does not by itself establish a physical interaction.

## Fractal covariance

For a unitary scale action D_r require

    D_r U_g D_r^(-1) = U_(alpha_r(g)).

The corresponding relation tower is

    R_ab^(w) = D_w^(-1) R_ab D_w.

A 36D implementation must state whether Pi_36 intertwines this action:

    Pi_36(D_w^(-1) a D_w) ?= rho_w(Pi_36(a)).

If this equality is not tested, scale covariance is OPEN.

## Mandatory tests for promotion

1. exact 36 finite coordinates for a 36D phase carrier;
2. finite-value fail-closed validation;
3. common-phase invariance where the representation is projective;
4. layer-exchange conjugation/sign test;
5. zero residual for identical relations;
6. nonzero residual control for heterogeneous relative phase;
7. explicit information-loss ledger for Pi_36;
8. replay against the historical Moire-hyperlayer candidate only after a clean rebase.

## Firewall

Not established here:
- physical gravity from Moire;
- unique 36D realization of H_MF;
- prime-driven physical dynamics;
- equivalence of local residual and winding;
- universal physical validity of the fractal-orbital algebra.
