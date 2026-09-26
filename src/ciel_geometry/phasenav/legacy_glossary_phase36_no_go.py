"""Audit helpers for the recovered legacy PhaseNav glossary phase-marker family.

This module preserves the recovered phase-marker formula as an audit object.
It is not a physical basis adapter.

Recovered form:
    phi_i(q) =
      [kappa*tau
       + alpha_M*tau*(i mod 7)
       + (2/7)*tau*floor(i/7)
       + (q mod 5)*tau/7] mod tau

Consequently every q-dependence is a common U(1) shift of one fixed
36-coordinate template.
"""
from __future__ import annotations

import math

from .orbital_rotation36 import generator36_xy

TAU = 2.0 * math.pi
KAPPA = math.log(2.0) / (24.0 * math.pi)
ALPHA_M = 0.0072973113787402075
DIM = 36


def _wrap(theta: float) -> float:
    return (float(theta) + math.pi) % TAU - math.pi


def recovered_legacy_glossary_phase36(quark_prime: int) -> tuple[float, ...]:
    q = int(quark_prime)
    return tuple(
        (
            KAPPA * TAU
            + ALPHA_M * TAU * (i % 7)
            + (2.0 / 7.0) * TAU * (i // 7)
            + (q % 5) * TAU / 7.0
        )
        % TAU
        for i in range(DIM)
    )


def relative_phase36(q_left: int, q_right: int) -> tuple[float, ...]:
    a = recovered_legacy_glossary_phase36(q_left)
    b = recovered_legacy_glossary_phase36(q_right)
    return tuple(_wrap(y - x) for x, y in zip(a, b))


def common_shift_spread(q_left: int, q_right: int) -> float:
    delta = relative_phase36(q_left, q_right)
    ref = delta[0]
    return max(abs(_wrap(x - ref)) for x in delta)


def forced_row_major_so2_projection(q_left: int, q_right: int) -> tuple[float, float]:
    """Negative-control projection if legacy delta were forcibly read as 6x6.

    This reinterpretation is NOT authorized. It is used only to show that even
    the historical row-major 6x6 guess does not align with the calibrated
    orbital generator J_36.
    """
    delta = relative_phase36(q_left, q_right)
    x = tuple(tuple(delta[6 * r + c] for c in range(6)) for r in range(6))
    j = generator36_xy()
    den = math.fsum(j[r][c] * j[r][c] for r in range(6) for c in range(6))
    theta_hat = math.fsum(x[r][c] * j[r][c] for r in range(6) for c in range(6)) / den
    residual = math.sqrt(
        math.fsum(
            (x[r][c] - theta_hat * j[r][c]) ** 2
            for r in range(6)
            for c in range(6)
        )
    )
    return theta_hat, residual
