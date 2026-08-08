# CI failure correction — 2026-08-04

Run `Tests #95` on PR #7 produced `8 failed, 90 passed`.

Corrections applied on `canon/observer-to-generation-v1`:

1. HTRI projection now maps every non-empty oscillator population onto all 36
   axes without taking a mean of an empty slice. Populations smaller than 36 use
   deterministic modulo fallback for otherwise empty dimensions.
2. Straight trajectory curvature is stabilized to exact numerical zero when
   adjacent normalized tangents are collinear within `1e-12`.
3. Arbitrary binary payloads enter `PhaseGateEngine` through canonical URL-safe
   base64 text, eliminating invalid UTF-8 surrogate code points.
4. The phase-interference cipher now uses keyed quadrature carrier pairs
   `(c, c + pi/2)`, making the 256 symbol phases exactly separable by the fixed
   matched-filter geometry.

The corrections preserve the existing security boundary: the cipher remains an
experimental research construction and is not represented as a standardized or
independently reviewed primitive.
