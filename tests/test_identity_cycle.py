import math

import pytest

from ciel_geometry.phasenav.canon.identity_cycle import (
    CrossDerivation24,
    CycleCoordinate,
    IdentityAxis,
    INFORMATION_PER_PROJECTIVE_CYCLE,
    INFORMATION_QUANTUM,
    KAPPA,
    SIGMA_AXIS,
    TAU,
    cycle_from_phase,
    information_from_projective_cycles,
    information_rate,
    phase_from_cycle,
    phase_information_density,
    projective_cycles_from_information,
    spinor_parity,
    verify_runtime_identity,
    winding_frequency,
)


def test_sigma_is_complement_fixed_axis():
    axis = IdentityAxis()
    assert axis.center == SIGMA_AXIS == 0.5
    assert axis.is_on_axis(0.5)
    assert axis.centered(0.5) == 0.0
    assert axis.complement(0.5) == 0.5
    assert not axis.is_on_axis(0.5001)


def test_normalized_cycle_does_not_require_pi():
    q = CycleCoordinate(3.25)
    assert q.projective == pytest.approx(0.25)
    assert q.spinor == pytest.approx(1.25)
    assert winding_frequency(9.0, 3.0) == 3.0


def test_phase_projection_round_trip():
    q = 7.25
    phi = phase_from_cycle(q)
    assert phi == pytest.approx(q * TAU)
    assert cycle_from_phase(phi) == pytest.approx(q)


def test_information_cycle_closes_at_twelve_projective_cycles():
    assert information_from_projective_cycles(12.0) == pytest.approx(
        INFORMATION_QUANTUM
    )
    assert projective_cycles_from_information(INFORMATION_QUANTUM) == pytest.approx(
        12.0
    )
    assert INFORMATION_PER_PROJECTIVE_CYCLE == pytest.approx(math.log(2.0) / 12.0)


def test_information_rate_is_cycle_rate_not_angular_rate():
    f = 7.83
    assert information_rate(f) == pytest.approx((math.log(2.0) / 12.0) * f)


def test_spinor_double_cover_parity():
    assert spinor_parity(0) == 1
    assert spinor_parity(1) == -1
    assert spinor_parity(2) == 1


def test_cross_derivation_24_is_exact():
    proof = CrossDerivation24()
    assert proof.mix_flavour_units == 8 * 3 == 24
    assert proof.projective_units == 12 * 2 == 24
    assert proof.spinor_units == 6 * 4 == 24
    assert proof.common_units == 24
    assert proof.phase_closure == pytest.approx(24.0 * math.pi)


def test_cross_derivation_reproduces_kappa():
    proof = CrossDerivation24()
    assert proof.kappa == pytest.approx(KAPPA, abs=1e-15)
    assert phase_information_density() == pytest.approx(KAPPA, abs=1e-15)
    assert verify_runtime_identity()


def test_invalid_time_and_closure_are_rejected():
    with pytest.raises(ValueError):
        winding_frequency(1.0, 0.0)
    with pytest.raises(ValueError):
        phase_from_cycle(1.0, closure=0.0)
    with pytest.raises(ValueError):
        cycle_from_phase(1.0, closure=-1.0)
