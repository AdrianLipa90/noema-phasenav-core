# Semantic U(1) holonomy — W_sem from A_sem

Status: `EXECUTABLE_MODEL_BINDING / CHYBA / READ_ONLY`

Date: 2026-09-19

PhaseNav now exposes a typed scalar U(1) semantic transporter

\[
W^{\rm sem}_{ij}[\gamma]
=
\exp\!\left(i\int_{\gamma_{ij}}A_{\rm sem}\right),
\]

with the discrete implementation

\[
W^{\rm sem}_{ij}[\gamma]
=
\exp\!\left(i\sum_{e\in\gamma}A_e^{\rm sem}\right).
\]

`A_sem` is local connection/potential data. `W_sem` is its nonlocal path transport / phase holonomy.

For PhaseNav projective states,

\[
z_{ij}=\langle\psi_i|\psi_j\rangle,
\qquad
\mathcal C_{ij}=W^{\rm sem}_{ij}z_{ij}.
\]

The receipt exposes

\[
S_{ij}=|\mathcal C_{ij}|,
\qquad
\Phi_W=\arg W^{\rm sem}_{ij}.
\]

A pure U(1) transport changes phase without changing `|z_ij|`.

## Gauge contract

With

\[
A_{\rm sem}\mapsto A_{\rm sem}+d\chi,
\]

open transport is endpoint-covariant and a closed loop is gauge invariant because the discrete gauge increments telescope.

This module is intentionally distinct from:

- the existing scalar context potential `U_C`;
- RIFC affect notation;
- non-Abelian spatial/colour transport;
- physical electromagnetic or electroweak identification.

The implementation is read-only and carries `canon_allowed=False`.

## API

`src/ciel_geometry/phasenav/canon/semantic_holonomy.py`

- `u1_semantic_transport`
- `u1_semantic_holonomy_phase`
- `phase_overlap`
- `semantic_holonomy_coupling`
- `SemanticHolonomyReceipt`

## Evidence boundary

Tests establish the finite U(1) transport identities, gauge covariance/invariance and consistency of the PhaseNav overlap realization. They do not establish physical nonlocal signalling or a measured gauge field.
