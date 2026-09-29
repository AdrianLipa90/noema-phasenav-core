# Fractal Moire-Hilbert 36D v0.5 Validation Receipt

Date: 2026-09-26
Status: REFERENCE_PASS / HOSTED_CI_NOT_PRESENT / REPRESENTATION_CONTRACT_ONLY

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.5-20260926

Independent contract replay confirms:

- BRANCH_PERMUTATION_UNITARY accepts a bijection such as [1,0];
- invalid/non-bijective permutations fail closed;
- CUNTZ_BLOCK_COCYCLE_UNITARY remains distinct from fixed-branch semantics;
- ARPL_ODOMETER_CARRY requires
      branch_count = refinement_branching,
      coarse_clock_size >= 1,
      refinement_branching >= 2,
      carry_cocycle_residual <= tolerance;
- control packet with
      L_N=6,
      b_N=3
  gives
      L_{N+1}=18;
- block unitarity/reconstruction/mismatch residuals are independently typed;
- exact-36 coordinate firewall is inherited;
- overlap-Gram and unitary-dilation surfaces remain separate.

Hosted GitHub commit status on the implementation head returned no status checks.

Verdict:

PHASENAV_36D_BRANCH_PERMUTATION_CONTRACT = PASS_REFERENCE
PHASENAV_36D_BLOCK_COCYCLE_CONTRACT = PASS_REFERENCE
PHASENAV_36D_ARPL_CARRY_SUBTYPE = PASS_REFERENCE
HOSTED_CI = NOT_PRESENT

No source-owned physical 36D ARPL state is promoted.

canon_allowed = false.
