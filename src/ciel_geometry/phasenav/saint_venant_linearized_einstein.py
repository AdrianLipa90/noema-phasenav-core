"""Saint-Venant incompatibility / linearized Einstein bridge in 3D.

Conventions
-----------
Coordinates i,j,k,l in {0,1,2}; Euclidean background delta_ij.

For a matrix field A, row-wise Curl is
    (Curl A)_{ij} = epsilon_{jkl} partial_k A_{il}.

For a symmetric strain epsilon,
    inc(epsilon)
      = Curl[(Curl epsilon)^T].

For the perturbed spatial metric
    h_ij = delta_ij + 2 epsilon_ij,

the first-order Einstein tensor is exactly

    G_ij^(1) = inc(epsilon)_ij

with the conventions above.

If the total distortion beta=Grad u is compatible and
    beta = beta_e + beta_p,
    epsilon_e = sym beta_e,
    alpha = Curl beta_p,

then
    inc(epsilon_e) = - sym Curl(alpha^T).

This is a geometric/continuum identity. It does not identify material defects
with physical gravity.
"""
from __future__ import annotations

import math
from typing import Sequence

from .hyperelastic_field36 import HyperelasticFieldError


DIM=3


def levi(i:int,j:int,k:int)->int:
    if len({i,j,k})<3:
        return 0
    if (i,j,k) in ((0,1,2),(1,2,0),(2,0,1)):
        return 1
    return -1


def _validate_d2_tensor(d2,name:str):
    if len(d2)!=DIM:
        raise HyperelasticFieldError(f"{name} must have shape 3x3x3x3")
    out=[]
    for i in range(DIM):
        if len(d2[i])!=DIM:
            raise HyperelasticFieldError(f"{name} must have shape 3x3x3x3")
        rows=[]
        for j in range(DIM):
            if len(d2[i][j])!=DIM:
                raise HyperelasticFieldError(f"{name} must have shape 3x3x3x3")
            ks=[]
            for k in range(DIM):
                if len(d2[i][j][k])!=DIM:
                    raise HyperelasticFieldError(f"{name} must have shape 3x3x3x3")
                vals=tuple(float(x) for x in d2[i][j][k])
                if not all(math.isfinite(x) for x in vals):
                    raise HyperelasticFieldError(f"{name} entries must be finite")
                ks.append(vals)
            rows.append(tuple(ks))
        out.append(tuple(rows))
    return tuple(out)


def _validate_d1_tensor(d1,name:str):
    if len(d1)!=DIM:
        raise HyperelasticFieldError(f"{name} must have shape 3x3x3")
    out=[]
    for i in range(DIM):
        if len(d1[i])!=DIM:
            raise HyperelasticFieldError(f"{name} must have shape 3x3x3")
        rows=[]
        for j in range(DIM):
            if len(d1[i][j])!=DIM:
                raise HyperelasticFieldError(f"{name} must have shape 3x3x3")
            vals=tuple(float(x) for x in d1[i][j])
            if not all(math.isfinite(x) for x in vals):
                raise HyperelasticFieldError(f"{name} entries must be finite")
            rows.append(vals)
        out.append(tuple(rows))
    return tuple(out)


def incompatibility_from_second_strain_derivatives(d2eps):
    """inc(eps)=Curl[(Curl eps)^T] from d2eps[i][j][k][l]."""
    d=_validate_d2_tensor(d2eps,"d2eps")
    out=[]
    for i in range(DIM):
        row=[]
        for j in range(DIM):
            value=0.0
            for k in range(DIM):
                for l in range(DIM):
                    eb=levi(j,k,l)
                    if eb==0:
                        continue
                    for m in range(DIM):
                        for n in range(DIM):
                            ea=levi(i,m,n)
                            if ea==0:
                                continue
                            # eps_{l n, k m}
                            value+=eb*ea*d[l][n][k][m]
            row.append(value)
        out.append(tuple(row))
    return tuple(out)


