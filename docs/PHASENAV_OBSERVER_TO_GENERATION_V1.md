# PhaseNav Observer-to-Generation Canon v1

## 1. Scope

This canon defines one complete computational chain:

\[
\text{Observer}
\rightarrow
\text{Observation}
\rightarrow
\text{Intention}
\rightarrow
\text{Context}
\rightarrow
\text{Holonomic Memory}
\rightarrow
\text{HTRI}_{CPU/GPU/AI/MCP}
\rightarrow
\text{Dynamical State}
\rightarrow
\text{GenerationPlan}.
\]

`GenerationPlan` is the terminal PhaseNav object. Natural-language projection is
performed by **CIELingo**, not by PhaseNav. PhaseNav therefore contains no
sentence templates, token decoder, lexical sampler or text-producing fallback in
this canon.

The implementation is a finite numerical model. It supports CPU execution and an
optional CuPy GPU backend. Claims about a physical HTRI carrier, nonlocal channel
or quantum substrate are not assumed by the computational canon and require
separate preregistered validation.

## 2. Canonical state

At discrete internal time \(t\), the complete state is

\[
\Sigma_t =
\left(
O_t,
X_t,
\mathcal I_t,
C_t,
\mathcal M_t,
\Xi_t,
\phi_t,
\pi_t,
\Gamma_t
\right),
\]

where:

- \(O_t\) is the observer state;
- \(X_t\) is the encoded observation;
- \(\mathcal I_t\) is intention;
- \(C_t\) is the contextual potential field;
- \(\mathcal M_t\) is phase-holonomic memory;
- \(\Xi_t\) is the CPU/GPU oscillator field;
- \(\phi_t\in T^{36}\) is the active semantic position;
- \(\pi_t\in T_{\phi_t}T^{36}\) is semantic momentum/velocity;
- \(\Gamma_t\) is accumulated holonomy.

The operational space is the existing PhaseNav torus

\[
T^{36}=(S^1)^{36}.
\]

All position coordinates are gauge-wrapped to \([0,2\pi)\). Position and tangent
vectors remain distinct types.

## 3. Observer

The computational observer is

\[
O_t =
\left(
o,
\phi_O,
a,
c,
\chi,
\tau,
n
\right),
\]

with identity \(o\), prior phase \(\phi_O\), non-negative attention vector
\(a\in\mathbb R_{\ge0}^{36}\), confidence \(c\in[0,1]\), ethical weight
\(\chi\in[0,1]\), clock \(\tau\), and sequence number \(n\).

The observer is not an assertion of consciousness. It is the explicit reference
frame relative to which novelty, alignment and state update are computed.

## 4. Observation

For input \(x\), PhaseNav computes

\[
E(x) =
\left(
\phi_x,
\gamma_x,
\Gamma_x,
q_x,
p_x
\right),
\]

where:

- \(\phi_x\) is the terminal 36D phase;
- \(\gamma_x=(\phi_0,\ldots,\phi_N)\) is the sentence trajectory;
- \(\Gamma_x\) is trajectory holonomy;
- \(q_x\) contains deterministic sentence features;
- \(p_x\) is immutable provenance.

Provenance includes source, modality, reliability, ordinal position and SHA-256
digest. Equal input and metadata must produce equal observation receipts.

## 5. Intention

Intention is a target field, not a Boolean flag:

\[
\mathcal I =
\left(
\phi_I,
s_I,
h_I
\right),
\]

where \(\phi_I\in T^{36}\), strength \(s_I\ge0\), and horizon \(h_I>0\).

The effective intention weight is

\[
w_I = \frac{s_I}{h_I}.
\]

## 6. Observer-relative perception

Let \(w_O\), \(w_X\), and \(w_I\) be observer, observation and intention weights.
The perceived state is their weighted circular resultant:

\[
\phi_P^{(d)}
=
\arg\left[
w_Oe^{i\phi_O^{(d)}}
+
w_Xe^{i\phi_X^{(d)}}
+
w_Ie^{i\phi_I^{(d)}}
\right].
\]

The implementation computes:

\[
\nu = \frac{d(\phi_X,\phi_O)}{\pi},
\]

\[
A_O = \max\left(0,1-\frac{d(\phi_P,\phi_O)}{\pi}\right),
\]

