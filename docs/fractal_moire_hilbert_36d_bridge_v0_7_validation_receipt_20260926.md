# Fractal Moire-Hilbert 36D v0.7 Summable-Defect Validation Receipt

Date: 2026-09-26
Status: REFERENCE_PASS / HOSTED_CI_NOT_PRESENT / NOISY_LIMIT_CONTRACT_ONLY

Branch:

formalism/fractal-moire-hilbert-36d-bridge-v0.7-20260926

Independent control:

    A=0.2,
    q=0.5,
    N=5.

Computed current envelope:

    A q^N = 0.00625.

Observed control defect:

    0.005 <= 0.00625.

Computed certified remaining tail:

    tau_N
      = A q^N/(1-q)
      = 0.0125.

Computed mismatch tail:

    2 tau_N
      = 0.025.

Negative controls:
- q=1.0: rejected;
- q=1.2: rejected;
- observed defect 0.02 above envelope 0.00625: rejected;
- missing summability witness: contract rejection by design;
- exact-36 firewall remains inherited.

Verdict:

PHASENAV_36D_SUMMABLE_DEFECT_MODE = PASS_REFERENCE
GEOMETRIC_ENVELOPE_TAIL_BUDGET = PASS_REFERENCE
NOISY_PACKET_SELF_PROMOTES_TO_EXACT_LIMIT = NO_GO

GitHub combined status on the implementation head returned no hosted status
checks. Hosted CI PASS is not claimed.

canon_allowed = false.
