"""Nonlinear coframe incompatibility firewall.

Two controls distinguish raw triad Curl from intrinsic curvature.

A. Flat local-rotation gauge:
    E(x,y)=R_z(theta(x,y))
    h=E^T E=I
so intrinsic curvature is exactly zero, while row-wise Curl E is generally
nonzero when Grad theta != 0.

The torsion-free spin connection is
    omega_mu = -J_z partial_mu theta,
and its curvature vanishes because mixed partials commute and [J_z,J_z]=0.

B. Nonflat conformal triad:
    E=diag(exp(sigma),exp(sigma),1),
    sigma=a(x^2+y^2).
At the origin Grad sigma=0, hence row-wise Curl E=0 there, but curvature remains
nonzero because Delta sigma=4a.

Therefore raw Curl E is neither sufficient nor pointwise necessary for
intrinsic curvature.
"""
from __future__ import annotations

import math

from .cartan_conformal_reference import QuadraticConformalCoframe
from .hyperelastic_field36 import HyperelasticFieldError


def _frob3(a)->float:
    if len(a)!=3 or any(len(r)!=3 for r in a):
        raise HyperelasticFieldError("expected 3x3 matrix")
    return math.sqrt(math.fsum(float(x)*float(x) for r in a for x in r))


def rotation_z_triad(theta:float):
    t=float(theta)
    if not math.isfinite(t):
        raise HyperelasticFieldError("theta must be finite")
    c,s=math.cos(t),math.sin(t)
    return (
        (c,-s,0.0),
        (s, c,0.0),
        (0.0,0.0,1.0),
    )


def rotation_z_metric(theta:float):
    """E^T E, identically I for a pure local spatial rotation."""
    e=rotation_z_triad(theta)
    return tuple(tuple(
        sum(e[k][i]*e[k][j] for k in range(3))
        for j in range(3)
    ) for i in range(3))


def rotated_flat_row_curl(theta:float,theta_x:float,theta_y:float):
    """Row-wise Curl E for E=R_z(theta), with no z dependence."""
    t=float(theta); tx=float(theta_x); ty=float(theta_y)
    if not all(math.isfinite(v) for v in (t,tx,ty)):
        raise HyperelasticFieldError("theta and derivatives must be finite")
    c,s=math.cos(t),math.sin(t)
    return (
        (0.0,0.0,-c*tx+s*ty),
        (0.0,0.0,-s*tx-c*ty),
        (0.0,0.0,0.0),
    )


def rotated_flat_row_curl_norm(theta:float,theta_x:float,theta_y:float)->float:
    return _frob3(rotated_flat_row_curl(theta,theta_x,theta_y))


def spatial_jz():
    return (
        (0.0,-1.0,0.0),
        (1.0, 0.0,0.0),
        (0.0, 0.0,0.0),
    )


def rotated_flat_spin_connection(theta_x:float,theta_y:float):
    """omega_x, omega_y for the torsion-free rotated-flat frame."""
    j=spatial_jz()
    wx=tuple(tuple(-float(theta_x)*j[i][k] for k in range(3)) for i in range(3))
    wy=tuple(tuple(-float(theta_y)*j[i][k] for k in range(3)) for i in range(3))
    return wx,wy


def rotated_flat_spin_curvature(
    theta_xy:float,
    theta_yx:float,
):
    """Omega_xy for omega=-J dtheta. Vanishes when mixed partials commute."""
    q=float(theta_xy)-float(theta_yx)
    j=spatial_jz()
    # d_x omega_y-d_y omega_x = -J theta_xy + J theta_yx
    return tuple(tuple(-q*j[i][k] for k in range(3)) for i in range(3))


def conformal_triad_row_curl_norm(a:float,x:float,y:float)->float:
    aa=float(a);xx=float(x);yy=float(y)
    if not all(math.isfinite(v) for v in (aa,xx,yy)):
        raise HyperelasticFieldError("arguments must be finite")
    sigma=aa*(xx*xx+yy*yy)
    s=math.exp(sigma)
    sx=2.0*aa*xx
    sy=2.0*aa*yy
    return s*math.hypot(sx,sy)


def conformal_intrinsic_curvature_witness(a:float,x:float,y:float)->float:
    """Absolute scalar curvature of the validated 3+1 conformal reference."""
    ref=QuadraticConformalCoframe(float(a))
    return abs(ref.scalar_curvature4(float(x),float(y)))
