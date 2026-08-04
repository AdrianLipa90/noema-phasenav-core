# PhaseNav Operator Calculus Canon v1

## Scope

This document defines the canonical operator layer acting on the same
\(T^{36}\) positions and tangent spaces used by the observer-to-generation
runtime. It does not introduce another state representation.

The operator layer contains:

- semantic CRC;
- semantic diff;
- interference merge;
- bounded phase compression;
- gauge transformations;
- trajectory curvature;
- linear operator composition and commutators;
- projection of forbidden tangent directions;
- path-specific holonomy cache;
- semantic scheduling.

Natural-language generation remains outside this module and belongs to
CIELingo.

## 1. Semantic CRC

For state \(\phi\in T^{36}\) and canonical metadata \(m\), define

\[
\operatorname{CRC}_\Psi(\phi,m)
=
\operatorname{SHA256}
\left(
\operatorname{canon}(\phi,m)
\right).
\]

The phase coordinates are serialized in fixed order with bounded decimal
precision. The CRC is not a semantic metric; it is an identity and provenance
receipt for exact computational states.

## 2. Semantic diff

For two phase positions \(\phi_A,\phi_B\), the signed shortest tangent
displacement is

\[
\Delta_i
=
\operatorname{wrap}_{[-\pi,\pi)}
\left(
\phi_{B,i}-\phi_{A,i}
\right).
\]

The semantic distance is

\[
d_\Psi(A,B)
=
\sqrt{
\frac1{36}
\sum_{i=1}^{36}\Delta_i^2
}.
\]

The diff record also carries:

- maximum absolute component;
- coherence on both sides;
- coherence change;
- CRC of both states.

This makes textual, structural and runtime comparisons reducible to the same
phase-state comparison after encoding.

## 3. Interference merge

For states \(\phi_k\) with non-negative weights \(w_k\),

\[
z_i
=
\sum_k w_k e^{i\phi_{k,i}},
\]

\[
\phi_{\mathrm{merge},i}
=
\arg z_i.
\]

The normalized resultant amplitude is

\[
r_i
=
\frac{|z_i|}{\sum_kw_k}.
\]

The mean cancellation coefficient is

\[
C
=
1-\frac1{36}\sum_i r_i.
\]

Equal states have \(C=0\). Opposed contributions increase \(C\), making conflict
an explicit interference observable instead of a line-based merge failure.

## 4. Phase compression

Each phase coordinate can be quantized to \(b\in\{8,16,32\}\) bits:

\[
q_i
=
\operatorname{round}
\left(
\frac{\phi_i}{2\pi}(2^b-1)
\right).
\]

Reconstruction is

\[
\tilde\phi_i
=
\frac{q_i}{2^b-1}2\pi.
\]

The maximum scalar quantization error is

\[
\epsilon_{\max}
=
\frac{2\pi}{2(2^b-1)}.
\]

The binary payload carries SHA-256 integrity. Compression is therefore bounded,
portable and independently verifiable.

## 5. Gauge transform

A gauge transform is

\[
G_\alpha(\phi)
=
(\phi+\alpha)\bmod 2\pi,
\]

where \(\alpha\) may be global or dimension-wise.

For a common gauge shift,

\[
d_\Psi(G_\alpha\phi_A,G_\alpha\phi_B)
=
d_\Psi(\phi_A,\phi_B).
\]

This is a regression invariant.

## 6. Trajectory curvature

For trajectory \(\gamma=(\phi_0,\ldots,\phi_n)\), define tangent increments

\[
v_k
=
\operatorname{wrap}(\phi_{k+1}-\phi_k).
\]

For non-zero adjacent tangents, the turning angle is

\[
\vartheta_k
=
\arccos
\frac{v_k\cdot v_{k+1}}
{\|v_k\|\|v_{k+1}\|}.
\]

The runtime curvature observable is

\[
K_\gamma
=
\sqrt{
\frac1N\sum_k\vartheta_k^2
}.
\]

A straight constant-direction trajectory has zero curvature. Abrupt changes in
semantic direction increase \(K_\gamma\).

## 7. Linear operator algebra

A linear tangent operator is a finite matrix

\[
\hat O\in\mathbb R^{36\times36}.
\]

Application:

\[
v'=\hat Ov.
\]

Composition:

\[
\hat O_{12}
=
\hat O_1\hat O_2.
\]

Commutator:

\[
[\hat O_1,\hat O_2]
=
\hat O_1\hat O_2-\hat O_2\hat O_1.
\]

Projection test:

\[
\hat P^2=\hat P.
\]

Orthogonality test:

\[
\hat O^\mathsf T\hat O=I.
\]

These checks make operator properties executable rather than documentary.

## 8. Forbidden-direction projection

Let rows of \(N\) be forbidden tangent normals. The orthogonal projector onto
their span is

\[
P_F
=
N^\mathsf T
(NN^\mathsf T)^+
N,
\]

where \(+\) denotes the Moore–Penrose pseudoinverse.

For candidate tangent \(v\),

\[
v_F=P_Fv,
\qquad
v_A=(I-P_F)v.
\]

The runtime returns both the allowed component and removed component. This is the
canonical mathematical form of a semantic firewall: it removes a direction,
rather than matching a command string.

## 9. Holonomy cache

A cache key is

\[
K=
(
\operatorname{id}(\hat O),
\operatorname{CRC}(\phi_a),
\operatorname{CRC}(\phi_b),
\operatorname{round}(\Gamma,p)
).
\]

A result is reusable only when operator, endpoints and holonomy match. Equal
endpoints with different path holonomy are separate entries.

## 10. Semantic scheduler

For state \(x\), define the scheduling cost

\[
J(x)
=
\frac{
V(x)+S(x)-U(x)
}{
P(x)
},
\]

where:

- \(V\) is potential;
- \(S\) is entropy;
- \(U\) is urgency;
- \(P>0\) is provenance weight.

The scheduler selects the minimum \(J\), with insertion sequence as a
deterministic tie-breaker. This replaces FIFO with an explicit semantic cost
functional while preserving reproducibility.

## 11. Computational invariants

1. Diff uses wrapped shortest displacement.
2. Merge is a weighted circular resultant.
3. Compression reports and respects its error bound.
4. Common gauge shifts preserve distance.
5. Straight trajectories have zero curvature.
6. Projection operators satisfy idempotence.
7. Forbidden-direction removal is orthogonal in the local tangent space.
8. Holonomy cache keys are path-specific.
9. Scheduler ordering is deterministic.
10. None of these operators performs natural-language projection.

## 12. Evidence boundary

These are finite numerical operators on software states. Their correctness is
established by algebraic and regression tests. They do not by themselves
establish physical quantum behaviour, nonlocal communication or a new hardware
carrier.
