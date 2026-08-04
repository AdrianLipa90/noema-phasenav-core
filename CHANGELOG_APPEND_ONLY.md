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

## 2026-08-04 — PhaseNav Canon v1.0.0 / package v0.3.0

**Scope**

- Established the canonical source state as a normalized vector in `C^2048` with an 11-bit basis.
- Added the anti-linear complement `Jψ[j] = conj(ψ[j xor 2047])`, satisfying `J² = I`.
- Added complementary channel weights `(p_plus, p_minus)`, reciprocal coordinate `q`, half-deficit and continuous self-dual radius `|ln q|`.
- Defined the operational projection `H2048 → T36` and enforced exact compatibility with `_phase36_from_id` for numeric Metatime IDs and textual Collatz fallback IDs.
- Split semantic mass into the positional glossary formula and the non-positional textual fallback `κ(1 + R)`.
- Added an epsilon-free orbital audit that separates mass attractor, coherence peak, nearest self-dual state, full 36D distance, Berry connection and repository architectural role.
- Added a compact 115-card seed ledger and deterministic H2048/T36 card materialization.
- Preserved 2 internally consistent cards as canonical and retained `chyba` with `canon_allowed=false` for 113 unresolved cards.
- Replaced zero-distance-only emergent edges with a composite orbital relation using 36D distance, semantic-mass distance, reciprocal-channel distance and Berry correction.
- Added `CURRENT`, a machine-readable canon manifest, public package exports, documentation, CLI audit and regression tests.
- Bumped package version from `0.2.0` to `0.3.0`.

**Authority**

`TO_JEST_MOJE`, issued by Adrian Lipa, records authorial conformity and quality approval for PhaseNav Canon v1.0.0.

**Mutation boundary**

The orbital audit is read-only. Orbital shell metadata does not authorize repository file movement; architectural placement and mutation require separate authorization.

**Validation**

Targeted local canon suite: `7 passed`.
