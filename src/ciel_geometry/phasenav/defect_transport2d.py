"""Source-free periodic transport reference for incompatibility/defect density.

The continuum hyperelastic layer defines the diagnostic

    alpha = Curl F.

This module does not invent a stress-driven dislocation constitutive law.
Instead it provides a conservative transport harness for an independently
admitted defect-density field under a prescribed 2D velocity:

    partial_tau alpha_c + div(v alpha_c) = 0

component by component, with periodic boundaries.

The finite-volume update is first-order upwind and fails closed unless the
2D CFL number |vx|dt/dx + |vy|dt/dy <= 1.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .hyperelastic_field36 import HyperelasticFieldError


@dataclass(frozen=True)
class DefectField2D:
    """components x ny x nx periodic field."""

    values: tuple[tuple[tuple[float, ...], ...], ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise HyperelasticFieldError("defect field needs at least one component")
        comps=[]
        ny=None
        nx=None
        for component in self.values:
            if not component:
                raise HyperelasticFieldError("component grid cannot be empty")
            rows=[]
            for row in component:
                rr=tuple(float(x) for x in row)
                if not rr:
                    raise HyperelasticFieldError("grid row cannot be empty")
                if not all(math.isfinite(x) for x in rr):
                    raise HyperelasticFieldError("defect field values must be finite")
                rows.append(rr)
            if ny is None:
                ny=len(rows); nx=len(rows[0])
            if len(rows)!=ny or any(len(r)!=nx for r in rows):
                raise HyperelasticFieldError("all defect components must share one rectangular grid")
            comps.append(tuple(rows))
        object.__setattr__(self,"values",tuple(comps))

    @property
    def components(self)->int:
        return len(self.values)

    @property
    def ny(self)->int:
        return len(self.values[0])

    @property
    def nx(self)->int:
        return len(self.values[0][0])


def cfl_number(dt:float,dx:float,dy:float,vx:float,vy:float)->float:
    vals=tuple(float(x) for x in (dt,dx,dy,vx,vy))
    if not all(math.isfinite(x) for x in vals):
        raise HyperelasticFieldError("transport parameters must be finite")
    dt,dx,dy,vx,vy=vals
    if dt<0.0 or dx<=0.0 or dy<=0.0:
        raise HyperelasticFieldError("require dt>=0 and dx,dy>0")
    return abs(vx)*dt/dx+abs(vy)*dt/dy


def _advect_scalar_periodic(
    q:Sequence[Sequence[float]],
    dt:float,
    dx:float,
    dy:float,
    vx:float,
    vy:float,
)->tuple[tuple[float,...],...]:
    ny=len(q); nx=len(q[0])
    out=[]
    for j in range(ny):
        row=[]
        for i in range(nx):
            qi=float(q[j][i])
            # Conservative interface fluxes.
            ql=float(q[j][(i-1)%nx]); qr=float(q[j][(i+1)%nx])
            qd=float(q[(j-1)%ny][i]); qu=float(q[(j+1)%ny][i])
            fx_r=vx*(qi if vx>=0.0 else qr)
            fx_l=vx*(ql if vx>=0.0 else qi)
            fy_u=vy*(qi if vy>=0.0 else qu)
            fy_d=vy*(qd if vy>=0.0 else qi)
            row.append(qi-dt*(fx_r-fx_l)/dx-dt*(fy_u-fy_d)/dy)
        out.append(tuple(row))
    return tuple(out)


def advect_defect_periodic(
    field:DefectField2D,
    dt:float,
    dx:float,
    dy:float,
    vx:float,
    vy:float,
    *,
    cfl_tolerance:float=1e-14,
)->DefectField2D:
    cfl=cfl_number(dt,dx,dy,vx,vy)
    if cfl>1.0+cfl_tolerance:
        raise HyperelasticFieldError(f"2D upwind CFL violated: {cfl:.17g} > 1")
    return DefectField2D(tuple(
        _advect_scalar_periodic(component,dt,dx,dy,vx,vy)
        for component in field.values
    ))


def component_inventories(
    field:DefectField2D,
    dx:float,
    dy:float,
)->tuple[float,...]:
    h1,h2=float(dx),float(dy)
    if not math.isfinite(h1) or not math.isfinite(h2) or h1<=0.0 or h2<=0.0:
        raise HyperelasticFieldError("dx and dy must be finite and positive")
    cell=h1*h2
    return tuple(
        cell*math.fsum(x for row in component for x in row)
        for component in field.values
    )


def defect_l2_energy(
    field:DefectField2D,
    dx:float,
    dy:float,
    defect_modulus:float=1.0,
)->float:
    gamma=float(defect_modulus)
    if not math.isfinite(gamma) or gamma<0.0:
        raise HyperelasticFieldError("defect_modulus must be finite and non-negative")
    cell=float(dx)*float(dy)
    if not math.isfinite(cell) or cell<=0.0:
        raise HyperelasticFieldError("dx*dy must be finite and positive")
    return 0.5*gamma*cell*math.fsum(
        x*x for component in field.values for row in component for x in row
    )


def minmax(field:DefectField2D)->tuple[float,float]:
    vals=[x for component in field.values for row in component for x in row]
    return min(vals),max(vals)


def central_divergence_periodic(
    ax:Sequence[Sequence[float]],
    ay:Sequence[Sequence[float]],
    dx:float,
    dy:float,
)->tuple[tuple[float,...],...]:
    ny=len(ax); nx=len(ax[0])
    if len(ay)!=ny or any(len(r)!=nx for r in ay) or any(len(r)!=nx for r in ax):
        raise HyperelasticFieldError("ax and ay must share one rectangular grid")
    h1,h2=float(dx),float(dy)
    out=[]
    for j in range(ny):
        row=[]
        for i in range(nx):
            ddx=(float(ax[j][(i+1)%nx])-float(ax[j][(i-1)%nx]))/(2.0*h1)
            ddy=(float(ay[(j+1)%ny][i])-float(ay[(j-1)%ny][i]))/(2.0*h2)
            row.append(ddx+ddy)
        out.append(tuple(row))
    return tuple(out)


def streamfunction_divergence_free_pair(
    nx:int,
    ny:int,
    dx:float,
    dy:float,
    mode_x:int=1,
    mode_y:int=1,
)->tuple[tuple[tuple[float,...],...],tuple[tuple[float,...],...]]:
    """Construct ax=D_y psi, ay=-D_x psi using the same periodic central D."""
    nx=int(nx); ny=int(ny)
    if nx<3 or ny<3:
        raise HyperelasticFieldError("need at least 3x3 grid")
    psi=tuple(tuple(
        math.sin(2.0*math.pi*mode_x*i/nx)*math.sin(2.0*math.pi*mode_y*j/ny)
        for i in range(nx)
    ) for j in range(ny))
    ax=[]; ay=[]
    for j in range(ny):
        rx=[]; ry=[]
        for i in range(nx):
            dpsi_dy=(psi[(j+1)%ny][i]-psi[(j-1)%ny][i])/(2.0*dy)
            dpsi_dx=(psi[j][(i+1)%nx]-psi[j][(i-1)%nx])/(2.0*dx)
            rx.append(dpsi_dy)
            ry.append(-dpsi_dx)
        ax.append(tuple(rx)); ay.append(tuple(ry))
    return tuple(ax),tuple(ay)
