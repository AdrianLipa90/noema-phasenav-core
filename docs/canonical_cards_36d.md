# Canonical PhaseNav cards and emergent 36D glossary paths

## Status

This layer canonicalizes **schema and identity**, not truth by proximity.
Source records are never rewritten. Generated outputs are additive sidecars.

Two independent markers are defined:

- `PHASENAV-36D/1` — marker of one card's 36-dimensional phase state;
- `PHASENAV-36D-PATH/1` — marker of a directed relation between two cards.

An emergent relation is always emitted as:

```json
{
  "epistemic_status": "chyba",
  "canon_allowed": false,
  "provenance": {
    "source_binding": "INFERENCE",
    "canon_rule": "manual-review-required"
  }
}
```

Geometric proximity is evidence for exploration, not sufficient evidence for
canonical semantics.

## Why a sidecar

The recovered stack contains multiple card ontologies:

1. PhaseNav concept cards;
2. CIELingo runtime word cards;
3. NOEMA relational cards;
4. lingophysics operator cards;
5. 36D crystal facets.

They cannot be flattened safely into one source format. The canonical view
therefore preserves `card_type`, original identifiers, provenance, aliases,
conflicts and epistemic state.

The source files remain authoritative for their own ontology. The sidecar is a
common navigation surface.

## Canonical card

Minimum stable fields:

```json
{
  "schema": "PHASENAV-CARD/1",
  "card_id": "concept:031",
  "card_type": "operator",
  "label": "Consciousness",
  "phase_36d": ["36 finite phases"],
  "phase36_marker": {
    "schema": "PHASENAV-36D/1",
    "dimension": 36,
    "encoding": "metatime-v36",
    "fingerprint": "p36:...",
    "order_parameter": 0.0,
    "mean_phase_rad": 0.0,
    "sector_order": {},
    "sector_phase_rad": {}
  },
  "epistemic_status": "candidate",
  "canon_allowed": false,
  "provenance": []
}
```

The fingerprint is a technical integrity identifier. It is not semantic proof,
a consent token or a NOEMA `SOURCE` seal.

## Sector geometry

The marker preserves the established LIE4 partition:

| Sector | Dimensions | Weight |
|---|---:|---:|
| Lorentz | `φ[0:6]` | 2.0 |
| Intention | `φ[6:12]` | 2.0 |
| Soul | `φ[12]` | 1.5 |
| Semantic remainder | `φ[13:36]` | 1.0 |

For two cards with phase vectors `φ_a` and `φ_b`, the wrapped displacement is

\[
\Delta\phi_j = ((\phi_{b,j}-\phi_{a,j}+\pi)\bmod 2\pi)-\pi.
\]

The weighted torus distance is

\[
d_{36}(a,b)=\frac{\sum_j w_j|\Delta\phi_j|}{\sum_j w_j}.
\]

The marker also records sector distances, Pancharatnam/Berry connection,
coherence and a per-dimension winding signature.

## Emergent edges

`EmergentGlossary.build()` creates a deterministic k-nearest-neighbour graph in
the real phasor embedding `(cos φ, sin φ) ∈ R^72`, then evaluates exact weighted
torus distance in 36D.

For each edge:

\[
A_{ab}=\exp[-d_{36}(a,b)/\eta_M],
\qquad
\eta_M=36\frac{\ln2}{24\pi},
\]

\[
\nu_{ab}=\frac{d_{36}(a,b)}{d_{36}(a,b)+\eta_M},
\]

\[
S_{ab}=\frac{\nu_{ab}d_{36}(a,b)}{A_{ab}}.
\]

Here `A` is PhaseNav affordance, `ν` is holonomic viscosity and `S` is the path
cost used by Dijkstra tracing. These formulas rank paths; they do not promote
paths to canon.

## Target-aware solver correction

Legacy holonomic edge records contain only a source concept. They do not contain
a destination, even though the producing runtime internally computed one.
Treating the best source edge as an arbitrary requested source→target edge was
therefore invalid.

The updated loader:

- indexes explicit `(src, dst)` pairs;
- retains targetless legacy records for audit;
- loads `PHASENAV_EMERGENT_GLOSSARY_36D.noema.jsonl` when present.

The updated solver:

- uses an exact target edge;
- optionally falls back to an attached `EmergentGlossary`;
- never treats a targetless legacy edge as proof of an arbitrary transition;
- propagates `epistemic_status`, `canon_allowed` and the 36D path marker.

## Generation

Dry-run is the default:

```bash
python scripts/canonize_cards_36d.py \
  --runtime-dir runtime/phasenav \
  --glossary src/ciel_geometry/phasenav/glossary.pnv
```

Create sidecars explicitly:

```bash
python scripts/canonize_cards_36d.py \
  --runtime-dir runtime/phasenav \
  --glossary src/ciel_geometry/phasenav/glossary.pnv \
  --output build/phasenav_36d_cards \
  --write
```

Optional crystal-facet views can be included without modifying the crystal:

```bash
python scripts/canonize_cards_36d.py \
  --runtime-dir runtime/phasenav \
  --glossary src/ciel_geometry/phasenav/glossary.pnv \
  --include-crystal \
  --crystal-vectors src/ciel_geometry/phasenav/data/phase_crystal_36d.npy \
  --crystal-metadata src/ciel_geometry/phasenav/data/phase_crystal_meta.jsonl \
  --write
```

Generated files:

- `PHASENAV_CANONICAL_CARDS_36D.noema.jsonl`;
- `PHASENAV_EMERGENT_GLOSSARY_36D.noema.jsonl`;
- `PHASENAV_CANONICALIZATION_REPORT.json`;
- `PHASENAV_CANONICALIZATION_MANIFEST.json`.

## Canonization boundary

A card can have a canonical ID and schema while remaining `candidate` or
`chyba`. A generated path remains `chyba` until an explicit source, validation
record or Operator decision promotes it. No automatic graph operation may set
`canon_allowed=true`.
