from __future__ import annotations

import math

import pytest

from ciel_geometry.phasenav.canon.orbital import (
    ATOMIC_ORBITAL_ADAPTER_STATUS,
    AtomicOrbitalState,
    atomic_poincare_radius,
    atomic_quantum_address,
    cayley_radius_from_ratio,
    centered_dual_coordinate,
    central_phase_address,
    coulomb_phase_address,
    energy_ratio_from_poincare,
    full_spin_orbital_address,
    orbital_inversion,
    period_ratio_from_poincare,
    principal_coordinate_from_poincare,
    quantized_principal_shell,
    radial_ratio_from_poincare,
)


def _phase_delta(a: float, b: float) -> float:
    return ((a - b + math.pi) % (2.0 * math.pi)) - math.pi


def test_cayley_three_anchors_and_roundtrip() -> None:
    assert cayley_radius_from_ratio(0.0) == 0.0
    assert cayley_radius_from_ratio(1.0) == 0.5
    assert cayley_radius_from_ratio(1.0e12) > 1.0 - 1.0e-12

    for x in (0.01, 0.1, 0.5, 1.0, 2.0, 10.0, 100.0):
        rho = cayley_radius_from_ratio(x)
        assert radial_ratio_from_poincare(rho) == pytest.approx(x, rel=1e-12, abs=1e-12)


def test_orbital_inversion_is_involution_and_reverses_centered_coordinate() -> None:
    for rho in (0.01, 0.2, 0.5, 0.8, 0.99):
        for phi in (0.0, 0.3, 1.2, math.pi, 5.7):
            rho_i, phi_i = orbital_inversion(rho, phi)
            rho_ii, phi_ii = orbital_inversion(rho_i, phi_i)
            assert rho_ii == pytest.approx(rho, abs=1e-15)
            assert _phase_delta(phi_ii, phi) == pytest.approx(0.0, abs=1e-15)
            assert centered_dual_coordinate(rho_i) == pytest.approx(
                -centered_dual_coordinate(rho), abs=1e-15
            )


def test_hydrogenic_principal_lattice_roundtrip_and_ratios() -> None:
    for n in range(1, 11):
        rho = atomic_poincare_radius(n)
        assert rho == pytest.approx(n * n / (n * n + 1.0), abs=1e-15)
        assert principal_coordinate_from_poincare(rho) == pytest.approx(float(n), abs=2e-13)
        assert quantized_principal_shell(rho) == n
        assert radial_ratio_from_poincare(rho) == pytest.approx(float(n * n), rel=1e-13)
        assert energy_ratio_from_poincare(rho) == pytest.approx(1.0 / (n * n), rel=1e-13)
        assert period_ratio_from_poincare(rho) == pytest.approx(float(n**3), rel=1e-12)

    assert quantized_principal_shell(0.7) is None


def test_coulomb_address_preserves_l_m_spin_degeneracy() -> None:
    for n in range(1, 6):
        addresses = {
            atomic_quantum_address(n, l, m, spin, mode="coulomb")
            for l in range(n)
            for m in range(-l, l + 1)
            for spin in (-0.5, 0.5)
        }
        assert addresses == {n}
        assert coulomb_phase_address(n) == n


def test_central_address_preserves_m_and_spin_degeneracy() -> None:
    for n in range(1, 6):
        for l in range(n):
            addresses = {
                atomic_quantum_address(n, l, m, spin, mode="central")
                for m in range(-l, l + 1)
                for spin in (-0.5, 0.5)
            }
            assert addresses == {central_phase_address(n, l)}


def test_full_spin_orbital_address_is_contiguous_for_first_four_shells() -> None:
    addresses = []
    for n in range(1, 5):
        for l in range(n):
            for m in range(-l, l + 1):
                for spin in (-0.5, 0.5):
                    addresses.append(full_spin_orbital_address(n, l, m, spin))
    assert sorted(addresses) == list(range(1, 61))


def test_atomic_state_keeps_semantic_mass_separate_from_radial_energy() -> None:
    a = AtomicOrbitalState.from_quantum_numbers(
        3, 1, -1, -0.5, azimuth=0.7, address_mode="coulomb"
    )
    b = AtomicOrbitalState.from_quantum_numbers(
        3, 2, 2, 0.5, azimuth=1.1, address_mode="coulomb"
    )

    # Coulomb symmetry: one PhaseNav numeric state for the whole n=3 multiplet.
    assert a.phase_address == b.phase_address == 3
    assert a.semantic_mass == pytest.approx(b.semantic_mass, abs=1e-15)
    assert a.order_parameter == pytest.approx(b.order_parameter, abs=1e-15)
    assert a.phase36 == b.phase36

    # Orbital labels remain separate from semantic mass.
    assert a.winding == -1
    assert b.winding == 2
    assert a.energy_ratio == pytest.approx(1.0 / 9.0)
    assert b.energy_ratio == pytest.approx(1.0 / 9.0)
    assert a.semantic_mass != pytest.approx(a.energy_ratio)
    assert a.epistemic_status == ATOMIC_ORBITAL_ADAPTER_STATUS


def test_inversion_view_does_not_mutate_canonical_phase_or_semantic_mass() -> None:
    state = AtomicOrbitalState.from_quantum_numbers(
        2, 1, 1, 0.5, azimuth=0.4, address_mode="coulomb"
    )
    phase_before = state.phase36
    mass_before = state.semantic_mass
    winding_before = state.winding

    rho_i, phi_i = state.inverted_coordinate()
    assert rho_i == pytest.approx(1.0 - state.rho_atomic)
    assert _phase_delta(phi_i, -state.azimuth) == pytest.approx(0.0, abs=1e-15)
    assert state.phase36 == phase_before
    assert state.semantic_mass == mass_before
    assert state.winding == winding_before


def test_numeric_phase_order_parameter_is_global_phase_invariant() -> None:
    states = [
        AtomicOrbitalState.from_quantum_numbers(n, 0, 0, 0.5, address_mode="coulomb")
        for n in range(1, 7)
    ]
    reference = states[0].order_parameter
    for state in states[1:]:
        assert state.order_parameter == pytest.approx(reference, abs=2e-12)


def test_invalid_quantum_numbers_are_rejected() -> None:
    with pytest.raises(ValueError):
        AtomicOrbitalState.from_quantum_numbers(0, 0, 0, 0.5)
    with pytest.raises(ValueError):
        AtomicOrbitalState.from_quantum_numbers(2, 2, 0, 0.5)
    with pytest.raises(ValueError):
        AtomicOrbitalState.from_quantum_numbers(2, 1, 2, 0.5)
    with pytest.raises(ValueError):
        AtomicOrbitalState.from_quantum_numbers(2, 1, 0, 0.0)
    with pytest.raises(ValueError):
        atomic_quantum_address(1, 0, 0, 0.5, mode="unknown")
