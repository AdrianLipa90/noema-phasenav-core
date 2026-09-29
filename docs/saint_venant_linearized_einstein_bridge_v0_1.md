# Saint-Venant Incompatibility / Linearized Einstein Bridge v0.1
Date: 2026-09-26
Status: EXACT_LINEAR_IDENTITY / PHYSICAL_GRAVITY_BINDING_NOT_IMPLIED

## 1. Compatibility firewall

If a spatial triad is literally a compatible deformation gradient

    E=Grad y,

then

    h=E^T E=y^* delta

is a pullback of Euclidean metric.

Therefore its intrinsic Riemann curvature is zero wherever y is a smooth local
diffeomorphism.

So:

    compatible ordinary deformation
      != intrinsic curved spatial geometry.

A nonflat metric built from a triad requires either:
- an incompatible/nonintegrable triad;
- an independent connection/background structure;
- or a different physical interpretation of E.

This is a geometric theorem, not a model preference.

## 2. Saint-Venant operator

Use row-wise Curl

    (Curl A)_ij
      =epsilon_jkl partial_k A_il.

For symmetric strain epsilon define

    inc(epsilon)
      =Curl[(Curl epsilon)^T].

Compatible infinitesimal strain

    epsilon=sym Grad u

obeys

    inc(epsilon)=0.

## 3. Exact linearized Einstein identity

For the spatial metric perturbation

    h_ij=delta_ij+2 epsilon_ij,

the first-order Ricci tensor is

    Ric_ij^(1)
      =partial_k partial_i epsilon_jk
       +partial_k partial_j epsilon_ik
       -Delta epsilon_ij
       -partial_i partial_j tr epsilon.

The scalar curvature is

    R^(1)
      =2[
        partial_i partial_j epsilon_ij
        -Delta tr epsilon
      ].

Therefore

    G_ij^(1)
      =Ric_ij^(1)
       -1/2 delta_ij R^(1).

With the Curl convention above, direct tensor contraction gives exactly

    boxed:
    G^(1)=inc(epsilon).

No fitted coefficient or constitutive parameter appears.

This is the standard differential compatibility operator expressed as a
linearized spatial Einstein tensor.

## 4. Plastic distortion / defect density

Let total distortion be compatible:

    beta=Grad u=beta_e+beta_p.

Define

    epsilon_e=sym beta_e

and project defect convention

    alpha=Curl beta_p.

The Kröner identity in the same convention is

    inc(sym beta_p)
      =sym Curl(alpha^T).

Since

    inc(sym beta)=0,

we get

    boxed:
    inc(epsilon_e)
      =-sym Curl(alpha^T).

Combining with the linearized geometric identity:

    boxed:
    G^(1)[delta+2epsilon_e]
      =-sym Curl(alpha^T).

The sign depends on the declared alpha=Curl beta_p convention. A convention
alpha=-Curl beta_p flips it.

## 5. Conformal reference control

For

    epsilon=diag(sigma,sigma,0),

    sigma=a(x^2+y^2),

the linearized tensor is

    G^(1)=diag(0,0,4a).

The exact spatial metric

    h=diag(e^(2sigma),e^(2sigma),1)

has

    G_zz=4a e^(-2sigma),

so at the origin the exact and linearized values agree exactly, and for small
sigma the latter is the first-order limit.

## 6. Critical distinction: incompatibility != Cartan torsion

The nonflat conformal triad

    E=diag(e^sigma,e^sigma,1)

is not a compatible Euclidean deformation gradient for a!=0; its row-wise Curl
is nonzero.

Nevertheless the previously validated Cartan spin connection satisfies

    T^a
      =de^a+omega^a_b wedge e^b
      =0.

Therefore:

    material/triad incompatibility
      != spacetime torsion.

The spin connection can cancel de^a in Cartan's first structure equation.

This distinction must remain explicit.

## 7. Scope

Established mathematically:
- compatible strain -> zero Saint-Venant incompatibility;
- inc(epsilon)=linearized 3D Einstein tensor;
- Kröner defect-gradient identity;
- exact linear bridge from plastic incompatibility to spatial metric curvature
  at first order.

Not established physically:
- defects are gravity;
- PhaseNav alpha is a spacetime source;
- the material triad is a physical spacetime triad;
- nonlinear Einstein dynamics follows from the linear identity.

The next gate is nonlinear incompatibility/coframe geometry, not a physical
gravity promotion.
