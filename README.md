# noema-phasenav-core

> **Research prototype.** PhaseNav is an experimental 36D semantic/phase-space runtime. Scientific interpretations remain subject to separate validation; executable software integrity is tested independently.

## Runtime contract

PhaseNav uses a 36-dimensional torus `T^36 = (S^1)^36`. Every public phase vector, operator vector and orbit vector must therefore contain exactly **36 finite coordinates**.

The active repository crystal currently contains **34,770 × 36 float64 phase vectors**, with one metadata JSONL record per facet. The older 35,836-facet copy was a stale distribution snapshot and is not described here as the active dataset.

Core runtime:

```text
src/ciel_geometry/phasenav/
  pnv_runtime.py           legacy/runtime math surface
  artifact_registry.py     canonical -> runtime artifact materializer
  runtime_integrity.py     compatibility repair / fail-closed binding
  loader.py                validated runtime loader with canonical fallback
  solver.py                target-aware 36D solver
  phase_memory.py          36D memory crystal
  operator_algebra.py      36D operator algebra
  canon/                   canonical H2048 -> T36 cards and executable bindings
  data/
    phase_crystal_36d.npy
    phase_crystal_meta.jsonl
```

## Canonical fallback

Historical PhaseNav expected `glossary.pnv` / `glossarius/ciel_omega_glossary.json`. Those files are not present in the current repository. v0.14 repairs that compatibility boundary by rebuilding the runtime view from the canonical card registry.

Missing or zero-length runtime JSONL no longer means “empty state”. The loader either validates and uses the supplied runtime artifact or reconstructs the full runtime tables from canonical cards. Malformed JSONL, non-finite values and vectors whose dimension is not 36 fail explicitly.

```python
from ciel_geometry.phasenav.artifact_registry import write_runtime_artifacts
write_runtime_artifacts("/dev/shm/ciel_noema/phasenav")
```

The materializer writes name/mass, concept phase, operator vector, holonomic edge and orbit vector JSONLs plus a SHA-256 manifest.

## Orbit-vector schema

`orbit_vector` now means a **full 36D phase-orbit vector**. The old 11 labels (`mass`, `sin`, `cos`, `align`, …) are preserved only as legacy feature names and are no longer attached to `phi_0..phi_10`.

```python
from ciel_geometry.phasenav import PhaseNavSolver
solver = PhaseNavSolver.load()
v = solver.get_orbit("001")
assert len(v) == 36
```

## Executable repository surfaces

The formerly README-only top-level directories now contain real executable entry points:

| Directory | Executable role |
|---|---|
| `concept_phases/` | canonical concept-phase catalogue and JSONL export |
| `orbit_vectors/` | canonical full-36D orbit catalogue and export |
| `kuramoto/` | Kuramoto order parameter, stepping, simulation and diagnostics |
| `solver/` | repository-level solver façade and CLI |
| `encryption/` | façade and deterministic smoke validation for the experimental phase-interference cipher |

The phase-interference cipher remains a **research construction**, not standardized or independently reviewed cryptography.

## Quick start

```python
from ciel_geometry.phasenav import M_sentence_phase, M_sentence_phase_trajectory
v = M_sentence_phase("the nature of consciousness")
assert len(v) == 36
v_final, trajectory, holonomy = M_sentence_phase_trajectory("words carry semantic phase")
```

Memory:

```python
from ciel_geometry.phasenav import PhaseMemoryHypercrystal
crystal = PhaseMemoryHypercrystal()
assert crystal.load()
assert len(crystal) >= 34770
results = crystal.retrieve("Berry connection holonomy", top_k=5)
```

## Repository integrity audit

```text
python scripts/repo_integrity_audit.py --json
```

The audit checks executable directory completeness, Python compilation, crystal `N × 36` shape, metadata count equality, canonical/runtime population, finite 36D operator/orbit vectors, empty-runtime reconstruction and stale dataset documentation. CI invokes it after pytest.

## Installation

```text
pip install -e ".[dev]"
pytest tests/ -v --tb=short
python scripts/repo_integrity_audit.py --json
```

Python ≥ 3.10.

## Epistemic boundary

Software states remain distinct from scientific states. `implemented`, `tested`, `validated`, `candidate`, and `canon` are not interchangeable. Executable compatibility repair does not promote a scientific claim, legacy CIEL algorithm, or unresolved theorem.

## License

Copyright © 2026 Adrian Lipa. See `LICENSE`.
