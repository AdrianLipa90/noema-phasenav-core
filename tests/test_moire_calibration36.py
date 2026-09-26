import math

from ciel_geometry.phasenav.moire_calibration36 import residual36


def test_identical_state_zero():
    x=[0.03*i for i in range(36)]
    r=residual36(x,x)
    assert math.isclose(r.raw,0.0,abs_tol=1e-14)
    assert math.isclose(r.shape,0.0,abs_tol=1e-14)


def test_exact_decomposition():
    a=[0.02*i for i in range(36)]
    b=[0.09*i+0.4 for i in range(36)]
    r=residual36(a,b)
    assert math.isclose(r.raw,r.shape+r.coherent,rel_tol=1e-13,abs_tol=1e-13)


def test_uniform_phase_is_visible_raw_and_invisible_shape():
    theta=math.radians(3.5)
    a=[0.0]*36
    b=[theta]*36
    r=residual36(a,b)
    expected=4.0*math.sin(theta/2.0)**2
    assert math.isclose(r.raw,expected,rel_tol=1e-13)
    assert math.isclose(r.shape,0.0,abs_tol=1e-13)
    assert math.isclose(r.coherent,expected,rel_tol=1e-13)


def test_layer_swap_preserves_raw_and_shape():
    a=[0.01*i for i in range(36)]
    b=[0.07*i+0.2 for i in range(36)]
    ab=residual36(a,b)
    ba=residual36(b,a)
    assert math.isclose(ab.raw,ba.raw,rel_tol=1e-13)
    assert math.isclose(ab.shape,ba.shape,rel_tol=1e-13)
    assert math.isclose(ab.coherence_phase,-ba.coherence_phase,rel_tol=1e-13,abs_tol=1e-13)