def linearized_ricci_from_second_strain_derivatives(d2eps):
    """Ric^(1) for h=delta+2eps."""
    d=_validate_d2_tensor(d2eps,"d2eps")
    out=[]
    for i in range(DIM):
        row=[]
        for j in range(DIM):
            term=0.0
            for k in range(DIM):
                # partial_k partial_i eps_{j k}
                term+=d[j][k][k][i]
                # partial_k partial_j eps_{i k}
                term+=d[i][k][k][j]
                # - partial_k partial_k eps_{ij}
                term-=d[i][j][k][k]
            # - partial_i partial_j tr eps
            term-=sum(d[k][k][i][j] for k in range(DIM))
            row.append(term)
        out.append(tuple(row))
    return tuple(out)


def linearized_scalar_curvature_from_second_strain_derivatives(d2eps)->float:
    d=_validate_d2_tensor(d2eps,"d2eps")
    divdiv=sum(d[i][j][i][j] for i in range(DIM) for j in range(DIM))
    laptr=sum(d[j][j][i][i] for i in range(DIM) for j in range(DIM))
    return 2.0*(divdiv-laptr)


def linearized_einstein_from_second_strain_derivatives(d2eps):
    ric=linearized_ricci_from_second_strain_derivatives(d2eps)
    r=linearized_scalar_curvature_from_second_strain_derivatives(d2eps)
    return tuple(tuple(
        ric[i][j]-0.5*(1.0 if i==j else 0.0)*r
        for j in range(DIM)
    ) for i in range(DIM))


def symmetric_second_derivatives_of_distortion(d2beta):
    """Return d2 sym(beta) from d2beta[i][j][k][l]."""
    d=_validate_d2_tensor(d2beta,"d2beta")
    return tuple(tuple(tuple(tuple(
        0.5*(d[i][j][k][l]+d[j][i][k][l])
        for l in range(DIM))
        for k in range(DIM))
        for j in range(DIM))
        for i in range(DIM))


def alpha_derivatives_from_second_plastic_distortion(d2beta_p):
    """dalpha[i][j][m]=partial_m alpha_ij, alpha=Curl beta_p."""
    d=_validate_d2_tensor(d2beta_p,"d2beta_p")
    return tuple(tuple(tuple(
        sum(
            levi(j,k,l)*d[i][l][m][k]
            for k in range(DIM)
            for l in range(DIM)
        )
        for m in range(DIM))
        for j in range(DIM))
        for i in range(DIM))


def sym_curl_alpha_transpose_from_alpha_derivatives(dalpha):
    """sym Curl(alpha^T), with row-wise Curl convention."""
    d=_validate_d1_tensor(dalpha,"dalpha")
    raw=[]
    for i in range(DIM):
        row=[]
        for j in range(DIM):
            # Curl(alpha^T)_{ij}
            value=sum(
                levi(j,k,l)*d[l][i][k]
                for k in range(DIM)
                for l in range(DIM)
            )
            row.append(value)
        raw.append(tuple(row))
    raw=tuple(raw)
    return tuple(tuple(
        0.5*(raw[i][j]+raw[j][i])
        for j in range(DIM)
    ) for i in range(DIM))


def kroner_incompatibility_from_second_plastic_distortion(d2beta_p):
    dalpha=alpha_derivatives_from_second_plastic_distortion(d2beta_p)
    return sym_curl_alpha_transpose_from_alpha_derivatives(dalpha)


def frobenius_norm3(a)->float:
    if len(a)!=3 or any(len(r)!=3 for r in a):
        raise HyperelasticFieldError("expected 3x3 matrix")
    return math.sqrt(math.fsum(float(x)*float(x) for r in a for x in r))


def subtract3(a,b):
    if len(a)!=3 or len(b)!=3 or any(len(r)!=3 for r in a) or any(len(r)!=3 for r in b):
        raise HyperelasticFieldError("expected 3x3 matrices")
    return tuple(tuple(float(a[i][j])-float(b[i][j]) for j in range(3)) for i in range(3))


def conformal_quadratic_strain_second_derivatives(a:float):
    """eps=diag(sigma,sigma,0), sigma=a(x^2+y^2)."""
    q=float(a)
    if not math.isfinite(q):
        raise HyperelasticFieldError("a must be finite")
    d=[[[[0.0]*3 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    for comp in (0,1):
        d[comp][comp][0][0]=2.0*q
        d[comp][comp][1][1]=2.0*q
    return tuple(tuple(tuple(tuple(v for v in ls) for ls in ks) for ks in js) for js in d)
