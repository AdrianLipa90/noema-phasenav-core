# GL(4) Coframe / Bivector36 Kinematics v0.1
Date: 2026-09-26
Status: CANDIDATE_KINEMATICS / NO_CURVATURE_CLAIM

## 1. General 4D carrier

Let

    A in GL(4).

The exterior-square representation acts on

    Lambda^2(R^4)

and, in the declared pair basis

    (01,02,03,23,31,12),

is a 6x6 operator:

    rho_36(A)=Lambda^2 A.

Thus the same 36-coefficient carrier extends from spatial GL(3) to a general
4D linear/coframe transformation without introducing a new ambient dimension.

Exact identities:

    Lambda^2(AB)
      =Lambda^2(A)Lambda^2(B),

    det(Lambda^2 A)
      =det(A)^3.

## 2. Recovery of the previous GL(3) sector

For

    A=diag(1,F),
    F in GL(3),

the representation reduces exactly to

    Lambda^2 A
      =diag(F,cof(F)),

which is the already validated GL(3) deformation carrier.

For F=R in SO(3), this further reduces to

    diag(R,R).

So the previous rotation/deformation stack is an exact subgroup restriction of
the GL(4) carrier.

## 3. Lorentz sector

Take

    eta=diag(-1,1,1,1).

A proper orthochronous Lorentz transformation satisfies

    Lambda^T eta Lambda=eta,
    det Lambda=1,
    Lambda^0_0>=1.

The metric induced on bivectors is

    G_(ij)(kl)
      =eta_ik eta_jl
       -eta_il eta_jk.

In the declared basis,

    G=diag(-1,-1,-1,+1,+1,+1),

so it has signature

    (3,3).

Therefore

    B=Lambda^2 Lambda

obeys

    B^T G B=G,
    det B=1.

The Lorentz image is thus a specific subgroup of SO(3,3), not the whole
SO(3,3).

## 4. Coframe metric and local Lorentz gauge

For a coframe matrix e define

    g=e^T eta e.

A local Lorentz action on the internal index is

    e -> Lambda e.

Then

    g'
      =e^T Lambda^T eta Lambda e
      =g.

The coframe carries more information than the metric because Lorentz-related
coframes represent the same g.

This gate is purely kinematic. A local x-dependent coframe does not acquire
curvature merely by being written down; a connection and its field strength
are separate objects.

## 5. Unavoidable Z2 kernel

Exterior-square reconstruction is not injective:

    Lambda^2(-A)=Lambda^2(A).

Thus the 36-coefficient bivector operator cannot distinguish A from -A.

The carrier therefore has at least the exact kernel

    {+I,-I} ~= Z2

relative to the underlying 4x4 transformation.

Any future inverse adapter from Bivector36 to a coframe must expose this
ambiguity or supply an independent orientation/time-orientation witness. It
must not silently choose a sign.

## 6. Validation gates

Required:
- exterior-square homomorphism;
- determinant identity;
- exact GL(3) restriction;
- proper Lorentz metric preservation;
- induced (3,3) bivector-metric preservation;
- exact SO(3) restriction;
- coframe-metric gauge invariance;
- exact Z2 kernel control;
- rejection of generic GL(4) matrices as Lorentz matrices.

## 7. Open frontier

Not established here:
- spin connection;
- torsion;
- Riemann curvature;
- Einstein equations;
- identification of the coframe with physical spacetime;
- gravitational dynamics.

The next lawful gate is connection/holonomy kinematics with flat and pure-gauge
negative controls before any curvature interpretation.
