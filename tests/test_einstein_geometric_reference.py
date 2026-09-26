import math

from ciel_geometry.phasenav.einstein_geometric_reference import EinsteinConformalReference
from ciel_geometry.phasenav.gl4_coframe_bivector36 import frobenius_norm


def _norm(v):
    return math.sqrt(sum(x*x for x in v))


def test_ricci_matches_analytic_reference():
    ref=EinsteinConformalReference(0.2)
    ric=ref.ricci_cov4(0.3,-0.4)
    assert ric[0][0]==0.0
    assert math.isclose(ric[1][1],-0.8,abs_tol=1e-14)
    assert math.isclose(ric[2][2],-0.8,abs_tol=1e-14)
    assert ric[3][3]==0.0


def test_einstein_covariant_components():
    ref=EinsteinConformalReference(0.2)
    x,y=0.3,-0.4
    q=0.8*math.exp(-2*ref.sigma(x,y))
    G=ref.einstein_cov4(x,y)
    assert math.isclose(G[0][0],-q,rel_tol=1e-14)
    assert abs(G[1][1])<1e-14
    assert abs(G[2][2])<1e-14
    assert math.isclose(G[3][3],q,rel_tol=1e-14)


def test_mixed_trace_identity_G_equals_minus_R():
    ref=EinsteinConformalReference(0.2)
    for x,y in ((0.0,0.0),(0.3,-0.4),(1.0,0.2)):
        assert math.isclose(
            ref.einstein_trace_mixed(x,y),
            -ref.scalar_curvature4(x,y),
            rel_tol=1e-14,
            abs_tol=1e-14,
        )


def test_contracted_bianchi_identity():
    ref=EinsteinConformalReference(0.2)
    for x,y in ((0.0,0.0),(0.3,-0.4),(1.0,0.2),(-0.7,0.9)):
        assert _norm(ref.contracted_bianchi_mixed(x,y))<1e-13


def test_flat_limit_has_zero_einstein_tensor():
    ref=EinsteinConformalReference(0.0)
    assert frobenius_norm(ref.einstein_cov4(0.4,-0.2))==0.0
    assert _norm(ref.contracted_bianchi_mixed(0.4,-0.2))==0.0


def test_einstein_tensor_is_symmetric():
    ref=EinsteinConformalReference(0.2)
    assert ref.symmetry_residual(0.3,-0.4)==0.0


def test_geometry_does_not_require_source_constant():
    ref=EinsteinConformalReference(0.2)
    # Construction is fully geometric; no kappa or T_mu_nu parameter appears.
    G1=ref.einstein_cov4(0.2,0.1)
    G2=ref.einstein_cov4(0.2,0.1)
    assert G1==G2
