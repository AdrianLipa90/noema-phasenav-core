# PhaseNav Quantum Application State v0.1

Status: `CANDIDATE / EXACT_36D / MULTI-BRANCH_STATE / NO_EARLY_COLLAPSE / HARDWARE_REALIZATION_SEPARATE`

Date: 2026-09-29

## Purpose

PhaseNav is the native state space for PNCS quantum applications.

A running application is not represented by a Boolean value. It is represented by a multidimensional relational phase state that may contain multiple active alternatives and is preserved until an explicit observation boundary is invoked.

The architectural invariant is:

```text
classical bit = observation result
classical bit != running application state
```

## State carrier

For N active alternatives:

\[
\boxed{
\mathcal Q =
(\Phi, C, T, s, \tau, \Sigma, P)
}
\]

where

\[
\Phi\in T^{N\times 36}
\]

contains one exact finite PhaseNav 36D phase vector per active alternative, and

\[
C=(c_1,\ldots,c_N),
\qquad
\sum_k |c_k|^2=1
\]

is the normalized complex amplitude carrier.

The remaining components are:

- \(T\): typed relational/dependency tensor;
- \(s\): bounded scalar control/admission field;
- \(\tau\): internal evolution coordinate;
- \(\Sigma\): residual/uncertainty structure;
- \(P\): immutable provenance/operator lineage.

The existing PhaseNav 36D integrity requirement remains exact and unchanged.

## Internal evolution

A PhaseNav quantum application evolves as

\[
\boxed{
\mathcal Q_{t+1}=\mathcal U_t(\mathcal Q_t).
}
\]

Operators may update amplitudes, phase carriers, relational structure, residuals and local runtime coordinates.

Internal predicates, scheduler readiness, test results, worker lifecycle states and release gates MUST NOT replace \(\mathcal Q\) with a Boolean.

They may influence admissibility or operator selection while the state itself remains intact.

## Observation

A declared binary observable defines a measurement/projection pair

\[
\mathcal M_2=\{\Pi_0,\Pi_1\}.
\]

Only the explicit observation boundary may produce

\[
\boxed{
b\in\{0,1\}.
}
\]

The observation is therefore a boundary operation from the multidimensional PhaseNav state to a classical interface.

A receipt must identify:

1. exact pre-observation state;
2. observable / basis;
3. realization backend;
4. observation kernel;
5. result;
6. post-observation state if applicable;
7. provenance.

## Realization classes

The state model is independent of backend.

Declared backend classes are:

```text
PHASENAV_DIGITAL
PHASENAV_ANALOG_CANDIDATE
QPU_PHYSICAL
HYBRID
```

A digital implementation of the state/evolution contract is not automatically evidence of physical quantum execution.

A physical QPU backend requires separate hardware evidence.

## Classical interface firewall

The following may be represented as classical values without collapsing the application state:

```text
transport status
worker lifecycle
admission gate
safety gate
release gate
filesystem/network return code
test PASS/FAIL
```

They are interface/control observations.

They are not the native PhaseNav state.

## Serialization

The machine-readable candidate state envelope is defined by:

`schemas/phasenav_quantum_application_state_v0_1.schema.json`.

Schema validity does not establish amplitude normalization or physical quantum realization by itself; those require runtime validation.

## Dependency direction

\[
\boxed{
\text{PhaseNav multidimensional state}
\to
\text{PNCS quantum application evolution}
\to
\text{explicit observation}
\to
\text{classical interface}
}
\]

This contract deliberately prevents architecture inversion in which repeated Boolean decisions become the primary state model.
