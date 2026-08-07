# CIEL / PhaseNav geometry dependencies

This package is the low-level dependency layer for geometry-first PhaseNav vectorization.

Dependency direction:

```text
IdentityAxis / oriented displacement
CycleCoordinate R/Z / winding
PhaseCrystal (R/Z)^N
Typed RelationGraph + optional normalized holonomy turns
                 |
                 v
        VectorizationOperator
                 |
                 v
     PhaseNav semantic/runtime layers
```

## Contract

1. **Zero is geometric.** A zero component means no displacement from the selected axis or no tangent displacement between phase coordinates.
2. **Sign is orientation.** Negative/positive components are opposite orientations of a centered or shortest-path tangent coordinate.
3. **Cycles precede radians.** Primitive phase coordinates are normalized turns in `R/Z`; conversion to radians is an explicit downstream `PhaseClosure` representation.
4. **Holonomy belongs to eligible paths.** A semantic pair does not receive a phase unless a connection/path law exists.
5. **Vectorization consumes geometry.** Opaque identifiers are not accepted as evidence-bearing vector coordinates by this layer.
6. **Epistemic status is carried with relations.** `EXACT`, `STANDARD`, `MODEL`, and `OPEN` edges are not interchangeable.
7. **Generated geometry is diagnostic until provenanced.** PhaseNav-generated candidate paths cannot promote semantic truth on their own.

The first canonical consumer is the `sigma=1/2` identity-axis slice.  Broader CIEL/PhaseNav operators can depend on these primitives without redefining their algebra.
