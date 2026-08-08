import math

from ciel_geometry.phasenav.canon import (
    KAPPA,
    ContextAnchor,
    ContextPotential,
    PhaseVector36,
    TangentVector36,
    find_attractors,
    trace_orbit,
)


def _vector(value: float) -> PhaseVector36:
    return PhaseVector36((value,) * 36)


def _anchor(name: str, value: float, weight: float = 1.0) -> ContextAnchor:
    return ContextAnchor(
        anchor_id=name,
        vector=_vector(value),
        weight=weight,
        semantic_mass=0.02,
    )


def test_single_anchor_is_exact_context_attractor():
    context = ContextPotential((_anchor("core", 0.25),))
    sample = context.sample(_vector(0.25))
    assert math.isclose(sample.density, 1.0, abs_tol=1e-15)
    assert math.isclose(sample.potential, 0.0, abs_tol=1e-15)
    assert math.isclose(sample.viscosity, 2.0 * KAPPA, abs_tol=1e-15)
    assert sample.gradient.norm == 0.0
    attractors = find_attractors(context)
    assert len(attractors) == 1
    assert attractors[0].support_ids == ("core",)
    assert attractors[0].vector.angular_distance(_vector(0.25)) < 1e-12


def test_context_gradient_matches_finite_difference():
    context = ContextPotential(
        (
            _anchor("left", 0.2, 1.0),
            _anchor("right", 0.8, 2.0),
        )
    )
    point = PhaseVector36((0.45,) + (0.5,) * 35)
    sample = context.sample(point)
    eps = 1e-6
    plus = PhaseVector36((0.45 + eps,) + (0.5,) * 35)
    minus = PhaseVector36((0.45 - eps,) + (0.5,) * 35)
    numerical = (
        context.sample(plus).potential
        - context.sample(minus).potential
    ) / (2.0 * eps)
    assert math.isclose(
        sample.gradient.components[0],
        numerical,
        rel_tol=2e-6,
        abs_tol=1e-10,
    )


def test_density_and_viscosity_are_positive_context_observables():
    context = ContextPotential(
        (
            _anchor("a", 0.0),
            _anchor("b", 1.0),
            _anchor("c", 2.0),
        )
    )
    for point in (_vector(0.0), _vector(1.0), _vector(math.pi)):
        sample = context.sample(point)
        assert 0.0 < sample.density <= 1.0
        assert sample.potential >= 0.0
        assert sample.viscosity >= KAPPA
        assert sample.local_variance >= 0.0
        assert all(
            math.isclose(force, -gradient, abs_tol=1e-15)
            for force, gradient in zip(
                sample.force.components,
                sample.gradient.components,
            )
        )


def test_mean_shift_resolves_two_context_attractors():
    context = ContextPotential(
        (
            _anchor("a0", 0.00),
            _anchor("a1", 0.04),
            _anchor("b0", math.pi),
            _anchor("b1", math.pi + 0.04),
        ),
        bandwidth=0.20,
    )
    attractors = find_attractors(context, merge_radius=0.10)
    assert len(attractors) == 2
    assert sorted(len(attractor.support_ids) for attractor in attractors) == [2, 2]
    assert all(attractor.gradient_norm < 1e-8 for attractor in attractors)


def test_damped_orbit_falls_into_single_context_basin():
    attractor_vector = _vector(0.2)
    context = ContextPotential(
        (
            ContextAnchor("core", attractor_vector, 1.0, 0.02),
        )
    )
    initial = _vector(1.2)
    initial_distance = initial.angular_distance(attractor_vector)
    attractors = find_attractors(context)
    trace = trace_orbit(
        context,
        initial,
        semantic_mass=0.02,
        initial_velocity=TangentVector36.zero(),
        dt=1.0,
        max_steps=1024,
        tolerance=1e-5,
        attractors=attractors,
    )
    final = trace.steps[-1]
    assert (
        final.position.angular_distance(attractor_vector)
        < initial_distance * 0.01
    )
    assert final.total_energy < trace.steps[0].total_energy
    assert trace.converged
    assert trace.terminal_attractor == "A000"


def test_context_digest_and_orbit_receipt_are_deterministic():
    anchor_x = _anchor("x", 0.1)
    anchor_y = _anchor("y", 0.7)
    context = ContextPotential((anchor_x, anchor_y))
    reversed_context = ContextPotential((anchor_y, anchor_x))
    assert context.digest_sha256 == reversed_context.digest_sha256
    first = trace_orbit(
        context,
        _vector(0.4),
        semantic_mass=0.03,
        max_steps=3,
    )
    second = trace_orbit(
        reversed_context,
        _vector(0.4),
        semantic_mass=0.03,
        max_steps=3,
    )
    assert first.to_dict() == second.to_dict()
