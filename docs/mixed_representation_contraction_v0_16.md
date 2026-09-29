# PhaseNav mixed-representation contraction primitives v0.16

Status: `CANDIDATE_ONLY`  
`canon_allowed=false`

This layer extends the v0.15 orbital/scalar/tensor primitives with exact typed
fast paths and an explicit contraction-planning surface.  It is designed for
the current atomized-circuit programme: keep local structure in its native
representation for as long as possible, expose every numerical threshold, and
fall back to generic tensors only when no certified structure remains.

## 1. Quadratic computational-basis phase atoms

`QuadraticPhasePolynomial` represents

\[
\phi(x)=\phi_0+\sum_i a_i x_i+\sum_{i<j}b_{ij}x_ix_j,
\qquad x_i\in\{0,1\}.
\]

The representation is exact for:

- CZ layers: `b_ij = pi`;
- local `RZ(theta)`: global `-theta/2` plus linear `theta*x_i`;
- compositions of such commuting diagonal atoms;
- exact restriction/slicing of any subset of bits.

No diagonal layer is expanded to a `2^n` vector.

For the released 61-qubit RCS topology, the ABCD matching sizes are

\[
29,\ 22,\ 29,\ 22.
\]

At depth 36 this gives 918 CZ gates, but only 36 top-level quadratic phase
atoms, with at most 29 quadratic terms per atom.  This is an IR/representation
compression; the 918 pair interactions remain present as polynomial terms and
are not claimed to have disappeared computationally.

## 2. Abelian block-sparse sectors

`AbelianChargeRule` and `BlockSparseTensor` provide a finite exact sectoring
surface for additive charges, either over `Z` or `Z_n`.

A dense tensor may be converted only when every forbidden sector is zero within
the explicitly supplied `zero_atol`.  Otherwise conversion fails closed.

This matters for mixed routing: symmetry is used only when actually present.
Generic Haar-SU(2) layers do not receive a symmetry fast path merely because
adjacent CZ layers preserve computational-basis parity.

## 3. Gate-family fast-path classification

`clifford_unitary` checks the conjugation of Pauli generators and records the
largest normalized Pauli residual.

`matchgate_unitary` checks the two-qubit parity-preserving block pattern and the
equal-determinant matchgate condition.

Controls in the v0.16 suite include:

- CZ: Clifford = PASS;
- CNOT: Clifford = PASS;
- H: Clifford = PASS;
- generic deterministic SU(2): Clifford = FAIL;
- fSWAP: matchgate = PASS;
- CZ: matchgate = FAIL.

These are routing predicates, not physical claims.

## 4. Polar and Schur boundary reduction

`polar_decompose` separates

\[
A = U P
\]

into an orbital/unitary factor and a positive singular-weight factor.  This
allows PhaseNav to keep phase/orbit transport separate from scalar stretching.

`schur_complement` eliminates an interior block,

\[
M=
\begin{pmatrix}
A&B\\
C&D
\end{pmatrix},
\qquad
M_{\rm eff}=A-BD^{-1}C,
\]

with a fail-closed condition-number gate.  A pseudoinverse is never silently
substituted.  This is the finite linear-algebra primitive for converting an
atom with internal degrees of freedom into an effective boundary object.

## 5. Typed representation router

`route_atom` records all policy thresholds and chooses among:

- `QUADRATIC_PHASE_POLYNOMIAL`;
- `STABILIZER`;
- `FERMIONIC_GAUSSIAN`;
- `MPS_TT`;
- `TUCKER_HOSVD`;
- `DENSE`;
- `TENSOR_NETWORK`.

`BLOCK_SPARSE_SYMMETRY` is an overlay rather than a mutually exclusive
representation.

The router is deterministic and does not infer unmeasured low rank.  MPS and
Tucker routes require supplied/measured rank information.

## 6. Tensor-network contraction planner

`TensorNetworkSpec` describes a pairwise Einstein network whose index
multiplicity is at most two.

`greedy_contraction_plan` returns an explicit contraction order with:

- peak element count;
- peak `log2(elements)`;
- peak byte estimate;
- total arithmetic estimate;
- final open indices;
- outer-product count.

The result is an upper bound for that explicit order.  It is not represented as
a globally optimal treewidth proof.

`slice_to_memory_budget` trades memory for exact external slicing.  Every
sliced dimension multiplies the slice count and the total-work estimate.

`plan_disk_shards` converts the slice plan into a content-addressed cold-storage
plan with an explicit maximum live-shard count for a RAM budget.

## 7. Graph-width diagnostics

Two graph elimination diagnostics are exposed:

- `min_fill_graph_width` — stronger small/medium heuristic;
- `min_degree_graph_width` — scalable deterministic upper bound.

For the released 61-qubit IBM interaction graph, the min-fill interaction-graph
upper width is 7.  For a full 10x10 nearest-neighbour grid it is 13 under this
heuristic.

These numbers describe the *static interaction graph only*.  They are not the
spacetime tensor-network contraction width, not the paper's width 64, and not a
replacement for `C_amp`.

## 8. RCS mixed-representation probe

The focused probe records:

```text
matching sizes        = 29, 22, 29, 22
d=36 CZ total         = 918
quadratic phase atoms = 36
max terms / phase atom= 29
CZ Clifford           = true
CZ matchgate          = false
generic SU(2) Clifford= false
```

The immediate consequence is architectural rather than a speedup claim:
the RCS should be represented as alternating local non-Clifford SU(2) atoms and
compact diagonal quadratic-phase layers, instead of flattening every layer into
one generic dense representation.

## 9. Validation

Focused local validation:

```text
v0.15 orbital/scalar/tensor suite: 20 passed
v0.16 mixed-representation suite: 23 passed
py_compile: PASS
```

Full-repository pytest is not claimed in this session.

## 10. Epistemic boundary

This layer establishes finite software/mathematical primitives only.  It does
not establish:

- a physical QPU;
- generic classical simulation of arbitrary 100-qubit circuits in small memory;
- a reduction of the IBM d=36 contraction width to the static graph width;
- quantum advantage or its absence;
- physical spacetime, gauge-field, or thermodynamic identification.

Promotion to canon requires separate evidence and authority.