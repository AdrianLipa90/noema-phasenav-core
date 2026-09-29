# PhaseNav orbital / scalar / tensor primitives v0.15

Status: **candidate computational layer**. `canon_allowed=false`.

This layer extends PhaseNav with finite, substrate-neutral primitives needed by
rank-revealing atomization, tensor-network contraction and orbital geometry. It
does not identify the carrier with a physical quantum processor, spacetime, a
measured gauge field, or a new physical law.

## 1. Scalar primitives

The singular spectrum is treated as a first-class invariant. `spectral_scalars`
returns numerical rank, right-nullity (`dim ker A`), spectral/Frobenius/nuclear norms, stable rank,
entropy rank, non-zero condition number and log singular volume.

The default rank threshold is not fitted:

\[
\tau = \epsilon_{mach}\,\max(m,n)\,\sigma_{max}.
\]

An explicit `rtol` or `atol` may override this policy, and the selected
threshold is always returned in the receipt.

These scalars distinguish several notions that must not be conflated:

- algebraic/numerical dimension (`rank`),
- concentration of spectral weight (`stable_rank`),
- effective information dimension (`entropy_rank`),
- invertibility/conditioning (`condition_number_nonzero`).

## 2. Orbital primitives

### Complex-projective orbit

`projective_orbit(a,b)` computes normalized overlap, fidelity, Fubini--Study
distance and open-path Pancharatnam phase. The distance and fidelity are
projective quantities; the open-path phase is common-gauge invariant but is not
claimed to be invariant under independent endpoint gauges.

### Exterior wedge and Pluecker simplicity

`wedge2_4d` builds the canonical six-component exterior product directly from two 4D vectors.

### Pluecker simplicity

For the ordered 4D bivector basis

\[
(01,02,03,23,31,12),
\]

`plucker_simplicity` evaluates the decomposability relation

\[
p_{01}p_{23}+p_{02}p_{31}+p_{03}p_{12}=0.
\]

This gives PhaseNav an explicit gate between a generic six-component bivector
and a simple wedge of two vectors. When no tolerance is supplied, the gate uses
machine precision scaled by the six-coordinate carrier rather than a fitted cutoff.

### Hodge sectors

`hodge_split_euclidean_4d` computes

\[
B_\pm=\frac12(B\pm *B),
\]

with explicit reconstruction residual. This exposes the `3+3` self-dual and
anti-self-dual sectors without promoting them to a physical field.

### Principal angles and Grassmann geometry

`principal_angles` compares orbital subspaces through the singular values of
`Q_A^* Q_B`, giving a basis-independent relation between finite subspaces.
`grassmann_distance` adds chordal, geodesic and projector-Frobenius distances. For unequal-rank subspaces, unmatched dimensions are explicitly extended by principal angle `pi/2`, and the dimension gap is recorded.

### Bargmann triangle

`bargmann_triangle` evaluates the closed three-point product

\[
\langle a|b\rangle\langle b|c\rangle\langle c|a\rangle,
\]

returning its gauge-invariant phase, strength and Fubini--Study perimeter. This
provides a closed projective holonomy primitive distinct from the open-path
Pancharatnam phase.

## 3. Tensor primitives

Implemented primitives:

- mode unfolding/folding;
- n-mode matrix product;
- Schmidt decomposition across an arbitrary declared tensor-product cut;
- Schmidt-spectrum scalar information: purity, participation ratio, von Neumann, Renyi-2 and min entropy;
- operator-Schmidt decomposition of bipartite operators;
- numerically exact-to-declared-threshold or explicitly truncated TT-SVD / MPS factorization;
- TT/MPS reconstruction;
- Tucker/HOSVD factorization and reconstruction with per-mode ranks and a declared HOSVD error upper bound;
- rank-revealing compression of many boundary-state branches;
- streaming incremental boundary basis;
- branch/rank capacity bounds from operator-Schmidt ranks.

A truncated factorization is never reported as exact. Receipts carry retained
rank and discarded norm.

## 4. Atomization interface

For a boundary crossed by bipartite operators of Schmidt ranks `r_i`, naive
branching has

\[
\log_2 N_{branches}=\sum_i\log_2 r_i.
\]

The boundary Schmidt rank is additionally capped by the smaller Hilbert space:

\[
\log_2\chi\le
\min\left(\sum_i\log_2r_i,\log_2 d_L,\log_2 d_R\right).
\]

`boundary_capacity` computes this bound without enumerating branches.

`compress_boundary_states` addresses the more important question: how many
**linearly independent** boundary states remain. It performs rank-revealing SVD
and returns a basis plus coefficients. Therefore PhaseNav no longer needs to
confuse duplicate detection with linear dependence.

`IncrementalBoundaryBasis` supplies the streaming form: each atom can be
hydrated, projected against the current orthonormal boundary basis, accepted as
a new direction only when its residual exceeds the declared numerical
threshold, and then released.

This directly supports RAM-bounded / disk-backed contraction planning.

## 5. Exact two-qubit control

The two-qubit CZ operator has operator-Schmidt rank 2. The v0.15 tests verify
this from the generic decomposition routine and reconstruct CZ numerically.
SWAP is independently checked at operator-Schmidt rank 4.

These are structural operator facts, not a statement that a deep random
circuit remains low-rank.

## 6. GREMLIN alignment

The rank logic is deliberately compatible with the existing GREMLIN
identifiability discipline: rank, nullity, smallest retained singular value and
conditioning are separate observables. A formally full-rank object may still be
ill-conditioned; a lower-rank object may still be exactly representable in its
minimal subspace.

## 7. Next primitive queue

The next useful additions are deliberately separated from this implementation:

1. symmetry-sector / block-sparse tensor carriers with explicit conserved
   charges;
2. exact Clifford/stabilizer and matchgate/free-fermion detectors before dense
   hydration;
3. phase-polynomial and ZX-style exact rewrite gates for circuit DAGs;
4. MPO/PEPS boundary carriers and canonicalization;
5. Tucker/HOSVD and higher-order singular spectra;
6. hypergraph separators, treewidth/pathwidth receipts and contraction-order
   lower/upper bounds;
7. Pfaffian/determinantal fast paths for antisymmetric/Gaussian sectors;
8. automatic mixed-representation routing: dense, sparse, MPS, stabilizer,
   Gaussian or tensor-sliced per atom;
9. content-addressed disk shards with deterministic recombination receipts;
10. error-budget algebra that composes truncation, floating-point and sampling
    error separately.

The gate for every future primitive is the same: exact mathematical identity
or explicitly declared approximation, provenance, a measurable residual and no
silent physical promotion.