# CIEL executable algorithms → PhaseNav concepts v0.13

## Status

`IMPLEMENTED_CANDIDATE / SOURCE_PROVENANCE_BOUND / NO_AUTO_EXECUTION / NOT_PROMOTED`

This receipt records the v0.13 mapping of executable CIEL/PhaseNav algorithms
onto PhaseNav concept cards. It is a software routing layer. It does not promote
scientific claims, does not promote legacy CIEL code to current canon, and does
not execute a function merely because a concept is recognized.

## Branch boundary

- repository: `AdrianLipa90/noema-phasenav-core`
- branch: `canon/ciel-executable-concept-map-v0.13`
- stacked parent: `canon/reciprocal-zeta-heisenberg-v0.12`
- exact stacked parent SHA: `3be5df43492ef011ad0847ba3b9891aa86de994f`
- direct write to `master`: **NOT PERFORMED**

v0.13 intentionally builds on v0.12 so the existing concept-bound reciprocal,
Riemann-zeta-zero and Heisenberg regularization algorithms remain attached to
cards 116–118.

## Source classes

### 1. PHASENAV_NATIVE_CURRENT

Current executable algorithms already present in the PhaseNav runtime at the
v0.12 parent state.

Source anchor:

- repo: `AdrianLipa90/noema-phasenav-core`
- commit: `3be5df43492ef011ad0847ba3b9891aa86de994f`

Exact native source blobs used by the map:

- `src/ciel_geometry/phasenav/canon/observer_generation.py`
  - blob: `24a2965c42ecedfd27555f055643c3e0c7671fda`
- `src/ciel_geometry/phasenav/canon/operator_calculus.py`
  - blob: `557689f8e207ba4537397b3bae591379f211ef32`
- `src/ciel_geometry/phasenav/canon/context_dynamics.py`
  - blob: `1a8e82faaf6dcfeae2b56853bc289f6215ed65c7`
- `src/ciel_geometry/phasenav/canon/numerical_guards.py`
  - blob: `22acc82bd88a408d04f34ddd8c0c31f4940727a5`

Examples mapped from this class:

- `HolonomicMemory.recall`, `.ingest`, `.decay`
- `HolonomyCache.get`, `.put`
- `Observation.from_text`
- `IntentionState.from_text`
- `ObserverToGenerationPipeline.observe`, `.run`
- `ContextPotential.from_concepts`, `.context_vector`, `.sample`
- `find_attractors`, `trace_orbit`
- `evolve_generation_state`
- `stable_trajectory_curvature`
- `SemanticScheduler.cost`, `.push`, `.pop`
- `project_forbidden_directions`

### 2. CANONICAL_V15

Promoted CIEL/NOEMA/CIELingo integration boundary from:

- repo: `AdrianLipa90/CIEL-NOEMA-HTRI-CIELingo-Phasenav`
- source commit: `f24b125039833d47316e5be1bcb4e18ce030a893`

Exact source blobs:

- `integration/canonical_v15/canonical_memory_commit.py`
  - blob: `2930a7335f71f52d3cafdd9ded734c4aea4a2227`
- `integration/canonical_v15/integration_pipeline.py`
  - blob: `ee482a6a51dcbe54f1f51a2e38639881877aa9ab`
- `integration/canonical_v15/runtime_adapters.py`
  - blob: `f25c7f8c7901db295b976cff99546316377e5d02`
- `integration/canonical_v15/doctor.py`
  - blob: `9f47b0a6e240c01dfefa021cfaacf8cea73e437c`

Mapped examples:

- safe durable memory reconstruction
- Memory Home packet construction
- fail-closed durable/deep memory commit
- admission classification/validation gate
- predecessor-linked receipt verification
- Lingophysics proposal analysis
- CIELingo surface proposal generation
- canonical language-loop orchestration
- Doctor verification

### 3. LEGACY_EXECUTABLE_SOURCE

Executable source from the older full CIEL/Ω kernel. This code is mapped because
it contains the requested paradox and temporal algorithm families, but it is
**not** reclassified as current canon.

Source anchor:

- repo: `AdrianLipa90/CIEL-Omega-General-Quantum-Consciousness`
- commit: `5812b547a6308d79ef6b42606b9bda28f1879274`
- file: `paradoxes/ultimate_operators.py`
- blob: `ba3d8d48a40306a50dc67835419c43e130adf705`

Mapped examples include:

- paradox graph construction and coherence
- Russell/Gödel/Liar self-reference operator
- Sorites, Theseus, Newcomb, Simpson and mereology operators
- temporal-field initialization and evolution
- Zeno temporal operator
- tachyonic causal-loop phase
- bootstrap, grandfather and predestination temporal-loop operators
- entropy/time attenuation
- intention/ethical/consciousness field evolution
- resonance and Collatz dynamics

These bindings require `include_legacy=True` in the unified planner.

### 4. LEGACY_TEST_EXECUTABLE

