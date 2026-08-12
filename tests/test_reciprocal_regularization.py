from __future__ import annotations

import math

import pytest

from ciel_geometry.phasenav.canon.reciprocal_regularization import (
    ReciprocalRegion,
    compactified_reciprocal_coordinates,
    concept_algorithm_registry,
    division_with_concept_guard,
    heisenberg_soft_reciprocal,
    heisenberg_uncertainty_floor,
    resolve_reciprocal,
    riemann_zeta_zero_regularization,
)


def test_zeta_zero_exact_analytic_continuation_value() -> None:
    assert riemann_zeta_zero_regularization() == complex(-0.5, 0.0)


def test_compactified_reciprocal_duality() -> None:
    for value in (0.0, 0.25, 1.0, 4.0, 100.0):
        source, reciprocal = compactified_reciprocal_coordinates(value)
        assert source + reciprocal == pytest.approx(1.0, abs=1e-15)
    source_zero, reciprocal_zero = compactified_reciprocal_coordinates(0.0)
    assert source_zero == 0.0
    assert reciprocal_zero == 1.0


def test_exact_zero_uses_zeta_before_boundary_soft_clip() -> None:
    result = resolve_reciprocal(0.0, delta_z=0.1, delta_k=5.0)
    assert result.region is ReciprocalRegion.ZERO_CENTER_ZETA
    assert result.value == complex(-0.5, 0.0)
    assert result.source_rho == 0.0
    assert result.reciprocal_rho == 1.0
    assert result.uncertainty_floor is None


def test_guarded_division_at_zero_is_tagged_project_continuation() -> None:
    result = division_with_concept_guard(8.0, 0.0)
    assert result.region is ReciprocalRegion.ZERO_CENTER_ZETA
    assert result.value == complex(-4.0, 0.0)
    receipt = result.receipt()
    assert receipt["ordinary_division_by_zero_identity_claimed"] is False
    assert receipt["zeta_zero_value_is_standard_analytic_continuation"] is True


def test_interior_uses_exact_reciprocal() -> None:
    result = resolve_reciprocal(2.0)
    assert result.region is ReciprocalRegion.INTERIOR_RECIPROCAL
    assert result.value == complex(0.5, 0.0)


def test_heisenberg_boundary_soft_reciprocal_is_finite() -> None:
    result = resolve_reciprocal(0.05, delta_z=0.1, delta_k=5.0)
    assert result.region is ReciprocalRegion.HEISENBERG_BOUNDARY
    assert math.isfinite(result.value.real)
    assert math.isfinite(result.value.imag)
    assert result.value.real == pytest.approx(4.0)
    assert result.reciprocal_rho > 0.9


def test_soft_reciprocal_matches_declared_formula() -> None:
    value = heisenberg_soft_reciprocal(0.05 + 0.02j, delta_z=0.1, delta_k=5.0)
    expected = (0.05 - 0.02j) / ((0.05**2 + 0.02**2) + 0.1**2)
    assert value == pytest.approx(expected)


def test_nan_requires_reference_and_uses_heisenberg_soft_clip() -> None:
    with pytest.raises(ValueError, match="finite_reference"):
        resolve_reciprocal(float("nan"), delta_z=0.1, delta_k=5.0)

    result = resolve_reciprocal(
        float("nan"),
        finite_reference=0.05,
        delta_z=0.1,
        delta_k=5.0,
    )
    assert result.region is ReciprocalRegion.NAN_HEISENBERG
    assert result.value.real == pytest.approx(4.0)
    assert math.isfinite(result.value.real)


def test_uncertainty_contract_is_fail_closed() -> None:
    assert heisenberg_uncertainty_floor(0.1, 5.0) == pytest.approx(0.1)
    with pytest.raises(ValueError, match="violates"):
        heisenberg_uncertainty_floor(0.1, 4.0)


def test_uncertainty_pair_must_be_complete() -> None:
    with pytest.raises(ValueError, match="supplied together"):
        resolve_reciprocal(1.0, delta_z=0.1)


def test_receipt_is_deterministic() -> None:
    left = resolve_reciprocal(0.05, delta_z=0.1, delta_k=5.0).receipt()
    right = resolve_reciprocal(0.05, delta_z=0.1, delta_k=5.0).receipt()
    assert left["receipt_sha256"] == right["receipt_sha256"]


def test_concept_algorithm_registry_has_all_three_bindings() -> None:
    registry = concept_algorithm_registry()
    assert set(registry) == {
        "RECIPROCAL_INVERSION",
        "RIEMANN_ZETA_ZERO",
        "HEISENBERG_UNCERTAINTY",
    }
    assert registry["RIEMANN_ZETA_ZERO"]["ordinary_division_identity"] is False
