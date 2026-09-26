"""Analytic Cartan coframe -> spin connection -> Riemann reference.

Reference family:
    e^0 = dt
    e^1 = exp(sigma) dx
    e^2 = exp(sigma) dy
    e^3 = dz

with
    sigma(x,y)=a(x^2+y^2).

Metric:
    g = diag(-1, exp(2sigma), exp(2sigma), 1).

The torsion-free spin connection is
    omega^1_2 = sigma_y dx - sigma_x dy
    omega^2_1 = -omega^1_2.

Curvature:
    Omega^1_2 = -(sigma_xx+sigma_yy) dx^dy.

For this family, the coordinate Riemann component is
    R^x_{ yxy} = -(sigma_xx+sigma_yy),

and Gaussian curvature of the x-y factor is
    K = -exp(-2sigma)(sigma_xx+sigma_yy).

This file is a controlled geometric reference, not a gravitational field law.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .gl4_coframe_bivector36 import coframe_metric4, frobenius_norm, inverse4, matmul, sub
from .lorentz_curvature_small_loop import (
    connection_field_strength4,
    matrix_exponential4,
    scale4,
)
from .lorentz_holonomy36 import induced_generator6, lorentz_lie_residual4


class CartanReferenceError(ValueError):
    pass


def _zero4():
    return tuple(tuple(0.0 for _ in range(4)) for _ in range(4))


@dataclass(frozen=True)
class QuadraticConformalCoframe:
    a: float

    def __post_init__(self):
        q=float(self.a)
        if not math.isfinite(q):
            raise CartanReferenceError("a must be finite")
        object.__setattr__(self,"a",q)

    def sigma(self,x:float,y:float)->float:
        x=float(x);y=float(y)
        return self.a*(x*x+y*y)

    def sigma_x(self,x:float,y:float)->float:
        return 2.0*self.a*float(x)

    def sigma_y(self,x:float,y:float)->float:
        return 2.0*self.a*float(y)

    def sigma_xx(self,x:float,y:float)->float:
        return 2.0*self.a

    def sigma_yy(self,x:float,y:float)->float:
        return 2.0*self.a

    def laplacian_sigma(self,x:float,y:float)->float:
        return 4.0*self.a

    def coframe4(self,x:float,y:float):
        s=math.exp(self.sigma(x,y))
        return (
            (1.0,0.0,0.0,0.0),
            (0.0,s,0.0,0.0),
            (0.0,0.0,s,0.0),
            (0.0,0.0,0.0,1.0),
        )

    def metric4(self,x:float,y:float):
        return coframe_metric4(self.coframe4(x,y))

    def spin_connection_x(self,x:float,y:float):
        sy=self.sigma_y(x,y)
        return (
            (0.0,0.0,0.0,0.0),
            (0.0,0.0, sy,0.0),
            (0.0,-sy,0.0,0.0),
            (0.0,0.0,0.0,0.0),
        )

    def spin_connection_y(self,x:float,y:float):
        sx=self.sigma_x(x,y)
        return (
            (0.0,0.0,0.0,0.0),
            (0.0,0.0,-sx,0.0),
            (0.0, sx,0.0,0.0),
            (0.0,0.0,0.0,0.0),
        )

    def d_x_spin_connection_y(self,x:float,y:float):
        sxx=self.sigma_xx(x,y)
        return (
            (0.0,0.0,0.0,0.0),
            (0.0,0.0,-sxx,0.0),
            (0.0, sxx,0.0,0.0),
            (0.0,0.0,0.0,0.0),
        )

    def d_y_spin_connection_x(self,x:float,y:float):
        syy=self.sigma_yy(x,y)
        return (
            (0.0,0.0,0.0,0.0),
            (0.0,0.0, syy,0.0),
            (0.0,-syy,0.0,0.0),
            (0.0,0.0,0.0,0.0),
        )

    def spin_curvature_xy(self,x:float,y:float):
        wx=self.spin_connection_x(x,y)
        wy=self.spin_connection_y(x,y)
        return connection_field_strength4(
            wx,
            wy,
            self.d_x_spin_connection_y(x,y),
            self.d_y_spin_connection_x(x,y),
        )

    def torsion_xy(self,x:float,y:float):
        """T^a_xy for the declared coframe/spin connection."""
        s=math.exp(self.sigma(x,y))
        sx=self.sigma_x(x,y);sy=self.sigma_y(x,y)
        # derivatives of e^a_mu for mu=x(1),y(2)
        d_x_e_y=(0.0,0.0,sx*s,0.0)
        d_y_e_x=(0.0,sy*s,0.0,0.0)
        e_x=(0.0,s,0.0,0.0)
        e_y=(0.0,0.0,s,0.0)
        wx=self.spin_connection_x(x,y)
        wy=self.spin_connection_y(x,y)
        out=[]
        for a in range(4):
            val=d_x_e_y[a]-d_y_e_x[a]
            val+=sum(wx[a][b]*e_y[b]-wy[a][b]*e_x[b] for b in range(4))
            out.append(val)
        return tuple(out)

    def torsion_xy_norm(self,x:float,y:float)->float:
        t=self.torsion_xy(x,y)
        return math.sqrt(math.fsum(v*v for v in t))

    def coordinate_riemann_xy_from_cartan(self,x:float,y:float):
        """Matrix R^rho_{ sigma x y}=e_a^rho Omega^a_{bxy} e^b_sigma."""
        e=self.coframe4(x,y)
        einv=inverse4(e)
        omega=self.spin_curvature_xy(x,y)
        return matmul(einv,matmul(omega,e))

    def coordinate_riemann_xy_direct_metric(self,x:float,y:float):
        """Direct coordinate result from conformal-metric Christoffels."""
        lap=self.laplacian_sigma(x,y)
        return (
            (0.0,0.0,0.0,0.0),
            (0.0,0.0,-lap,0.0),
            (0.0, lap,0.0,0.0),
            (0.0,0.0,0.0,0.0),
        )

    def gaussian_curvature(self,x:float,y:float)->float:
        return -math.exp(-2.0*self.sigma(x,y))*self.laplacian_sigma(x,y)

    def scalar_curvature4(self,x:float,y:float)->float:
        return 2.0*self.gaussian_curvature(x,y)

    def rectangle_curvature_integral(self,x0:float,x1:float,y0:float,y1:float)->float:
        area=(float(x1)-float(x0))*(float(y1)-float(y0))
        return self.laplacian_sigma(0.0,0.0)*area

    def rectangle_spin_holonomy4(self,x0:float,x1:float,y0:float,y1:float):
        """Exact abelian SO(2) spin holonomy for the rectangle.

        For this connection, Omega_xy = laplacian(sigma) * J_z.
        """
        curv=self.spin_curvature_xy(0.0,0.0)
        area=(float(x1)-float(x0))*(float(y1)-float(y0))
        return matrix_exponential4(scale4(area,curv))

    def bivector_curvature_xy(self,x:float,y:float):
        return induced_generator6(self.spin_curvature_xy(x,y))
