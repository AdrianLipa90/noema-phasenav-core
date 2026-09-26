import math
import pytest

from ciel_geometry.phasenav.hyperelastic_field36 import (
    HyperelasticFieldError,
    HyperelasticParameters,
    carrier_energy_density,
    curl_f_from_grad_f,
    deformation_gradient,
    defect_energy_density,
    first_piola_stress,
    gradient_energy_density,
    linear_dispersion_omega_sq,
    linear_elastic_energy_density,
    linear_wave_speeds,
    neo_hookean_energy_density,
    periodic_linear_acceleration_1d,
)
from ciel_geometry.phasenav.spatial_deformation36 import deformation36
from ciel_geometry.phasenav.spatial_rotation36 import rotation3_axis_angle


P = HyperelasticParameters(rho0=2.5, mu=3.0, lame_lambda=4.0, eta=0.7)


def _frob(a):
    return math.sqrt(sum(x*x for row in a for x in row))


def test_identity_and_pure_rotation_have_zero_stored_energy():
    eye=((1,0,0),(0,1,0),(0,0,1))
    assert math.isclose(neo_hookean_energy_density(eye,P),0.0,abs_tol=1e-14)
    for axis in ((1,0,0),(0,1,0),(1,2,3)):
        r=rotation3_axis_angle(axis,0.73)
        assert math.isclose(neo_hookean_energy_density(r,P),0.0,abs_tol=1e-13)
        assert _frob(first_piola_stress(r,P))<1e-12


def test_frame_indifference_left_rotation():
    f=((1.10,0.08,0.00),(0.02,0.94,0.03),(0.00,0.01,1.05))
    r=rotation3_axis_angle((1,2,3),0.51)
    rf=tuple(tuple(sum(r[i][k]*f[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    assert math.isclose(
        neo_hookean_energy_density(rf,P),
        neo_hookean_energy_density(f,P),
        rel_tol=1e-13,
        abs_tol=1e-13,
    )


def test_orientation_reversal_fails_closed():
    f=((-1,0,0),(0,1,0),(0,0,1))
    with pytest.raises(HyperelasticFieldError,match="det\(F\)>0"):
        neo_hookean_energy_density(f,P)


def test_small_strain_limit_matches_linear_elasticity_to_second_order():
    g0=((0.30,0.07,-0.02),(0.01,-0.20,0.05),(0.03,-0.04,0.10))
    for eps in (1e-3,5e-4,2.5e-4):
        g=tuple(tuple(eps*x for x in row) for row in g0)
        f=deformation_gradient(g)
        w=neo_hookean_energy_density(f,P)
        wl=linear_elastic_energy_density(g,P)
        # Error is cubic while energy is quadratic; relative error shrinks linearly.
        assert abs(w-wl) / max(abs(wl),1e-30) < 2e-3


def test_bivector_carrier_energy_agrees_with_direct_f():
    f=((1.03,0.04,0.0),(0.01,0.98,0.02),(0.0,0.01,1.02))
    assert math.isclose(
        carrier_energy_density(deformation36(f),P),
        neo_hookean_energy_density(f,P),
        rel_tol=1e-14,
        abs_tol=1e-14,
    )


def test_gradient_energy_positive_and_zero_for_uniform_f():
    zero=tuple(tuple((0.0,0.0,0.0) for _ in range(3)) for _ in range(3))
    assert gradient_energy_density(zero,P)==0.0
    g=[[[0.0]*3 for _ in range(3)] for _ in range(3)]
    g[0][1][2]=2.0
    assert math.isclose(gradient_energy_density(g,P),0.5*P.eta*4.0)


def test_linear_wave_speeds_and_dispersion():
    cl,ct=linear_wave_speeds(P)
    assert math.isclose(cl*cl,(P.lame_lambda+2*P.mu)/P.rho0)
    assert math.isclose(ct*ct,P.mu/P.rho0)
    k=1.7
    assert math.isclose(
        linear_dispersion_omega_sq(k,"L",P),
        cl*cl*k*k+(P.eta/P.rho0)*k**4,
    )
    assert math.isclose(
        linear_dispersion_omega_sq(k,"T",P),
        ct*ct*k*k+(P.eta/P.rho0)*k**4,
    )


def test_periodic_operator_matches_discrete_fourier_eigenvalue():
    n=128
    dx=0.05
    mode_index=3
    u=tuple(math.sin(2*math.pi*mode_index*j/n) for j in range(n))
    a=periodic_linear_acceleration_1d(u,dx,"T",P)
    q=2*math.pi*mode_index/n
    discrete_k2=4*math.sin(q/2)**2/dx**2
    expected_lambda=-(P.mu/P.rho0)*discrete_k2-(P.eta/P.rho0)*discrete_k2**2
    err=max(abs(a[j]-expected_lambda*u[j]) for j in range(n))
    assert err<1e-10


def test_compatible_second_derivatives_have_zero_curl_f():
    # F=Grad y => partial_K F_iL = partial_K partial_L y_i, symmetric in K,L.
    h=[[[0.0]*3 for _ in range(3)] for _ in range(3)]
    for i in range(3):
        # arbitrary symmetric Hessian for each displacement component
        h[i][0][0]=0.1*(i+1)
        h[i][1][1]=-0.2*(i+1)
        h[i][2][2]=0.05*(i+1)
        h[i][0][1]=h[i][1][0]=0.03
        h[i][0][2]=h[i][2][0]=-0.02
        h[i][1][2]=h[i][2][1]=0.04
    alpha=curl_f_from_grad_f(h)
    assert _frob(alpha)<1e-14
    assert defect_energy_density(h,2.0)<1e-28


def test_incompatible_gradient_has_positive_defect_energy():
    g=[[[0.0]*3 for _ in range(3)] for _ in range(3)]
    # partial_1 F_02 != partial_2 F_01
    g[0][2][1]=0.5
    alpha=curl_f_from_grad_f(g)
    assert abs(alpha[0][0]-0.5)<1e-14
    assert defect_energy_density(g,2.0)>0.0
