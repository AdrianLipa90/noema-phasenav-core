# GL(3) Hyperelastic Field Dynamics v0.1
Date: 2026-09-26
Status: CANDIDATE_DYNAMICS / OBJECTIVE_HYPERELASTIC_REFERENCE

## 1. Primary field

Use a material-coordinate displacement field

    u(X,tau)

with deformation gradient

    F = I + Grad_X u,
    J = det F > 0.

The calibrated Bivector36 geometry remains

    rho_36(F)=Lambda^2 diag(1,F)
             =diag(F,cof(F)).

The field dynamics acts on F; it does not redefine the carrier.

## 2. Objective stored energy

Define

    C=F^T F.

The compressible neo-Hookean density is

    W(F)
      = mu/2 [tr(C)-3-2 ln J]
        + lambda/2 (ln J)^2.

This is frame-indifferent under left multiplication by a proper rotation:

    W(RF)=W(F),  R in SO(3).

In particular

    W(R)=0

for every rigid rotation, which is why this replaces a naive |F-I|^2 energy.

The first Piola stress is

    P(F)
      = mu(F-F^{-T})
        + lambda ln(J) F^{-T}.

At a rigid rotation R,

    P(R)=0.

## 3. Second-gradient regularization

For a spatially varying deformation field add

    W_grad
      = eta/2 |Grad F|^2,
    eta >= 0.

Let

    H_{iAB}
      = partial W_grad / partial(partial_B F_{iA})
      = eta partial_B F_{iA}.

The Lagrangian density is

    L
      = rho0/2 |u_tau|^2
        - W(F)
        - W_grad.

The Euler-Lagrange equation is

    rho0 u_{i,tau tau}
      = partial_A P_{iA}
        - partial_A partial_B H_{iAB}.

For constant eta,

    rho0 u_tt
      = Div P - eta Delta^2 u

because F=I+Grad u.

This is a second-gradient elastic continuum. No gravity interpretation is made.

## 4. Linearized limit

For small Grad u, with

    eps = sym Grad u,

the stored energy reduces to

    W_lin
      = mu |eps|^2
        + lambda/2 [tr eps]^2.

The usual homogeneous wave speeds are

    c_L^2=(lambda+2mu)/rho0,
    c_T^2=mu/rho0.

With the gradient term,

    omega_L^2
      = c_L^2 k^2 + (eta/rho0) k^4,

    omega_T^2
      = c_T^2 k^2 + (eta/rho0) k^4.

Thus the new scale enters as a controlled dispersive correction rather than an
arbitrary extra phase term.

## 5. Compatibility / defect diagnostic

For a general F field define the row-wise Curl

    alpha_{iJ}
      = epsilon_{JKL} partial_K F_{iL}.

For a smooth compatible deformation

    F=Grad y,

mixed partial symmetry gives

    Curl F=0.

Nonzero Curl F therefore measures incompatibility/defect content of an
independently specified F field.

A candidate defect penalty is

    W_defect
      = gamma/2 |Curl F|^2,
    gamma >= 0.

This term is diagnostic/regularizing only at this gate. A plasticity or
dislocation transport law is not yet introduced.

## 6. Typed status

CLOSED in this gate:
- objective finite-strain stored energy;
- exact first Piola stress;
- Bivector36 -> F -> energy evaluation;
- second-gradient regularization;
- linear longitudinal/transverse dispersions;
- compatibility Curl F diagnostic;
- nonnegative defect-density penalty.

OPEN:
- boundary conditions for a specific physical sample;
- spatially varying material coefficients;
- nonlinear time integrator;
- defect/dislocation transport law;
- multiplicative elastic/plastic decomposition;
- empirical material-parameter calibration;
- GL(4)/coframe dynamics and curvature.

The next gate should be a conservative numerical evolution with an explicit
energy ledger, followed separately by defect transport.
