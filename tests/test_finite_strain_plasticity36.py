import math
import pytest

from ciel_geometry.phasenav.finite_strain_plasticity36 import (
    FinitePlasticParameters,
    MultiplicativePlasticState,
    dev3,
    elastic_energy_density,
    elastic_f,
    fixed_total_energy,
    frobenius_inner3,
    frobenius_norm3,
    identity3,
    mandel_stress,
    matrix_exponential3,
    matmul3,
    plastic_dissipation_rate,
    plastic_step,
    plastic_velocity_gradient,
    rotated_total_state,
    scale3,
    sym3,
    total_first_piola,
    trace3,
)
from ciel_geometry.phasenav.hyperelastic_field36 import HyperelasticFieldError
from ciel_geometry.phasenav.spatial_deformation36 import det3
from ciel_geometry.phasenav.spatial_rotation36 import rotation3_axis_angle


P=FinitePlasticParameters(mu=3.0,lame_lambda=4.0,dev_mobility=0.6,volumetric_mobility=0.2)


def _sub(a,b):
    return tuple(tuple(a[i][j]-b[i][j] for j in range(3)) for i in range(3))


def test_factorization_roundtrip():
    f=((1.2,0.1,0.0),(0.0,0.9,0.05),(0.02,0.0,1.1))
    fp=((1.05,0.02,0.0),(0.0,0.97,0.01),(0.0,0.0,1.02))
    fe=elastic_f(f,fp)
    assert frobenius_norm3(_sub(matmul3(fe,fp),f))<1e-13


def test_objectivity_under_left_rigid_rotation():
    f=((1.12,0.08,0.0),(0.01,0.93,0.03),(0.0,0.02,1.04))
    fp=((1.02,0.01,0.0),(0.0,0.99,0.02),(0.0,0.0,1.01))
    s=MultiplicativePlasticState(f,fp)
    sr=rotated_total_state(s,(1,2,3),0.7)
    assert math.isclose(fixed_total_energy(s,P),fixed_total_energy(sr,P),rel_tol=1e-13,abs_tol=1e-13)


def test_pure_rotation_has_zero_mandel_and_no_plastic_flow():
    r=rotation3_axis_angle((1,2,3),0.8)
    s=MultiplicativePlasticState(r,identity3())
    assert frobenius_norm3(mandel_stress(s.total_f,s.plastic_f,P))<1e-12
    assert frobenius_norm3(plastic_velocity_gradient(s.total_f,s.plastic_f,P))<1e-12


def test_mandel_is_symmetric_for_isotropic_elastic_energy():
    f=((1.12,0.08,0.0),(0.01,0.93,0.03),(0.0,0.02,1.04))
    fp=((1.02,0.01,0.0),(0.0,0.99,0.02),(0.0,0.0,1.01))
    m=mandel_stress(f,fp,P)
    assert frobenius_norm3(_sub(m,sym3(m)))<1e-12


def test_dissipation_is_nonnegative_and_matches_mandel_lp():
    f=((1.2,0.1,0.0),(0.0,0.9,0.05),(0.02,0.0,1.1))
    fp=((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))
    m=sym3(mandel_stress(f,fp,P))
    lp=plastic_velocity_gradient(f,fp,P)
    expected=frobenius_inner3(m,lp)
    got=plastic_dissipation_rate(f,fp,P)
    assert got>=0.0
    assert math.isclose(got,expected,rel_tol=1e-14,abs_tol=1e-14)


def test_exponential_update_preserves_gl_plus():
    f=((1.2,0.1,0.0),(0.0,0.9,0.05),(0.02,0.0,1.1))
    s=MultiplicativePlasticState(f,identity3())
    s1=plastic_step(s,0.02,P)
    assert det3(s1.plastic_f)>0.0


def test_isochoric_flow_preserves_plastic_volume():
    p=FinitePlasticParameters(mu=3.0,lame_lambda=4.0,dev_mobility=0.6,volumetric_mobility=0.0)
    f=((1.2,0.1,0.0),(0.0,0.9,0.05),(0.02,0.0,1.1))
    fp=((1.03,0.0,0.0),(0.0,0.97,0.0),(0.0,0.0,1.0))
    s=MultiplicativePlasticState(f,fp)
    d0=det3(fp)
    for _ in range(20):
        s=plastic_step(s,0.01,p)
    assert math.isclose(det3(s.plastic_f),d0,rel_tol=2e-12,abs_tol=2e-12)


def test_fixed_total_energy_derivative_is_minus_dissipation():
    f=((1.2,0.1,0.0),(0.0,0.9,0.05),(0.02,0.0,1.1))
    s=MultiplicativePlasticState(f,identity3())
    e0=fixed_total_energy(s,P)
    rate=plastic_dissipation_rate(s.total_f,s.plastic_f,P)
    dt=1e-7
    s1=plastic_step(s,dt,P)
    numerical=(fixed_total_energy(s1,P)-e0)/dt
    assert math.isclose(numerical,-rate,rel_tol=3e-6,abs_tol=3e-8)


def test_total_piola_matches_energy_finite_difference():
    f=((1.15,0.04,0.0),(0.01,0.96,0.03),(0.0,0.02,1.03))
    fp=((1.02,0.01,0.0),(0.0,0.99,0.01),(0.0,0.0,1.01))
    p=total_first_piola(f,fp,P)
    h=1e-6
    for i,j in ((0,0),(0,1),(1,2),(2,2)):
        fp1=[list(r) for r in f]; fm1=[list(r) for r in f]
        fp1[i][j]+=h; fm1[i][j]-=h
        ep=elastic_energy_density(elastic_f(tuple(tuple(r) for r in fp1),fp),P)
        em=elastic_energy_density(elastic_f(tuple(tuple(r) for r in fm1),fp),P)
        num=(ep-em)/(2*h)
        assert math.isclose(num,p[i][j],rel_tol=2e-7,abs_tol=2e-8)


def test_matrix_exponential_determinant_identity():
    a=((0.2,0.1,0.0),(0.1,-0.3,0.02),(0.0,0.02,0.4))
    e=matrix_exponential3(a)
    assert det3(e)>0.0
    assert math.isclose(det3(e),math.exp(trace3(a)),rel_tol=2e-13,abs_tol=2e-13)


def test_nonpositive_determinant_fails_closed():
    with pytest.raises(HyperelasticFieldError,match=r"GL\+\(3\)"):
        MultiplicativePlasticState(((-1,0,0),(0,1,0),(0,0,1)),identity3())
