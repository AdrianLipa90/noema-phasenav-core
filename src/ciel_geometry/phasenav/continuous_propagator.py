#!/usr/bin/env python3
"""Continuous phase propagator on S¹ — Zeta-Schrödinger evolution.

Replaces discrete Kuramoto (36 osc, dt stepping) with a continuous spline
representation. The phase field φ(θ, t) lives on a circle, evolved by:
    i·∂φ/∂t = H·φ + V_zeta(φ)
where V_zeta is Zeta-regularized potential (no collaps, continuous).

Discrete 36 points are kept as B-spline control knots, not oscillators.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline, PPoly
from scipy.linalg import expm

N_KNOTS = 36
N_SAMPLES = 512  # evaluation grid for continuous representation


def spline_phi(phi_knots: np.ndarray) -> CubicSpline:
    """Build a continuous C² phase field φ(θ) from knots on S¹."""
    theta = np.linspace(0, 2 * np.pi, len(phi_knots) + 1)
    phi_wrap = np.append(phi_knots, phi_knots[0])
    return CubicSpline(theta, phi_wrap, bc_type="periodic")


def zeta_potential(phi: np.ndarray) -> np.ndarray:
    """Zeta-regularized potential: smooth, non-collapsing.

    V(φ) = Σ_{n=1}^{∞} cos(n·φ) / n^{σ}
    Truncated at n=32, σ=1.5 → continuous, no Gibbs.
    """
    n = np.arange(1, 33, dtype=np.float64)  # (32,)
    # Wektorowo: (N, 32) * (32,) → (N, 32) → (N,)
    return np.sum(np.cos(n[None, :] * phi[:, None]) / n[None, :] ** 1.5, axis=1)


def evolve_continuous(
    phi_knots: np.ndarray,
    dt: float = 0.01,
    hbar: float = 0.1,
    coupling: np.ndarray | None = None,  # coupling field [36] from g*sin(diff)
    omega_eff: np.ndarray | None = None,  # effective frequencies
) -> tuple[np.ndarray, float, float]:
    """Single step of continuous Schrödinger evolution on S¹.

    Returns (new_knots, max_dphi, second_deriv_norm).
    """
    cs = spline_phi(phi_knots)
    theta_dense = np.linspace(0, 2 * np.pi, N_SAMPLES, endpoint=False)
    phi_dense = cs(theta_dense)

    # Kinetic energy: second derivative from spline
    d2phi = cs.derivative(2)(theta_dense)

    # Zeta potential
    V = zeta_potential(phi_dense)

    # Hamiltonian: -hbar²/2 · ∇² + V
    H_kinetic = -hbar * 0.5 * d2phi
    H_potential = V * phi_dense

    # Kuramoto coupling projected onto dense grid
    if coupling is not None and omega_eff is not None:
        # Interpolate coupling field to dense theta
        cs_g = CubicSpline(np.linspace(0, 2 * np.pi, len(coupling) + 1),
                           np.append(coupling, coupling[0]), bc_type="periodic")
        cs_omega = CubicSpline(np.linspace(0, 2 * np.pi, len(omega_eff) + 1),
                               np.append(omega_eff, omega_eff[0]), bc_type="periodic")
        g_dense = cs_g(theta_dense)
        omega_dense = cs_omega(theta_dense)
        H_drive = omega_dense + g_dense * np.sin(phi_dense - np.roll(phi_dense, 1))
    else:
        H_drive = 0.0

    # Schrödinger evolution
    phi_new_dense = phi_dense + dt * (H_kinetic + H_potential + H_drive)
    phi_new_dense = np.mod(phi_new_dense, 2 * np.pi)

    # Metrics
    max_dphi = float(np.max(np.abs(phi_new_dense - phi_dense)))
    d2_norm = float(np.mean(np.abs(d2phi)))

    # Project back to knots
    theta_knots = np.linspace(0, 2 * np.pi, N_KNOTS + 1)
    phi_wrap = np.asarray(phi_new_dense).copy()
    phi_wrap[-1] = phi_wrap[0]
    from scipy.interpolate import CubicSpline as CS2
    cs_new = CS2(theta_dense, phi_wrap, bc_type="periodic")
    return cs_new(theta_knots[:-1]), max_dphi, d2_norm


def self_test():
    rng = np.random.default_rng(42)
    phi_knots = rng.uniform(0, 2 * np.pi, N_KNOTS)

    cs = spline_phi(phi_knots)
    theta_test = np.linspace(0, 2 * np.pi, N_SAMPLES, endpoint=False)
    phi_cont = cs(theta_test)
    print(f"Continuous spline: min={phi_cont.min():.3f} max={phi_cont.max():.3f}")
    print(f"C² continuity: derr={np.max(np.abs(cs.derivative(2)(theta_test) - cs.derivative(2)(theta_test + 0.01))):.6f}")

    phi_next = evolve_continuous(phi_knots, dt=0.05)
    delta = float(np.mean(np.abs(phi_next - phi_knots)))
    print(f"Evolution (1 step): mean |Δφ| = {delta:.4f}")
    print(f"  min={phi_next.min():.3f} max={phi_next.max():.3f}")

    return delta


if __name__ == "__main__":
    self_test()
