# PhaseNav Sigma Identity Relations v1

Status: `CANON_CANDIDATE`  
Scope: only the `Sigma = 1/2` identity-cycle slice.

## 1. Principle

The relation layer does **not** hand-author PhaseNav geometry.

Only semantic obligations are declared:

- every declared object has one reciprocal semantic pair;
- the fixed identity axis `Sigma = 1/2` is explicitly self-dual;
- relation type and epistemic status are explicit;
- generated holonomy never promotes a claim automatically.

The native PhaseNav generator supplies the geometry:

`semantic ID -> CanonicalConceptState.from_id -> C^2048 -> T^36 -> EmergentGlossary.build`

The resulting generated edges carry weighted torus distance, Berry connection,
winding signature, coherence, holonomic viscosity, PhaseNav affordance and path
integral.

## 2. Declared pair registry

The current 1/2 slice declares the following reciprocal structures:

- `sigma <-> 1-sigma`;
- `0 <-> 1`;
- normalized cycle `q <-> angular phase phi`;
- `12 projective cycles <-> 6 spinor cycles`;
- `8 mixes <-> 3 flavours`;
- `ln(2) information quantum <-> 24*pi phase closure`;
- `information arithmetic <-> phase geometry`.

`Sigma = 1/2` is the only self-dual seed in this slice because

`1 - 1/2 = 1/2`.

Pairing is a semantic constraint.  It does **not** mean that every pair carries
a canonical Berry phase.

## 3. Generated semantic paths

`build_identity_relation_glossary()` generates canonical PhaseNav cards from
stable semantic IDs and runs the existing symmetric emergent-edge generator.

`generated_pair_paths()` then asks the generated graph for a path between each
declared pair.

For every resolved pair it records:

- generated card sequence;
- total PhaseNav path integral;
- accumulated Berry holonomy;
- relation type;
- declared epistemic status.

All generated Berry paths remain:

`epistemic_status = chyba`

and

`canon_allowed = false`.

This is deliberate. Semantic declaration and geometric proximity do not by
themselves establish a physical holonomy law.

## 4. Standard spinor holonomy kept separate

The standard spin-1/2 representative sign change is encoded independently from
generated semantic geometry.

For an integer number `n` of projective loops:

`gamma_spinor(n) = n*pi mod 2*pi`.

Hence

- one projective loop -> `pi` representative phase -> sign `-1`;
- two projective loops -> `0 mod 2*pi` -> sign `+1`.

This standard double-cover result is not inferred from the hashed/generated
semantic positions in `T^36`.

## 5. Relation to the 24-unit cross derivation

The exact arithmetic certificate remains

`8*3 = 12*2 = 6*4 = 24`.

The relation layer now makes the semantics around those counts explicit while
allowing PhaseNav to generate geometric paths among their canonical states.

After choosing the radian half-turn `pi`, the angular image is

`24*pi`,

and the existing runtime identity is recovered:

`kappa = ln(2)/(24*pi) = (ln(2)/12)/(2*pi)`.

## 6. W_[ij] boundary

TIR `W_[ij]` is referenced only as the broader holonomic relational object.
The generated PhaseNav `EmergentEdge` is **not** silently identified with
`W_[ij]`.

A future adapter may bind a validated PhaseNav path receipt to `W_[ij]`, but
that promotion requires an explicit bridge rule and provenance.

## 7. Implementation

Runtime module:

`src/ciel_geometry/phasenav/canon/identity_relations.py`

Tests:

`tests/test_identity_relations.py`

The module intentionally reuses:

- `CanonicalConceptState.from_id()` for native state generation;
- `Phase36Marker` for T^36 representation;
- `EmergentGlossary.build()` for generated semantic edges;
- `EmergentGlossary.trace()` for pair-path resolution.

No alternative PhaseNav graph engine is introduced.
