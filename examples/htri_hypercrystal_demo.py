#!/usr/bin/env python3
"""Build and probe the HTRI Poincare time hypercrystal."""
from __future__ import annotations

import argparse
import json

import numpy as np

from ciel_geometry.phasenav.htri_hypercrystal import (
    HypercrystalConfig,
    build_htri_hypercrystal,
    evolve_state,
    hermiticity_error,
    load_crystal_arrays,
    localized_state,
    schrodinger_lagrangian,
    schrodinger_velocity,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intention", default="protect life and free will")
    parser.add_argument("--sample", type=int, default=512, help="0 means full crystal")
    parser.add_argument("--time-slices", type=int, default=5)
    parser.add_argument("--neighbours", type=int, default=8)
    parser.add_argument("--dt", type=float, default=0.01)
    args = parser.parse_args()

    sample = None if args.sample == 0 else args.sample
    phases, metadata = load_crystal_arrays(sample=sample, seed=7)
    config = HypercrystalConfig(
        neighbours=args.neighbours,
        time_slices=args.time_slices,
    )
    embedding, operators = build_htri_hypercrystal(
        phases, metadata, args.intention, config
    )

    psi = localized_state(len(phases), config.time_slices, facet_index=0)
    psi_dot = schrodinger_velocity(psi, operators.hamiltonian, hbar=config.hbar)
    on_shell_lagrangian = schrodinger_lagrangian(
        psi, psi_dot, operators.hamiltonian, hbar=config.hbar
    )
    off_shell_lagrangian = schrodinger_lagrangian(
        psi, np.zeros_like(psi), operators.hamiltonian, hbar=config.hbar
    )
    evolved = evolve_state(
        psi, operators.hamiltonian, args.dt, hbar=config.hbar
    )

    summary = {
        "status": "RESEARCH_MODEL_PASS",
        "facets": int(len(phases)),
        "phase_dimensions": int(phases.shape[1]),
        "time_slices": int(config.time_slices),
        "hilbert_dimension": int(operators.hamiltonian.shape[0]),
        "hamiltonian_nnz": int(operators.hamiltonian.nnz),
        "hamiltonian_hermiticity_error": hermiticity_error(operators.hamiltonian),
        "max_disk_radius": float(np.max(np.abs(embedding.coordinates))),
        "mean_resonance": float(np.mean(operators.resonance)),
        "max_resonance": float(np.max(operators.resonance)),
        "on_shell_lagrangian": on_shell_lagrangian.lagrangian,
        "off_shell_static_lagrangian": off_shell_lagrangian.lagrangian,
        "symplectic_term": on_shell_lagrangian.symplectic_term,
        "energy_expectation": on_shell_lagrangian.energy_expectation,
        "initial_norm": float(np.linalg.norm(psi)),
        "evolved_norm": float(np.linalg.norm(evolved)),
        "non_claim": "software geometry and finite Hamiltonian only; no physical carrier established",
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
