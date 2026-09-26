import math

from ciel_geometry.phasenav.gl4_coframe_bivector36 import (
    frobenius_norm,
    identity4,
    lambda2_gl4,
    lorentz_boost4,
    matmul,
    spatial_rotation4,
    sub,
)
from ciel_geometry.phasenav.lorentz_holonomy36 import (
    bivector_lie_residual6,
    boost_generator4,
    conjugate4,
    gauge_transform_link4,
    holonomy_witness,
    induced_generator6,
    link_from_vertex_frames,
    loop_residual4,
    loop_residual6,
    lorentz_lie_residual4,
    noncommuting_commutator_loop,
    path_holonomy4,
    path_holonomy6_from_links4,
    pure_gauge_square_links,
    rotation_generator4,
    trace,
)


def test_lorentz_generators_satisfy_lie_metric_condition():
    for w in (boost_generator4((1,2,3)),rotation_generator4((1,2,3))):
        assert lorentz_lie_residual4(w)<1e-14
        assert bivector_lie_residual6(induced_generator6(w))<1e-14


def test_induced_generator_matches_exterior_square_derivative():
    w=boost_generator4((1,2,3))
    j=induced_generator6(w)
    eps=1e-7
    a=tuple(tuple((1.0 if i==k else 0.0)+eps*w[i][k] for k in range(4)) for i in range(4))
    b=lambda2_gl4(a)
    approx=tuple(tuple((1.0 if i==k else 0.0)+eps*j[i][k] for k in range(6)) for i in range(6))
    assert frobenius_norm(sub(b,approx))<2e-13


def test_pure_gauge_square_has_identity_holonomy_in_4d_and_6d():
    g0=identity4()
    g1=lorentz_boost4((1,0,0),0.2)
    g2=matmul(spatial_rotation4((0,0,1),0.3),lorentz_boost4((1,1,0),0.1))
    g3=matmul(lorentz_boost4((0,1,0),-0.15),spatial_rotation4((1,0,0),0.2))
    links=pure_gauge_square_links(g0,g1,g2,g3)
    assert loop_residual4(links)<2e-14
    assert loop_residual6(links)<4e-14


def test_lambda2_commutes_with_path_composition():
    u=lorentz_boost4((1,0,0),0.3)
    v=spatial_rotation4((0,0,1),0.4)
    links=(u,v)
    lhs=lambda2_gl4(path_holonomy4(links))
    rhs=path_holonomy6_from_links4(links)
    assert frobenius_norm(sub(lhs,rhs))<1e-13


def test_closed_loop_gauge_transforms_by_basepoint_conjugation():
    u=lorentz_boost4((1,0,0),0.3)
    v=spatial_rotation4((0,0,1),0.4)
    links=noncommuting_commutator_loop(u,v)
    h=path_holonomy4(links)

    h0=lorentz_boost4((1,1,0),0.2)
    h1=spatial_rotation4((1,0,0),0.1)
    h2=lorentz_boost4((0,1,1),-0.12)
    h3=spatial_rotation4((0,1,0),-0.18)
    hs=(h0,h1,h2,h3)
    transformed=(
        gauge_transform_link4(links[0],hs[0],hs[1]),
        gauge_transform_link4(links[1],hs[1],hs[2]),
        gauge_transform_link4(links[2],hs[2],hs[3]),
        gauge_transform_link4(links[3],hs[3],hs[0]),
    )
    ht=path_holonomy4(transformed)
    expected=conjugate4(h0,h)
    assert frobenius_norm(sub(ht,expected))<2e-13
    assert math.isclose(trace(ht),trace(h),rel_tol=1e-13,abs_tol=1e-13)


def test_noncommuting_loop_is_nontrivial_but_not_called_curvature():
    u=lorentz_boost4((1,0,0),0.3)
    v=spatial_rotation4((0,0,1),0.4)
    w=holonomy_witness(noncommuting_commutator_loop(u,v))
    assert w.residual4>1e-3
    assert w.residual6>1e-3


def test_pure_gauge_links_are_exactly_built_from_vertex_frames():
    a=lorentz_boost4((1,0,0),0.2)
    b=spatial_rotation4((0,0,1),0.3)
    u=link_from_vertex_frames(a,b)
    assert frobenius_norm(sub(matmul(u,a),b))<1e-13
