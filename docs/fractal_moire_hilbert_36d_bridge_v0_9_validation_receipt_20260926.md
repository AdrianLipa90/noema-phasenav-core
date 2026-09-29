# Fractal Moire-Hilbert 36D v0.9 Matrix-Overlap Validation Receipt

Date: 2026-09-26
Status: REFERENCE_CONTRACT_PASS / HOSTED_CI_NOT_PRESENT / MATRIX_OVERLAP_FIREWALL_ACTIVE

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.9-20260926

Pinned operator theorem:

AdrianLipa90/Orbital-System-base
branch formalism/fractal-orbital-moire-hilbert-v0.8-20260926
commit 074f04328f7a615928d24b33474acb056e151985

Reference contract controls:

1. TRIVIAL_INTERNAL_TENSOR

   Requires

   \[
   A_{pq}=g_{pq}I_d
   \]

   semantics, a stabilizer residual below tolerance, and

   channel_dependent_internal_claim = false.

   The contract reports one independent unitary per connected overlap component.

2. FULL_RANK_FRAME_CONJUGACY

   Requires frame-unitarity and external-operator-equality residuals below
   tolerance.

   independent_external_dynamics_claim = true is rejected.

3. RANK_DEFICIENT_STABILIZER

   Requires

   \[
   0\le rank(A_{pq})<d
   \]

   plus a hidden-freedom witness and visible-support consistency receipt.

   The contract reports at least

   \[
   d-rank(A_{pq})
   \]

   hidden complement dimensions.

4. GENERAL_MATRIX_GRAM_STABILIZER

   Requires source-owned matrix-Gram and stabilizer witnesses and consistent
   rank bounds

   \[
   0\le r_{min}\le r_{max}\le d.
   \]

5. Matrix-overlap modes are rejected outside

   OVERLAP_GRAM_COVARIANT.

6. The exact-36 PhaseNav firewall remains inherited.

Hosted status:

GitHub combined status on implementation head

000229c8fc92af68c07e9beaab92026f950d9175

returned no status checks.

Therefore:

HOSTED_CI = NOT_PRESENT.

Verdict:

PHASENAV_36D_TRIVIAL_INTERNAL_TENSOR_NO_GO = PASS_REFERENCE_CONTRACT  
PHASENAV_36D_FULL_RANK_FRAME_CONJUGACY = PASS_REFERENCE_CONTRACT  
PHASENAV_36D_RANK_DEFICIENT_STABILIZER = PASS_REFERENCE_CONTRACT  
PHASENAV_36D_GENERAL_MATRIX_GRAM_SURFACE = PASS_REFERENCE_CONTRACT

The contract does not promote a physical hidden sector or a physical matrix
Gram.

canon_allowed = false.
