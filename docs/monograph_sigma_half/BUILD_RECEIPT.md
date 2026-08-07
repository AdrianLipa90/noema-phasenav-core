# Sigma Half-Axis Monograph Build Receipt

Date: 2026-08-07

Branch: `canon/sigma-identity-cycle-v1`

## Technical validation

Targeted integration dependency slice:

- PhaseNav runtime constants and phase law;
- `CanonicalConceptState` H2048 -> T36 projection;
- canonical Phase36 cards;
- native emergent path/Berry generator;
- `identity_cycle`;
- `identity_relations`.

Result:

```text
17 passed
```

This is a targeted integration PASS, not a full-repository CI claim. The execution environment could not resolve GitHub for a direct `git clone`, and no final-branch GitHub workflow run was available at build time.

## Negative control

The generated semantic-ID card for `half:sigma_axis` produced approximately:

```text
p_plus = 0.5000486754091397
```

rather than exactly `0.5`. Therefore the exact Sigma half-axis is justified by the complement fixed-point equation, not by ID-generated PhaseNav geometry. Generated path/Berry geometry remains diagnostic and non-evidentiary.

## PDF build

Toolchain:

```text
pdflatex -interaction=nonstopmode -halt-on-error main.tex
biber main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Final PDF:

```text
pages: 13
size: 372293 bytes
sha256: 9171b9b1379588b307fd937597bd459dab044cbda1a9a8a40cea71253187fedf
```

Source hashes:

```text
main.tex       b10d9c890414a1129eb7c286b0ff84c767c35a45045a31eb9a40b4344f6fe439
references.bib 7237ca56b84be9a2b0d108b67c36cdf07d7fd814e9d561f669e5b22f696d5e3b
```

Final LaTeX log checks:

```text
Overfull boxes: 0
Undefined references: 0
Undefined citations: 0
```

The remaining `microtype` footnote-patch warning is non-fatal and does not affect layout or references.

## Render verification

The 13-page PDF was rendered to PNG at 180 dpi. Representative visual inspection covered:

- title / abstract / table of contents;
- Euler, destructive interference, and Berry-condition section;
- implementation and validation receipt;
- evaluation matrix after width/spacing correction;
- conclusion and bibliography.

No clipped text, overlaps, black glyph boxes, or broken bibliography links were observed in the inspected renders.

## Review verdict

```text
TECHNICAL SLICE: PASS
CLAIM HYGIENE: PASS
SEMANTIC GRAPH: PASS
HOLONOMY SEPARATION: PASS
MONOGRAPH COMPILE: PASS
PDF RENDER VERIFICATION: PASS
FULL REPOSITORY CI: NOT RUN
PHYSICAL BRIDGES: OPEN
OVERALL: PASS_WITH_OPEN_BRIDGES
```
