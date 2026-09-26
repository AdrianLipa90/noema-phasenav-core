# Fractal Moire-Hilbert 36D v0.3 Validation Receipt

Date: 2026-09-26
Status: PASS / BRANCH_COVARIANCE_CONTRACT_REPLAY

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.3-20260926

Independent replay:
- COMPRESSION_ONLY packet: PASS;
- FIXED_BRANCH_UNITARY_INTERTWINER packet: PASS;
- UNITARY_DILATION packet remains a distinct PASS path;
- common-phase projective residual after numerical positivity clamp:
  4.440892098500626e-16;
- exact-36 and mixed-semantics failure surfaces remain fail-closed.

Verdict:

PHASENAV_36D_IFS_COMPRESSION = PASS_CONTRACT
PHASENAV_36D_FIXED_BRANCH_INTERTWINER = PASS_CONTRACT
PHASENAV_36D_UNITARY_DILATION_SEPARATION = PASS_CONTRACT

This validates representation contracts only. It does not establish a physical
IFS, branch word, or orbital covariance witness.

canon_allowed = false.
