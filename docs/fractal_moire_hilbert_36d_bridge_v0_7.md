# Fractal Moire-Hilbert -> PhaseNav 36D Bridge v0.7

Status: CANDIDATE_ONLY / SUMMABLE_DEFECT_DEPTH_MODE / NOISY_LIMIT_FIREWALL
Date: 2026-09-26

## 1. Purpose

v0.7 adds a noisy cross-level mode without weakening the exact v0.6 gates.

New depth mode:

SUMMABLE_DEFECT_INDUCTIVE_COVARIANCE.

It is admitted only through a certified summable defect envelope.

## 2. Parent stability theorem

For cross-level defects

\[
\varepsilon_N
=
\|R_{N+1}J_N-J_NR_N\|,
\]

if

\[
\sum_N\varepsilon_N<\infty,
\]

then a unitary limit exists and the remaining finite-to-limit error at level
\(N\) is bounded by

\[
\boxed{
\tau_N
=
\sum_{k=N}^{\infty}\varepsilon_k.
}
\]

The mismatch error is bounded by

\[
\boxed{
2\tau_N.
}
\]

Finite eigenvalues lie within \(\tau_N\) of the limit unitary spectrum, while
finite mismatch eigenvalues lie within \(2\tau_N\) of the limit mismatch
spectrum.

## 3. Geometric-envelope admission

v0.7 initially supports one executable defect model:

GEOMETRIC_ENVELOPE.

The packet declares

\[
\varepsilon_N
\le
Aq^N,
\qquad
A\ge0,
\quad
0\le q<1.
\]

At current level \(N\), the certified tail is

\[
\boxed{
\tau_N
=
\frac{Aq^N}{1-q}.
}
\]

The measured current intertwiner defect must satisfy

\[
\varepsilon_N^{obs}
\le
Aq^N.
\]

A ratio \(q\ge1\) is rejected because it does not certify summability.

## 4. Required witnesses

SUMMABLE_DEFECT_INDUCTIVE_COVARIANCE requires:

- defect_model = GEOMETRIC_ENVELOPE;
- defect_model_witness_ref;
- summability_witness_ref;
- limit_theorem_witness_ref;
- current_level_index;
- defect_envelope_amplitude;
- defect_envelope_ratio;
- current_intertwiner_defect;
- noisy_family_witness_ref;
- noisy_depth_information_loss_ledger;
- noisy_limit_reconstruction_contract.

The contract computes rather than trusts:

- current envelope;
- remaining tail bound;
- mismatch tail bound;
- unitary spectral-distance bound;
- mismatch spectral-distance bound.

## 5. Separation from exact mode

A packet with exact cross-level covariance should use v0.6
INDUCTIVE_LIMIT_COVARIANT.

A noisy packet must not replace its measured residual by zero to pass the exact
gate.

The v0.7 wrapper validates all pre-existing branch/36D semantics and then adds
the noisy depth certificate separately.

## 6. No-go

Reject:
- q >= 1;
- negative/nonfinite envelope parameters;
- measured defect above the declared envelope;
- missing summability theorem witness;
- empty noisy depth loss ledger;
- exact-36 violation.

A finite decreasing defect list with no certified summable tail remains
insufficient.

## 7. Promotion ledger

PASS at contract level:
- executable geometric defect envelope;
- computed tail error budget;
- computed mismatch error budget;
- spectral-distance budgets;
- separation from exact inductive mode;
- inherited branch, overlap, cocycle and exact-36 firewalls.

OPEN:
- physical/statistical error model;
- confidence intervals for experimental noise;
- source-owned infinite 36D family;
- calibration.

canon_allowed = false.
