# PhaseNav TIR × Secret-of-a-Half Dependency Canon v0.7

## Scope

This layer makes the recovered TIR × Secret-of-a-Half dependency structure
executable on the existing PhaseNav canon. It does **not** introduce another
phase engine and does **not** identify intrinsic scientific state with the
PhaseNav routing envelope.

The operational representation remains `T^36`. The recovered coefficient state
`(h,a,b,c)` remains intrinsically four-dimensional.

## Canonical boundary

The v0.6 recovery established the following project-level structural facts:

- `(h,a,b,c)` slot-role routing: `STRUCTURAL_ROLE_ROUTING_PASS`;
- directed orbital sign convention: `IMPLEMENTED_PROJECT_ORBITAL_RULE`;
- relational-gradient orientation operator:
  `IMPLEMENTED_SOURCE_OPERATOR_CANDIDATE_TIR_BINDING`;
- coefficient-enriched or mass-enriched inputs are forbidden as parents of the
  assignment derivation.

v0.7 canonizes these as typed executable dependencies. It does **not** canonize
the still-open physical assignment

`atomic/orbital state -> sign/orientation -> TIR coefficient slot`.

That edge remains `OPEN` until it passes a prospective test without coefficient,
mass, or Yukawa inputs.

## Epistemic firewall

Vectorization is transport and routing, not scientific promotion.

Only `EXACT` and `STANDARD` nodes are proof-strength consumable. Project-derived
algebra, structural runtime results, candidates, open claims, and failed physical
claims preserve their labels downstream.

In particular:

- `KAPPA` remains `PROJECT_DERIVED_EXACT_ALGEBRA`;
- `SOH_C004` remains `OPEN`;
- `SOH_C005` remains `OPEN`;
- Collatz stopping-orientation remains
  `RETROSPECTIVE_CANDIDATE_NEEDS_PROSPECTIVE_TEST`;
- the current TIR neutron-EDM relation remains `PHYSICAL_FAIL`;
- the TIR common-likelihood construction remains `OPEN`.

No PhaseNav execution, routing vector, holonomy receipt, or NOEMA storage event
may change those statuses by itself.

## PhaseNav representation

Every dependency node has a deterministic finite `T^36` routing envelope produced
by the existing hard-canon PhaseNav state generator. Every vector has a SHA-256
identity receipt.

The following invariant is mandatory:

`intrinsic_state != routing_envelope`

Specifically:

`intrinsic coefficient dimension = 4`

while

`PhaseNav routing dimension = 36`.

## NOEMA dependency projection

The module exposes a read-only `noema_projection()` payload containing:

- source schema and receipt SHA;
- PhaseNav routing dimension;
- intrinsic coefficient dimension;
- per-node epistemic status;
- blocked-node set;
- explicit `scientific_promotion = NOT_PERFORMED`;
- explicit `memory_mutation = NOT_PERFORMED`.

NOEMA therefore receives provenance and dependency state. It does not become a
scientific evidence generator, and this PhaseNav module performs no direct NOEMA
memory write.

The durable NOEMA side must retain the same statuses and bind the payload to the
exact PhaseNav commit SHA.

## Scientific debt preserved

This changeset closes a software/dependency debt, not the underlying open
mathematical or physical problems.

Still open after v0.7:

1. prospective TIR slot binding from coefficient-free atomic/orbital state;
2. `SOH_C004`: Xi zero -> canonical native/self-dual closure;
3. `SOH_C005`: dense-family arithmetic Weil positivity, regularization and
   null-space -> native closure;
4. TIR common likelihood with uncertainty/covariance;
5. RG-consistent electroweak comparison;
6. failed neutron-EDM formula, retained as failure;
7. prospective validation of the retrospective Collatz orientation pattern.

## Validation gates

The repository CI must verify:

- every dependency vector is finite and exactly 36D;
- the intrinsic coefficient dimension remains 4;
- v0.6 structural statuses survive unchanged;
- open/failed/retrospective nodes remain canon-blocked;
- `KAPPA` is not silently promoted to external proof strength;
- receipts are deterministic;
- NOEMA projection performs neither memory mutation nor scientific promotion;
- the complete existing PhaseNav test suite still passes.

A merge is promotable only after those gates pass on the exact head commit.
