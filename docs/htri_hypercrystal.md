# HTRI Poincaré Time Hypercrystal v0.2

## Status

This is a finite software model and derivation scaffold. It models phase geometry, an internal-time fibre, a Hermitian Hamiltonian and a variational Lagrangian on the existing 35,836-facet PhaseNav crystal. It does **not** establish a physical HTRI antenna, a neutrino carrier, nonlocal signalling or an external NOEMA source of truth.

## 1. Crystal Hilbert states

For a crystal facet with phase vector

\[
\phi_a=(\phi_{a1},\ldots,\phi_{a36})\in\mathbb T^{36},
\]

define the normalized phasor state

\[
|a\rangle=\frac1{\sqrt{36}}
\begin{pmatrix}
e^{i\phi_{a1}}&\cdots&e^{i\phi_{a36}}
\end{pmatrix}^{\!T}.
\]

These states are used only as a finite representation of the crystal. Their Pancharatnam link phase is

\[
A_{ab}=\arg\langle a|b\rangle,
\]

and transforms as a discrete gauge connection when the representatives are rephased.

## 2. Poincaré-disk embedding

The torus point is embedded into a real 72-dimensional phasor representation,

\[
x_a=(\cos\phi_a,\sin\phi_a)\in\mathbb R^{72}.
\]

After centring, the two dominant singular directions form a deterministic plane. Let its coordinates be \(y_a\in\mathbb R^2\), with radius \(r_a=\|y_a\|\). The open-disk coordinate is

\[
z_a=\tanh\!\left(\frac{r_a}{s}\right)
\frac{y_{a1}+iy_{a2}}{r_a},\qquad |z_a|<1,
\]

where \(s\) is a robust radial quantile. The Poincaré distance is

\[
d_{\mathbb D}(z,w)=2\operatorname{artanh}
\left|\frac{z-w}{1-\bar z w}\right|.
\]

This is an embedding of the measured crystal, not a claim that the original 36-dimensional phase torus is globally isometric to \(\mathbb D\).

## 3. Covariant crystal Hamiltonian

A symmetric k-nearest-neighbour graph is constructed in the disk. Edge magnitudes are

\[
w_{ab}=\exp\left[-\frac{d_{\mathbb D}(z_a,z_b)^2}{2\sigma^2}\right].
\]

The magnetic adjacency carries the phase connection,

\[
(W_A)_{ab}=w_{ab}e^{iA_{ab}},\qquad
(W_A)_{ba}=(W_A)_{ab}^{*}.
\]

The covariant graph Laplacian is

\[
L_A=D-W_A,
\qquad D_{aa}=\sum_b w_{ab}.
\]

It is Hermitian by construction.

## 4. Potential on the crystal

The diagonal potential uses quantities already stored with the facets:

\[
V_a=E_0\left[
 g_P d_{\mathbb D}(0,z_a)^2
 +g_\kappa\tilde\kappa_a^2
 -g_T\tilde T_a
 -g_M\tilde\rho_{M,a}
 +g_R\left(-\log(R_a+\varepsilon)\right)
\right].
\]

Here \(\tilde\kappa\), \(\tilde T\) and \(\tilde\rho_M\) are robustly standardized versions of `kappa_i`, `t_score` and `memory_density`. The target-intention resonance is

\[
R_a=|\langle a|I\rangle|^2.
\]

## 5. Hermitian intention-fluctuation operator

Define the bounded intention observable

\[
\hat{\mathcal I}=\sum_a (2R_a-1)|a\rangle\langle a|,
\]

and its centred fluctuation

\[
\Delta\hat{\mathcal I}
=\hat{\mathcal I}-\overline{\mathcal I}\,\mathbf 1,
\qquad
\overline{\mathcal I}=\frac1N\operatorname{tr}\hat{\mathcal I}.
\]

Both are Hermitian. The fluctuation energy is

\[
H_I=E_0\,\kappa_I g_I
(\Delta\hat{\mathcal I})^2,
\qquad
\kappa_I=\frac{\ln2}{24\pi}.
\]

The spatial Hamiltonian is therefore

\[
H_{\mathrm{crystal}}
=E_0g_L L_A+\operatorname{diag}(V)+H_I.
\]

## 6. Hypercrystal of internal time

Introduce a discrete internal-time basis \(|\tau_n\rangle\), with a Hermitian finite momentum

\[
P_\tau=-iD_\tau,
\]

where \(D_\tau\) is a real skew-symmetric central-difference matrix. The time Hamiltonian is

\[
H_\tau=E_0\left[g_\tau P_\tau^2
+\frac12\omega_\tau^2\tau^2\right].
\]

The complete hypercrystal space is

\[
\mathcal H_{\mathrm{HTRI}}
=\mathcal H_\tau\otimes\mathcal H_{\mathrm{crystal}}.
\]

Temporal shear couples time flow to intention fluctuation:

\[
H_{\mathrm{shear}}
=E_0g_{\mathrm{shear}}
P_\tau\otimes\Delta\hat{\mathcal I}.
\]

Because the two factors are Hermitian and act on separate tensor factors, this term is Hermitian. The total Hamiltonian is

\[
\boxed{
H_{\mathrm{HTRI}}
=\mathbf1_\tau\otimes H_{\mathrm{crystal}}
+H_\tau\otimes\mathbf1_C
+H_{\mathrm{shear}}.
}
\]

## 7. Lagrangian

For a complex hypercrystal state \(|\Psi(t)\rangle\), use the real first-order Schrödinger Lagrangian

\[
\boxed{
L[\Psi,\dot\Psi]
=\frac{i\hbar}{2}
\left(
\langle\Psi|\dot\Psi\rangle
-\langle\dot\Psi|\Psi\rangle
\right)
-\langle\Psi|H_{\mathrm{HTRI}}|\Psi\rangle.
}
\]

Variation with respect to \(\langle\Psi|\) gives

\[
i\hbar\,\partial_t|\Psi\rangle
=H_{\mathrm{HTRI}}|\Psi\rangle.
\]

For an on-shell state satisfying this equation, the two displayed contributions are equal and the pointwise first-order Lagrangian evaluates to zero; the action remains the correct variational generator, and off-shell paths need not have zero Lagrangian.

## 8. Reproduction

```bash
python -m pytest -q
python examples/htri_hypercrystal_demo.py --sample 512 \
  --intention "protect life and free will"
```

Use `--sample 0` to build the sparse model on all 35,836 facets. The resulting Hilbert dimension is `facets × time_slices`; the matrix remains sparse.
