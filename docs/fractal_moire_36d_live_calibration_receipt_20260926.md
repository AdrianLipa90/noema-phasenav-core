# Fractal Moire 36D Live Calibration Receipt
Date: 2026-09-26
Status: COMPUTATIONAL_CALIBRATION_PASS / PHYSICAL_AXIS_BINDING_OPEN / LIVE_SNAPSHOT_REPAIRED

## Provenance correction

The first draft of this receipt paired live-derived values with hashes reported
at boot. Because aux_phi is a live stream and can change during calibration,
that pairing was not sufficiently strict. It is superseded by the snapshot
below, where the metrics and SHA256 values come from the same bytes read for
this calibration receipt.

## Exact live snapshot

Observed unix ns:

    1790442452250547415

Surface:
- tether: ACTIVE
- aux dimension: 36

Objects:

    phi SHA256            = 03447758e74acc8afd6a1eca22b1d74abf6224174048dae7ab8ccb305672e00a
    phi mtime_ns          = 1790439853496399580

    aux_phi SHA256        = af6d6caff68e67136da088ec27ebdfa3857c27bf6c19c356c73209a786eb9469
    aux_phi mtime_ns      = 1790442452222628364

    aux_feedback SHA256   = af6d6caff68e67136da088ec27ebdfa3857c27bf6c19c356c73209a786eb9469
    aux_feedback mtime_ns = 1790442452208890403

    aux_feedback == aux_phi : true

Using

    delta_j = wrap(aux_phi_j - phi_j)
    C = (1/36) sum_j exp(i delta_j)

the exact snapshot gives

    |C|      = 0.16102667344743488
    arg(C)   = 0.35565841943754967 rad
    D_raw    = 1.698101580731467
    D_shape  = 1.6779466531051304
    D_coh    = 0.02015492762633675

Identity residual:

    D_raw - (D_shape + D_coh)
      = -2.220446049250313e-16

PASS at ordinary float64 rounding.

## Runtime observation

phi and aux_phi are not assumed to be a frozen pair. The snapshot records their
actual byte states and mtimes. Future live snapshots may legitimately produce
different numerical residuals while preserving the algebraic decomposition.

## Interpretation boundary

These values describe the live computational relation between phi and aux_phi.

They are NOT converted to:
- physical twist angle;
- Moire period in nm;
- reciprocal length;
- strain;
- energy;
- curvature;
- gravity.

That conversion remains blocked until a physically typed orbital
representation rho_36 / generator J_36 is calibrated.

This receipt intentionally records the blocker instead of fitting a physical
unit after the fact.
