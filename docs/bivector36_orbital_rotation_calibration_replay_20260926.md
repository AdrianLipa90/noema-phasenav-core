# Bivector36 Orbital Rotation Calibration Replay
Date: 2026-09-26
Status: PASS / 6 OF 6

Independent local replay:

1. trace formula tr rho_36(theta)=2+4cos(theta) — PASS;
2. SO(2) group law rho(a)rho(b)=rho(a+b) — PASS;
3. typed 36D trace residual equals 4sin^2(theta/2) — PASS;
4. graphene 1.12 deg maps to ~12.6 nm for a=0.246 nm — PASS;
5. inverse trace-to-angle map — PASS;
6. J_36 generator nonzero-entry structure — PASS.

Verdict:
- physical orbital-axis binding is calibrated for BIVECTOR_OPERATOR_36;
- generic legacy PhaseNav 36D remains unbound unless explicitly converted to
  this typed carrier through a validated adapter.
