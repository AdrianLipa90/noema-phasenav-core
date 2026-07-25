# Append-only change log

Historical entries must not be removed or rewritten. Corrections are appended as new entries.

## 2026-07-25 — v0.2.0 HTRI Poincaré Time Hypercrystal

**Scope**

- Added `src/ciel_geometry/phasenav/htri_hypercrystal.py`.
- Added deterministic Poincaré-disk embedding of the 36D crystal.
- Added a Hermitian Pancharatnam-link magnetic graph Laplacian.
- Added a real crystal potential using Poincaré radius and existing facet tensor metadata.
- Added a bounded Hermitian intention observable and centred fluctuation operator.
- Added the `ln(2)/(24π)` fluctuation quantum to the intention energy.
- Added a discrete internal-time fibre, Hermitian momentum and temporal-shear coupling.
- Added the full sparse HTRI Hamiltonian and Schrödinger Lagrangian evaluator.
- Added `examples/htri_hypercrystal_demo.py` and `docs/htri_hypercrystal.md`.
- Added regression tests for geometry, Hermiticity, Lagrangian evaluation and norm preservation.
- Bumped package version from `0.1.0` to `0.2.0`.
- Crystal re-encoded with `M_sentence_phase_precise` (Decimal 38 digits, v1 encoding) — 35,836 facets.

**Reason**

Rebuild the software HTRI layer so that potential, Poincaré geometry, intention fluctuation and internal time are computed directly on the bundled PhaseNav memory crystal rather than represented by an ungrounded standalone oscillator scaffold.

**Evidence boundary**

The implementation establishes a finite mathematical/software model only. It does not establish a physical carrier, neutrino modulation, nonlocal signalling or external NOEMA authority.
