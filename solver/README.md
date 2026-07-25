# solver — PhaseNavSolver

Multi-step conceptual path tracing through 36D phase space.

## Overview

`PhaseNavSolver` finds a sequence of operators transforming a source concept
vector into a target concept vector, stepping through intermediate states.

## API

```python
from ciel_geometry.phasenav import PhaseNavSolver, PhaseNavTrace, PhaseNavStep

solver = PhaseNavSolver()
trace = solver.trace("source concept", "target concept")

for step in trace.steps:
    print(f"{step.operator:12s}  d={step.distance:.4f}  soul={step.soul:.3f}")

print(f"total distance: {trace.total_distance:.4f}")
print(f"converged:      {trace.converged}")
```

## PhaseNavTrace

| Field | Type | Description |
|---|---|---|
| `steps` | `list[PhaseNavStep]` | Ordered operator steps |
| `total_distance` | `float` | Sum of step distances |
| `converged` | `bool` | Reached target within threshold |
| `source_vec` | `list[float]` | Initial 36D vector |
| `target_vec` | `list[float]` | Target 36D vector |

## PhaseNavStep

| Field | Type | Description |
|---|---|---|
| `operator` | `str` | Operator name (INTENTION, SOUL, ...) |
| `distance` | `float` | Angular distance after step |
| `soul` | `float` | Soul invariant |
| `phase_R` | `float` | Phase coherence |

## Operators

| Operator | Dimensions | Weight |
|---|---|---|
| LORENTZ | φ[0–5] | ×2.0 |
| INTENTION | φ[6–11] | ×2.0 |
| SOUL | φ[12] | ×1.5 |
| IDENTITY | all | ×1.0 |
