# Recovered Legacy Glossary -> Bivector36 SO(2) No-Go v0.1
Date: 2026-09-26
Status: ANALYTIC_NO_GO + FULL_GLOSSARY_AUDIT_PASS

## 1. Recovered source

The persistent `glossary_36d.jsonl` contains 115 PhaseNav cards with a
recovered phase-marker formula of the form

    phi_i(q) =
      [kappa*tau
       + alpha_M*tau*(i mod 7)
       + (2/7)*tau*floor(i/7)
       + (q mod 5)*tau/7] mod tau.

Thus the quark-prime dependence is independent of coordinate index i.

Write

    B_i =
      [kappa*tau
       + alpha_M*tau*(i mod 7)
       + (2/7)*tau*floor(i/7)] mod tau.

Then

    phi_i(q) = B_i + delta(q) mod tau,

where

    delta(q)=(q mod 5)*tau/7.

Therefore for any two recovered glossary markers

    wrap(phi_i(q2)-phi_i(q1)) = Delta(q1,q2)

for all i.

The entire recovered family is consequently a global-U(1) orbit of a fixed
36-coordinate template, modulo the finite q mod 5 selection used by the
recovered formula.

## 2. Full-file computational audit

The full 115-line glossary was parsed.

Observed:
- 115 valid phase-marker records;
- 6 quark_prime values: 3,5,7,11,13,17;
- one recovered phase-marker formula;
- 4 unique 36D vectors;
- records sharing a quark_prime use identical vectors;
- all pairwise vector differences are coordinate-independent to maximum
  circular spread 7.82e-11;
- the observed common shifts match the q mod 5 term with maximum error
  1.21e-12;
- after removing the q mod 5 shift, every observed vector reduces to one
  template with maximum circular error 7.70e-11.

The four-vector count follows from residue collisions, e.g.

    3 mod 5 = 13 mod 5,
    7 mod 5 = 17 mod 5.

## 3. Bivector SO(2) incompatibility

Suppose, only as a negative control, that the 36 relative phases were forcibly
reshaped row-major into a 6x6 matrix.

Because every coordinate difference is the same,

    X_legacy = Delta * Ones_(6x6).

The calibrated physical orbital generator J_36 has four nonzero entries:

    -1,+1,-1,+1,

whose total sum is zero. Hence

    <X_legacy,J_36>_F
      = Delta * sum_(r,c) J_36[r,c]
      = 0.

Therefore the best SO(2) generator coefficient is

    theta_hat
      = <X_legacy,J_36>_F / <J_36,J_36>_F
      = 0.

For every nonzero legacy common shift,

    ||X_legacy-theta_hat J_36||_F
      = ||X_legacy||_F
      > 0.

So even the unauthorized historical row-major reinterpretation is orthogonal
to the calibrated x-y orbital generator.

## 4. Consequence

The recovered legacy glossary phase family cannot be promoted into the typed
physical BIVECTOR_OPERATOR_36 SO(2) carrier by:
- dimension matching;
- row-major 6x6 reshaping;
- treating the recovered q-dependent common phase as physical x-y twist.

The only zero-residual cases are q pairs with the same q mod 5 phase marker,
which carry zero relative angle under this test.

This does not invalidate generic PhaseNav T36. It establishes that the
recovered glossary phase-marker family and the typed physical bivector SO(2)
carrier are different representations and require an explicit new relation if
they are ever to interact physically.

## 5. Closed status

    direct recovered-glossary phase marker
      -> physical Bivector36 SO(2)

is CLOSED as NO_GO under the recovered formula and current typed basis.

The valid physical path remains

    measured/declared physical Moire geometry
      -> typed Moire log-phase basis
      -> theta J_36
      -> BIVECTOR_OPERATOR_36.
