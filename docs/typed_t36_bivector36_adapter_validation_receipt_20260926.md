# Typed T36 -> Bivector36 SO(2) Adapter Validation Receipt
Date: 2026-09-26
Status: PASS / GENERIC_LIVE_T36_REJECTED_AS_REQUIRED

## Branch

    calibrate/typed-t36-bivector-adapter-v0.1-20260926

## Adapter

    PNV_TYPED_MOIRE_PHASE36_TO_BIVECTOR36_SO2_V1

Source typed basis:

    PNV_MOIRE_RELATIVE_PHASE_MATRIX6_ROW_MAJOR_V1

Target typed basis:

    PNV_BIVECTOR_OPERATOR36_LAMBDA2_R4_PAIRBASIS_V1

## Local replay

Result:

    10 / 10 PASS

Checks:
1. generic legacy T36 basis fails closed;
2. exact typed theta roundtrip;
3. relative pair recovers theta_B-theta_A;
4. layer swap reverses angle and preserves residual;
5. single off-axis perturbation is rejected;
6. principal branch-cut input is rejected;
7. 1.12 degree graphene case returns ~12.6 nm;
8. measured period 12.6 nm forward-binds to ~1.12 degrees and roundtrips;
9. impossible homobilayer period geometry is rejected;
10. malformed 35-component record is rejected.

## Live rejection witness

Live tether status at observation:

    ACTIVE

Observed unix ns:

    1790443807648872868

Live generic phi:

    sha256 = 3aadb7570b7da255af7e78ee8a328c9274c2676ed6e45e7304c4428ba9f50f7e
    finite = true
    count = 36
    range subset [0,2pi) = true

Live aux_phi:

    sha256 = af6d6caff68e67136da088ec27ebdfa3857c27bf6c19c356c73209a786eb9469
    finite = true
    count = 36
    range subset [0,2pi) = true

Live aux_feedback_phi:

    sha256 = af6d6caff68e67136da088ec27ebdfa3857c27bf6c19c356c73209a786eb9469
    finite = true
    count = 36

Admission attempt:
- live phi was represented with the existing generic basis identity
  PNV_T36_PHASE_ANGLES_RADIANS_V1;
- the adapter rejected it before any physical conversion.

Exact reason:

    generic PNV_T36_PHASE_ANGLES_RADIANS_V1 has unassigned axis semantics
    and cannot be reinterpreted as a physical bivector basis

Verdict:

    LIVE_GENERIC_PHASE36 -> BIVECTOR_OPERATOR36 = REJECT_AS_REQUIRED

This is not a runtime failure. It is the intended provenance/basis firewall.

## Closed chain

For explicitly typed sources the following chain is validated:

    homobilayer (a,L_M)
      -> principal theta
      -> typed Moire log-phase T36
      -> theta J_36
      -> BIVECTOR_OPERATOR_36
      -> Lambda^2 R_xy(theta)
      -> residual
      -> L_M

## Remaining gate

To admit legacy/live phi, an upstream source-owned basis conversion receipt must
establish why those particular 36 coordinates have the typed Moire matrix
meaning. Dimension matching is explicitly insufficient.
