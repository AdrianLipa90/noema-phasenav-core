# noema-phasenav-core

> **Research prototype.** This is an experimental implementation of PhaseNav 36D
> concepts. The public API is unstable, mathematical claims are unvalidated against
> external benchmarks, and several modules depend on a running NOEMA host system.
> Do not rely on v0.1.0 for production use.

**PhaseNav 36D** — oscillatory semantic phase space engine.

Text → 36-dimensional phase vector via Collatz-seeded phasor superposition.  
Memory retrieval via Berry holonomy correction and Scalar of Meaning M_x(V).

---

## What is PhaseNav?

PhaseNav encodes any text as a point in a 36-dimensional torus **T³⁶ = (S¹)³⁶**.  
Each dimension is a phase angle φᵢ ∈ [0, 2π).

The encoding pipeline:

1. Each word `w` → Collatz hash `h(w)` → 36 phasors `φᵢ = (h · κ · 2π · (i+1)) mod 2π`
2. Phasors accumulate via circular mean: `V[i] = atan2(Σ sin(φᵢ), Σ cos(φᵢ))`
3. Result: a single 36D vector representing the semantic centre of mass of the text

Distance between vectors uses the **LIE4 weighted angular metric**:

```
d(V, Q) = Σᵢ wᵢ · min(|Vᵢ - Qᵢ|, 2π - |Vᵢ - Qᵢ|) / W
```

Weights emphasise Lorentz (×2.0), Intention (×2.0), and Soul (×1.5) dimensions.

---

## Mathematical Foundations

### Collatz Hash

```python
M_collatz_hash(word) → int
```

Deterministic integer hash via Collatz sequence length on Unicode codepoint sum.
Produces uniform distribution across phase space dimensions.

### Sentence as Trajectory (Language Derived from Meaning)

Each word acts as an operator σᵢ: m → m′.
A sentence progressively narrows the interpretation space:

```
Ω₀ ⊃ Ω₁ ⊃ ... ⊃ Ωₙ
```

`M_sentence_phase_trajectory(text)` returns `(v_final, trajectory[V₀..Vₙ], holonomy Γ)`.

### Berry Connection & Holonomy

For a query trajectory V₀ → V₁ → ... → Vₙ:

```
A(Q, V) = mean_i(sin(Vᵢ − Qᵢ))   # imaginary part of ⟨Q|V⟩
Γ = Σₖ A(Vₖ₊₁, Vₖ)                # accumulated holonomy
```

Berry correction applied during retrieval:

```
berry_corr = 1 / (1 + |A| · 0.5)
```

### Scalar of Meaning M_x(V)

Implementation of **M_x(V) = χ · T_μνλ · O^μ · C^ν · V^λ** (Valov & Ahmad):

```
M_score = χ · t_score · align · berry_corr
        + |soul_obs| · |cos(φ[12])| · 0.3
        + κ_I⁻¹ · 0.1
```

where:
- `χ` = ethical weight ∈ [0, 1]
- `t_score = phase_R² / max(κ_I, 0.1) + |soul| · 0.5`
- `align = clip(1 − d/π, 0, 1)`
- `κ_I` = informational curvature (mean angular distance to k=5 nearest neighbours)

### η_M Threshold

Semantic basin radius derived from first principles:

```
κ = 0.009210...       # KAPPA — base semantic unit
η_M = 36·κ ≈ 0.331   # basin distinguishability
BASIN_RADIUS = 4·η_M ≈ 1.324
```

---

## Installation

```bash
pip install ciel-phasenav
```

From source:

```bash
git clone https://github.com/AdrianLipa90/noema-phasenav-core.git
cd noema-phasenav-core
pip install -e .
```

**Requirements:** Python ≥ 3.10, numpy ≥ 1.24

---

## Quick Start

```python
from ciel_geometry.phasenav import M_sentence_phase, M_sentence_phase_trajectory

# Text → 36D phase vector
v = M_sentence_phase("the nature of consciousness")
print(len(v))   # 36

# Text → trajectory + Berry holonomy
v_final, trajectory, holonomy = M_sentence_phase_trajectory("the nature of consciousness")
print(f"words: {len(trajectory)}, holonomy Γ: {holonomy:.4f}")
```

### Memory Crystal (35 836 facets)

```python
from ciel_geometry.phasenav import PhaseMemoryHypercrystal

crystal = PhaseMemoryHypercrystal()
crystal.load()

# Retrieval with M_score (Berry-corrected Scalar of Meaning)
results = crystal.retrieve("Berry connection holonomy", top_k=5)
for r in results:
    print(f"[{r['m_score']:.4f}] {r['text'][:80]}")

# Trajectory-based narrowing
out = crystal.retrieve_trajectory("words as semantic operators")
print(f"Ω-sizes: {out['omega_sizes']}")   # e.g. [2394, 145, 30, 2, 1, 1]
print(f"holonomy: {out['holonomy']:.4f}")
```

### Solver

```python
from ciel_geometry.phasenav import PhaseNavSolver

solver = PhaseNavSolver()
trace = solver.trace("concept1", "concept2")
for step in trace.steps:
    print(f"  {step.operator}: d={step.distance:.4f}")
```

---

## Package Structure

```
src/ciel_geometry/phasenav/
  pnv_runtime.py        core math — Collatz hash, phasors, Berry, trajectory
  phase_memory.py       PhaseMemoryHypercrystal — store, retrieve, M_score
  phase_gate_engine.py  PhaseGateEngine — text → {soul, ethics, phase_R}
  phase_voice.py        PhaseVoice — phase-grammar response generation
  solver.py             PhaseNavSolver — multi-step conceptual path tracing
  semantic_mesh.py      SemanticMesh — graph over phase space
  data/
    phase_crystal_36d.npy       35 836 × 36 float64 phase vectors
    phase_crystal_meta.jsonl    metadata per facet (text, t_score, kappa_i, ...)
```

---

## Submodule Docs

| Directory | Description |
|---|---|
| [solver/](solver/README.md) | PhaseNavSolver — conceptual path tracing |
| [kuramoto/](kuramoto/README.md) | Kuramoto synchronisation substrate |
| [concept_phases/](concept_phases/README.md) | Concept-to-phase operator mapping |
| [orbit_vectors/](orbit_vectors/README.md) | Orbit vector algebra |
| [encryption/](encryption/README.md) | Collatz hash & phase-space encoding |

---

## Key Constants

| Constant | Value | Meaning |
|---|---|---|
| `KAPPA` | 0.009210... | Semantic basin unit |
| `ETA_M_36D` | 36·κ ≈ 0.331 | Basin distinguishability |
| `BASIN_RADIUS` | 4·η_M ≈ 1.324 | Neighbourhood radius |
| `DEFAULT_MAX_DIST` | 1.45 | Max retrieval distance |
| `TAU` | 2π | Full circle |

---

## Citation

```
Lipa, A. (2026). PhaseNav: Collatz-seeded Oscillatory Semantic Phase Space
with Berry Holonomy Correction. NOEMA Project.
https://github.com/AdrianLipa90/noema-phasenav-core
```

---

## License

Copyright © 2026 Adrian Lipa. See [LICENSE](LICENSE).
