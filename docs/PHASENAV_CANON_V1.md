# PhaseNav Canon v1.0.0

## Authority and quality seal

```yaml
operator: TO_JEST_MOJE
issuer: Adrian Lipa
meaning: authorial conformity and quality approval
scope: PhaseNav Canon v1.0.0
```

This operator records authorial approval. It is not substituted for mathematical proof or external physical validation.

## Hard architecture

\[
\mathrm{TIR}\rightarrow\mathcal H_{2048}\rightarrow
J_{11}\rightarrow(p_+,p_-,q)\rightarrow T^{36}\rightarrow
\text{PhaseNav runtime}.
\]

- Source state: normalized \(\mathbb C^{2048}\), equivalently an 11-bit Hilbert basis.
- Complement: anti-linear bitwise complement
  \(J\psi[j]=\overline{\psi[j\oplus2047]}\), with \(J^2=I\).
- Binary channels: the two 1024-dimensional halves exchanged by \(J\).
- Operational projection: phases of coordinates 0–35, exactly reproducing the existing 36D runtime.
- Numeric EIDs use the Metatime TIR phase law.
- Text EIDs use the exact Decimal Collatz fallback.

## Canonical constants

\[
\kappa=\frac{\ln2}{24\pi},\quad L_3=7,\quad L_4=2,\quad L_5=5,
\]

\[
\alpha_M^{-1}=(L_3L_4)^2-L_3^2-L_4L_5+L_4^2\kappa.
\]

## Semantic mass

Numeric glossary entry:

\[
m_k=\kappa(1+\alpha_M k)+\frac{2}{7}R_k.
\]

Text fallback without a glossary position:

\[
m_{\mathrm{fallback}}=\kappa(1+R).
\]

The fallback must not fabricate \(k=1\).

## Orbital audit

The audit separates:

- mass attractor,
- coherence peak,
- nearest self-dual state,
- full 36D distance,
- Berry connection,
- reciprocal channel coordinate \(q=p_+/p_-\),
- continuous radius \(|\ln q|\).

Shell width is the internal PhaseNav distinguishability quantum
\(\eta_M=36\kappa\), not a free `epsilon`.

Repository placement is governed by architectural role. Orbital shell metadata does not authorize file movement. Every mutation remains outside the read-only audit and requires a separate authorization record.

## Cards and glossary

The frozen seed ledger contains 115 cards. Two source entries are already internally consistent and remain canonical. The remaining 113 retain `chyba` and `canon_allowed=false`; the hard system canon does not silently promote disputed card metadata.

The earlier zero-distance nearest-neighbour graph is replaced by a composite orbital relation using:

\[
d_{\mathrm{orb}}^2=d_{36}^2+\left|\ln\frac{m_a}{m_b}\right|^2+\left|\ln\frac{q_a}{q_b}\right|^2,
\]

with Berry correction applied to the edge weight. Generated semantic relations retain the epistemic operator `chyba`.

## Compatibility

The existing 36D runtime is retained as the operational compatibility surface. The canon layer is additive and verifies that H2048 projection reproduces `_phase36_from_id` exactly.
