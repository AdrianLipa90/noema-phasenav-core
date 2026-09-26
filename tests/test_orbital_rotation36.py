import math

from ciel_geometry.phasenav.orbital_rotation36 import (
    calibrated_twist_residual36,
    generator36_xy,
    moire_period_from_rotation36,
    rotation36_xy,
    trace6,
    twist_from_rotation36_trace,
)


def _matmul(a,b):
    return tuple(
        tuple(sum(a[i][k]*b[k][j] for k in range(6)) for j in range(6))
        for i in range(6)
    )


def _maxerr(a,b):
    return max(abs(a[i][j]-b[i][j]) for i in range(6) for j in range(6))


def test_trace_formula():
    for theta in (0.0,0.1,math.radians(3.5),0.7):
        r=rotation36_xy(theta)
        assert math.isclose(trace6(r),2.0+4.0*math.cos(theta),rel_tol=1e-13,abs_tol=1e-13)


def test_group_law():
    a,b=0.21,-0.07
    assert _maxerr(_matmul(rotation36_xy(a),rotation36_xy(b)),rotation36_xy(a+b))<1e-13


def test_residual_matches_scalar_phase_law():
    for theta in (0.0,math.radians(1.12),math.radians(3.5),math.radians(21.8)):
        d=calibrated_twist_residual36(rotation36_xy(theta))
        expected=4.0*math.sin(theta/2.0)**2
        assert math.isclose(d,expected,rel_tol=1e-13,abs_tol=1e-14)


def test_period_matches_graphene_anchor():
    a_nm=0.246
    theta=math.radians(1.12)
    L=moire_period_from_rotation36(a_nm,rotation36_xy(theta))
    assert abs(L-12.6)<0.05


def test_trace_inverse_angle():
    for theta in (0.1,math.radians(3.5),math.radians(21.8)):
        got=twist_from_rotation36_trace(rotation36_xy(theta))
        assert math.isclose(got,abs(theta),rel_tol=1e-13,abs_tol=1e-13)


def test_generator_structure():
    j=generator36_xy()
    nonzero={(i,k):j[i][k] for i in range(6) for k in range(6) if j[i][k]!=0.0}
    assert nonzero=={(0,1):-1.0,(1,0):1.0,(3,4):-1.0,(4,3):1.0}
