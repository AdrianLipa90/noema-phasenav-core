# PhaseNav channel / transfer / Krylov primitives v0.17

Status: `CANDIDATE_ONLY`  
`canon_allowed=false`

v0.17 adds a channel-level layer above the v0.15 tensor and v0.16
mixed-representation primitives.  The purpose is to separate four objects that
must not be conflated:

\[
\text{state},\quad
\text{channel},\quad
\text{transfer operator},\quad
\text{hardware/noise calibration}.
\]

The first three can be manipulated mathematically without claiming the fourth.

## 1. Density and information primitives

The module adds:

- state normalization and density-matrix construction;
- arbitrary finite subsystem partial traces;
- von Neumann entropy;
- purity;
- Renyi-2 entropy;
- min entropy;
- mutual information.

For a Bell control,

\[
S(\rho_A)=1\ {\rm bit},
\qquad
\operatorname{Tr}\rho_A^2=\frac12,
\qquad
I(A:B)=2\ {\rm bits}.
\]

This gives PhaseNav explicit information scalars rather than using rank alone as
a proxy for entanglement/information content.

## 2. Kraus, Choi and superoperator representations

A finite channel is represented by Kraus operators

\[
\mathcal E(\rho)=\sum_k K_k\rho K_k^\dagger.
\]

The candidate layer provides:

- direct channel application;
- Choi matrix construction in output \(\otimes\) input ordering;
- Choi-to-Kraus reconstruction;
- column-vectorized superoperator construction;
- CP, TP and unitality residual receipts.

No channel is labelled as a measured physical device channel unless external
calibration is supplied.

## 3. Pauli transfer representation

For \(n\le 3\) qubits per local channel in the current implementation,

\[
R_{ij}
=
\frac1{2^n}
\operatorname{Tr}
\left[
P_i\,\mathcal E(P_j)
\right].
\]

The PTM receipt records sparsity and whether the matrix is a signed permutation.
This gives an independent routing surface:

- Clifford unitary channels become signed Pauli permutations;
- generic rotations produce genuine Pauli mixing;
- sparse transfer structure can be retained without constructing global state
  vectors.

## 4. Exact second-moment transport

For a unitary PTM \(R\),

\[
T_{ij}=|R_{ij}|^2
\]

transports squared Pauli amplitudes and is column stochastic.

For the RCS local-Haar + CZ control, PhaseNav now exposes the exact
parameter-free support transition

\[
T_{\rm CZ}^{\rm Haar}
=
\begin{pmatrix}
1&0&0&0\\
0&1/3&0&2/9\\
0&0&1/3&2/9\\
0&2/3&2/3&5/9
\end{pmatrix},
\]

with basis order

\[
(00,10,01,11).
\]

The nonzero-support sector has eigenvalues

\[
1,\quad \frac13,\quad -\frac19,
\]

and stationary distribution

\[
\boxed{
(10,01,11)=\left(\frac15,\frac15,\frac35\right).
}
\]

This replaces an arbitrary local retention coefficient with an exact
second-moment primitive at the single-edge level.  It does **not** by itself
solve the global 61-qubit XEB/severing problem; the appropriate replicated
network still has to be contracted.

## 5. Transfer spectrum and fixed points

`transfer_spectrum` returns the complete finite eigenvalue spectrum, spectral
radius, subleading magnitude and gap.

`channel_fixed_point` extracts and validates a unit-eigenvalue density operator
for square finite channels.

These quantities can be used as scalar routing diagnostics for mixing,
relaxation and iterative contraction, while remaining distinct from physical
time constants unless a physical channel has been calibrated.

## 6. Low-rank updates

`woodbury_inverse_update` implements

\[
(A+UCV)^{-1}
=
A^{-1}
-
A^{-1}U
(C^{-1}+VA^{-1}U)^{-1}
VA^{-1},
\]

with a fail-closed condition-number gate.

This gives PhaseNav an exact update path for small local changes without
recomputing a full inverse/boundary response from scratch.

## 7. Krylov / Lanczos orbit

`lanczos_hermitian` constructs a Krylov basis

\[
\mathcal K_m(A,v)
=
\operatorname{span}
\{v,Av,A^2v,\ldots,A^{m-1}v\}
\]

and a tridiagonal projected operator.  Full reorthogonalization is used in the
candidate implementation, with explicit orthogonality and recurrence
residuals.

This is useful for large Hermitian transfer/Hamiltonian operators when only the
dominant orbital sector is needed.

## 8. Validation

Focused local suite:

```text
24 passed
py_compile: PASS
```

Controls include:

- Bell partial trace / entropy / mutual information;
- identity and amplitude-damping Choi/Kraus roundtrips;
- CP/TP/unitality receipts;
- Clifford PTM signed-permutation controls;
- unitary second-moment column stochasticity;
- exact Haar+CZ support coefficients;
- fixed points for depolarizing and amplitude-damping channels;
- Woodbury against direct inversion;
- Lanczos recovery of a known Hermitian spectrum.

Full repository pytest is not claimed in this session.

## 9. Epistemic boundary

This module does not establish:

- the measured IBM noise channel;
- a physical-QPU execution;
- a global RCS classical speedup;
- global XEB from the local support matrix alone;
- any physical interpretation of PhaseNav information scalars without an
  external binding.

The layer remains a mathematical/software candidate until separately promoted.