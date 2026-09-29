# noema-phasenav-core

> **Research prototype.** PhaseNav is an experimental 36D semantic/phase-space runtime. Scientific interpretations remain subject to separate validation; executable software integrity is tested independently.

## Runtime contract

PhaseNav uses a 36-dimensional torus `T^36 = (S^1)^36`. Every public phase vector, operator vector and orbit vector must therefore contain exactly **36 finite coordinates**.

The active repository crystal currently contains **34,770 × 36 float64 phase vectors**, with one metadata JSONL record per facet. The older 35,836-facet copy was a stale distribution snapshot and is not described here as the active dataset.

Core runtime:

```text
src/ciel_geometry/phasenav/
  pnv_runtime.py           side-effect-free 36D numerical runtime
  artifact_registry.py     canonical -> runtime artifact materializer
  runtime_integrity.py     compatibility repair / fail-closed binding
  loader.py                validated runtime loader with canonical fallback
  solver.py                target-aware 36D solver
  phase_memory.py          36D memory crystal
  operator_algebra.py      strict 36D operator algebra/runtime loaders
  canon/                   canonical H2048 -> T36 cards and executable bindings
  data/
    phase_crystal_36d.npy
    phase_crystal_meta.jsonl
```

Importing `pnv_runtime` does **not** write runtime artifacts or mutate `/dev/shm`. Runtime materialization is an explicit operation only.

## Canonical fallback

Historical PhaseNav expected `glossary.pnv` / `glossarius/ciel_omega_glossary.json`. Those files are not present in the current repository. v0.14 repairs that compatibility boundary by rebuilding the runtime view from the canonical card registry.

Missing runtime JSONL uses an explicit canonical fallback. Existing malformed or zero-record runtime data is not accepted as success. Malformed JSONL, non-finite values and vectors whose dimension is not 36 fail explicitly.

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

The audit checks executable-directory completeness, Python compilation, crystal `N × 36` shape, metadata count equality, canonical/runtime population, finite 36D operator/orbit vectors, explicit materialization, canonical fallback and stale dataset documentation. It also fails if the critical runtime reintroduces broad silent exception swallowing, `v36[:11]` truncation, solver zero-padding, malformed non-36D acceptance, or placeholder substitution for unknown operators. CI invokes the audit after pytest.

## Installation

```text
pip install -e ".[dev]"
pytest tests/ -v --tb=short
python scripts/repo_integrity_audit.py --json
```

Python ≥ 3.10.

## Validation status

The repair branch contains executable pytest and whole-repository audit gates. GitHub Actions is currently infrastructure-blocked before runner execution (`steps=null` / no runner steps), so no full-suite PASS is claimed until the exact checkout actually executes.

## Epistemic boundary

Software states remain distinct from scientific states. `implemented`, `tested`, `validated`, `candidate`, and `canon` are not interchangeable. Executable compatibility repair does not promote a scientific claim, legacy CIEL algorithm, or unresolved theorem.

## License

Copyright © 2026 Adrian Lipa. See `LICENSE`.


## Orbital / scalar / tensor primitives v0.15

The candidate v0.15 layer adds substrate-neutral primitives for rank-revealing
atomization and orbital/tensor geometry:

- singular-spectrum scalars with a machine-epsilon default rank threshold;
- complex-projective Fubini--Study / Pancharatnam orbit receipts;
- 4D exterior wedge, Pluecker simplicity and Euclidean Hodge 3+3 decomposition;
- principal subspace angles, Grassmann distances and closed Bargmann-triangle holonomy;
- tensor unfolding, mode products, Schmidt/operator-Schmidt decomposition and Schmidt-spectrum entropies;
- TT-SVD / MPS and Tucker/HOSVD factorizations with explicit truncation accounting;
- boundary-state linear-rank compression, streaming basis construction and
  operator-Schmidt boundary-capacity bounds.

The layer is `CANDIDATE_ONLY`, keeps `canon_allowed=false`, and makes no
physical-QPU, physical-spacetime or measured-field claim. See
`docs/orbital_scalar_tensor_primitives_v0_15.md`.


## Mixed-representation contraction primitives v0.16

