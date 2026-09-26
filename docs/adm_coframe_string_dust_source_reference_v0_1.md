# ADM Coframe + Independent String-Dust Source Reference v0.1
Date: 2026-09-26
Status: TYPED_3PLUS1_COFRAME_PASS_CANDIDATE / SOURCE_REFERENCE_CANDIDATE

## 1. Typed 3+1 coframe bridge

Let the already calibrated spatial carrier supply a triad

    E in GL+(3).

Add independently typed lapse and shift:

    N>0,
    beta in R^3.

Choose time gauge

    e^0=N dt,
    e^a=E^a_i(dx^i+beta^i dt).

Then

    e=
      [ N      0 ]
      [ E beta E ].

The metric is

    h=E^T E,

    g_tt=-N^2+beta^T h beta,

    g_ti=(h beta)_i,

    g_ij=h_ij.

This is an exact kinematic bridge from the spatial GL+(3) triad sector to a
3+1 coframe once N and beta are supplied.

It does NOT infer N or beta from generic PhaseNav T36.

For

    N=1,
    beta=0,

the Bivector36 carrier reduces exactly to the previous spatial GL(3) carrier.

The validated quadratic-conformal Cartan reference is itself exactly the
special case

    N=1,
    beta=0,
    E=diag(e^sigma,e^sigma,1).

Thus the reference geometry is now explicitly connected to the earlier spatial
deformation carrier without changing its meaning.

## 2. Independent source semantics: straight string dust

As a source-admission reference, use a static congruence of straight strings
aligned with z.

With unit timelike tangent u and unit spacelike string tangent s,

    T^{mu nu}
      =rho(u^mu u^nu-s^mu s^nu).

For the static product coordinates:

    T_cov
      =diag(rho,0,0,-rho),

    T^mu_nu
      =diag(-rho,0,0,-rho).

This source semantics is defined independently of the Einstein tensor.

It has transverse pressure zero and longitudinal tension equal to its energy
density.

For rho>=0 it saturates the longitudinal dominant-energy bound.

## 3. Exact source match for the analytic reference

For the validated geometry,

    G_cov
      =diag(-q,0,0,+q),

    q=4a e^(-2sigma).

With positive coupling kappa and Lambda=0, the Einstein equation

    G_cov=kappa T_cov

requires

    rho_required
      =-q/kappa
      =-(4a/kappa)e^(-2sigma).

Therefore:

- if a<0, rho_required>0 and the aligned string-dust reference obeys the
  standard positive-energy sign;
- if a>0, exact matching requires rho<0 and fails the positive-density
  string-dust admission gate.

This is an exact sign result, not a fit.

## 4. Conservation

For the static product metric and a density rho=rho(x,y), the mixed tensor

    T^mu_nu=diag(-rho,0,0,-rho)

obeys

    nabla_mu T^mu_nu=0.

Time or z dependence requires additional source/transport terms and is rejected
by the static source-free reference.

## 5. Global limitation

For the exactly matched profile,

    rho_required e^(2sigma)
      =-4a/kappa,

so the proper string energy per coordinate transverse area is constant.

Hence on an infinite x-y plane the total energy diverges with area.

Therefore the matched analytic source is a local/reference geometry, not an
isolated globally finite matter configuration.

## 6. What this establishes

Mathematically:
- spatial GL+(3) -> time-gauge 3+1 coframe adapter;
- exact recovery of the prior spatial Bivector36 carrier;
- exact inclusion of the Cartan reference as an ADM special case;
- one independently defined conserved source family whose tensor structure can
  exactly match the reference for a<0.

Not established:
- that Moire/PhaseNav triads are physical spacetime triads;
- that lapse/shift come from PhaseNav;
- that cosmic/string dust is the physical source of the user's model;
- a globally realistic isolated solution;
- empirical gravity.

The source result is a typed reference match, not evidence that nature realizes
this source.
