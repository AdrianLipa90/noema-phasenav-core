import math

from ciel_geometry.phasenav.gl4_coframe_bivector36 import (
    frobenius_norm,
    lorentz_boost4,
    matmul,
    spatial_rotation4,
    sub,
    validate_lorentz4,
)
from ciel_geometry.phasenav.lorentz_curvature_small_loop import (
    commutator4,
    connection_field_strength4,
    constant_connection_plaquette_holonomy,
    constant_gauge_transform_connection,
    induced_field_strength6,
    jacobi_bianchi_residual_constant,
    matrix_exponential4,
    normalized_small_loop_generator,
    small_loop_error,
)
from ciel_geometry.phasenav.lorentz_holonomy36 import (
    boost_generator4,
    induced_generator6,
    rotation_generator4,
)


def test_exponential_of_lorentz_generator_is_lorentz():
    for a in (boost_generator4((1,2,3)),rotation_generator4((1,2,3))):
        u=matrix_exponential4(tuple(tuple(0.7*x for x in row) for row in a))
        assert validate_lorentz4(u,tolerance=2e-12).admitted


def test_constant_connection_small_loop_converges_to_commutator():
    ax=boost_generator4((1,0,0))
    ay=rotation_generator4((0,0,1))
    hs=(0.1,0.05,0.025,0.0125)
    errors=[small_loop_error(ax,ay,h) for h in hs]
    assert all(errors[i+1]<0.55*errors[i] for i in range(len(errors)-1))
    assert errors[-1]<0.013


def test_orientation_reversal_flips_leading_curvature_sign():
    ax=boost_generator4((1,0,0))
    ay=rotation_generator4((0,0,1))
    h=1e-3
    plus=normalized_small_loop_generator(ax,ay,h,orientation=1)
    minus=normalized_small_loop_generator(ax,ay,h,orientation=-1)
    target=connection_field_strength4(ax,ay)
    assert frobenius_norm(sub(plus,target))<1.1e-3
    neg_target=tuple(tuple(-x for x in row) for row in target)
    assert frobenius_norm(sub(minus,neg_target))<1.1e-3


def test_commuting_connection_has_zero_constant_curvature_and_trivial_loop():
    ax=boost_generator4((1,0,0))
    ay=tuple(tuple(0.3*x for x in row) for row in ax)
    f=connection_field_strength4(ax,ay)
    assert frobenius_norm(f)<1e-14
    hloop=constant_connection_plaquette_holonomy(ax,ay,0.2)
    eye=tuple(tuple(1.0 if i==j else 0.0 for j in range(4)) for i in range(4))
    assert frobenius_norm(sub(hloop,eye))<1e-13


def test_induced_curvature_preserves_lie_bracket():
    ax=boost_generator4((1,0,0))
    ay=rotation_generator4((0,0,1))
    f=commutator4(ax,ay)
    jx=induced_generator6(ax);jy=induced_generator6(ay)
    lhs=induced_field_strength6(f)
    rhs=sub(matmul(jx,jy),matmul(jy,jx))
    assert frobenius_norm(sub(lhs,rhs))<1e-13


def test_constant_global_gauge_covariance():
    ax=boost_generator4((1,0,0))
    ay=rotation_generator4((0,0,1))
    g=matmul(lorentz_boost4((1,1,0),0.2),spatial_rotation4((0,1,0),0.3))
    f=connection_field_strength4(ax,ay)
    ax2=constant_gauge_transform_connection(g,ax)
    ay2=constant_gauge_transform_connection(g,ay)
    f2=connection_field_strength4(ax2,ay2)
    expected=constant_gauge_transform_connection(g,f)
    assert frobenius_norm(sub(f2,expected))<2e-13


def test_constant_connection_bianchi_is_jacobi_identity():
    a=boost_generator4((1,0,0))
    b=boost_generator4((0,1,0))
    c=rotation_generator4((0,0,1))
    assert jacobi_bianchi_residual_constant(a,b,c)<1e-14


def test_derivative_terms_enter_field_strength_with_correct_sign():
    ax=boost_generator4((1,0,0))
    ay=rotation_generator4((0,0,1))
    d_x_ay=rotation_generator4((1,0,0))
    d_y_ax=boost_generator4((0,1,0))
    got=connection_field_strength4(ax,ay,d_x_ay,d_y_ax)
    expected=tuple(tuple(
        d_x_ay[i][j]-d_y_ax[i][j]+commutator4(ax,ay)[i][j]
        for j in range(4)
    ) for i in range(4))
    assert frobenius_norm(sub(got,expected))<1e-14
