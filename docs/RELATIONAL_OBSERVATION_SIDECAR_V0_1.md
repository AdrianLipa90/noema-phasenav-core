# Relational Observation Sidecar v0.1

Status: `RUNTIME_SIDECAR / STRICT_36D_CORE_PRESERVED / SCIENTIFIC_BINDING_EXTERNAL`

This contract lets the PhaseNav runtime carry a validated relational-observation packet alongside the canonical 36D state without reinterpreting that packet as part of (T^{36}).

## 1. Core invariant

The runtime state remains exactly

[
oxed{T^{36}=(S^1)^{36}.}
]

Every public phase/operator/orbit vector still contains exactly 36 finite coordinates.

The relational observation object is stored and validated as a sidecar:

[
oxed{
	ext{T36 state}
oplus
	ext{relational observation sidecar}
}
]

with no coordinate injection.

## 2. Accepted upstream packet

The preferred upstream execution packet is

[
	exttt{PNCS_RELATIONAL_OBSERVATION_PACKET_V0_1}
]

from:

https://github.com/AdrianLipa90/PhaseNav-Natural-Coding-System/pull/70

The sidecar must preserve:
- observable tuple ((omega,I,phi,Gamma,C));
- identifiability ranks;
- cycle rank;
- exact upstream commit provenance;
- `flatten_into_t36=false`;
- `semantic_holonomy_equivalence=OPEN`.

## 3. Runtime behavior

The runtime may:
- validate the packet;
- retain it as immutable observation metadata;
- attach it to an execution/retrieval result;
- expose its local identifiability status.

The runtime must not:
- append five coordinates to T36;
- replace any canonical 36D coordinate;
- infer a physical source from the packet;
- identify chemical/spectroscopic holonomy with semantic holonomy;
- promote candidate science because software validation succeeds.

## 4. Cross-repository links

- FPDG: https://github.com/AdrianLipa90/Fundamental-Physics-Dependency-Graph/pull/22
- PNCS: https://github.com/AdrianLipa90/PhaseNav-Natural-Coding-System/pull/70
- PhaseNav Telescope: https://github.com/AdrianLipa90/PhaseNav-Telescope-Spectral-Modulation/pull/24
- Resonant Chemistry: https://github.com/AdrianLipa90/Resonant-Chemistry/pull/27
- OES: https://github.com/AdrianLipa90/Orbital-Eclipse-Spectroscopy/pull/14
- IDT: https://github.com/AdrianLipa90/Informational-Dynamics-of-Time/pull/101
- GREMLIN: https://github.com/AdrianLipa90/GREMLIN/pull/88
- QHTRI phase optics: https://github.com/AdrianLipa90/QHTRI-Induced-Holonomic-Potentials-for-Neutrino-Flavour-Transport-and-Phase-Optics/pull/1
- TIR: https://github.com/AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations/pull/174
- RFC: https://github.com/AdrianLipa90/Relational-Field-Closure/pull/142
