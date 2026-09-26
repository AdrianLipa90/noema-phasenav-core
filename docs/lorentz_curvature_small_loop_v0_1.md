# Lorentz Connection Curvature Small-Loop Gate v0.1
Date: 2026-09-26
Status: CONNECTION_CURVATURE_CANDIDATE / SPACETIME_RIEMANN_BINDING_OPEN

## 1. Connection field strength

Let

    A_mu(x) in so(1,3),

so

    A_mu^T eta+eta A_mu=0.

Define the Lorentz connection curvature / field strength

    F_mu_nu
      =partial_mu A_nu
       -partial_nu A_mu
       +[A_mu,A_nu].

This object is an internal Lorentz-gauge curvature 2-form.

At this gate it is NOT automatically identified with the spacetime Riemann
curvature tensor.

## 2. Shrinking-loop test

For a constant connection the derivative terms vanish.

Using the declared positive orientation

    +nu,+mu,-nu,-mu,

the plaquette holonomy obeys

    H(h)
      =I+h^2[A_mu,A_nu]+O(h^3).

Therefore

    [H(h)-I]/h^2
      -> F_mu_nu

for the constant-connection case.

The implementation explicitly measures this convergence instead of declaring
curvature from a single finite loop.

Reversing loop orientation gives the opposite leading sign.

## 3. Negative control

If

    [A_mu,A_nu]=0

for a constant connection, then

    F_mu_nu=0

and the commutator plaquette is exactly trivial up to floating-point roundoff.

This separates noncommutativity from arbitrary path length effects.

## 4. Gauge covariance

For a constant Lorentz gauge transformation G,

    A_mu -> G A_mu G^{-1},

and therefore

    F_mu_nu
      -> G F_mu_nu G^{-1}.

So scalar conjugacy invariants may be compared between gauges while raw matrix
entries are gauge-dependent.

## 5. Bivector36 curvature representation

The differential exterior-square representation maps

    A_mu -> J_mu=d(Lambda^2)(A_mu)

and preserves Lie brackets:

    d(Lambda^2)([A_mu,A_nu])
      =[J_mu,J_nu].

Hence the Lorentz field strength has a consistent Bivector36 representation in

    so(3,3).

This does not enlarge the physical degrees of freedom; it is a representation
of the same gauge curvature.

## 6. Bianchi control

For a constant connection, the covariant Bianchi identity reduces to the
Jacobi identity:

    [A_mu,[A_nu,A_rho]]
    +cyclic
    =0.

The reference implementation tests this exactly.

## 7. What remains before spacetime curvature

To identify this Lorentz-gauge curvature with gravitational/spacetime
curvature, a further binding is required:

1. a coframe e^a_mu(x);
2. a spin connection omega^a_b;
3. a declared relation between omega and e;
4. torsion

       T^a=de^a+omega^a_b wedge e^b;

5. a choice such as torsion-free metric compatibility if Levi-Civita geometry
   is intended;
6. demonstration that the connection curvature components reproduce the
   Riemann tensor of

       g=e^T eta e.

Until those gates pass:

    Lorentz connection curvature != established spacetime curvature.

No Einstein field equation is asserted here.
