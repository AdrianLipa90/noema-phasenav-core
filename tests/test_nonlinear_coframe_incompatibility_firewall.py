import math

from ciel_geometry.phasenav.nonlinear_coframe_incompatibility_firewall import (
    conformal_intrinsic_curvature_witness,
    conformal_triad_row_curl_norm,
    rotated_flat_row_curl_norm,
    rotated_flat_spin_curvature,
    rotation_z_metric,
)


def _frob(a):
    return math.sqrt(sum(x*x for row in a for x in row))


def test_local_rotation_has_identity_metric_for_any_angle():
    for theta in (0.0,0.3,-1.2,2.1):
        g=rotation_z_metric(theta)
        assert _frob(tuple(tuple(g[i][j]-(1.0 if i==j else 0.0) for j in range(3)) for i in range(3)))<1e-14


def test_local_rotation_can_have_nonzero_raw_curl_with_flat_metric():
    # theta=b*x gives Grad theta=(b,0) and a spatially varying orthonormal frame.
    b=0.7
    curl_norm=rotated_flat_row_curl_norm(0.4,b,0.0)
    assert math.isclose(curl_norm,abs(b),rel_tol=1e-14)
    assert curl_norm>0.0


def test_rotated_flat_torsion_free_connection_has_zero_curvature():
    # smooth theta has theta_xy=theta_yx
    omega_curv=rotated_flat_spin_curvature(0.37,0.37)
    assert _frob(omega_curv)==0.0


def test_noncommuting_mixed_partials_are_rejected_as_non_smooth_control():
    omega_curv=rotated_flat_spin_curvature(0.37,0.21)
    assert _frob(omega_curv)>0.0


def test_nonflat_conformal_reference_can_have_zero_raw_curl_at_point():
    a=0.2
    assert conformal_triad_row_curl_norm(a,0.0,0.0)==0.0
    assert conformal_intrinsic_curvature_witness(a,0.0,0.0)>0.0


def test_conformal_raw_curl_nonzero_away_from_critical_point():
    a=0.2
    assert conformal_triad_row_curl_norm(a,0.3,-0.4)>0.0
    assert conformal_intrinsic_curvature_witness(a,0.3,-0.4)>0.0