The candidate v0.16 layer extends atomized PhaseNav execution with:

- exact quadratic computational-basis phase polynomials for CZ/RZ atoms;
- fail-closed Abelian block-sparse charge sectors;
- Clifford and two-qubit matchgate routing predicates;
- polar and Schur boundary-reduction primitives;
- a typed mixed-representation router across phase-polynomial, stabilizer,
  Gaussian, MPS/TT, Tucker, dense and generic tensor-network paths;
- explicit greedy contraction, slicing-to-memory and content-addressed disk-shard plans;
- min-fill and scalable min-degree graph-width upper-bound receipts.

The released 61-qubit RCS topology is represented as alternating local generic
SU(2) atoms and compact quadratic CZ-layer atoms; no static interaction-graph
width is promoted as the full spacetime tensor-network contraction width.

Focused local validation: v0.15 **20 passed**, v0.16 **23 passed**.
The layer remains `CANDIDATE_ONLY` with `canon_allowed=false`.
See `docs/mixed_representation_contraction_v0_16.md`.


## Channel / transfer / Krylov primitives v0.17

The candidate v0.17 layer adds:

- density, partial-trace and information-scalar primitives;
- Kraus, Choi and superoperator channel representations;
- Pauli-transfer matrices with signed-permutation routing diagnostics;
- exact unitary second-moment transport;
- the parameter-free local-Haar + CZ support transition used by the RCS audit;
- transfer-spectrum and channel-fixed-point receipts;
- fail-closed Woodbury low-rank updates;
- fully reorthogonalized Hermitian Lanczos/Krylov projection.

For the local-Haar + CZ support channel, the nonzero sector has eigenvalues
`1, 1/3, -1/9` and stationary support weights `1/5, 1/5, 3/5`.
This is a local second-moment identity, not a global XEB result.

Focused local validation: **24 passed** plus `py_compile PASS`.
The layer remains `CANDIDATE_ONLY` with `canon_allowed=false`.
See `docs/channel_transfer_krylov_v0_17.md`.


## Global support-transfer audit v0.18

The candidate v0.18 layer lifts the exact local Haar-SU(2)+CZ support channel to
the released 61-site IBM topology.

It adds exact dense controls for small systems, labelled MPS support evolution,
Monte-Carlo trajectory validation, physical-row block atomization and explicit
resource-stop receipts.

On the 61-site d=36 topology, 100,000 local support trajectories complete in
about 3.1 s on the current ordinary host and give final mean support weight
45.64694 +/- 0.01085 (standard error). This is a second-moment/operator-support
statistic, not quantum output sampling or XEB.

Exact rank-revealing tensorizations expose the current bottleneck: the bit-MPS
route reaches retained bond 884 and then requires rank 1323 before completing
depth 36; the row-block route removes SWAP routing but encounters a
41,943,040-element SVD matrix after seven matching layers under the declared
workspace budget.

Focused validation: **9 passed**, `py_compile PASS`.
The layer remains `CANDIDATE_ONLY` with `canon_allowed=false`.
See `docs/global_support_transfer_v0_18.md`.


## Adaptive separator tree v0.19

The candidate v0.19 layer adds exact fixed-cardinality graph cuts using
SciPy/HiGHS MILP, dynamic operator-Schmidt cut weights and recursive separator
trees for atomized execution planning.

For the released IBM 61-site graph at d=36, exact near-balanced cuts are:

- 27/34: 6 static edges, 54 dynamic CZ-capacity bits;
- 28/33: 7 edges, 63 bits;
- 29/32: 7 edges, 63 bits;
- 30/31: 7 edges, 63 bits.

The Pareto frontier is therefore 27/34 versus 30/31: lower maximum separator
versus better balance. Recursive exact-half cuts below those roots produce
leaf atoms of at most eight vertices without hiding the trade behind a fitted
scalar score.

Focused validation: **6 passed**, `py_compile PASS`.
Static graph separators are not promoted as the full spacetime contraction
width or IBM `C_amp`. The layer remains `CANDIDATE_ONLY`.
See `docs/adaptive_separator_tree_v0_19.md`.
