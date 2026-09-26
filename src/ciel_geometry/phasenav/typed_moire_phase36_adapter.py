"""Fail-closed adapter from a typed T^36 Moire phase basis to Bivector36 SO(2).

This module does NOT reinterpret the generic legacy PhaseNav basis
PNV_T36_PHASE_ANGLES_RADIANS_V1. The generic basis has no canonical axis
semantics, so direct physical conversion is rejected.

The admitted source basis is a separate typed carrier:
PNV_MOIRE_RELATIVE_PHASE_MATRIX6_ROW_MAJOR_V1

Its 36 angles are the row-major wrapped coefficients of a 6x6 Lie-generator
matrix on Lambda^2(R^4).
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .orbital_rotation36 import (
    calibrated_twist_residual36,
    generator36_xy,
    moire_period_from_rotation36,
    rotation36_xy,
)

TAU = 2.0 * math.pi
DIM = 36
GENERIC_T36_BASIS_ID = "PNV_T36_PHASE_ANGLES_RADIANS_V1"
MOIRE_PHASE_MATRIX6_BASIS_ID = "PNV_MOIRE_RELATIVE_PHASE_MATRIX6_ROW_MAJOR_V1"
BIVECTOR36_BASIS_ID = "PNV_BIVECTOR_OPERATOR36_LAMBDA2_R4_PAIRBASIS_V1"
ADAPTER_ID = "PNV_TYPED_MOIRE_PHASE36_TO_BIVECTOR36_SO2_V1"


class Phase36AdapterError(ValueError):
    pass


def _wrap(theta: float) -> float:
    if not math.isfinite(theta):
        raise Phase36AdapterError("phase must be finite")
    return (float(theta) + math.pi) % TAU - math.pi


def _matrix6_from_flat(values: Sequence[float]) -> tuple[tuple[float, ...], ...]:
    if len(values) != DIM:
        raise Phase36AdapterError("expected exactly 36 values")
    vals = tuple(float(x) for x in values)
    if not all(math.isfinite(x) for x in vals):
        raise Phase36AdapterError("all values must be finite")
    return tuple(tuple(vals[6 * r + c] for c in range(6)) for r in range(6))


def _frob(matrix6: Sequence[Sequence[float]]) -> float:
    return math.sqrt(math.fsum(float(x) * float(x) for row in matrix6 for x in row))


@dataclass(frozen=True)
class Phase36Record:
    angles: tuple[float, ...]
    basis_id: str
    derivation_id: str
    source_id: str

    def __post_init__(self) -> None:
        if len(self.angles) != DIM:
            raise Phase36AdapterError("Phase36Record requires exactly 36 angles")
        vals = tuple(float(x) for x in self.angles)
        if not all(math.isfinite(x) for x in vals):
            raise Phase36AdapterError("Phase36Record angles must be finite")
        if not all(0.0 <= x < TAU for x in vals):
            raise Phase36AdapterError("Phase36Record angles must lie in [0,2pi)")
        if not self.basis_id or not self.derivation_id or not self.source_id:
            raise Phase36AdapterError("basis_id, derivation_id and source_id are required")
        object.__setattr__(self, "angles", vals)


@dataclass(frozen=True)
class Bivector36SO2Binding:
    adapter_id: str
    source_basis_id: str
    target_basis_id: str
    reference_source_id: str
    target_source_id: str
    theta_radians: float
    generator_fit_abs: float
    generator_fit_rel: float
    operator6: tuple[tuple[float, ...], ...]
    calibrated_residual: float
    admitted: bool


def encode_so2_log_phase36(
    theta_radians: float,
    *,
    source_id: str,
    derivation_id: str = "PNV_BIVECTOR36_SO2_FORWARD_LOG_PHASE_V1",
    branch_cut_margin: float = 1e-9,
) -> Phase36Record:
    """Encode theta*J_36 as wrapped row-major phase coordinates.

    This is a typed forward model, not a conversion of a generic legacy T36 vector.
    """
    theta = float(theta_radians)
    if not math.isfinite(theta):
        raise Phase36AdapterError("theta must be finite")
    if abs(theta) >= math.pi - branch_cut_margin:
        raise Phase36AdapterError("theta is too close to the principal phase branch cut")
    j = generator36_xy()
    angles = tuple((theta * j[r][c]) % TAU for r in range(6) for c in range(6))
    return Phase36Record(
        angles=angles,
        basis_id=MOIRE_PHASE_MATRIX6_BASIS_ID,
        derivation_id=derivation_id,
        source_id=source_id,
    )


def relative_log_matrix36(
    reference: Phase36Record,
    target: Phase36Record,
) -> tuple[tuple[float, ...], ...]:
    """Recover the principal relative Lie-coordinate matrix.

    Generic legacy T36 is rejected because its axis semantics are unassigned.
    """
    for record in (reference, target):
        if record.basis_id == GENERIC_T36_BASIS_ID:
            raise Phase36AdapterError(
                "generic PNV_T36_PHASE_ANGLES_RADIANS_V1 has unassigned axis "
                "semantics and cannot be reinterpreted as a physical bivector basis"
            )
        if record.basis_id != MOIRE_PHASE_MATRIX6_BASIS_ID:
            raise Phase36AdapterError(
                f"unsupported source basis {record.basis_id!r}; expected "
                f"{MOIRE_PHASE_MATRIX6_BASIS_ID}"
            )
    delta = tuple(_wrap(b - a) for a, b in zip(reference.angles, target.angles))
    return _matrix6_from_flat(delta)


def fit_xy_so2_generator(
    generator_matrix6: Sequence[Sequence[float]],
) -> tuple[float, float, float]:
    """Project a typed 6x6 log generator onto the calibrated J_36 axis."""
    x = _matrix6_from_flat(tuple(float(v) for row in generator_matrix6 for v in row))
    j = generator36_xy()
    den = math.fsum(j[r][c] * j[r][c] for r in range(6) for c in range(6))
    theta = math.fsum(x[r][c] * j[r][c] for r in range(6) for c in range(6)) / den
    residual = tuple(
        tuple(x[r][c] - theta * j[r][c] for c in range(6))
        for r in range(6)
    )
    abs_err = _frob(residual)
    scale = max(_frob(x), abs(theta) * math.sqrt(den), 1e-300)
    rel_err = abs_err / scale
    return theta, abs_err, rel_err


def adapt_typed_phase36_to_bivector36_so2(
    reference: Phase36Record,
    target: Phase36Record,
    *,
    fit_tolerance: float = 1e-10,
    branch_cut_margin: float = 1e-9,
) -> Bivector36SO2Binding:
    """Admit only records lying on the typed principal SO(2) log-generator axis."""
    if fit_tolerance < 0.0 or not math.isfinite(fit_tolerance):
        raise Phase36AdapterError("fit_tolerance must be finite and non-negative")
    x = relative_log_matrix36(reference, target)
    theta, abs_err, rel_err = fit_xy_so2_generator(x)
    if abs(theta) >= math.pi - branch_cut_margin:
        raise Phase36AdapterError("recovered theta is too close to the principal branch cut")
    if abs_err > fit_tolerance:
        raise Phase36AdapterError(
            f"typed phase matrix is off the calibrated SO(2) generator axis: "
            f"abs residual {abs_err:.17g} > tolerance {fit_tolerance:.17g}"
        )
    op = rotation36_xy(theta)
    return Bivector36SO2Binding(
        adapter_id=ADAPTER_ID,
        source_basis_id=MOIRE_PHASE_MATRIX6_BASIS_ID,
        target_basis_id=BIVECTOR36_BASIS_ID,
        reference_source_id=reference.source_id,
        target_source_id=target.source_id,
        theta_radians=theta,
        generator_fit_abs=abs_err,
        generator_fit_rel=rel_err,
        operator6=op,
        calibrated_residual=calibrated_twist_residual36(op),
        admitted=True,
    )


def physical_moire_period(
    binding: Bivector36SO2Binding,
    lattice_constant: float,
) -> float:
    if not binding.admitted:
        raise Phase36AdapterError("binding is not admitted")
    return moire_period_from_rotation36(lattice_constant, binding.operator6)
