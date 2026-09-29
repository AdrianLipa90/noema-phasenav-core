# Einstein Geometric Tensor Reference v0.1
Date: 2026-09-26
Status: GEOMETRIC_IDENTITY_CANDIDATE / SOURCE_EQUATION_OPEN

## 1. Input geometry

Use the already validated nonflat coframe reference

    g=diag(-1,e^(2sigma),e^(2sigma),1),

    sigma=a(x^2+y^2).

The Cartan and direct-metric calculations agree on

    R^x_{ yxy}=-4a,

    R_scalar=-8a e^(-2sigma).

## 2. Ricci tensor

For this product geometry,

    Ric_mu_nu
      =diag(0,-4a,-4a,0).

Equivalently, with

    Delta sigma=4a,

    Ric_xx=Ric_yy=-Delta sigma.

## 3. Einstein tensor

Define geometrically

    G_mu_nu
      =Ric_mu_nu
       -1/2 g_mu_nu R.

Let

    q=e^(-2sigma) Delta sigma.

Then

    G_mu_nu
      =diag(-q,0,0,+q).

The mixed tensor is

    G^mu_nu
      =diag(q,0,0,q).

Its trace obeys the standard four-dimensional identity

    G^mu_mu=-R.

## 4. Contracted Bianchi identity

Using the Christoffel symbols of the same metric, the implementation evaluates

    nabla_mu G^mu_nu

directly and obtains zero for every component.

This is a geometric identity. It is not an empirical field equation.

## 5. Source firewall

Nothing in the construction requires or defines

    T_mu_nu.

One may later test a candidate source equation such as

    G_mu_nu + Lambda g_mu_nu
      =kappa T_mu_nu,

but neither kappa, Lambda nor T_mu_nu is inferred from the geometry in this
gate.

In particular, defining

    T_eff=G/kappa

would merely rename the geometric tensor unless kappa and the source semantics
are independently physically bound.

## 6. What this closes

For the analytic reference, the full geometric chain is now checked:

    coframe
      -> metric
      -> torsion-free spin connection
      -> curvature 2-form
      -> Riemann
      -> Ricci
      -> scalar curvature
      -> Einstein tensor
      -> contracted Bianchi identity.

## 7. Remaining physical gate

Still open:
- PhaseNav/Moire -> physical spacetime coframe identification;
- stress-energy source construction;
- gravitational coupling constant;
- Einstein constraint/evolution system for dynamical initial data;
- empirical tests.

No source equation is promoted by this reference.
