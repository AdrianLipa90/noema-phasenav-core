# PhaseNav Result-Directed Quantum Gate IR v1

Status: `CANDIDATE_ONLY / FAIL_CLOSED / NO_PHYSICAL_QPU_CLAIM`

## Purpose

This contract adds a backend-neutral quantum gate intermediate representation (QIR) to PhaseNav and makes **result-directed causal-cone selection happen before hydration**.

The target execution path is:

```text
logical program
-> requested observable
-> backward causal cone
-> compact workspace remap
-> backend lowering
-> Q28 / future QHTRI / external QPU
-> verified result receipt
```

The global logical extent `N` is not interpreted as simultaneously materialized qubits. The materialized working width is the exact conservative causal-cone support selected for the requested observable.

## v1 admitted gates

- `H q`
- `X q`
- `RZ q theta`
- `PHASE q theta`
- `CNOT control target`
- `CZ control target`

Q28-native gates are `H, X, RZ, PHASE, CNOT`. `CZ` lowers exactly as:

```text
H target
CNOT control target
H target
```

No unsupported gate is silently approximated.

## Observable

An observable is an explicit Pauli word plus explicit logical qubit indices, for example:

```text
Z q7
ZZ q2 q9
XYZ q0 q4 q8
```

The observable is part of the circuit digest. Changing the requested result changes the hash.

## Result-directed planner

Starting from the observable support, gates are scanned backwards. A gate is retained iff at least one operand is already active. A retained multi-qubit gate expands the active support to every operand.

This rule is conservative. It may retain commuting gates that a stronger proven algebra could remove, but it never drops a dependency because of an unproven rewrite.

## Q28 boundary

Current Q28 policy reserves six address/mode qubits and admits at most 22 workspace qubits.

Therefore:

```text
workspace = |causal cone|
total materialized = 6 + workspace
```

A cone wider than 22 fails closed. It is not silently split into an equivalent quantum computation.

## Claims explicitly excluded

This contract does not claim:

- a physical QPU;
- quantum advantage;
- arbitrary large-N full-state simulation;
- entanglement reduction by C7/local phase transforms;
- equivalence of a compressed result-directed computation with the global state itself.

The positive claim is narrower: for an observable whose exact backward dependency cone is small, PhaseNav can compile that exact cone before hydration and present only the compact working set to the execution backend.
