"""Small-loop Lorentz connection curvature reference.

This module promotes finite holonomy to a *Lorentz gauge connection
field-strength* only after an explicit shrinking-loop check.

For a Lorentz-algebra connection A_mu,

    F_mn = partial_m A_n - partial_n A_m + [A_m,A_n].

For a constant connection the derivative terms vanish.

With the orientation used here, the plaquette path

    +nu, +mu, -nu, -mu

has

    H(h) = I + h^2 [A_mu,A_nu] + O(h^3).

This is connection curvature in the internal Lorentz gauge bundle. It is not
yet identified with the spacetime Riemann tensor; that requires a coframe
binding and a specified spin/affine connection relation.
"""
from __future__ import annotations

import math
from typing import Sequence

from .gl4_coframe_bivector36 import (
    frobenius_norm,
    identity4,
    inverse4,
    matmul,
    sub,
    validate_lorentz4,
)
from .lorentz_holonomy36 import (
    bivector_lie_residual6,
    induced_generator6,
    lorentz_lie_residual4,
    path_holonomy4,
)


class CurvatureGateError(ValueError):
    pass


def _m4(a):
    if len(a)!=4 or any(len(r)!=4 for r in a):
        raise CurvatureGateError("expected 4x4 matrix")
    m=tuple(tuple(float(x) for x in r) for r in a)
    if not all(math.isfinite(x) for r in m for x in r):
        raise CurvatureGateError("matrix entries must be finite")
    return m


def add4(a,b):
    x=_m4(a);y=_m4(b)
    return tuple(tuple(x[i][j]+y[i][j] for j in range(4)) for i in range(4))


def scale4(s,a):
    q=float(s);m=_m4(a)
    if not math.isfinite(q):
        raise CurvatureGateError("scale must be finite")
    return tuple(tuple(q*m[i][j] for j in range(4)) for i in range(4))


def commutator4(a,b):
    x=_m4(a);y=_m4(b)
    return sub(matmul(x,y),matmul(y,x))


def _inf_norm4(a):
    m=_m4(a)
    return max(math.fsum(abs(x) for x in row) for row in m)


def matrix_exponential4(a, *, tolerance:float=1e-16, max_terms:int=96):
    m=_m4(a)
    norm=_inf_norm4(m)
    if norm==0.0:
        return identity4()
    scale_power=max(0,int(math.ceil(math.log(norm/0.5,2.0)))) if norm>0.5 else 0
    scaled=scale4(2.0**(-scale_power),m)
    term=identity4()
    result=identity4()
    converged=False
    for k in range(1,max_terms+1):
        term=scale4(1.0/k,matmul(term,scaled))
        result=add4(result,term)
        if _inf_norm4(term)<=tolerance*max(1.0,_inf_norm4(result)):
            converged=True
            break
    if not converged:
        raise CurvatureGateError("matrix exponential failed to converge")
    for _ in range(scale_power):
        result=matmul(result,result)
    return result


def connection_field_strength4(
    a_mu,
    a_nu,
    d_mu_a_nu=None,
    d_nu_a_mu=None,
):
    """F_mn = d_m A_n - d_n A_m + [A_m,A_n]."""
    x=_m4(a_mu);y=_m4(a_nu)
    if lorentz_lie_residual4(x)>1e-10 or lorentz_lie_residual4(y)>1e-10:
        raise CurvatureGateError("connection values must lie in so(1,3)")
    z=((0.0,0.0,0.0,0.0),)*4
    dx=_m4(d_mu_a_nu) if d_mu_a_nu is not None else z
    dy=_m4(d_nu_a_mu) if d_nu_a_mu is not None else z
    f=add4(sub(dx,dy),commutator4(x,y))
    if lorentz_lie_residual4(f)>1e-9:
        raise CurvatureGateError("field strength left so(1,3)")
    return f


def constant_connection_plaquette_links(a_mu,a_nu,h:float, *, orientation:int=1):
    """Return links with a declared small-loop orientation.

    orientation=+1: +nu,+mu,-nu,-mu -> +[A_mu,A_nu] h^2.
    orientation=-1: +mu,+nu,-mu,-nu -> -[A_mu,A_nu] h^2.
    """
    step=float(h)
    if not math.isfinite(step) or step<=0.0:
        raise CurvatureGateError("h must be finite and positive")
    x=_m4(a_mu);y=_m4(a_nu)
    if lorentz_lie_residual4(x)>1e-10 or lorentz_lie_residual4(y)>1e-10:
        raise CurvatureGateError("connection values must lie in so(1,3)")
    ux=matrix_exponential4(scale4(step,x))
    uy=matrix_exponential4(scale4(step,y))
    uxm=matrix_exponential4(scale4(-step,x))
    uym=matrix_exponential4(scale4(-step,y))
    if not all(validate_lorentz4(q,tolerance=5e-10).admitted for q in (ux,uy,uxm,uym)):
        raise CurvatureGateError("exponentiated connection did not produce Lorentz links")
    if orientation==1:
        return (uy,ux,uym,uxm)
    if orientation==-1:
        return (ux,uy,uxm,uym)
    raise CurvatureGateError("orientation must be +1 or -1")


def constant_connection_plaquette_holonomy(a_mu,a_nu,h:float, *, orientation:int=1):
    return path_holonomy4(constant_connection_plaquette_links(a_mu,a_nu,h,orientation=orientation))


def normalized_small_loop_generator(a_mu,a_nu,h:float, *, orientation:int=1):
    hol=constant_connection_plaquette_holonomy(a_mu,a_nu,h,orientation=orientation)
    return scale4(1.0/(h*h),sub(hol,identity4()))


def small_loop_error(a_mu,a_nu,h:float, *, orientation:int=1)->float:
    target=connection_field_strength4(a_mu,a_nu)
    if orientation==-1:
        target=scale4(-1.0,target)
    return frobenius_norm(sub(normalized_small_loop_generator(a_mu,a_nu,h,orientation=orientation),target))


def conjugate4(g,x):
    return matmul(g,matmul(x,inverse4(g)))


def constant_gauge_transform_connection(g,a):
    q=_m4(g);x=_m4(a)
    if not validate_lorentz4(q).admitted:
        raise CurvatureGateError("g must be Lorentz")
    return conjugate4(q,x)


def jacobi_bianchi_residual_constant(a,b,c)->float:
    """Constant-connection covariant Bianchi/Jacobi control."""
    term1=commutator4(a,commutator4(b,c))
    term2=commutator4(b,commutator4(c,a))
    term3=commutator4(c,commutator4(a,b))
    return frobenius_norm(add4(add4(term1,term2),term3))


def induced_field_strength6(f4):
    f=_m4(f4)
    j=induced_generator6(f)
    if bivector_lie_residual6(j)>1e-9:
        raise CurvatureGateError("induced field strength left so(3,3)")
    return j
