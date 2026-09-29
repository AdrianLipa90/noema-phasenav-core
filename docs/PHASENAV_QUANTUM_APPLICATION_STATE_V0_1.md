# PhaseNav Quantum Application State v0.1

Schema: `PHASENAV_QUANTUM_APPLICATION_STATE_V0_1`

Status: `CANDIDATE_CONTRACT / T36_NATIVE / NO_EARLY_COLLAPSE / BACKEND_EXPLICIT`

## State

PhaseNav represents a quantum application by the typed state

$
\Psi=(\Phi_{36},\mathcal A,\mathcal T,s,\tau,\Sigma,\mathcal P).
$

`Phi36` remains exactly 36 finite phase coordinates. The additional fields are sidecar/typed relational state and do not flatten into the 36D carrier.

The application state is not a Boolean.

## Evolution

An admitted application operator acts on the complete state,

$
\Psi_{t+1}=\mathcal U(\Psi_t),
$

while preserving provenance and every field not explicitly transformed by the operator contract.

No operator may silently replace an unresolved coefficient, residual, relation, or scalar field with 0/1.

## Observation

Observation is an explicit typed map

$
\mathcal M_c:\Psi\rightarrow(y_c,\Psi'_c,\mathcal P_c).
$

`y_c` belongs to the declared outcome space for channel `c`. A two-outcome measurement may return 0/1, but PhaseNav does not require every channel to be binary.

The pre-measurement state digest and measurement channel are retained in provenance.

## No-early-collapse invariant

$
\boxed{\text{full state} \rightarrow \text{evolution} \rightarrow \text{explicit measurement} \rightarrow \text{classical result}}
$

Forbidden shortcut:

$
\boxed{\text{full state} \not\rightarrow \text{implicit Boolean} \rightarrow \text{continued inference}}
$

Boolean safety/admission gates are allowed because they are explicit observation/protocol boundaries.

## Relationship to Observer-to-Generation canon

The existing Observer-to-Generation state \(\Sigma_t\) already contains continuous phase, momentum, context, memory and holonomy. This contract generalizes the same discipline to application runtime: observation creates a typed result but does not redefine the whole internal state as a bit.

## Backend typing

Every execution receipt must distinguish:

- `CLASSICAL_PHASE_SIMULATION`;
- `ANALOG_PHASE_RUNTIME`;
- `QPU_PHYSICAL`.

Only the last type can support a claim of physical quantum execution. The state model itself is backend-independent.

## PNCS binding

PNCS owns execution and measurement scheduling. PhaseNav owns the state geometry and operators. The binding is:

$
\text{PhaseNav state}\rightarrow\text{PNCS evolution}\rightarrow\text{explicit measurement boundary}.
$

Canonical PNCS consumer: `PNCS_QUANTUM_APPLICATION_RUNTIME_V0_31`.
