# CIEL executable concept map v0.13 — extended inventory addendum

## Scope

This addendum extends the v0.13 CIEL executable-source inventory without
changing its promotion or execution policy.

Source anchor remains:

- repository: `AdrianLipa90/CIEL-Omega-General-Quantum-Consciousness`
- commit: `5812b547a6308d79ef6b42606b9bda28f1879274`
- file: `paradoxes/ultimate_operators.py`
- blob: `ba3d8d48a40306a50dc67835419c43e130adf705`
- provenance class: `LEGACY_EXECUTABLE_SOURCE`

## Additional mapped families

The extension adds explicit concept routing for:

- quantum superposition;
- legacy Heisenberg uncertainty;
- legacy zeta protection;
- Banach–Tarski and Hilbert-hotel paradox operators;
- Watanabe coherence;
- quantum-observer construction;
- self/universe relation;
- Fermi, EPR, Wigner-friend, Olbers and Moravec paradox operators;
- paradox-field initialization and evolution.

## Critical disambiguations

`CIEL.UNCERTAINTY.HEISENBERG.LEGACY` and the current PhaseNav v0.12
`HEISENBERG_UNCERTAINTY` are separate algorithms with separate provenance.
The legacy symbol is never substituted for the current reciprocal-boundary
soft clip.

`CIEL.ZETA.PROTECTION.LEGACY` and current PhaseNav v0.12
`RIEMANN_ZETA_ZERO` are likewise separate. Mapping the legacy symbol to concept
117 does not change the v0.12 zero regularization and does not assert the Riemann
Hypothesis or redefine ordinary division by zero.

## Execution boundary

All extended rows retain:

- `provenance_class = LEGACY_EXECUTABLE_SOURCE`;
- `execution_activation = EXPLICIT_RUNTIME_DISPATCH`;
- `scientific_promotion = NOT_PERFORMED`.

Therefore `execution_plan_for_concept()` excludes every extended row by default.
They become visible in a unified plan only with `include_legacy=True`.

## Validation additions

`tests/test_ciel_executable_map.py` now checks:

- extended paradox inventory on concept 119;
- direct distinction between current and legacy Heisenberg mappings;
- direct distinction between current and legacy zeta mappings;
- observer/coherence/cosmos routes;
- concept target validity for the complete extended inventory;
- explicit legacy gating in the unified planner;
- no auto-execution for any extended binding.

No direct write to `master` and no legacy-to-current promotion is performed by
this addendum.
