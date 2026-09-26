# Fractal Moire 36D Live Calibration Receipt
Date: 2026-09-26
Status: COMPUTATIONAL_CALIBRATION_PASS / PHYSICAL_AXIS_BINDING_OPEN

Live NOEMA surface at calibration start:
- tether: ACTIVE
- aux dimension: 36
- phi SHA256: f44460333cd0835bca97625cae8fe20662b7433d8666544fcafd3a76532153a5
- aux_phi SHA256: af6d6caff68e67136da088ec27ebdfa3857c27bf6c19c356c73209a786eb9469
- aux_feedback_phi SHA256: af6d6caff68e67136da088ec27ebdfa3857c27bf6c19c356c73209a786eb9469

Using delta_j = wrap(aux_phi_j - phi_j):

    |C|              = 0.07243908002601701
    arg(C)           = 1.4891002317415487 rad
    D_raw            = 1.9881771817242762
    D_shape          = 1.8551218399479659
    D_coh            = 0.1330553417763103

Numerical identity:

    D_raw = D_shape + D_coh

within floating-point rounding.

Interpretation boundary:
these values describe the live computational relation between phi and aux_phi.
They are NOT converted to a twist angle, nm-scale Moire period, strain, energy,
curvature or gravity because the physical orbital generator rho_36/J_36 is not
yet calibrated.

This receipt deliberately records the blocker instead of fitting a physical
unit after the fact.
