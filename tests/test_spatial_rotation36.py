import math
import pytest

from ciel_geometry.phasenav.orbital_rotation36 import rotation36_xy
from ciel_geometry.phasenav.spatial_rotation36 import (
    calibrated_spatial_residual36,
    generator36_spatial,
    rotation36_spatial,
    axis_angle_from_rotation36,
    validate_spatial_rotation36,
    z_axis_compatibility_residual,
)
from ciel_geometry.phasenav.typed_spatial_phase36_adapter import (
    SpatialLogPhase36Record,
    SpatialPhase36AdapterError,
    SPATIAL_LOG_PHASE36_BASIS_ID,
    GENERIC_T36_BASIS_ID,
    adapt_spatial_log_phase36,
    encode_spatial_rotvec_log_phase36,
)


def _matmul(a,b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(6)) for j in range(6)) for i in range(6))


def _sub(a,b):
    return tuple(tuple(a[i][j]-b[i][j] for j in range(6)) for i in range(6))


def _frob(a):
    return math.sqrt(sum(x*x for row in a for x in row))


def _comm(a,b):
    return _sub(_matmul(a,b),_matmul(b,a))


def test_lambda2_spatial_is_two_identical_rotation_blocks():
    m=rotation36_spatial((1.0,2.0,3.0),0.4)
    assert validate_spatial_rotation36(m).admitted
    assert max(abs(m[i][j]) for i in range(3) for j in range(3,6))<1e-13
    assert max(abs(m[i][j]) for i in range(3,6) for j in range(3))<1e-13
    assert max(abs(m[i][j]-m[i+3][j+3]) for i in range(3) for j in range(3))<1e-13


def test_so3_generator_commutators():
    jx=generator36_spatial((1,0,0))
    jy=generator36_spatial((0,1,0))
    jz=generator36_spatial((0,0,1))
    assert _frob(_sub(_comm(jx,jy),jz))<1e-13


def test_trace_residual_axis_independent():
    theta=0.7
    expected=4*math.sin(theta/2)**2
    for axis in ((1,0,0),(0,1,0),(0,0,1),(1,2,3)):
        assert math.isclose(calibrated_spatial_residual36(rotation36_spatial(axis,theta)),expected,rel_tol=1e-13)


def test_z_axis_exactly_recovers_previous_so2_representation():
    for theta in (0.1,0.7,-0.3):
        assert z_axis_compatibility_residual(theta)<1e-13
        assert _frob(_sub(rotation36_spatial((0,0,1),theta),rotation36_xy(theta)))<1e-13


def test_axis_angle_inverse():
    axis=(1.0,2.0,3.0);theta=0.8
    got_axis,got_theta=axis_angle_from_rotation36(rotation36_spatial(axis,theta))
    n=math.sqrt(sum(x*x for x in axis)); expected=tuple(x/n for x in axis)
    assert math.isclose(got_theta,theta,rel_tol=1e-13)
    assert max(abs(a-b) for a,b in zip(got_axis,expected))<1e-13


def test_typed_so3_log_phase_roundtrip():
    ref=encode_spatial_rotvec_log_phase36((0,0,0),source_id="ref")
    w=(0.12,-0.08,0.17)
    target=encode_spatial_rotvec_log_phase36(w,source_id="target")
    b=adapt_spatial_log_phase36(ref,target)
    assert max(abs(a-bb) for a,bb in zip(b.rotation_vector,w))<1e-13
    assert b.generator_fit_abs<1e-13


def test_generic_t36_rejected():
    generic=SpatialLogPhase36Record((0.0,)*36,GENERIC_T36_BASIS_ID,"legacy","generic")
    typed=encode_spatial_rotvec_log_phase36((0.1,0,0),source_id="typed")
    with pytest.raises(SpatialPhase36AdapterError):
        adapt_spatial_log_phase36(generic,typed)


def test_off_subspace_perturbation_rejected():
    ref=encode_spatial_rotvec_log_phase36((0,0,0),source_id="ref")
    target=encode_spatial_rotvec_log_phase36((0.1,0.2,-0.1),source_id="target")
    bad=list(target.angles);bad[0]=(bad[0]+0.01)%(2*math.pi)
    corrupt=SpatialLogPhase36Record(tuple(bad),SPATIAL_LOG_PHASE36_BASIS_ID,target.derivation_id,"bad")
    with pytest.raises(SpatialPhase36AdapterError):
        adapt_spatial_log_phase36(ref,corrupt)
