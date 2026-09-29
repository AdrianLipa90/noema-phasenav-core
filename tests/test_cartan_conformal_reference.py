import math

from ciel_geometry.phasenav.cartan_conformal_reference import QuadraticConformalCoframe
from ciel_geometry.phasenav.gl4_coframe_bivector36 import (
    MINKOWSKI_ETA,
    frobenius_norm,
    identity4,
    sub,
)
from ciel_geometry.phasenav.lorentz_holonomy36 import bivector_lie_residual6, lorentz_lie_residual4


def test_metric_matches_declared_conformal_product():
    ref=QuadraticConformalCoframe(0.2)
    x,y=0.3,-0.4
    g=ref.metric4(x,y)
    s=math.exp(2.0*ref.sigma(x,y))
    expected=((-1.0,0.0,0.0,0.0),(0.0,s,0.0,0.0),(0.0,0.0,s,0.0),(0.0,0.0,0.0,1.0))
    assert frobenius_norm(sub(g,expected))<1e-14


def test_spin_connection_is_lorentz_algebra_valued():
    ref=QuadraticConformalCoframe(0.2)
    assert lorentz_lie_residual4(ref.spin_connection_x(0.3,-0.4))<1e-14
    assert lorentz_lie_residual4(ref.spin_connection_y(0.3,-0.4))<1e-14


def test_cartan_torsion_is_exactly_zero():
    ref=QuadraticConformalCoframe(0.2)
    for x,y in ((0.0,0.0),(0.3,-0.4),(1.2,0.7)):
        assert ref.torsion_xy_norm(x,y)<1e-14


def test_spin_curvature_is_nonzero_and_matches_minus_laplacian_component():
    ref=QuadraticConformalCoframe(0.2)
    omega=ref.spin_curvature_xy(0.3,-0.4)
    lap=ref.laplacian_sigma(0.3,-0.4)
    assert math.isclose(omega[1][2],-lap,rel_tol=1e-14,abs_tol=1e-14)
    assert math.isclose(omega[2][1], lap,rel_tol=1e-14,abs_tol=1e-14)


def test_cartan_to_coordinate_riemann_matches_direct_metric_result():
    ref=QuadraticConformalCoframe(0.2)
    for x,y in ((0.0,0.0),(0.3,-0.4),(1.2,0.7)):
        a=ref.coordinate_riemann_xy_from_cartan(x,y)
        b=ref.coordinate_riemann_xy_direct_metric(x,y)
        assert frobenius_norm(sub(a,b))<1e-13


def test_gaussian_and_scalar_curvature_formulae():
    ref=QuadraticConformalCoframe(0.2)
    x,y=0.3,-0.4
    lap=0.8
    expected_k=-math.exp(-2*ref.sigma(x,y))*lap
    assert math.isclose(ref.gaussian_curvature(x,y),expected_k,rel_tol=1e-14)
    assert math.isclose(ref.scalar_curvature4(x,y),2*expected_k,rel_tol=1e-14)


def test_flat_limit_a_zero_has_zero_connection_curvature_and_torsion():
    ref=QuadraticConformalCoframe(0.0)
    assert ref.torsion_xy_norm(0.4,-0.2)==0.0
    assert frobenius_norm(ref.spin_curvature_xy(0.4,-0.2))==0.0
    assert ref.scalar_curvature4(0.4,-0.2)==0.0


def test_rectangle_holonomy_has_curvature_area_small_loop_limit():
    ref=QuadraticConformalCoframe(0.2)
    target=ref.spin_curvature_xy(0.0,0.0)
    errors=[]
    for h in (0.2,0.1,0.05,0.025):
        H=ref.rectangle_spin_holonomy4(0.0,h,0.0,h)
        approx=tuple(tuple((H[i][j]-(1.0 if i==j else 0.0))/(h*h) for j in range(4)) for i in range(4))
        errors.append(frobenius_norm(sub(approx,target)))
    assert all(errors[i+1]<0.55*errors[i] for i in range(len(errors)-1))


def test_bivector_curvature_stays_in_so_3_3():
    ref=QuadraticConformalCoframe(0.2)
    assert bivector_lie_residual6(ref.bivector_curvature_xy(0.3,-0.4))<1e-14
