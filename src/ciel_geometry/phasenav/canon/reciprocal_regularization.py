"""Reciprocal compactification with concept-bound zero and boundary regularization.

This module makes three PhaseNav concepts executable as one typed algorithmic
chain without changing the underlying mathematical claim ledger:

* ``RECIPROCAL_INVERSION`` — the existing Cayley/Poincare reciprocal geometry;
* ``RIEMANN_ZETA_ZERO`` — exact analytic-continuation value ``zeta(0)=-1/2``
  used as a *project regularization convention* at an exact zero denominator;
* ``HEISENBERG_UNCERTAINTY`` — a finite soft reciprocal inside the declared
  uncertainty neighbourhood of the reciprocal boundary, and for NaN only when
  a finite reference state is supplied.

The statement ``a/0 = a*zeta(0)`` is NOT asserted as ordinary arithmetic.  The
zeta branch is an explicitly tagged PhaseNav continuation rule.  Likewise, the
Heisenberg branch is a numerical/semantic regularizer whose uncertainty inputs
must satisfy the declared normalized uncertainty inequality.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Mapping

from .orbital import cayley_radius_from_ratio


RECIPROCAL_REGULARIZATION_VERSION = "0.12.0"
RECIPROCAL_REGULARIZATION_STATUS = (
    "PROJECT_CONCEPT_ALGORITHM_CANDIDATE_NO_SCIENTIFIC_PROMOTION"
)
RIEMANN_ZETA_AT_ZERO = -0.5


class ReciprocalRegion(str, Enum):
    ZERO_CENTER_ZETA = "ZERO_CENTER_ZETA"
    INTERIOR_RECIPROCAL = "INTERIOR_RECIPROCAL"
    HEISENBERG_BOUNDARY = "HEISENBERG_BOUNDARY"
    NAN_HEISENBERG = "NAN_HEISENBERG"


@dataclass(frozen=True)
class ReciprocalResolution:
    """Typed result of the PhaseNav reciprocal concept chain."""

    value: complex
    region: ReciprocalRegion
    algorithm: str
    source_rho: float
    reciprocal_rho: float
    uncertainty_floor: float | None
    epistemic_status: str = RECIPROCAL_REGULARIZATION_STATUS

    def to_dict(self) -> dict[str, object]:
        return {
            "value": {"real": float(self.value.real), "imag": float(self.value.imag)},
            "region": self.region.value,
            "algorithm": self.algorithm,
            "source_rho": float(self.source_rho),
            "reciprocal_rho": float(self.reciprocal_rho),
            "uncertainty_floor": (
                None if self.uncertainty_floor is None else float(self.uncertainty_floor)
            ),
            "epistemic_status": self.epistemic_status,
        }

    def receipt(self) -> dict[str, object]:
        payload = {
            "schema": "phasenav.reciprocal-regularization/v0.12",
            "version": RECIPROCAL_REGULARIZATION_VERSION,
            "result": self.to_dict(),
            "concept_chain": [
                "RECIPROCAL_INVERSION",
                "RIEMANN_ZETA_ZERO",
                "HEISENBERG_UNCERTAINTY",
            ],
            "scientific_promotion": "NOT_PERFORMED",
            "ordinary_division_by_zero_identity_claimed": False,
            "zeta_zero_value_is_standard_analytic_continuation": True,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        payload["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
        return payload


def _finite_positive(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")
    return number


def _finite_complex(value: complex | float | int) -> bool:
    number = complex(value)
    return math.isfinite(number.real) and math.isfinite(number.imag)


def riemann_zeta_zero_regularization() -> complex:
    """Return the exact analytic-continuation value ``zeta(0) = -1/2``.

    PhaseNav may use this value as a tagged continuation at the ZERO_CENTER gate.
    This function does not redefine ordinary division by zero.
    """

    return complex(RIEMANN_ZETA_AT_ZERO, 0.0)


def compactified_reciprocal_coordinates(
    denominator: complex | float | int,
    *,
    scale: float = 1.0,
) -> tuple[float, float]:
    """Return source and reciprocal Cayley/Poincare radii.

    For ``d = |z|/scale`` the source coordinate is ``rho=d/(1+d)``.  Existing
    PhaseNav reciprocal inversion then gives ``rho_rec=1-rho``.  Thus
    ``z=0`` is the source centre while its reciprocal image is the compactified
    boundary ``rho_rec=1``.
    """

    radius_scale = _finite_positive("scale", scale)
    z = complex(denominator)
    if not _finite_complex(z):
        raise ValueError("denominator must be finite for compactified coordinates")
    source_ratio = abs(z) / radius_scale
    source_rho = cayley_radius_from_ratio(source_ratio)
    reciprocal_rho = 1.0 - source_rho
    return float(source_rho), float(reciprocal_rho)


def heisenberg_uncertainty_floor(
    delta_z: float,
    delta_k: float,
    *,
    hbar: float = 1.0,
) -> float:
    """Validate a normalized conjugate uncertainty pair and return ``delta_z``.

    The normalized PhaseNav guard requires ``delta_z * delta_k >= hbar/2``.
    Units/calibration remain the caller's responsibility; this function only
    enforces the declared dimensionless contract.
    """

    dz = _finite_positive("delta_z", delta_z)
    dk = _finite_positive("delta_k", delta_k)
    hb = _finite_positive("hbar", hbar)
    lower_bound = hb / 2.0
    if dz * dk < lower_bound and not math.isclose(
        dz * dk, lower_bound, rel_tol=1e-12, abs_tol=1e-15
    ):
        raise ValueError("uncertainty pair violates delta_z*delta_k >= hbar/2")
    return dz


def heisenberg_soft_reciprocal(
    denominator: complex | float | int,
    *,
    delta_z: float,
    delta_k: float,
    hbar: float = 1.0,
) -> complex:
    """Finite uncertainty-bounded reciprocal.

    With uncertainty floor ``eps=delta_z`` the soft reciprocal is

    ``conj(z) / (|z|^2 + eps^2)``.

    It converges to ``1/z`` away from the uncertainty neighbourhood as the
    floor tends to zero and remains finite near the reciprocal singularity.
    Exact zero is handled separately by the zeta ZERO_CENTER gate.
    """

    z = complex(denominator)
    if not _finite_complex(z):
        raise ValueError("soft reciprocal requires a finite denominator/reference")
    eps = heisenberg_uncertainty_floor(delta_z, delta_k, hbar=hbar)
    return z.conjugate() / (abs(z) ** 2 + eps**2)


def _boundary_threshold(*, delta_z: float, scale: float) -> float:
    """Reciprocal compactified radius reached at the uncertainty floor."""

    return 1.0 - cayley_radius_from_ratio(delta_z / scale)


def resolve_reciprocal(
    denominator: complex | float | int,
    *,
    scale: float = 1.0,
    zero_tol: float = 0.0,
    delta_z: float | None = None,
    delta_k: float | None = None,
    hbar: float = 1.0,
    finite_reference: complex | float | int | None = None,
) -> ReciprocalResolution:
    """Resolve reciprocal geometry through concept-bound PhaseNav gates.

    Order of authority:

    1. exact/numerical ZERO_CENTER -> ``RIEMANN_ZETA_ZERO``;
    2. NaN with a finite reference -> ``HEISENBERG_UNCERTAINTY`` soft clip;
    3. finite point inside the declared uncertainty boundary -> Heisenberg soft
       reciprocal;
    4. otherwise -> exact reciprocal ``1/z``.

    ``delta_z`` and ``delta_k`` must be supplied together.  NaN never invents a
    direction: a finite reference is mandatory.
    """

    radius_scale = _finite_positive("scale", scale)
    tolerance = float(zero_tol)
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("zero_tol must be finite and >= 0")
    if (delta_z is None) != (delta_k is None):
        raise ValueError("delta_z and delta_k must be supplied together")

    z = complex(denominator)

    if not _finite_complex(z):
        if finite_reference is None:
            raise ValueError("NaN/non-finite denominator requires finite_reference")
        reference = complex(finite_reference)
        if not _finite_complex(reference) or abs(reference) <= tolerance:
            raise ValueError("finite_reference must be finite and outside ZERO_CENTER")
        if delta_z is None or delta_k is None:
            raise ValueError("NaN soft clipping requires delta_z and delta_k")
        eps = heisenberg_uncertainty_floor(delta_z, delta_k, hbar=hbar)
        source_rho, reciprocal_rho = compactified_reciprocal_coordinates(
            reference, scale=radius_scale
        )
        return ReciprocalResolution(
            value=heisenberg_soft_reciprocal(
                reference, delta_z=eps, delta_k=delta_k, hbar=hbar
            ),
            region=ReciprocalRegion.NAN_HEISENBERG,
            algorithm="HEISENBERG_UNCERTAINTY_SOFT_CLIP_FROM_FINITE_REFERENCE",
            source_rho=source_rho,
            reciprocal_rho=reciprocal_rho,
            uncertainty_floor=eps,
        )

    source_rho, reciprocal_rho = compactified_reciprocal_coordinates(
        z, scale=radius_scale
    )

    if abs(z) <= tolerance:
        return ReciprocalResolution(
            value=riemann_zeta_zero_regularization(),
            region=ReciprocalRegion.ZERO_CENTER_ZETA,
            algorithm="RIEMANN_ZETA_ZERO_ANALYTIC_CONTINUATION",
            source_rho=source_rho,
            reciprocal_rho=reciprocal_rho,
            uncertainty_floor=None,
        )

    if delta_z is not None and delta_k is not None:
        eps = heisenberg_uncertainty_floor(delta_z, delta_k, hbar=hbar)
        threshold = _boundary_threshold(delta_z=eps, scale=radius_scale)
        if reciprocal_rho >= threshold:
            return ReciprocalResolution(
                value=heisenberg_soft_reciprocal(
                    z, delta_z=eps, delta_k=delta_k, hbar=hbar
                ),
                region=ReciprocalRegion.HEISENBERG_BOUNDARY,
                algorithm="HEISENBERG_UNCERTAINTY_BOUNDARY_SOFT_RECIPROCAL",
                source_rho=source_rho,
                reciprocal_rho=reciprocal_rho,
                uncertainty_floor=eps,
            )

    return ReciprocalResolution(
        value=1.0 / z,
        region=ReciprocalRegion.INTERIOR_RECIPROCAL,
        algorithm="RECIPROCAL_INVERSION_EXACT_INTERIOR",
        source_rho=source_rho,
        reciprocal_rho=reciprocal_rho,
        uncertainty_floor=None,
    )


def division_with_concept_guard(
    numerator: complex | float | int,
    denominator: complex | float | int,
    **kwargs: object,
) -> ReciprocalResolution:
    """Apply the reciprocal concept chain to ``numerator / denominator``.

    At ZERO_CENTER this returns ``numerator * zeta(0)`` as an explicitly tagged
    PhaseNav continuation.  It must not be interpreted as ordinary arithmetic
    equality for division by zero.
    """

    a = complex(numerator)
    if not _finite_complex(a):
        raise ValueError("numerator must be finite")
    reciprocal = resolve_reciprocal(denominator, **kwargs)
    return ReciprocalResolution(
        value=a * reciprocal.value,
        region=reciprocal.region,
        algorithm=reciprocal.algorithm,
        source_rho=reciprocal.source_rho,
        reciprocal_rho=reciprocal.reciprocal_rho,
        uncertainty_floor=reciprocal.uncertainty_floor,
        epistemic_status=reciprocal.epistemic_status,
    )


def concept_algorithm_registry() -> Mapping[str, Mapping[str, object]]:
    """Return the executable concept bindings introduced by v0.12."""

    return {
        "RECIPROCAL_INVERSION": {
            "algorithm": "resolve_reciprocal",
            "geometry": "rho=|z|/(scale+|z|); reciprocal rho'=1-rho",
            "interior_rule": "1/z",
            "status": "EXISTING_GEOMETRY_BOUND_TO_ALGORITHM",
        },
        "RIEMANN_ZETA_ZERO": {
            "algorithm": "riemann_zeta_zero_regularization",
            "trigger": "ZERO_CENTER",
            "value": "zeta(0)=-1/2",
            "ordinary_division_identity": False,
            "status": "STANDARD_VALUE_PROJECT_REGULARIZATION_CONVENTION",
        },
        "HEISENBERG_UNCERTAINTY": {
            "algorithm": "heisenberg_soft_reciprocal",
            "trigger": "RECIPROCAL_BOUNDARY_OR_NAN_WITH_FINITE_REFERENCE",
            "constraint": "delta_z*delta_k>=hbar/2",
            "soft_rule": "conj(z)/(|z|^2+delta_z^2)",
            "status": "PROJECT_NUMERICAL_REGULARIZATION_CANDIDATE",
        },
    }
