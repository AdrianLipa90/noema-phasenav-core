# PhaseNav adaptive separator tree v0.19

Status: `CANDIDATE_ONLY`  
`canon_allowed=false`

This layer adds exact fixed-cardinality graph separators for atomized PhaseNav planning. It exists because v0.18 showed that fixed one-bit MPS and fixed physical-row atoms move the bottleneck rather than remove it.

## Exact cut primitive

`minimum_fixed_size_cut` solves

\[
\min \sum_{e=(u,v)} w_e y_e
\]

with binary vertex-side variables and constraints forcing

\[
y_e \ge |x_u-x_v|,
\qquad
\sum_v x_v=k.
\]

The implementation uses SciPy/HiGHS MILP. A returned `solver_optimal=true` means optimality for the stated fixed cardinality and supplied edge weights, not a heuristic cut.

## Dynamic edge weights

For a circuit schedule, one edge use contributes

\[
\log_2 r_{
m op}
\]

where \(r_{
m op}\) is the operator-Schmidt rank. For CZ, \(r_{
m op}=2\), so each crossing use contributes one capacity bit. At depth 36 under ABCD each released IBM interaction edge is used nine times.

This is an upper-capacity accounting quantity. It is not the actual Schmidt rank and not the paper's spacetime contraction width.

## IBM 61-site exact near-balanced cuts

The exact MILP results for target sizes 27--30 are:

| split | static cut | d36 dynamic cut capacity | imbalance |
|---|---:|---:|---:|
| 27 / 34 | 6 | 54 bits | 7 |
| 28 / 33 | 7 | 63 bits | 5 |
| 29 / 32 | 7 | 63 bits | 3 |
| 30 / 31 | 7 | 63 bits | 1 |

The Pareto frontier in `(cut capacity, imbalance)` is therefore:

- `27 / 34` with six cut edges;
- `30 / 31` with seven cut edges.

The six-edge 27/34 cut is

```text
(27,34), (28,35), (29,36), (30,37), (32,38), (33,39)
```

and is certified optimal for fixed side size 27. This independently reproduces the six-edge balanced-ish cut discussed in the RCS analysis.

## Recursive atom trees

Using exact half-cuts below each Pareto root and stopping at atoms of at most eight vertices gives two explicit policies.

Low-root-cut policy (`27/34`):

```text
leaves            10
max leaf size       8
max tree depth       4
max static cut       6
max d36 cut weight  54
sum static cuts     36
sum d36 weights    324
```

Near-balanced-root policy (`30/31`):

```text
leaves             8
max leaf size       8
max tree depth      3
max static cut      7
max d36 cut weight 63
sum static cuts    29
sum d36 weights   261
```

Neither dominates the other: the first minimizes the worst root separator, while the second produces a shallower tree with fewer total separator edges. PhaseNav therefore keeps both as Pareto alternatives rather than hiding the trade behind an arbitrary scalar score.

## Next execution layer

The next step is to bind separator-tree leaves to the v0.16 mixed-representation router and v0.18 support-transfer engine. Each leaf can independently choose phase-polynomial, stabilizer, block-sparse, MPS/Tucker or generic tensor representation; separator bonds carry only the typed boundary object.

## Evidence boundary

These exact graph cuts do not establish a reduction of the IBM amplitude-sampling `C_amp`, because a static interaction separator is not the full spacetime tensor network. They provide a certified atomization scaffold on which that contraction can be built and measured.