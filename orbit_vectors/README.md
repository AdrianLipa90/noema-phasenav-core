# orbit_vectors — Orbit Vector Algebra

36D orbital vector operations for PhaseNav state space navigation.

## Overview

Orbit vectors define the structure of semantic orbits — closed trajectories
in T³⁶ that correspond to stable conceptual attractors.

## Operations

```python
from ciel_geometry.phasenav.pnv_runtime import (
    M_36d_inner_product,
    M_36d_distance,
    M_36d_edge_weight,
    M_berry_holonomy_36d,
    M_36d_order_parameter,
)

v1 = M_sentence_phase("consciousness")
v2 = M_sentence_phase("awareness")

# Inner product (complex — encodes Berry phase)
z = M_36d_inner_product(v1, v2)
print(f"|⟨v1|v2⟩| = {abs(z):.4f}")

# LIE4 weighted distance
d = M_36d_distance(v1, v2)

# Kuramoto order parameter over a set of vectors
R, psi = M_36d_order_parameter([v1, v2])
print(f"coherence R = {R:.4f}, mean phase Ψ = {psi:.4f}")

# Berry holonomy over a closed loop
loop = [v1, v2, v1]
gamma = M_berry_holonomy_36d(loop)
```

## Edge Weight

Semantic edge weight between two concepts:

```
w(v1, v2) = exp(−d(v1, v2) / σ)
```

where σ = BASIN_RADIUS ≈ 1.324.