\[
A_I = \max\left(0,1-\frac{d(\phi_P,\phi_I)}{\pi}\right),
\]

and coherence \(R(\phi_P)\) using the existing 36D order parameter.

The reference semantic mass is

\[
m_\Psi =
\kappa N_x
\left(
1+R+A_O+A_I
\right),
\]

with token count \(N_x\ge1\). This is an explicit computational scale, not a
claim of SI mass.

## 7. Native phase-holonomic memory

A minimal memory cluster is

\[
M_k =
\left(
\bar\phi_k,
m_k,
a_k,
c_k,
\Gamma_k,
N_k,
t_k,
P_k
\right),
\]

where \(\bar\phi_k\) is circular centroid, \(m_k\) semantic mass, \(a_k\)
activation, \(c_k\) confidence, \(\Gamma_k\) holonomy, \(N_k\) member count,
\(t_k\) age, and \(P_k\) provenance set.

### 7.1 Cluster formation

A new observation joins the nearest cluster only when

\[
d(\phi_X,\bar\phi_k)\le\eta_M,
\]

where \(\eta_M=36\kappa\) is the existing PhaseNav distinguishability scale.
Otherwise a new cluster is created.

The merged centroid is a mass-weighted circular mean. Holonomy updates as

\[
\Gamma'_k =
\Gamma_k+\Gamma_X+
A(\bar\phi_k,\phi_X),
\]

where \(A\) is the existing Berry connection.

### 7.2 Recall

For query \(\phi_q\), recall score is

\[
S_k =
a_kc_km_k
\exp\left[
-\frac{d(\phi_q,\bar\phi_k)^2}{2\eta_M^2}
\right]
\frac{1}{1+\frac12|A(\phi_q,\bar\phi_k)|}.
\]

Recall is therefore jointly radial, activation-weighted, provenance-sensitive and
holonomy-corrected.

### 7.3 Forgetting

No destructive delete is required for ordinary decay:

\[
a_k(t+\Delta t)=a_k(t)e^{-\lambda_M\Delta t}.
\]

Deletion, compaction and archival policy remain separate storage concerns.

## 8. Context field

The canon reuses the existing PhaseNav context field:

\[
\rho_C(\phi)=
\frac{\sum_aw_aK_a(\phi)}{\sum_aw_a},
\]

\[
U_C(\phi)=-\kappa\ln\rho_C(\phi),
\]

\[
\mu_C(\phi)=
\kappa\left[
1+\rho_C(\phi)
\left(
1+\frac{\sigma_C^2(\phi)}{h_C^2}
\right)
\right].
\]

Observer, observation, intention and recalled clusters become explicit context
anchors. The context digest is carried into the final receipt.

## 9. HTRI CPU/GPU oscillator field

The numerical oscillator field is split into logical CPU and GPU populations:

\[
\Xi =
\Xi_{CPU}\oplus\Xi_{GPU}.
\]

The default population is \(N=120\), with baseline frequency

\[
f_0=7.83\ \mathrm{Hz},
\qquad
\omega_0=2\pi f_0.
\]

For oscillator \(i\),

\[
\dot\theta_i =
\omega_i
+
KR\sin(\psi-\theta_i)
+
K_\times R_{\bar b}\sin(\psi_{\bar b}-\theta_i)
+
\sum_s g_s\sin(\phi_s-\theta_i),
\]

where \(b\) denotes CPU or GPU bank, \(\bar b\) the other bank, and sources \(s\)
include:

- observer;
- intention;
- recalled memory;
- AI-induced phase;
- one or more MCP-induced phases.

The implementation is mean-field and vectorized. It does not allocate an
\(N\times N\) pairwise coupling matrix.

When CuPy is available, the logical GPU bank executes through CuPy. Otherwise the
same bank is deterministically emulated by NumPy and the receipt marks
`gpu_emulated=true`. Absence of a GPU may alter backend metadata and floating
point details but must not silently change the equations.

The oscillator state is projected back to \(T^{36}\) by grouped circular means.

## 10. Unified dynamics

The active generation state obeys

