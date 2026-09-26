# Nonlinear Coframe Incompatibility Firewall v0.1
Date: 2026-09-26
Status: NONLINEAR_FIREWALL / RAW_CURL_NOT_CURVATURE

## 1. Why this gate is necessary

The linear identity

    inc(epsilon)=G^(1)

is exact, but it does not license replacing nonlinear curvature by a raw
first-derivative object such as

    Curl E.

A nonlinear coframe has local frame gauge freedom. Raw derivatives of one frame
representative are not themselves intrinsic curvature observables.

## 2. Counterexample: nonzero Curl E with zero curvature

Take a spatial triad that is a local rotation of the Cartesian frame:

    E(x,y)=R_z(theta(x,y)).

Then

    h=E^T E=I

identically.

So the intrinsic spatial metric is exactly flat for arbitrary smooth theta.

However, with row-wise Curl,

    ||Curl E||^2
      =theta_x^2+theta_y^2.

Thus a varying local rotation can give

    Curl E != 0

while

    Riemann(h)=0.

The torsion-free spin connection is

    omega=-J_z dtheta.

Its curvature is

    Omega
      =d omega+omega wedge omega
      =-J_z d^2 theta
      =0

for a smooth scalar theta.

Therefore nonzero raw coframe Curl is not sufficient for curvature.

## 3. Opposite control: zero Curl E at a point with nonzero curvature

For the validated conformal triad

    E=diag(e^sigma,e^sigma,1),

    sigma=a(x^2+y^2),

row-wise Curl has magnitude

    ||Curl E||
      =e^sigma |Grad sigma|.

At the origin,

    Grad sigma=0,

so

    Curl E=0

at that point.

But

    Delta sigma=4a

and the scalar curvature is

    R=-8a e^(-2sigma),

which is nonzero for a!=0.

Therefore raw Curl E is not pointwise necessary for curvature either.

## 4. Correct nonlinear hierarchy

The nonlinear gauge-covariant chain is

    coframe e
      -> torsion-free or otherwise declared connection omega
      -> curvature
           Omega=domega+omega wedge omega
      -> Riemann(g).

Raw coframe derivatives enter the connection through the torsion equation, but
curvature is a second-level, gauge-covariant object.

## 5. Relation to material defects

For a material deformation gradient F, row-wise Curl F is a legitimate
compatibility/defect diagnostic.

For a spacetime/spatial coframe e, local frame rotations are gauge freedom.

These are not the same semantic role even if both are represented by 3x3 or
4x4 matrices.

The same numeric array MUST carry a typed role:
- MATERIAL_DEFORMATION_GRADIENT, or
- SPATIAL_TRIAD / COFRAME.

No silent role conversion is admitted.

## 6. Consequence for the PhaseNav bridge

A future physical binding may connect a material/Moire deformation carrier to
a coframe, but then it must specify:
- reference coordinates and units;
- triad gauge;
- lapse and shift;
- whether incompatibility is material, geometric, or both;
- the spin/affine connection used for curvature.

The validated linearized Saint-Venant bridge remains useful, but the nonlinear
object to compare with gravity is curvature, not raw Curl.

No gravity claim is promoted by this firewall.
