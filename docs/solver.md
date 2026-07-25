# solver — PhaseNavSolver

Multi-step conceptual path tracing through 36D phase space.

## Overview

`PhaseNavSolver` finds a sequence of operator edges connecting concept IDs through
holonomic phase-space transitions, using data written by `pnv_runtime._init()`.

## Constructor

```python
from ciel_geometry.phasenav import PhaseNavSolver, PhaseNavData

# Load from NOEMA data files (written by pnv_runtime on import)
solver = PhaseNavSolver.load()                        # default path /dev/shm/ciel_noema/phasenav
solver = PhaseNavSolver.load(base_path="/custom/path")

# Construct directly with pre-loaded data
data: PhaseNavData = ...
solver = PhaseNavSolver(data=data)
```

`PhaseNavSolver.load()` requires NOEMA data files at the base path — these are
written automatically when `pnv_runtime` is imported while NOEMA is running.

## trace()

```python
# trace() takes a list of card IDs (concept strings or glossary IDs)
trace = solver.trace(["curiosity", "understanding"])
trace = solver.trace(["concept_A", "concept_B", "concept_C"])

for step in trace.steps:
    print(f"{step.operator_hook:12s}  Δφ={step.phase_delta:.4f}  "
          f"viscosity={step.holonomic_viscosity:.4f}  "
          f"affordance={step.phasenav_affordance:.4f}")

print(f"total path integral: {trace.total_path_integral:.4f}")
print(f"mean viscosity:      {trace.mean_viscosity:.4f}")
print(f"mean affordance:     {trace.mean_affordance:.4f}")
```

## PhaseNavTrace

| Field | Type | Description |
|---|---|---|
| `steps` | `list[PhaseNavStep]` | Ordered operator steps |
| `total_path_integral` | `float` | Sum of step path integrals (viscosity × \|Δφ\|) |
| `mean_viscosity` | `float` | Mean holonomic viscosity across steps |
| `mean_affordance` | `float` | Mean phasenav affordance across steps |
| `card_sequence` | `list[str]` | Input card IDs |

## PhaseNavStep

| Field | Type | Description |
|---|---|---|
| `source_card_id` | `str` | Source concept ID |
| `target_card_id` | `str` | Target concept ID |
| `operator_hook` | `str` | Operator type (e.g. `differential`, `affect`, `orbit`) |
| `operator_card_id` | `str` | Operator card identifier |
| `phase_start` | `float` | Geometric phase at source (radians) |
| `phase_end` | `float` | Geometric phase at target (radians) |
| `phase_delta` | `float` | Phase change (phase_end − phase_start) |
| `holonomic_viscosity` | `float` | Holonomic viscosity of transition |
| `phasenav_affordance` | `float` | Transition affordance (1/(dist+0.01)) |
| `transition_lane` | `str` | Lane type (frequency, phase, mass) |
| `path_integral` | `float` | viscosity × \|Δφ\| |

## LIE4 Sector Weights

| Sector | Dimensions | Weight |
|---|---|---|
| Lorentz | φ[0–5] | ×2.0 |
| Intention | φ[6–11] | ×2.0 |
| Soul | φ[12] | ×1.5 |
| Rest | φ[13–35] | ×1.0 |
