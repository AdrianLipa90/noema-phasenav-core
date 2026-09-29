import math
import pytest

from ciel_geometry.phasenav.defect_transport2d import (
    DefectField2D,
    advect_defect_periodic,
    central_divergence_periodic,
    cfl_number,
    component_inventories,
    defect_l2_energy,
    minmax,
    streamfunction_divergence_free_pair,
)
from ciel_geometry.phasenav.hyperelastic_field36 import HyperelasticFieldError


def _maxabs(grid):
    return max(abs(x) for row in grid for x in row)


def test_zero_velocity_is_identity():
    q=tuple(tuple(float(i+3*j) for i in range(8)) for j in range(6))
    f=DefectField2D((q,))
    got=advect_defect_periodic(f,0.1,1.0,1.0,0.0,0.0)
    assert got==f


def test_integer_cell_shift_at_cfl_one():
    nx,ny=9,5
    q=tuple(tuple(float(10*j+i) for i in range(nx)) for j in range(ny))
    f=DefectField2D((q,))
    got=advect_defect_periodic(f,1.0,1.0,1.0,1.0,0.0)
    expected=tuple(tuple(q[j][(i-1)%nx] for i in range(nx)) for j in range(ny))
    assert got.values[0]==expected


def test_each_component_inventory_is_conserved():
    nx,ny=32,24
    comps=[]
    for c in range(4):
        comps.append(tuple(tuple(
            1.0+0.1*math.sin(2*math.pi*(i+c)/nx)+0.05*math.cos(2*math.pi*(j+2*c)/ny)
            for i in range(nx)
        ) for j in range(ny)))
    f=DefectField2D(tuple(comps))
    inv0=component_inventories(f,0.2,0.3)
    dt=0.25/max(abs(0.7)/0.2+abs(-0.4)/0.3,1e-30)
    for _ in range(100):
        f=advect_defect_periodic(f,dt,0.2,0.3,0.7,-0.4)
    inv1=component_inventories(f,0.2,0.3)
    assert max(abs(a-b) for a,b in zip(inv0,inv1))<1e-10


def test_nonnegative_field_stays_nonnegative_under_cfl():
    nx=32;ny=32
    q=tuple(tuple(
        math.exp(-0.05*((i-10)**2+(j-12)**2))
        for i in range(nx)
    ) for j in range(ny))
    f=DefectField2D((q,))
    dt=0.8/(abs(0.6)+abs(0.2))
    for _ in range(50):
        f=advect_defect_periodic(f,dt,1.0,1.0,0.6,0.2)
    lo,_=minmax(f)
    assert lo>=-1e-14


def test_cfl_violation_fails_closed():
    f=DefectField2D((((1.0,)*8,)*8,))
    assert cfl_number(1.0,1.0,1.0,0.7,0.4)>1.0
    with pytest.raises(HyperelasticFieldError,match="CFL"):
        advect_defect_periodic(f,1.0,1.0,1.0,0.7,0.4)


def test_divergence_free_row_stays_divergence_free_under_uniform_advection():
    nx=48;ny=40;dx=0.2;dy=0.3
    ax,ay=streamfunction_divergence_free_pair(nx,ny,dx,dy,2,3)
    d0=central_divergence_periodic(ax,ay,dx,dy)
    assert _maxabs(d0)<1e-13
    f=DefectField2D((ax,ay))
    dt=0.4/(abs(0.5)/dx+abs(-0.25)/dy)
    for _ in range(80):
        f=advect_defect_periodic(f,dt,dx,dy,0.5,-0.25)
    d1=central_divergence_periodic(f.values[0],f.values[1],dx,dy)
    assert _maxabs(d1)<2e-12


def test_upwind_transport_does_not_increase_l2_for_scalar_periodic_case():
    nx=64;ny=32
    q=tuple(tuple(
        math.sin(2*math.pi*i/nx)+0.5*math.cos(2*math.pi*j/ny)
        for i in range(nx)
    ) for j in range(ny))
    f=DefectField2D((q,))
    e0=defect_l2_energy(f,1.0,1.0)
    dt=0.7/(abs(0.4)+abs(0.3))
    for _ in range(20):
        f=advect_defect_periodic(f,dt,1.0,1.0,0.4,0.3)
    assert defect_l2_energy(f,1.0,1.0)<=e0+1e-12
