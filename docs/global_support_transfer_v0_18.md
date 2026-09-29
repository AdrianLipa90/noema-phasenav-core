# PhaseNav global support-transfer audit v0.18

Status: `CANDIDATE_ONLY`  
`canon_allowed=false`

This layer lifts the exact local Haar-SU(2)+CZ support transition from v0.17 to a full labelled support process. It is a second-moment/operator-support model. It is **not** an amplitude simulator and it is **not** XEB.

## 1. Exact local transfer

In basis `(00,10,01,11)` the local channel is

```text
[[1,   0,   0,   0],
 [0, 1/3,   0, 2/9],
 [0,   0, 1/3, 2/9],
 [0, 2/3, 2/3, 5/9]]
```

No fitted retention coefficient is used.

## 2. Exact small-system controls

`exact_dense_support` provides an exact dense control up to 20 support bits. The labelled MPS implementation is cross-checked against the dense control, including variable reordering by explicit SWAP maps.

Focused validation: **9 passed** across the bit-MPS and row-block suites. `py_compile`: **PASS**.

## 3. Full 61-site IBM topology: stochastic support propagation

Using the released ABCD matchings and one initially active central/high-degree support bit, 100,000 independent exact local-transition trajectories reach depth 36 in about 3.1 s on the current ordinary host. Final support weight is

```text
mean = 45.64694
standard error = 0.01085
```

The mean active fraction is therefore about 0.748. This is an operator-support statistic only. It must not be described as one million quantum output samples, circuit fidelity, XEB, or amplitude simulation.

## 4. Bit-MPS rank-growth audit

The numerically rank-revealing MPS uses the declared machine-epsilon rule. Under a bond cap of 1024 it reaches 10 complete matching layers and 276 pair updates before the next factorization requires bond rank 1323. The peak retained bond before that point is 884. Probability normalization remains `0.9999999999999932`; discarded numerical-null L2 weight accumulated before the resource stop is about `7.27e-12`.

This is a negative result for naive one-dimensional atomization: the support process develops substantial correlation rank long before depth 36.

## 5. Row-block atomization

A second representation groups the physical 8x8-minus-3 device into eight row atoms with local bit counts

```text
7, 8, 8, 8, 7, 7, 8, 8
```

Horizontal interactions are internal to an atom; vertical interactions couple adjacent row atoms. This removes variable SWAP routing entirely.

Under a conservative SVD-matrix budget of 25,000,000 float64 elements, the exact row-block route completes seven matching layers with peak row-bond 32. The next required factorization contains 41,943,040 matrix elements (about 320 MiB raw before SVD workspaces), so the run fails closed rather than allocating an uncontrolled workspace.

This exposes the actual trade: row atomization suppresses bond/reordering overhead but moves the cost into the local boundary factorization.

## 6. Consequence for the next planner

Neither "one bit per MPS site" nor "one physical row per MPS site" is uniformly adequate. The next PhaseNav primitive should therefore be an adaptive separator tree:

1. choose graph separators from the current spacetime/frontier graph;
2. group only until local factorization cost reaches a declared budget;
3. expose boundary operator-Schmidt capacity before materialization;
4. use Schur/Woodbury updates when interiors change locally;
5. use block-sparse/Clifford/phase-polynomial routes inside each atom;
6. spill independent separator slices through the existing content-addressed shard plan.

The objective is not a fixed nominal qubit limit. It is to minimize peak boundary rank times local factorization dimension under explicit RAM/I/O budgets.

## 7. Evidence boundary

This audit does **not** establish a classical solution of the IBM 61q d=36 amplitude-sampling problem. It does establish that the exact local second-moment dynamics can be lifted to the full released topology, and it identifies where two natural exact tensorizations hit resource growth.