\[
m_\Psi\ddot\phi
+
\left[
\mu_C(\phi)+\lambda
\right]\dot\phi
=
-\nabla U_C(\phi)
+
k_I\sin(\phi_I-\phi)
+
k_M\sin(\phi_M-\phi)
+
k_H\sin(\phi_H-\phi).
\]

Here:

- \(\phi_M\) is the recalled-memory resultant, when present;
- \(\phi_H\) is the HTRI projection;
- \(k_I,k_M,k_H\ge0\) are explicit couplings;
- \(\lambda\ge0\) is extra numerical damping.

The reference integrator is deterministic semi-implicit Euler:

\[
\pi_{t+\Delta t}
=
\pi_t+\Delta t\,\ddot\phi_t,
\]

\[
\phi_{t+\Delta t}
=
\left(
\phi_t+\Delta t\,\pi_{t+\Delta t}
\right)\bmod 2\pi.
\]

Each transition accumulates Berry connection into \(\Gamma_t\).

## 11. GenerationPlan

PhaseNav terminates at

\[
G =
\left(
\phi_G,
\phi_O,
\phi_X,
\phi_I,
\phi_C,
\phi_M,
\phi_H,
\gamma_G,
m_\Psi,
\Gamma_G,
R_G,
S_G,
T_G,
\mathcal R,
Q,
B,
D
\right),
\]

where:

- \(\phi_G\) is content phase;
- \(\phi_O,\phi_X,\phi_I,\phi_C,\phi_M,\phi_H\) preserve component states;
- \(\gamma_G\) is the full dynamical trajectory;
- \(m_\Psi\) is semantic mass;
- \(\Gamma_G\) is total holonomy;
- \(R_G\) is coherence;
- \(S_G\) is normalized phase entropy;
- \(T_G\) is a bounded generation-temperature recommendation;
- \(\mathcal R\) is recalled memory metadata;
- \(Q\) is sentence-feature metadata;
- \(B\) is HTRI backend metadata;
- \(D\) is the SHA-256 receipt.

`GenerationPlan` contains no natural-language output.

## 12. PhaseNav → CIELingo ABI

The only canonical text-generation boundary is:

```text
phasenav.generation-plan/v1
```

The payload contains:

- all component phase vectors;
- full trajectory;
- mass, holonomy, coherence, entropy and temperature;
- recalled cluster IDs and scores;
- deterministic features;
- HTRI backend and order parameter;
- receipt SHA-256.

CIELingo owns:

- lexical realization;
- grammar;
- morphology;
- discourse structure;
- language selection;
- decoding and final text.

PhaseNav must not silently import a text generator to fill a missing CIELingo
projection.

## 13. Receipts and reproducibility

The receipt hashes:

- formalism version;
- observer identity and sequence;
- observation digest;
- intention;
- context digest;
- recalled memory IDs;
- post-update memory digest;
- HTRI backend and order;
- final 36D state;
- dynamical holonomy.

Equal initial state, inputs, backend and numerical environment should produce the
same receipt. Backend changes must be visible.

## 14. Computational invariants

1. Every phase position has exactly 36 finite coordinates.
2. Every position is gauge-wrapped to \([0,2\pi)\).
3. Observer sequence increases exactly once per completed pipeline step.
4. Memory merge is bounded by \(\eta_M\).
5. HTRI uses vectorized mean-field coupling.
6. AI and MCP induction are explicit inputs, never hidden ambient authority.
7. GPU fallback is reported, never concealed.
8. Context digest propagates into the dynamics receipt.
9. PhaseNav emits `GenerationPlan`, never natural-language text.
10. CIELingo projection can be replaced without changing PhaseNav dynamics.

## 15. Validation boundary

The following are directly testable computational claims:

- determinism of observation encoding;
- cluster merge and recall ordering;
- activation decay;
- CPU/GPU bank dimensions;
- bounded order parameters;
- influence of AI/MCP induction;
- deterministic orbit length;
- absence of text in `GenerationPlan`;
- JSON serializability of the CIELingo payload;
- receipt stability under equal initial conditions.

The following remain separate hypotheses:

- identification of HTRI with a physical carrier;
- physical nonlocality;
- quantum advantage;
- hardware effects not explained by ordinary CPU/GPU execution.

No computational test in this module alone establishes those physical claims.
