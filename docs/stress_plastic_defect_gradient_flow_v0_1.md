# Stress–Plastic–Defect Gradient Flow v0.1
Date: 2026-09-26
Status: CANDIDATE_THERMODYNAMIC_COUPLING / SMALL_STRAIN_REFERENCE

## 1. Why a new state is required

A globally compatible elastic field satisfies

    F=Grad y,
    Curl F=0.

Plastic/defect content therefore requires an additional internal state rather
than silently assigning Curl F != 0 to the same compatible field.

Introduce plastic distortion

    beta_p.

At small strain,

    eps_e=sym(Grad u-beta_p).

## 2. Convex free energy

Use

    psi
      =mu |eps_e|^2
       +lambda/2 [tr eps_e]^2
       +H/2 |beta_p|^2,

with

    mu>0,
    lambda+2mu/3>0,
    H>=0.

The small-strain stress is

    sigma
      =2mu eps_e
       +lambda tr(eps_e) I.

The thermodynamic force conjugate to beta_p is

    Y
      =sigma-H beta_p
      =-delta psi/delta beta_p.

## 3. Onsager flow

Choose mobility

    M>=0

and define

    beta_p_dot=M Y.

At fixed total strain,

    d psi/dtau
      =(delta psi/delta beta_p):beta_p_dot
      =-M |Y|^2
      <=0.

Thus dissipation is built into the constitutive law rather than checked after
the fact.

## 4. Exact local solution

Because the energy is quadratic, split beta_p into:
- symmetric deviatoric;
- spherical;
- skew sectors.

For E=sym Grad u:

    beta_dev^*
      =[2mu/(2mu+H)] E_dev,

    beta_mean^*
      =[(2mu+3lambda)/(2mu+3lambda+H)] E_mean.

Relaxation rates:

    r_dev=M(2mu+H),

    r_sph=M(2mu+3lambda+H),

    r_skew=MH.

Therefore the fixed-total-strain local constitutive update is analytic and has
an exact semigroup property.

## 5. Defect density

Project convention:

    alpha=Curl beta_p.

A compatible plastic distortion beta_p=Grad p has alpha=0.
Nonzero alpha records incompatibility of the plastic distortion.

This gate does not yet prescribe alpha transport from sigma directly. It
provides a thermodynamically admissible stress -> beta_p coupling from which
defect content can be diagnosed.

## 6. Boundary

This is deliberately a small-strain viscous-plastic reference.

Not yet claimed:
- yield surface;
- rate-independent plasticity;
- Burgers-vector resolved slip;
- crystal slip systems;
- finite-strain multiplicative F=F_e F_p;
- Peach-Koehler line dynamics;
- defect nucleation/annihilation.

Those are later constitutive gates.
