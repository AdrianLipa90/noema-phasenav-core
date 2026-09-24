from __future__ import annotations

import math

import pytest

from ciel_geometry.phasenav.canon.spectroscopic_holonomy import (
    SpectroscopicHolonomyState,
    central_difference_jacobian,
    cycle_rank,
    fisher_information_diagonal_noise,
    phase_vibronic_linearization,
    relative_path_holonomy,
    ring_energy_levels,
    u1_transport,
)


def test_cycle_rank_counts_only_independent_graph_cycles() -> None:
    assert cycle_rank(4, 3) == 0
    assert cycle_rank(6, 6) == 1
    assert cycle_rank(4, 5) == 2


def test_tree_has_no_independent_u1_cycle_phase() -> None:
    state = SpectroscopicHolonomyState.build(
        vertex_count=4,
        edge_count=3,
        cycle_edge_potentials=(),
    )
    assert state.beta_1 == 0
    assert state.cycle_phases == ()

    with pytest.raises(ValueError):
        SpectroscopicHolonomyState.build(
            vertex_count=4,
            edge_count=3,
            cycle_edge_potentials=((0.2,),),
        )


def test_single_ring_has_exactly_one_holonomy_coordinate() -> None:
    state = SpectroscopicHolonomyState.build(
        vertex_count=6,
        edge_count=6,
        cycle_edge_potentials=((0.20, 0.35, -0.15),),
    )
    assert state.beta_1 == 1
    assert len(state.cycle_holonomies) == 1
    assert abs(abs(state.cycle_holonomies[0]) - 1.0) < 1.0e-12
    assert abs(state.cycle_phases[0] - 0.40) < 1.0e-12
    assert state.epistemic == "CHYBA"
    assert state.canon_allowed is False
    assert state.physical_gauge_field_claimed is False

    packet = state.to_packet()
    assert packet["schema"] == "PHASENAV_SPECTROSCOPIC_HOLONOMY_STATE_V0_1"
    assert packet["graph"]["beta_1"] == 1
    assert packet["claims"]["computational_graph_holonomy"] is True
    assert packet["claims"]["physical_gauge_field"] is False
    assert abs(packet["cycle_holonomies"][0]["modulus"] - 1.0) < 1.0e-12


def test_relative_same_endpoint_paths_reduce_to_closed_loop_holonomy() -> None:
    first = (0.20, 0.40)
    second = (-0.10, 0.30)
    relative = relative_path_holonomy(first, second)
    closed_loop = u1_transport(first + tuple(-x for x in reversed(second)))
    assert abs(relative - closed_loop) < 1.0e-12


def test_ring_spectrum_is_two_pi_periodic_as_an_unlabelled_spectrum() -> None:
    base = sorted(ring_energy_levels(6, onsite_energy=-0.3, hopping=1.7, holonomy_phase=0.41))
    shifted = sorted(
        ring_energy_levels(
            6,
            onsite_energy=-0.3,
            hopping=1.7,
            holonomy_phase=0.41 + 2.0 * math.pi,
        )
    )
    assert len(base) == len(shifted) == 6
    assert max(abs(a - b) for a, b in zip(base, shifted)) < 1.0e-12


def test_phase_vibronic_linearization_is_explicit_and_dimension_checked() -> None:
    value = phase_vibronic_linearization(
        0.25,
        gradient=(0.5, -0.2),
        normal_coordinates=(0.4, 0.1),
    )
    assert abs(value - 0.43) < 1.0e-12

    with pytest.raises(ValueError):
        phase_vibronic_linearization(0.0, gradient=(1.0,), normal_coordinates=(1.0, 2.0))


def test_spectroscopic_jacobian_and_fisher_information() -> None:
    def observable(phases: tuple[float, ...]) -> tuple[float, float]:
        return (math.sin(phases[0]), phases[0] + phases[1] ** 2)

    jac = central_difference_jacobian(observable, (0.3, 0.4), step=1.0e-6)
    assert len(jac) == 2
    assert len(jac[0]) == 2
    assert abs(jac[0][0] - math.cos(0.3)) < 1.0e-8
    assert abs(jac[0][1]) < 1.0e-8
    assert abs(jac[1][0] - 1.0) < 1.0e-8
    assert abs(jac[1][1] - 0.8) < 1.0e-8

    fisher = fisher_information_diagonal_noise(jac, variances=(1.0, 4.0))
    assert abs(fisher[0][0] - (math.cos(0.3) ** 2 + 0.25)) < 1.0e-7
    assert abs(fisher[0][1] - 0.20) < 1.0e-7
    assert abs(fisher[1][0] - 0.20) < 1.0e-7
    assert abs(fisher[1][1] - 0.16) < 1.0e-7
