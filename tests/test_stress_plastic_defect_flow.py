import math

from ciel_geometry.phasenav.stress_plastic_defect_flow import (
    PlasticFlowParameters,
    curl_plastic_distortion_from_grad_beta,
    dissipation_rate,
    equilibrium_plastic_distortion,
    exact_plastic_relaxation_step,
    plastic_driving_force,
    plastic_free_energy_density,
    skew,
    small_strain_stress,
)


P=PlasticFlowParameters(mu=3.0,lame_lambda=4.0,hardening=1.5,mobility=0.7)


def _frob(a):
    return math.sqrt(sum(x*x for row in a for x in row))


def _sub(a,b):
    return tuple(tuple(a[i][j]-b[i][j] for j in range(3)) for i in range(3))


def test_equilibrium_has_zero_driving_force():
    g=((0.12,0.03,-0.02),(0.01,-0.05,0.04),(0.02,0.00,0.08))
    beq=equilibrium_plastic_distortion(g,P)
    assert _frob(plastic_driving_force(g,beq,P))<1e-13


def test_exact_relaxation_monotonically_decreases_energy():
    g=((0.12,0.03,-0.02),(0.01,-0.05,0.04),(0.02,0.00,0.08))
    b=((0.20,-0.10,0.04),(0.03,0.05,-0.02),(-0.07,0.01,0.09))
    energies=[plastic_free_energy_density(g,b,P)]
    for dt in (0.01,0.1,1.0,10.0):
        b1=exact_plastic_relaxation_step(g,b,dt,P)
        energies.append(plastic_free_energy_density(g,b1,P))
    assert all(e<=energies[0]+1e-14 for e in energies[1:])


def test_semigroup_property_of_exact_step():
    g=((0.12,0.03,-0.02),(0.01,-0.05,0.04),(0.02,0.00,0.08))
    b=((0.20,-0.10,0.04),(0.03,0.05,-0.02),(-0.07,0.01,0.09))
    one=exact_plastic_relaxation_step(g,b,0.7,P)
    two=exact_plastic_relaxation_step(g,exact_plastic_relaxation_step(g,b,0.2,P),0.5,P)
    assert _frob(_sub(one,two))<1e-13


def test_instantaneous_energy_derivative_matches_minus_dissipation():
    g=((0.12,0.03,-0.02),(0.01,-0.05,0.04),(0.02,0.00,0.08))
    b=((0.20,-0.10,0.04),(0.03,0.05,-0.02),(-0.07,0.01,0.09))
    e0=plastic_free_energy_density(g,b,P)
    rate=dissipation_rate(g,b,P)
    dt=1e-7
    b1=exact_plastic_relaxation_step(g,b,dt,P)
    numerical=(plastic_free_energy_density(g,b1,P)-e0)/dt
    assert math.isclose(numerical,-rate,rel_tol=2e-6,abs_tol=2e-8)


def test_rigid_infinitesimal_rotation_has_zero_stress():
    g=((0.0,-0.2,0.1),(0.2,0.0,-0.05),(-0.1,0.05,0.0))
    zero=((0.0,0.0,0.0),)*3
    assert _frob(small_strain_stress(g,zero,P))<1e-14


def test_skew_plastic_distortion_does_not_enter_stress_but_hardening_relaxes_it():
    g=((0.1,0,0),(0,-0.05,0),(0,0,0.02))
    b=((0.0,-0.3,0.1),(0.3,0.0,-0.2),(-0.1,0.2,0.0))
    zero=((0.0,0.0,0.0),)*3
    assert _frob(_sub(small_strain_stress(g,b,P),small_strain_stress(g,zero,P)))<1e-14
    b1=exact_plastic_relaxation_step(g,b,1.0,P)
    assert _frob(skew(b1))<_frob(skew(b))


def test_zero_hardening_relaxes_symmetric_stress_to_zero_and_preserves_skew():
    p=PlasticFlowParameters(mu=3.0,lame_lambda=4.0,hardening=0.0,mobility=0.7)
    g=((0.1,0.02,0),(0.00,-0.05,0),(0,0,0.02))
    b=((0.0,-0.3,0.1),(0.3,0.0,-0.2),(-0.1,0.2,0.0))
    b1=exact_plastic_relaxation_step(g,b,100.0,p)
    assert _frob(small_strain_stress(g,b1,p))<1e-12
    assert _frob(_sub(skew(b1),skew(b)))<1e-14


def test_curl_plastic_distortion_zero_for_gradient_field():
    h=[[[0.0]*3 for _ in range(3)] for _ in range(3)]
    for i in range(3):
        h[i][0][1]=h[i][1][0]=0.03
        h[i][0][2]=h[i][2][0]=-0.02
        h[i][1][2]=h[i][2][1]=0.04
    assert _frob(curl_plastic_distortion_from_grad_beta(h))<1e-14
