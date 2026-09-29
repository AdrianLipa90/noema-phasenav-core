# Finite-Strain Multiplicative Plasticity v0.1
Date: 2026-09-26
Status: CANDIDATE_FINITE_STRAIN_DYNAMICS / GL_PLUS_3_PRESERVING

## 1. Kinematics

Replace the additive small-strain split by

    F=F_e F_p,

with

    F,F_e,F_p in GL+(3).

Thus

    F_e=F F_p^{-1}.

The existing Bivector36 carrier continues to represent the total deformation

    rho_36(F)=diag(F,cof(F)).

The multiplicative internal state F_p is separate and does not change that
geometric carrier contract.

## 2. Elastic energy

Use the same objective compressible neo-Hookean energy on the elastic factor:

    C_e=F_e^T F_e,
    J_e=det F_e>0,

    psi(F_e)
      =mu/2[tr C_e-3-2ln J_e]
       +lambda/2(ln J_e)^2.

Elastic first Piola stress:

    P_e
      =mu(F_e-F_e^{-T})
       +lambda ln(J_e)F_e^{-T}.

Total first Piola stress is

    P=P_e F_p^{-T}.

## 3. Mandel driving stress

Define

    M=F_e^T P_e.

For this isotropic elastic energy M is symmetric.

Let

    m=tr(M)/3,
    M_dev=M-mI.

Choose nonnegative plastic mobilities

    m_dev>=0,
    m_vol>=0

and

    L_p
      =m_dev M_dev
       +m_vol m I.

With

    L_p=dot(F_p)F_p^{-1},

fixed-total-F differentiation gives

    dot(F_e)=-F_e L_p

and therefore

    dot(psi)
      =P_e:dot(F_e)
      =-M:L_p

      =-m_dev |M_dev|^2
       -3 m_vol m^2
      <=0.

This is the finite-strain dissipation inequality for the candidate viscous
flow.

## 4. GL+(3)-preserving update

Update plastic distortion multiplicatively:

    F_p^{n+1}
      =exp(dt L_p) F_p^n.

Because

    det exp(A)=exp(tr A)>0,

a positive-determinant F_p remains in GL+(3).

If

    m_vol=0,

then

    tr L_p=0,

so

    det F_p^{n+1}=det F_p^n

up to numerical roundoff: the plastic flow is isochoric.

The reference implementation uses a pure-Python scaling-and-squaring matrix
exponential and validates its determinant identity.

## 5. Objectivity

A superposed rigid rotation Q acts by

    F -> QF,

while F_p is unchanged, giving

    F_e -> QF_e.

Because the elastic energy depends on F_e only through F_e^T F_e and det F_e,

    psi(QF_e)=psi(F_e).

Pure elastic rotation has

    M=0,
    L_p=0.

## 6. Relation to the earlier small-strain gate

For F and F_p close to identity,

    F approximately I+Grad u,
    F_p approximately I+beta_p,

so

    F_e approximately I+Grad u-beta_p.

Thus the previous

    eps_e=sym(Grad u-beta_p)

is the first-order limit of the multiplicative theory.

The finite-strain gate supersedes the additive kinematics only where finite
deformations matter; the small-strain model remains a valid linear reference.

## 7. Boundary

CLOSED by this gate:
- multiplicative F=F_e F_p kinematics;
- GL+(3) admission;
- objective elastic energy on F_e;
- total first Piola stress;
- Mandel driving stress;
- nonnegative finite-strain plastic dissipation;
- exponential update preserving det F_p>0;
- optional isochoric plastic flow.

OPEN:
- finite-strain defect density convention from F_p;
- spatial gradients of F_p and nonlocal plastic energy;
- yield surfaces / rate-independent return mapping;
- crystal slip systems and Burgers-vector resolution;
- temperature;
- empirical material calibration;
- GL(4)/coframe extension.

No spacetime or gravity interpretation is introduced.
