import math

from ciel_geometry.phasenav.gl4_coframe_bivector36 import (
    MINKOWSKI_ETA,
    bivector_metric6,
    coframe_metric4,
    determinant,
    frobenius_norm,
    lambda2_gl4,
    left_lorentz_action_on_coframe,
    lorentz_boost4,
    matmul,
    spatial_gl3_compatibility_residual,
    spatial_rotation4,
    spatial_so3_compatibility_residual,
    sub,
    validate_bivector_lorentz6,
    validate_lorentz4,
    z2_partner,
)


def test_exterior_square_is_group_homomorphism():
    a=((1.1,0.1,0.0,0.02),(0.0,0.9,0.03,0.0),(0.01,0.0,1.2,0.05),(0.0,0.02,0.0,1.05))
    b=((0.95,0.0,0.02,0.0),(0.03,1.1,0.0,0.01),(0.0,0.04,0.98,0.0),(0.02,0.0,0.01,1.07))
    lhs=lambda2_gl4(matmul(a,b))
    rhs=matmul(lambda2_gl4(a),lambda2_gl4(b))
    assert frobenius_norm(sub(lhs,rhs))<1e-12


def test_exterior_square_determinant_identity():
    a=((1.1,0.1,0.0,0.02),(0.0,0.9,0.03,0.0),(0.01,0.0,1.2,0.05),(0.0,0.02,0.0,1.05))
    assert math.isclose(determinant(lambda2_gl4(a)),determinant(a)**3,rel_tol=2e-13,abs_tol=2e-13)


def test_spatial_gl3_embedding_recovers_previous_carrier():
    f=((1.1,0.2,0.1),(0.0,0.9,0.05),(0.02,0.1,1.2))
    assert spatial_gl3_compatibility_residual(f)<1e-13


def test_lorentz_boost_and_bivector_metric_preservation():
    l=lorentz_boost4((1,2,3),0.8)
    assert validate_lorentz4(l).admitted
    b=lambda2_gl4(l)
    assert validate_bivector_lorentz6(b).admitted


def test_bivector_metric_has_3_3_signature_in_declared_basis():
    g=bivector_metric6()
    assert tuple(g[i][i] for i in range(6))==(-1.0,-1.0,-1.0,1.0,1.0,1.0)
    assert sum(abs(g[i][j]) for i in range(6) for j in range(6) if i!=j)==0.0


def test_spatial_rotation_recovers_previous_so3_carrier():
    for axis in ((1,0,0),(0,1,0),(1,2,3)):
        assert spatial_so3_compatibility_residual(axis,0.6)<1e-13


def test_coframe_metric_is_local_lorentz_gauge_invariant():
    e=((1.1,0.1,0.0,0.02),(0.0,0.95,0.03,0.0),(0.01,0.0,1.05,0.04),(0.0,0.02,0.0,1.02))
    l=lorentz_boost4((1,0,1),0.5)
    e2=left_lorentz_action_on_coframe(l,e)
    assert frobenius_norm(sub(coframe_metric4(e2),coframe_metric4(e)))<1e-12


def test_z2_kernel_is_exact():
    a=((1.1,0.1,0.0,0.02),(0.0,0.9,0.03,0.0),(0.01,0.0,1.2,0.05),(0.0,0.02,0.0,1.05))
    assert frobenius_norm(sub(lambda2_gl4(a),lambda2_gl4(z2_partner(a))))==0.0


def test_generic_gl4_matrix_is_not_silently_lorentz():
    a=((1.1,0.1,0.0,0.02),(0.0,0.9,0.03,0.0),(0.01,0.0,1.2,0.05),(0.0,0.02,0.0,1.05))
    assert not validate_lorentz4(a).admitted
    assert not validate_bivector_lorentz6(lambda2_gl4(a)).admitted
