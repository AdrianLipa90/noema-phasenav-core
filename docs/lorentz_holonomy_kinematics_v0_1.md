# Lorentz Connection / Holonomy Kinematics v0.1
Date: 2026-09-26
Status: CANDIDATE_HOLONOMY_KINEMATICS / CURVATURE_NOT_YET_PROMOTED

## 1. Purpose

The GL(4)/coframe carrier admits a Lorentz gauge sector. This gate introduces
connection information only at the level of finite transport links and loop
holonomy.

It deliberately separates:

    nontrivial holonomy

from

    continuum curvature tensor.

The latter requires an explicit small-loop/connection-field limit.

## 2. Lorentz links

Let a link transport an internal vector from vertex a to b:

    v_b=U_ba v_a,

with

    U_ba in SO^+(1,3).

For a sequence of links U_1,...,U_n, transport composition is

    H=U_n ... U_2 U_1.

The same path on the bivector carrier is

    H_6
      =Lambda^2(U_n)...Lambda^2(U_1)
      =Lambda^2(H).

## 3. Pure-gauge negative control

Given Lorentz frame values G_a at vertices, define

    U_ba=G_b G_a^{-1}.

For a closed loop

    0->1->2->...->0,

all intermediate frame factors telescope, so

    H=I

exactly.

Therefore a spatially varying choice of local Lorentz frame is not by itself
evidence for curvature.

This is a mandatory negative control.

## 4. Gauge covariance

Under a vertex gauge transformation H_a,

    U_ba
      -> H_b U_ba H_a^{-1}.

For a loop based at vertex 0,

    H_loop
      -> H_0 H_loop H_0^{-1}.

Thus conjugacy invariants such as

    tr H_loop

are gauge invariant.

The Bivector36 loop obeys the corresponding Lambda^2 conjugation.

## 5. Lie algebra

A Lorentz connection generator Omega obeys

    Omega^T eta+eta Omega=0.

The induced Bivector36 generator

    J_6=d(Lambda^2)_I(Omega)

obeys

    J_6^T G+G J_6=0

for the bivector metric

    G=diag(-1,-1,-1,+1,+1,+1).

Both boost and spatial-rotation generators are explicitly represented.

## 6. Noncommuting-loop witness

For noncommuting Lorentz transports U,V, the group commutator loop

    U,V,U^{-1},V^{-1}

may have

    H_loop != I.

At this gate the result is recorded only as a nontrivial holonomy witness:

    residual=||H_loop-I||.

It is NOT yet divided by an area or identified with a Riemann curvature tensor.

## 7. Promotion gate toward curvature

Curvature interpretation requires, at minimum:
- a coordinate/local-cell definition;
- loop area bivector Sigma^{mu nu};
- a family of shrinking loops;
- scaling

      H_loop
        =I + (1/2) R_{mu nu} Sigma^{mu nu}
         + o(|Sigma|);

- gauge-covariant convergence;
- pure-gauge loops remaining zero under refinement;
- orientation reversal changing the leading area term sign.

Until those pass, the repository should say holonomy, not curvature.
