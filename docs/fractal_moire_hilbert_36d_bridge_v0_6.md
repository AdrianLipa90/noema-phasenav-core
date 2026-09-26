# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.6

Status: CANDIDATE_ONLY / CROSS_LEVEL_INDUCTIVE_COVARIANCE_TYPED / INFINITE_DEPTH_FIREWALL
Date: 2026-09-26

## 1. Purpose

v0.6 adds an explicit cross-level consistency layer above the v0.5 branch
semantics.

A single 36D packet is finite data. It cannot by itself establish an
infinite-depth operator.

The new depth modes are:

- FINITE_LEVEL_ONLY;
- INDUCTIVE_STEP_COVARIANT;
- INDUCTIVE_LIMIT_COVARIANT.

The last mode requires a separate theorem/family witness in addition to one
finite transition receipt.

## 2. Parent theorem

For Hilbert levels

\[
\mathcal H_N
\xrightarrow{J_N}
\mathcal H_{N+1},
\qquad
J_N^*J_N=I,
\]

and unitaries \(R_N\), exact compatibility is

\[
\boxed{
R_{N+1}J_N=J_NR_N.
}
\]

Then

\[
\Delta_N=(I-R_N)^*(I-R_N)
\]

also satisfies

\[
\boxed{
\Delta_{N+1}J_N=J_N\Delta_N.
}
\]

A compatible cofinal family defines the inductive-limit unitary.

## 3. INDUCTIVE_STEP_COVARIANT

A finite packet may certify one transition \(N\to N+1\).

Required witnesses:

- level_index;
- coarse_level_id;
- fine_level_id;
- embedding_witness_ref;
- embedding_isometry_residual;
- cross_level_intertwiner_residual;
- mismatch_intertwiner_residual;
- spectral_nesting_residual.

All residuals must be finite, nonnegative and below tolerance.

This mode does not claim an infinite limit.

## 4. INDUCTIVE_LIMIT_COVARIANT

This mode includes all step witnesses and additionally requires:

- inductive_family_witness_ref;
- limit_theorem_witness_ref;
- cofinality_witness_ref;
- validated_level_count >= 2;
- infinite_depth_information_loss_ledger;
- limit_reconstruction_contract.

The packet is then allowed to reference an externally proved compatible family.

The packet itself remains only one finite projection.

## 5. ARPL infinite-depth subtype

A packet may declare

ARPL_PROCYCLIC_ODOMETER_LIMIT

only if it carries:

- arpl_infinite_spectrum_witness_ref;
- current_clock_size \(L_N\);
- next_clock_size \(L_{N+1}\);
- divisibility \(L_N\mid L_{N+1}\);
- current finite root-spectrum summary;
- current first positive mismatch value.

The parent theorem gives, on the genuinely infinite refinement sector,

\[
\boxed{
\sigma(U_\infty)=S^1
}
\]

and

\[
\boxed{
\sigma(\Delta_\infty)=[0,4].
}
\]

The point spectrum remains the countable ARPL dual eigenvalue group.

The zero mismatch eigenspace is the constant-character sector.

No positive mismatch spectral gap survives the infinite refinement.

## 6. Finite spectral nesting

For a valid finite transition, the packet must test that the coarse finite
spectrum embeds into the fine finite spectrum within tolerance.

For an exact ARPL clock refinement,

\[
L_N\mid L_{N+1},
\]

the root-of-unity spectra nest exactly.

The finite mismatch spectra nest by the same continuous spectral map.

## 7. Information-loss firewall

An INDUCTIVE_LIMIT_COVARIANT packet must explicitly record that a 36D finite
projection does not retain at least:

- all higher refinement levels;
- the full infinite operator spectrum;
- all cylinder amplitudes;
- full branch-transition matrices;
- complete inverse-limit address data.

An empty infinite-depth loss ledger is rejected.

## 8. No-go

Reject:
- infinite-depth claim with no family theorem witness;
- a single finite transition labeled as a proved infinite limit;
- non-isometric embedding above tolerance;
- failed cross-level orbital intertwining;
- failed mismatch intertwining;
- failed spectral nesting;
- ARPL subtype with non-divisible clock sizes;
- exact-36 coordinate violation.

## 9. Relation to v0.5

v0.5 classifies the operator geometry inside one finite refinement level:
fixed branch, permutation, cocycle, overlap, compression, or dilation.

v0.6 classifies consistency between levels.

These axes are independent.

For example an ARPL finite level may use CUNTZ_BLOCK_COCYCLE_UNITARY internally
while the recombined coarse pullback obeys INDUCTIVE_LIMIT_COVARIANT across
levels.

## 10. Promotion ledger

PASS at representation-contract level:
- finite-only versus step versus limit semantics separated;
- fail-closed cross-level residuals;
- family/cofinality witness required for infinite-depth claim;
- ARPL spectral subtype explicitly typed;
- inherited exact-36 and information-loss firewalls.

OPEN:
- source-owned physical family of 36D states;
- production cross-level embeddings;
- approximate/noisy inductive theorem;
- empirical physical spectrum.

canon_allowed = false.
