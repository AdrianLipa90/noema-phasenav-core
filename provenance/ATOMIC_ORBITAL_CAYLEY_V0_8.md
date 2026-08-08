# Atomic Orbital Cayley Adapter v0.8 — validation receipt

## Status

`PASS_FOCUSED / FULL_CI_INFRA_BLOCKED / NOT_PROMOTED`

This receipt records the validation boundary for the PhaseNav atomic-orbital
Cayley adapter. It does **not** promote a physical theory and it does not alter
`canon/CURRENT`.

## Implementation anchor

- repository: `AdrianLipa90/noema-phasenav-core`
- branch: `canon/atomic-orbital-cayley-v0.8`
- implementation head before this receipt: `46a95e4db78234904e8f562718d834d10ec7a435`
- base master: `b3f31a0cad78f6c7c9e908434b98d5e3132b2a0a`
- pull request: `#13`

## Implemented invariants

1. **Coulomb address**
   - `k = n`
   - preserves `l`, `m` and spin degeneracy in the ideal non-relativistic Coulomb baseline.

2. **Central-potential address**
   - `k = n(n-1)/2 + l + 1`
   - preserves magnetic and spin degeneracy.

3. **Fully resolved address**
   - contiguous spin-orbital indexing is available only for explicitly symmetry-broken dynamics.
   - it is not the default Coulomb address.

4. **Magnetic phase winding**
   - `w_phi = m`
   - magnetic winding remains a phase/orbital label rather than a semantic-mass index.

5. **Cayley/Poincare radial adapter**
   - `x = r/r_ref`
   - `rho = x/(1+x)`
   - `u = 2*rho - 1`
   - anchors: `0 -> 0`, `1 -> 1/2`, `infinity -> 1`.

6. **Orbital reciprocal involution**
   - `(rho, phi) -> (1-rho, -phi)`
   - applying the transform twice returns the original coordinate.

7. **Fixed-Z hydrogenic principal lattice**
   - with `r_ref = r_1`, `rho_n = n^2/(n^2+1)`
   - inverse gate: `n = sqrt(rho/(1-rho))`.

8. **Variable separation**
   - `semantic_mass` is retained from the canonical PhaseNav numeric state.
   - physical radial ratios (`r/r_1`, `|E|/|E_1|`, `T/T_1`) are stored separately.
   - atomic principal shell is not identified with a generic semantic/orbital shell.

## Focused numerical validation

The precursor focused validation executed in the session before repository mutation
and produced PASS for:

### Quantum-address/runtime checks

- numeric-`k` Kuramoto order parameter invariance:
  - `R_min = 0.22852419636154572`
  - `R_max = 0.22852419636154580`
  - span `8.326672684688674e-17`
- numeric semantic-mass affine-in-`k` second-difference residual:
  - `4.163336342344337e-17`
- Coulomb degeneracy preservation: PASS
- `(n,l)` central degeneracy preservation: PASS
- full spin-orbital uniqueness/contiguity for `n=1..4`: PASS (`60` states)

### Cayley radial checks

- inversion duality max error: `1.1102230246251565e-16` — PASS
- Cayley ratio round-trip max relative error: `4.987744614481926e-11` — PASS
- orbital involution max error: `5.551115123125783e-17` — PASS
- hydrogenic `n` recovery max error: `1.4210854715202004e-14` — PASS
- hydrogenic radius-ratio max error: `2.2737367544323206e-13` — PASS
- hydrogenic energy-ratio max error: `5.551115123125783e-17` — PASS
- hydrogenic period-ratio max error: `2.7284841053187847e-12` — PASS

The repository additionally contains `tests/test_atomic_orbital_cayley.py` covering
these invariants at package level.

## GitHub Actions status

For implementation head `46a95e4db78234904e8f562718d834d10ec7a435`:

- workflow `Tests`, run `31251692690`: `failure`
- workflow `PhaseNav canon validation`, run `31251692661`: `failure`

Inspection of the jobs returned **no executed steps** (`steps=[]`). The failure therefore
occurred before repository test commands ran. This matches the already documented
GitHub Actions infrastructure condition in earlier PhaseNav canon work (PR #11).

Accordingly this receipt does **not** reinterpret the workflow result as either a code
PASS or code FAIL. Full CI remains `INFRA_BLOCKED` until jobs actually execute.

## Epistemic boundary

### Implemented

- atomic address adapter
- Cayley radial coordinate adapter
- orbital inversion view
- public PhaseNav/canon exports
- focused pytest specification
- canon manifest entry

### Validated mathematics

- address combinatorics
- inversion involution
- radial compactification identities
- fixed-Z hydrogenic dimensionless ratios
- separation of magnetic winding from semantic address in Coulomb mode

### Candidate

- using `r_ref = r_1` as the native PhaseNav atomic reference radius
- using this adapter as the atomic radial projection of the broader TIR/PhaseNav model

### Not promoted / still open

- physical identification of `semantic_mass` with inertial or gravitational mass
- derivation of the physical central coupling from TIR first principles
- many-electron and multi-centre extension
- empirical/SI calibration
- global NOEMA/PhaseNav SoT promotion

## Canon rule

`canon/CURRENT` remains `1.3.0`.

The adapter is registered only as:

`CANON_CANDIDATE / scientific_promotion = NOT_PERFORMED`.