The older test-friendly `ciel_memory/orchestrator.py` memory implementation is
mapped separately from both native current memory and canonical V15.

- repo: `AdrianLipa90/CIEL-Omega-General-Quantum-Consciousness`
- commit: `5812b547a6308d79ef6b42606b9bda28f1879274`
- file blob: `d858c9543420a2f7b26d96455155c3d38c662cdb`

Mapped operations: capture, TMP evaluation, bifurcation promotion and daily
maintenance. These are legacy/test provenance and are not part of the default
execution plan.

## Concept-card model

Every PhaseNav card continues to expose one `algorithm_bindings` collection.
The collection can now contain three compatible binding forms:

1. local concept algorithm introduced by PhaseNav itself;
2. current native PhaseNav executable binding;
3. provenance-exact external CIEL executable-source binding.

Every source-backed row carries, where applicable:

- binding ID;
- algorithm family;
- source repository;
- exact source commit;
- exact source blob SHA;
- source path;
- callable/class-method symbol;
- provenance class;
- side-effect class;
- concept targets;
- deterministic priority;
- semantic role;
- `execution_activation = EXPLICIT_RUNTIME_DISPATCH`;
- `scientific_promotion = NOT_PERFORMED`.

## New concept nodes

Two previously missing semantic routing nodes were added as **candidates**:

- `119 Paradox`
- `120 Causality`

They use seed status `H`; therefore their card metadata keeps
`canon_allowed = false`. Adding the node makes algorithm routing possible but
does not itself canonize the concept definition or any physical interpretation.

## Families mapped in v0.13

The mapping covers, at minimum:

- memory / mnemonic;
- perception / reception;
- context / potential / attractors / orbits;
- temporal / Aion / Kairos / causality;
- semantic / Logos / Rhema / Poiesis;
- paradox;
- intention;
- ethics;
- resonance / coherence;
- dynamics / chaos;
- consciousness / self;
- scheduler / salience / evaluation;
- constraints / exclusion / justice;
- full observer-to-generation pipeline.

## Default execution policy

The unified `execution_plan_for_concept()` is fail-closed.

By default it may plan:

- `LOCAL_PHASE_NAV_CURRENT`;
- `PHASENAV_NATIVE_CURRENT`;
- `CANONICAL_V15`.

By default it excludes:

- `LEGACY_EXECUTABLE_SOURCE`;
- `LEGACY_TEST_EXECUTABLE`;
- every binding whose side effect is `WRITE`.

Legacy source requires `include_legacy=True`.
Write-capable algorithms require `include_writes=True`.

Even after opt-in the planner returns metadata only. No module import, callable
resolution or execution is performed by the mapping layer.

## Example semantic routes

### Memory (`090`)

Current/native routes include:

- holonomic recall;
- holonomic ingest;
- activation decay;
- holonomy-cache lookup/store.

Canonical V15 routes include:

- durable reconstruction;
- Memory Home packet read;
- receipt-chain verification;
- admission and durable commit (write-gated).

Legacy TMP/capture/maintenance is visible only as legacy provenance.

### Time (`018`)

Current/native routes include:

- coupled finite-dt generation dynamics;
- stable trajectory curvature;
- memory decay as a time-dependent memory operation.

Legacy historical routes remain available for temporal-field evolution, Zeno,
causal-loop and entropy-time operators only with legacy opt-in.

### Paradox (`119`)

The currently recovered explicit paradox implementations come from legacy CIEL
source. Therefore the default plan for `119` is empty. A caller must explicitly
request legacy provenance to obtain those algorithms. This is intentional.

### Kairos (`115`)

Current native mappings include semantic scheduler cost/push/pop together with
finite-dt generation dynamics. This makes the timing/selection concept carry an
actual executable planning family rather than only a semantic phase marker.

## Validation obligations

Repository tests in `tests/test_ciel_executable_map.py` cover:

- presence and candidate status of Paradox/Causality;
- native + V15 memory bindings;
- native + legacy temporal bindings;
- context and Kairos native mappings;
- paradox/causality legacy mappings;
- survival of v0.12 reciprocal/zeta/Heisenberg bindings;
- all target concept IDs resolving to cards;
- exact repository/commit/blob provenance;
- default fail-closed external and unified plans;
- explicit legacy and write opt-ins;
- deterministic family and priority routing;
- prohibition on auto-execution;
- deterministic non-promoting receipts.

GitHub Actions in this repository have an existing infrastructure condition in
which jobs can fail before any workflow step executes (`steps=[]`, runner id 0).
A workflow showing that condition must be recorded as `CI_INFRA_BLOCKED`, not as
a test-code FAIL. Promotion requires executable test evidence on the exact v0.13
head or another provenance-equivalent validated execution environment.

## Promotion boundary

`scientific_promotion = NOT_PERFORMED`

`legacy_to_current_promotion = NOT_PERFORMED`

`concept_auto_execution = FORBIDDEN`

`master_write = NOT_PERFORMED`
