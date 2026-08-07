import math

import pytest

from ciel_geometry.phasenav.canon.identity_cycle import (
    CROSS_DERIVATION_STATUS,
    CrossDerivation24,
    CycleCoordinate,
    IdentityAxis,
    INFORMATION_PER_PROJECTIVE_CYCLE,
    INFORMATION_QUANTUM,
    KAPPA,
    SIGMA_AXIS,
    TAU,
    cycle_from_phase,
    identity_cycle_claims,
    information_from_projective_cycles,
    information_rate,
    phase_from_cycle,
    phase_information_density,
    projective_cycles_from_information,
    spinor_parity,
    spinor_rotation_phase,
    verify_runtime_identity,
    winding_frequency,
)


def test_sigma_is_unique_complement_fixed_axis():
    axis = IdentityAxis()
    assert axis.center == SIGMA_AXIS == 0.5
    assert axis.is_on_axis(0.5)
    assert axis.centered(0.5) == 0.0
    assert axis.complement(0.5) == 0.5
    assert not axis.is_on_axis(0.5001)
    with pytest.raises(ValueError):
        IdentityAxis(center=0.4)


def test_normalized_cycle_does_not_require_pi():
    q = CycleCoordinate(3.25)
    assert q.projective == pytest.approx(0.25)
    assert q.spinor == pytest.approx(1.25)
    assert winding_frequency(9.0, 3.0) == 3.0


def test_cycle_reversal_has_symmetric_completed_count():
    assert CycleCoordinate(0.9).completed_projective_cycles == 0
    assert CycleCoordinate(-0.9).completed_projective_cycles == 0
    assert CycleCoordinate(1.2).completed_projective_cycles == 1
    assert CycleCoordinate(-1.2).completed_projective_cycles == -1
    assert CycleCoordinate(-0.2).projective_cell == -1
    with pytest.raises(ValueError):
        CycleCoordinate(math.inf)


def test_phase_projection_round_trip():
    q = 7.25
    phi = phase_from_cycle(q)
    assert phi == pytest.approx(q * TAU)
    assert cycle_from_phase(phi) == pytest.approx(q)


def test_information_cycle_closes_at_twelve_projective_cycles_in_model():
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


def test_spinor_double_cover_parity_and_rotation_phase():
    assert spinor_parity(0) == 1
    assert spinor_parity(1) == -1
    assert spinor_parity(2) == 1
    assert spinor_rotation_phase(0) == pytest.approx(0.0)
    assert spinor_rotation_phase(1) == pytest.approx(math.pi)
    assert spinor_rotation_phase(2) == pytest.approx(0.0)
    with pytest.raises(TypeError):
        spinor_rotation_phase(1.5)


def test_cross_factorisation_24_is_exact_but_model_dependent():
    proof = CrossDerivation24()
    assert proof.mix_flavour_units == 8 * 3 == 24
    assert proof.projective_units == 12 * 2 == 24
    assert proof.spinor_units == 6 * 4 == 24
    assert proof.common_units == 24
    assert proof.information_phase_span_rad == pytest.approx(24.0 * math.pi)
    assert proof.phase_closure == pytest.approx(proof.information_phase_span_rad)
    assert proof.status == CROSS_DERIVATION_STATUS


def test_cross_factorisation_reproduces_runtime_kappa_without_claiming_independence():
    proof = CrossDerivation24()
    assert proof.kappa_candidate == pytest.approx(KAPPA, abs=1e-15)
    assert proof.kappa == pytest.approx(KAPPA, abs=1e-15)
    assert phase_information_density() == pytest.approx(KAPPA, abs=1e-15)
    assert verify_runtime_identity()
    claims = identity_cycle_claims()
    assert "independent derivation of the integer 12" in claims["open"]
    assert "the complete branch uses 8 mixes and 3 flavours" in claims["model"]


def test_invalid_time_closure_and_nonfinite_values_are_rejected():
    with pytest.raises(ValueError):
        winding_frequency(1.0, 0.0)
    with pytest.raises(ValueError):
        phase_from_cycle(1.0, closure=0.0)
    with pytest.raises(ValueError):
        cycle_from_phase(1.0, closure=-1.0)
    with pytest.raises(ValueError):
        phase_from_cycle(math.inf)
    with pytest.raises(ValueError):
        cycle_from_phase(math.nan)
    with pytest.raises(ValueError):
        information_from_projective_cycles(math.inf)
    with pytest.raises(ValueError):
        projective_cycles_from_information(math.nan)
