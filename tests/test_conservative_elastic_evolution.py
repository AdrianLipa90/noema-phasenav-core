import math
import pytest

from ciel_geometry.phasenav.conservative_elastic_evolution import (
    PeriodicElasticState1D,
    energy_ledger,
    evolve_verlet,
    periodic_acceleration,
    verlet_stability_limit,
    verlet_step,
)
from ciel_geometry.phasenav.hyperelastic_field36 import (
    HyperelasticFieldError,
    HyperelasticParameters,
)


P=HyperelasticParameters(rho0=2.5,mu=3.0,lame_lambda=4.0,eta=0.7)


def test_constant_displacement_is_exact_zero_mode():
    s=PeriodicElasticState1D((2.0,)*32,(0.0,)*32,0.0)
    assert max(abs(x) for x in periodic_acceleration(s.displacement,0.1,"T",P))==0.0
    e=energy_ledger(s,0.1,"T",P)
    assert e.total==0.0


def test_constant_velocity_preserves_momentum_and_uniform_motion():
    n=32;dx=0.1
    s=PeriodicElasticState1D((0.0,)*n,(0.3,)*n,0.0)
    dt=0.1*verlet_stability_limit(dx,"T",P)
    s1=verlet_step(s,dt,dx,"T",P)
    assert max(abs(v-0.3) for v in s1.velocity)<1e-14
    assert max(abs(u-0.3*dt) for u in s1.displacement)<1e-14
    assert math.isclose(
        energy_ledger(s,dx,"T",P).momentum,
        energy_ledger(s1,dx,"T",P).momentum,
        rel_tol=1e-14,
    )


def test_fourier_mode_discrete_eigenvalue():
    n=128;dx=0.05;m=3
    u=tuple(math.sin(2*math.pi*m*j/n) for j in range(n))
    a=periodic_acceleration(u,dx,"T",P)
    q=2*math.pi*m/n
    k2=4*math.sin(q/2)**2/dx**2
    eig=-(P.mu/P.rho0)*k2-(P.eta/P.rho0)*k2*k2
    max_err=max(abs(a[j]-eig*u[j]) for j in range(n))
    # D4/dx^4 amplifies float64 cancellation; use a scale-aware roundoff gate.
    assert max_err < 5e-11*max(1.0,abs(eig))


def test_energy_ledger_is_nonnegative():
    n=64;dx=0.1
    u=tuple(0.01*math.sin(2*math.pi*j/n) for j in range(n))
    v=tuple(0.02*math.cos(4*math.pi*j/n) for j in range(n))
    e=energy_ledger(PeriodicElasticState1D(u,v,0.0),dx,"L",P)
    assert e.kinetic>=0.0 and e.elastic>=0.0 and e.gradient>=0.0 and e.total>=0.0


def test_verlet_long_run_energy_bounded():
    n=128;dx=0.05;m=3
    u=tuple(0.01*math.sin(2*math.pi*m*j/n) for j in range(n))
    s=PeriodicElasticState1D(u,(0.0,)*n,0.0)
    dt=0.2*verlet_stability_limit(dx,"T",P)
    _,ledger=evolve_verlet(s,5000,dt,dx,"T",P)
    e0=ledger[0].total
    max_rel=max(abs(e.total-e0)/e0 for e in ledger)
    assert max_rel<2.0e-6


def test_verlet_long_run_momentum_conserved():
    n=128;dx=0.05
    u=tuple(0.01*math.sin(6*math.pi*j/n) for j in range(n))
    v=tuple(0.02+0.005*math.cos(4*math.pi*j/n) for j in range(n))
    s=PeriodicElasticState1D(u,v,0.0)
    dt=0.2*verlet_stability_limit(dx,"L",P)
    _,ledger=evolve_verlet(s,2000,dt,dx,"L",P)
    p0=ledger[0].momentum
    assert max(abs(e.momentum-p0) for e in ledger)<1e-11


def test_stability_guard_fails_closed():
    s=PeriodicElasticState1D((0.0,)*16,(0.0,)*16,0.0)
    dt=verlet_stability_limit(0.1,"T",P)
    with pytest.raises(HyperelasticFieldError,match="stability"):
        verlet_step(s,dt,0.1,"T",P)
