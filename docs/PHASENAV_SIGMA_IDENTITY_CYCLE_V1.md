# PhaseNav Sigma Identity-Axis and Normalized Cycle Canon v1

## Status

**Implementation status:** CANON_CANDIDATE  
**Runtime scope:** pure PhaseNav arithmetic / phase geometry; no language projection  
**Time-from-tau derivation:** explicitly deferred to a separate TIR section  
**Jarlskog sector:** out of scope for this canon

This module formalizes the `1/2` branch developed from the Poincare/Bloch,
spinor and information-cycle construction.

The implementation deliberately separates exact identities from TIR/PhaseNav
model semantics.

---

## 1. Sigma: axis of identity

The canonical binary identity axis is

\[
\Sigma_*=\frac12.
\]

For a state coordinate \(\sigma\), define the centred displacement

\[
u_\Sigma=\sigma-\frac12.
\]

The complement involution is

\[
J_\Sigma(\sigma)=1-\sigma.
\]

Its unique fixed point on the binary interval is

\[
J_\Sigma(\sigma)=\sigma
\iff
\sigma=\frac12.
\]

PhaseNav interprets this fixed locus as an **axis of identity**, not as a frozen
state. A system state may evolve while remaining organized relative to the
same identity axis.

This interpretation is a canonical PhaseNav/TIR model statement. The fixed
point calculation itself is exact.

---

## 2. Normalized cycle coordinate

Before introducing radians, define

\[
q\in\mathbb R/\mathbb Z.
\]

One projective recurrence is simply

\[
q\mapsto q+1.
\]

Frequency can therefore be defined without \(\pi\):

\[
f_q=\frac{dq}{dt}
\]

for uniform evolution, or from winding count,

\[
f_q=\frac{\Delta N}{\Delta t}.
\]

Only after a geometric closure convention \(C>0\) is selected do we define

\[
\phi=Cq.
\]

For the ordinary radian convention,

\[
C=\tau=2\pi.
\]

Thus `q` is the primary cycle coordinate and angular phase is a projection of
that cycle into a chosen geometric measure.

---

## 3. Spin-1/2 double cover

For a spinorial representative, one projective recurrence may change the
representative sign while preserving the projective ray:

\[
\psi\mapsto-\psi.
\]

Two projective recurrences return the representative:

\[
[\psi]\xrightarrow{1\ {\rm cycle}}[\psi],
\qquad
\psi\xrightarrow{2\ {\rm cycles}}\psi.
\]

Under the radian projection this is the familiar

\[
2\pi\quad\text{versus}\quad4\pi
\]

distinction.

The canon therefore keeps projective cycle count and spinor cycle count as
separate integer structures before introducing angular units.

---

## 4. Information arithmetic before angular geometry

Define one PhaseNav information quantum as

\[
I_*=\ln2.
\]

The present canon assigns one information cycle to twelve projective
recurrences:

\[
N_{\rm proj}=12.
\]

Therefore in normalized cycle space,

\[
\frac{dI}{dq}
=
\frac{\ln2}{12}.
\]

This is exactly the simplification already used internally by PhaseNav:

\[
\kappa\tau
=
\frac{\ln2}{24\pi}(2\pi)
=
\frac{\ln2}{12}.
\]

Consequently, for projective winding frequency \(f_q\),

\[
\boxed{
\dot I
=
\frac{\ln2}{12}f_q
}
\]

without explicit use of \(\pi\).

Only after choosing the radian closure \(C=2\pi\),

\[
\frac{dI}{d\phi}
=
\frac{\ln2/12}{2\pi}
=
\frac{\ln2}{24\pi}
=
\kappa.
\]

This makes the distinction explicit:

- `ln(2)/12` is the information-per-normalized-cycle coefficient;
- `2*pi` is the angular image of one projective cycle;
- `KAPPA` is their quotient after angular projection.

---

## 5. Independent 24-unit arithmetic certificate

The current PhaseNav/TIR model provides three integer decompositions of the
same half-turn count:

\[
8\times3=24,
\]

\[
12\times2=24,
\]

\[
6\times4=24.
\]

Their interpretations are:

- \(8\): canonical mix count;
- \(3\): canonical flavour count;
- \(12\): projective cycles per information cycle;
- \(2\): half-turn units per projective \(2\pi\) cycle;
- \(6\): spinor cycles per information cycle;
- \(4\): half-turn units per spinor \(4\pi\) cycle.

Hence

\[
8\cdot3
=
12\cdot2
=
6\cdot4
=
24.
\]

After mapping one half-turn unit to \(\pi\),

\[
\Phi_I=24\pi,
\]

and therefore

\[
\kappa=\frac{\ln2}{\Phi_I}
=\frac{\ln2}{24\pi}.
\]

The equality of the three integer factorizations is exact. The physical
interpretation of the `8 mix / 3 flavour` count is a PhaseNav/TIR model
statement and remains independently falsifiable.

---

## 6. Poincare/Bloch relation

For a binary pure state

\[
|\psi\rangle
=
\sqrt{\sigma}|0\rangle
+
e^{i\phi}\sqrt{1-\sigma}|1\rangle,
\]

the Bloch polar imbalance is

\[
n_z=2\sigma-1.
\]

Therefore

\[
\sigma=\frac12
\iff
n_z=0,
\]

so the identity axis projects to the Bloch/Poincare equator. On this locus the
population imbalance vanishes and the remaining degree of freedom is phase.

This is why the `Sigma = 1/2` axis, normalized recurrence and spinorial phase
closure belong in the same PhaseNav layer.

---

## 7. API

Module:

`ciel_geometry.phasenav.canon.identity_cycle`

Primary objects:

- `IdentityAxis`
- `CycleCoordinate`
- `CrossDerivation24`

Primary functions:

- `winding_frequency`
- `phase_from_cycle`
- `cycle_from_phase`
- `information_from_projective_cycles`
- `projective_cycles_from_information`
- `information_rate`
- `phase_information_density`
- `spinor_parity`
- `verify_runtime_identity`

The code does not alter the existing 36D state generator, cipher, HTRI
oscillators or operator calculus.

---

## 8. Claim boundary

### Exact / executable

- complement fixed point at `Sigma = 1/2`;
- normalized cycle arithmetic;
- frequency as winding count per unit time;
- spinor parity over integer projective cycles;
- `KAPPA * TAU = ln(2)/12`;
- `8*3 = 12*2 = 6*4 = 24`;
- reproduction of the existing runtime `KAPPA` after selecting `TAU=2*pi`.

### Canonical model statements

- Sigma is the system's axis of identity;
- 8 mixes and 3 flavours are the complete PhaseNav counts for this branch;
- one information quantum `ln(2)` corresponds to 12 projective / 6 spinor
  recurrences;
- the above structures constitute a fundamental information-cycle mechanism.

### Not claimed here

- derivation of physical time `t` from `tau`;
- proof that `pi` is uniquely derivable from the local PhaseNav curvature;
- Jarlskog-sector identification;
- a proof of the Riemann hypothesis;
- any nonlocal or cosmological physical mechanism.

Those questions remain separate bridge obligations.
