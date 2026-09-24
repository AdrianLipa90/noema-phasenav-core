# PhaseNav 36D Moire Hyperlayer v0.1

Status: CANDIDATE_ONLY / EXECUTABLE_REPRESENTATION / PHYSICAL_GRAVITY_NOT_CLAIMED
Date: 2026-09-24

## Contract

PhaseNav already represents canonical states on \(T^{36}\) and already exposes scalar U(1) semantic holonomy. This candidate adds only a structured two-layer representation:

\[
36=6\times6,
\qquad
V_{36}\cong\mathbb R^6_L\otimes\mathbb R^6_R.
\]

The 6x6 view is a declared computational factorization, not a unique theorem about 36D space.

For two phase matrices \(\Phi^{(1)},\Phi^{(2)}\), each coordinate emits

\[
\bar\phi=\frac{\phi_1+\phi_2}{2},\qquad
\delta/2=\frac{\phi_1-\phi_2}{2},\qquad
E=2\cos(\delta/2),
\]

with circular shortest-arc handling in the implementation. The complex reconstruction equals the direct sum of the two unit phase carriers.

Exact antiphase \(\delta=\pi\) yields an interference null without deleting either parent state.

## Structured rotations

A matrix carrier admits a natural structured action \(X\mapsto LXR^T\) with \(L,R\in SO(6)\). Generator counts are:

- each SO(6): 15;
- SO(6)xSO(6): 30;
- unrestricted SO(36): 630.

The implementation currently records these invariants but does not pretend to execute a physical SO(36) gauge theory.

## Memory crosswalk

The candidate U(1) memory observable

\[
\mathfrak M[\gamma]=\exp\left(i\sum_{e\in\gamma}A_e\right)
\]

is intentionally compatible with the already canonical `semantic_holonomy.py`. No second canonical holonomy implementation is introduced.

## Gravity firewall

This module does not convert a phase shift directly into gravity. The TIR bridge owns the additional requirement

\[
\text{hyperlayer field}\to e\to\omega_{LC}\to R\neq0,
\]

with pure-gauge/integrable cases rejected.
