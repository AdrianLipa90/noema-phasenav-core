# Fractal Moire-Hilbert 36D v0.8 ARPL Overlap Validation Receipt

Date: 2026-09-26
Status: REFERENCE_CONTRACT_PASS / HOSTED_CI_NOT_PRESENT / ARPL_SCALAR_PULSE_ADAPTER_FAIL_PRESERVED

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.8-20260926

Pinned arithmetic source:

AdrianLipa90/On-Primes
branch integrate/arpl-fractal-orbital-bridge-v0.2-20260926
commit 705872f11aaf8b933ab3b713fb10443326fde62b

Contract controls:

1. ARPL_HIT_OVERLAP_GRAM is accepted only under
   OVERLAP_GRAM_COVARIANT.

2. The subtype requires:
   - distinct prime support p>=5;
   - h>=6 and 6|h;
   - ARPL bridge/Gram/normalized-Gram witnesses;
   - Gram-normalization residual below tolerance;
   - explicit arithmetic-pulse scalar-adapter status.

3. FAIL_STABILIZER does not invalidate the arithmetic source.
   It sets

       scalar_orbital_pulse_promotion = false.

4. PASS_STABILIZER with a residual above tolerance is rejected.

5. FAIL_STABILIZER with a residual at or below tolerance is rejected as an
   internally contradictory packet.

6. NOT_CLAIMED remains a lawful coordinate-only status.

Pinned h=6 reverse test:

support = {5,7,11,13,19}

arithmetic pulse angles:

\[
\left(
\pi,
2\pi/3,
4\pi/5,
2\pi/3,
10\pi/9
\right).
\]

Normalized overlap-Gram scalar adapter residual:

\[
\boxed{
1.0236181222825256
}.
\]

Therefore:

ARPL_H6_NAIVE_PULSE_TO_SCALAR_ORBITAL = FAIL_STABILIZER.

The exact ARPL hit-cylinder overlap Gram itself remains admitted.

Hosted status:

GitHub combined status on branch head
a5239d849bf2db3b2c98725cf9a44904832a0bb6
returned no status checks.

Therefore:

HOSTED_CI = NOT_PRESENT.

Verdict:

PHASENAV_36D_ARPL_HIT_OVERLAP_SUBTYPE = PASS_REFERENCE_CONTRACT
ARPL_OVERLAP_SOURCE_MATHEMATICS = RETAINED
NAIVE_SCALAR_ORBITAL_PULSE_PROMOTION = FAIL
FAIL_IS_NOT_SILENTLY_PROMOTED = PASS_FIREWALL

No physical prime-generated 36D state is promoted.

canon_allowed = false.
