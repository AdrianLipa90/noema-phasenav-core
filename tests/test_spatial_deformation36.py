import math
import pytest

from ciel_geometry.phasenav.spatial_deformation36 import (
    Deformation36Error,
    cofactor3,
    column_lengths2,
    deformation36,
    expected_block_deformation36,
    hex_direct_basis2,
    isotropic_scale2,
    moire_direct_basis2,
    recover_deformation3,
    rotation2,
    validate_deformation36,
)
from ciel_geometry.phasenav.spatial_rotation36 import (
    rotation3_axis_angle,
    rotation36_spatial,
)


def _frob_diff(a,b):
    return math.sqrt(sum((a[i][j]-b[i][j])**2 for i in range(len(a)) for j in range(len(a[0]))))


def test_exact_gl3_block_formula():
    f=((1.1,0.2,0.1),(0.0,0.9,0.05),(0.02,0.1,1.2))
    a=deformation36(f)
    b=expected_block_deformation36(f)
    assert _frob_diff(a,b)<1e-13
    assert validate_deformation36(a).admitted


def test_recover_gl3_from_top_block_and_cofactor_gate():
    f=((1.05,0.03,-0.02),(0.01,0.97,0.04),(0.0,-0.01,1.08))
    m=deformation36(f)
    got=recover_deformation3(m)
    assert _frob_diff(got,f)<1e-14


def test_corrupted_cofactor_block_fails_closed():
    f=((1.05,0,0),(0,0.98,0),(0,0,1.02))
    m=[list(r) for r in deformation36(f)]
    m[3][3]+=0.01
    assert not validate_deformation36(tuple(tuple(r) for r in m)).admitted
    with pytest.raises(Deformation36Error):
        recover_deformation3(tuple(tuple(r) for r in m))


def test_rotation_is_so3_special_case():
    r=rotation3_axis_angle((1,2,3),0.4)
    assert _frob_diff(deformation36(r),rotation36_spatial((1,2,3),0.4))<1e-13


def test_hex_rotation_moire_period_matches_scalar_formula():
    a=0.246
    direct=hex_direct_basis2(a)
    for deg in (1.12,3.5,21.8):
        theta=math.radians(deg)
        moire=moire_direct_basis2(direct,rotation2(theta))
        l1,l2=column_lengths2(moire)
        expected=a/(2*math.sin(abs(theta)/2))
        assert math.isclose(l1,expected,rel_tol=1e-12)
        assert math.isclose(l2,expected,rel_tol=1e-12)


def test_isotropic_lattice_mismatch_exact_scale():
    a=0.246
    direct=hex_direct_basis2(a)
    for eps in (0.01,0.02,-0.01):
        s=1.0+eps
        moire=moire_direct_basis2(direct,isotropic_scale2(s))
        expected=a*abs(s/(s-1.0))
        l1,l2=column_lengths2(moire)
        assert math.isclose(l1,expected,rel_tol=1e-12)
        assert math.isclose(l2,expected,rel_tol=1e-12)


def test_zero_mismatch_has_infinite_not_finite_2d_moire_cell():
    direct=hex_direct_basis2(0.246)
    with pytest.raises(Deformation36Error,match="singular"):
        moire_direct_basis2(direct,isotropic_scale2(1.0))
