# Cartan Coframe -> Riemann Reference v0.1
Date: 2026-09-26
Status: ANALYTIC_REFERENCE_PASS_CANDIDATE / PHYSICAL_GRAVITY_OPEN

## 1. Reference geometry

Choose

    e^0=dt,
    e^1=e^sigma dx,
    e^2=e^sigma dy,
    e^3=dz,

with

    sigma(x,y)=a(x^2+y^2).

Then

    g=e^T eta e
     =diag(-1,e^(2sigma),e^(2sigma),1).

This geometry is deliberately simple but nonflat for a!=0.

## 2. Torsion-free spin connection

Cartan's first structure equation is

    T^a
      =de^a+omega^a_b wedge e^b.

The torsion-free connection for this coframe is

    omega^1_2
      =sigma_y dx-sigma_x dy,

    omega^2_1=-omega^1_2,

with all other components zero.

Substitution gives

    T^a=0

exactly.

Thus nonzero curvature in this reference cannot be attributed to nonzero
torsion.

## 3. Curvature 2-form

Cartan's second structure equation gives

    Omega^a_b
      =d omega^a_b
       +omega^a_c wedge omega^c_b.

Here the active SO(2) connection is abelian inside the spatial plane, so

    Omega^1_2
      =-(sigma_xx+sigma_yy) dx wedge dy.

For the quadratic reference,

    Delta sigma=4a.

## 4. Conversion to coordinate Riemann

The coordinate-basis curvature is

    R^rho_{ sigma mu nu}
      =e_a^rho Omega^a_{b mu nu} e^b_sigma.

For mu nu=xy this gives

    R^x_{ yxy}
      =-Delta sigma,

    R^y_{ xxy}
      =+Delta sigma.

An independent direct calculation from the Christoffel symbols of

    g_xy=e^(2sigma) delta_xy

gives exactly the same result.

This is the missing binding between the Lorentz spin-connection curvature and
the Riemann tensor for the declared torsion-free coframe reference.

## 5. Scalar curvature

The Gaussian curvature of the conformal x-y factor is

    K
      =-e^(-2sigma) Delta sigma.

Since the 4D reference is the product of that 2D factor with flat time and z,

    R_scalar=2K
            =-2 e^(-2sigma) Delta sigma.

## 6. Holonomy crosscheck

For a rectangle in the x-y plane, this reference connection stays in one SO(2)
generator, so path ordering is trivial and Stokes applies directly.

For area A,

    H=exp(A Omega_xy).

Therefore

    (H-I)/A
      -> Omega_xy

as the rectangle shrinks.

This independently joins the earlier holonomy/small-loop gate to the Cartan
curvature of a concrete coframe.

## 7. Bivector36 representation

Applying d(Lambda^2) to Omega gives the same curvature in the Bivector36
so(3,3) representation.

Again, this is a representation of the same curvature, not 36 independent
curvature degrees of freedom.

## 8. What is now established and what is not

Established for this analytic reference:
- coframe -> metric;
- torsion-free spin connection;
- spin curvature 2-form;
- spin curvature -> coordinate Riemann;
- scalar curvature;
- shrinking-loop holonomy consistency;
- Bivector36 curvature representation.

Not established:
- that the user's physical Moire/fractal carrier is the spacetime coframe;
- an Einstein field equation;
- a stress-energy source law;
- dynamical evolution of the coframe;
- cosmological/gravitational empirical calibration.

Thus the mathematical Cartan/Riemann bridge is validated on a nonflat
reference geometry, while the physical binding remains a separate gate.
