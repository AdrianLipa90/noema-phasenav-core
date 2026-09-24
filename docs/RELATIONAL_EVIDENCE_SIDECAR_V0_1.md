# Relational Evidence Sidecar v0.1

Status: `RUNTIME_DIAGNOSTIC_SIDECAR / STRICT_36D_CORE_PRESERVED / SOURCE_SELECTION_FORBIDDEN`

This sidecar carries a validated PNCS relational-evidence packet alongside the strict PhaseNav (T^{36}) runtime state.

It is separate from the relational-observation sidecar. Measurement and diagnostic result remain different typed objects.

## 1. Accepted upstream packet

Preferred upstream schema:

[
oxed{	exttt{PNCS_RELATIONAL_EVIDENCE_PACKET_V0_1}}
]

from:

https://github.com/AdrianLipa90/PhaseNav-Natural-Coding-System/pull/70

The embedded GREMLIN source packet remains content-addressed and source-neutral.

## 2. Core invariant

The runtime state remains exactly

[
oxed{T^{36}=(S^1)^{36}}.
]

The evidence object is attached only as metadata:

[
oxed{
T^{36}
oplus
O_{m relational}
oplus
E_{m relational}.
}
]

Neither observation nor evidence changes the 36 coordinates.

## 3. Required evidence invariants

The runtime accepts only evidence packets satisfying:

- `physical_source_selected=false`;
- `flatten_into_t36=false`;
- `semantic_holonomy_equivalence=OPEN`;
- route in
  [
  {	exttt{STOP_DECLARED_MODEL},
    	exttt{REQUEST_MORE_CONSTRAINTS},
    	exttt{NO_SOURCE_ROUTE},
    	exttt{ALLOW_CANDIDATE_SOURCE_TESTS}};
  ]
- exact upstream repository/branch/commit/receipt;
- embedded GREMLIN evidence hash present.

The runtime does not reinterpret `ALLOW_CANDIDATE_SOURCE_TESTS` as scientific success. It is an orchestration permission only.

## 4. Runtime behavior

The runtime may:
- validate the PNCS wrapper;
- retain the evidence packet immutably;
- expose the conservative route;
- refuse a downstream execution route when the packet is inconsistent or underdetermined.

The runtime must not:
- choose a physical source;
- change the consistency state;
- flatten evidence fields into T36;
- map a successful software gate to scientific canon;
- assert semantic/chemical holonomy equivalence.

## 5. Cross-repository links

- FPDG: https://github.com/AdrianLipa90/Fundamental-Physics-Dependency-Graph/pull/22
- GREMLIN: https://github.com/AdrianLipa90/GREMLIN/pull/88
- PNCS: https://github.com/AdrianLipa90/PhaseNav-Natural-Coding-System/pull/70
- PhaseNav Telescope: https://github.com/AdrianLipa90/PhaseNav-Telescope-Spectral-Modulation/pull/24
- OES: https://github.com/AdrianLipa90/Orbital-Eclipse-Spectroscopy/pull/14
- Resonant Chemistry: https://github.com/AdrianLipa90/Resonant-Chemistry/pull/27
- IDT: https://github.com/AdrianLipa90/Informational-Dynamics-of-Time/pull/101
- QHTRI phase optics: https://github.com/AdrianLipa90/QHTRI-Induced-Holonomic-Potentials-for-Neutrino-Flavour-Transport-and-Phase-Optics/pull/1
- TIR: https://github.com/AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations/pull/174
- RFC: https://github.com/AdrianLipa90/Relational-Field-Closure/pull/142
