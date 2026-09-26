# Spatial SO(3) Bivector36 Validation Receipt
Date: 2026-09-26
Status: PASS / 8 OF 8

Branch:

    calibrate/spatial-so3-bivector36-v0.1-20260926

Validated structure:

    rho_36(R)=Lambda^2 diag(1,R)=diag(R,R), R in SO(3).

Replay:
1. exact two-block exterior-square form — PASS;
2. [J_x,J_y]=J_z — PASS;
3. axis-independent trace residual — PASS;
4. z-axis compatibility with prior SO(2) representation — PASS;
5. axis-angle inverse — PASS;
6. typed rotation-vector log-phase roundtrip — PASS;
7. generic T36 rejection contract — PASS;
8. off-subspace negative control — PASS.

Physical boundary:
- full spatial rotation carrier calibrated;
- planar Moire length mapping applies only for rotation about the common layer normal;
- generic live T36 remains untyped.
