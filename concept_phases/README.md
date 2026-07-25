# concept_phases — Concept-to-Phase Operator Mapping

Maps symbolic concepts and operators to 36D phase vectors.

## Overview

Each concept in the PhaseNav vocabulary has a canonical phase vector computed
from its semantic mass and operator type.

```python
from ciel_geometry.phasenav.pnv_runtime import concept_to_operator, _phase36_from_id

# Get phase vector for a concept ID
v = _phase36_from_id("INTENTION")
print(len(v))  # 36

# Map concept name to operator
op = concept_to_operator("curiosity")
print(op)  # {"operator": "INTENTION", "weight": 0.87}
```

## Phase Grammar

PhaseNav includes a grammar over operator types (`PHASE_GRAMMAR`).
Each operator has a gram type defining how it composes with others:

| Gram Type | Behaviour |
|---|---|
| INITIATOR | starts a trajectory |
| TRANSFORMER | modifies current state |
| TERMINATOR | closes a trajectory |
| BRIDGE | connects two sub-trajectories |

## Operator Composition

```python
from ciel_geometry.phasenav.pnv_runtime import M_grammar_compose

v_composed = M_grammar_compose(v1, v2, op_type="BRIDGE")
```
