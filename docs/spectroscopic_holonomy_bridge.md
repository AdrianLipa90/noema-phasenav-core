# PhaseNav Spectroscopic Holonomy Bridge v0.1

Status: `COMPUTATIONAL_GRAPH_HOLONOMY / CHYBA / CANON_NOT_PROMOTED`

Date: 2026-09-19

## Scope

This layer turns the already validated finite U(1) path algebra into a typed
spectroscopic graph state. It does **not** identify the semantic connection
`A_sem` with a chemical, electromagnetic, hypercharge, or other physical
field.

The common mathematical primitive is

[
mathcal T_G[A;gamma]
=
exp!left(iint_gamma Aight).
]

Typed realizations remain distinct. In particular,

[
W_{m sem}[gamma]
=
mathcal T_G[A_{m sem};gamma]
]

is the semantic nonlocal phase transporter, while a future physically bound
chemical realization would require its own independently justified
`A_chem` and `W_chem`.

## 1. Gauge-reduced graph coordinates

For a finite graph (G=(V,E)) with (C) connected components,

[
oxed{eta_1 = E - V + C}
]

is the first Betti number and therefore the number of independent graph cycles.

For U(1) edge phases, vertex-local gauge freedom removes all tree-edge phase
coordinates. The remaining closed-loop coordinates form

[
H^1(G;U(1)) simeq U(1)^{eta_1}.
]

Consequences:

- tree: (eta_1=0), no independent closed-loop U(1) phase;
- one ring: (eta_1=1), one independent holonomy;
- multi-cycle graph: one independent phase per cycle-basis element.

The implementation therefore rejects a graph state whose declared cycle-phase
count differs from (eta_1).

## 2. Same-endpoint path interference

For two paths (p_1,p_2:j	o i),

[
W[p_1]W[p_2]^*
=
W[p_1circ p_2^{-1}],
]

so their relative phase is exactly the holonomy of the closed loop obtained by
following (p_1) and returning along (p_2).

This is the computational bridge

[
A
	o
W[p]
	o
	ext{relative-path interference}
	o
	ext{response observables}.
]

No physical substrate is implied by this identity alone.

## 3. Exact ring control model

For an (N)-site nearest-neighbour ring with onsite energy (epsilon),
hopping amplitude (t), and total U(1) holonomy (Phi),

[
oxed{
E_m(Phi)
=
epsilon
+
2tcosleft(rac{2pi m+Phi}{N}ight),
quad m=0,ldots,N-1.
}
]

The unlabelled spectrum is (2pi)-periodic in (Phi). PhaseNav exposes this
as a deterministic control model and emits pairwise kinematic energy-gap
candidates. Those gaps are **not** asserted to be allowed optical transitions;
dipole operators, selection rules, spin, electron correlation, vibronic
structure, linewidths, and environmental effects remain separate model inputs.

## 4. Phase-vibronic expansion

For normal coordinates (Q_a), a cycle phase may be expanded around a declared
reference geometry,

[
Phi_k(Q)
=
Phi_k^{(0)}
+
sum_a g_{ka}Q_a
+
O(Q^2),
]

with

[
g_{ka}
=
left.rac{partialPhi_k}{partial Q_a}ight|_{Q_0}.
]

The v0.1 implementation provides the explicit first-order map only. A physical
interpretation of (g_{ka}) requires an independently validated mapping from
molecular geometry/electronic structure to the graph connection.

## 5. Spectroscopic inverse problem

Let observables be

[
O_alpha
=
O_alpha(Phi_1,ldots,Phi_{eta_1}).
]

PhaseNav evaluates the numerical sensitivity matrix

[
oxed{
J_{alpha k}
=
rac{partial O_alpha}{partialPhi_k}.
}
]

For diagonal observable-noise covariance
(Sigma=operatorname{diag}(sigma_alpha^2)), it also evaluates

[
oxed{
F
=
J^TSigma^{-1}J.
}
]

This supplies an explicit identifiability surface:

- (operatorname{rank}J=eta_1): all declared cycle phases are locally
  observable under the chosen observable model;
- (operatorname{rank}J<eta_1): at least one phase combination is locally
  spectroscopically unidentifiable.

Rank evaluation itself is left to the consuming numerical layer in v0.1;
PhaseNav emits the exact Jacobian and Fisher matrices.

## 6. Theorem chain

The implemented bridge is

[
oxed{
G_{m model}
	o
eta_1
	o
H^1(G;U(1))
	o
{Phi_k}
	o
W[p]
	o
H_{m model}(Phi)
	o
O(Phi)
	o
J
	o
F.
}
]

For the exact ring control model,

[
H_{m model}(Phi)
	o
{E_m(Phi)}
	o
{Delta E_{mn}(Phi)}.
]

A future chemistry binding may extend this to Green functions, response
functions, dipole observables, time-domain coherence and multidimensional
spectroscopy, but those physical bindings are not promoted here.

## PASS

The v0.1 software layer claims only:

- generic finite U(1) transport algebra reused without semantic/chemical
  identification;
- graph cycle rank (eta_1=E-V+C);
- exactly (eta_1) declared independent cycle holonomies;
- same-endpoint relative-path phase equals a closed-loop holonomy;
- exact (N)-ring spectrum formula and (2pi) spectral periodicity;
- explicit first-order phase-vibronic linearization;
- finite-difference spectroscopic Jacobian;
- Fisher information for diagonal observable-noise covariance.

## OPEN / NOT CLAIMED

- measured physical gauge field;
- physical nonlocal signalling;
- identification of `A_sem` with a chemical field;
- Standard Model hypercharge;
- weak-boson (W^pm);
- proof of consciousness;
- molecular Hamiltonian parameter extraction from first principles;
- optical selection rules or oscillator strengths;
- physical substrate identification.

Epistemic default remains `CHYBA`; `canon_allowed=false`.
