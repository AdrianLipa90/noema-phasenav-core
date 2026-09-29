import math
import pytest

from ciel_geometry.phasenav.adm_coframe_bridge import (
    ADMCoframeError,
    ADMFrame,
    bivector36_from_adm,
    conformal_reference_adm,
    coframe4_from_adm,
    expected_metric4_from_adm,
    metric4_from_adm,
    recover_adm_from_time_gauge_coframe,
    zero_shift_unit_lapse_gl3_residual,
)
from ciel_geometry.phasenav.cartan_conformal_reference import QuadraticConformalCoframe
from ciel_geometry.phasenav.gl4_coframe_bivector36 import frobenius_norm, sub


def _vnorm(v):
    return math.sqrt(sum(x*x for x in v))


def test_adm_metric_formula_matches_coframe_metric():
    f=ADMFrame(
        1.3,
        ((1.1,0.1,0.0),(0.0,0.9,0.05),(0.02,0.03,1.05)),
        (0.2,-0.1,0.05),
    )
    assert frobenius_norm(sub(metric4_from_adm(f),expected_metric4_from_adm(f)))<1e-13


def test_time_gauge_roundtrip():
    f=ADMFrame(
        1.3,
        ((1.1,0.1,0.0),(0.0,0.9,0.05),(0.02,0.03,1.05)),
        (0.2,-0.1,0.05),
    )
    got=recover_adm_from_time_gauge_coframe(coframe4_from_adm(f))
    assert math.isclose(got.lapse,f.lapse,rel_tol=1e-14)
    assert frobenius_norm(sub(got.triad,f.triad))<1e-14
    assert _vnorm(tuple(got.shift[i]-f.shift[i] for i in range(3)))<1e-14


def test_zero_shift_unit_lapse_exactly_recovers_spatial_gl3_carrier():
    e=((1.1,0.2,0.1),(0.0,0.9,0.05),(0.02,0.1,1.2))
    assert zero_shift_unit_lapse_gl3_residual(e)<1e-13


def test_conformal_cartan_reference_is_exact_adm_special_case():
    a=0.2;x=0.3;y=-0.4
    adm=conformal_reference_adm(a,x,y)
    cartan=QuadraticConformalCoframe(a)
    assert frobenius_norm(sub(coframe4_from_adm(adm),cartan.coframe4(x,y)))<1e-14
    assert frobenius_norm(sub(metric4_from_adm(adm),cartan.metric4(x,y)))<1e-14


def test_non_time_gauge_coframe_is_rejected():
    e=[
        [1.0,0.01,0.0,0.0],
        [0.0,1.0,0.0,0.0],
        [0.0,0.0,1.0,0.0],
        [0.0,0.0,0.0,1.0],
    ]
    with pytest.raises(ADMCoframeError,match="time gauge"):
        recover_adm_from_time_gauge_coframe(e)


def test_nonpositive_lapse_and_negative_triad_orientation_fail_closed():
    with pytest.raises(ADMCoframeError):
        ADMFrame(0.0,((1,0,0),(0,1,0),(0,0,1)),(0,0,0))
    with pytest.raises(ADMCoframeError):
        ADMFrame(1.0,((-1,0,0),(0,1,0),(0,0,1)),(0,0,0))
