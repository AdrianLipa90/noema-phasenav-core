"""HTRI time hypercrystal on the PhaseNav 36D memory crystal.

This module is a finite, explicitly testable research model.  It does not claim a
physical HTRI carrier.  The construction has four layers:

1. Every 36D phase facet is represented by the normalized phasor state
   |a> = exp(i phi_a) / sqrt(36).
2. The crystal is embedded in the open Poincare disk by a deterministic
   two-component projection of the 72D real phasor representation.
3. A Hermitian magnetic graph Laplacian models covariant motion between facets;
   its edge phase is the Pancharatnam/Bargmann phase arg <a|b>.
4. A discrete internal-time fibre is added.  The total Hamiltonian contains a
   Hermitian intention-fluctuation operator and a temporal-shear coupling.

The finite-dimensional Schrodinger Lagrangian is

    L = (i hbar / 2)(Psi^dagger Psi_dot - Psi_dot^dagger Psi)
        - Psi^dagger H Psi.

All default coefficients are dimensionless unless an external energy scale is
provided.  Physical units and carrier identification remain separate bridge
obligations.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy import sparse
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree
from scipy.sparse.linalg import expm_multiply

from .phase_memory import CRYSTAL_META_PATH, CRYSTAL_VEC_PATH
from .pnv_runtime import KAPPA, M_sentence_phase, TAU

_EPS = 1.0e-12


@dataclass(frozen=True)
class HypercrystalConfig:
    """Numerical parameters of the finite HTRI hypercrystal model."""

    neighbours: int = 8
    time_slices: int = 5
    delta_tau: float = 1.0
    spatial_coupling: float = 1.0
    poincare_coupling: float = 0.10
    curvature_coupling: float = 0.20
    tensor_well_coupling: float = 0.10
    memory_well_coupling: float = 0.05
    resonance_coupling: float = 0.10
    intention_fluctuation_coupling: float = 1.0
    temporal_kinetic_coupling: float = 0.25
    temporal_frequency: float = 0.10
    shear_coupling: float = 0.05
    energy_scale: float = 1.0
    hbar: float = 1.0
    embedding_quantile: float = 0.99

    def __post_init__(self) -> None:
        if self.neighbours < 1:
            raise ValueError("neighbours must be >= 1")
        if self.time_slices < 1:
            raise ValueError("time_slices must be >= 1")
        if self.delta_tau <= 0.0:
            raise ValueError("delta_tau must be positive")
        if self.energy_scale <= 0.0:
            raise ValueError("energy_scale must be positive")
        if self.hbar <= 0.0:
            raise ValueError("hbar must be positive")
        if not 0.5 <= self.embedding_quantile < 1.0:
            raise ValueError("embedding_quantile must be in [0.5, 1)")


@dataclass(frozen=True)
class PoincareEmbedding:
    """A deterministic embedding of crystal facets into the open unit disk."""

    coordinates: np.ndarray  # complex128, shape (N,)
    feature_mean: np.ndarray  # float64, shape (72,)
    basis: np.ndarray  # float64, shape (72, 2)
    radial_scale: float

    def __post_init__(self) -> None:
        if self.coordinates.ndim != 1:
            raise ValueError("coordinates must be one-dimensional")
        if np.any(np.abs(self.coordinates) >= 1.0):
            raise ValueError("all Poincare coordinates must lie inside the open unit disk")


@dataclass(frozen=True)
class HypercrystalOperators:
    """Sparse operators defining the crystal and time-fibre dynamics."""

    disk_coordinates: np.ndarray
    resonance: np.ndarray
    base_potential: np.ndarray
    intention_values: np.ndarray
    spatial_hamiltonian: csr_matrix
    intention_operator: csr_matrix
    intention_fluctuation: csr_matrix
    time_coordinates: np.ndarray
    temporal_momentum: csr_matrix
    temporal_hamiltonian: csr_matrix
    hamiltonian: csr_matrix


@dataclass(frozen=True)
class LagrangianEvaluation:
    """Decomposition of the finite-dimensional Schrodinger Lagrangian."""

    lagrangian: float
    symplectic_term: float
    energy_expectation: float
    norm: float


def load_crystal_arrays(
    vec_path: Path | str | None = None,
    meta_path: Path | str | None = None,
    *,
    sample: int | None = None,
    seed: int = 0,
) -> tuple[np.ndarray, list[dict]]:
    """Load crystal phase vectors and aligned metadata.

    ``sample`` selects a deterministic, sorted random subset without changing the
    original files.  It is useful for fast experiments and unit tests.
    """

    vp = Path(vec_path) if vec_path is not None else CRYSTAL_VEC_PATH
    mp = Path(meta_path) if meta_path is not None else CRYSTAL_META_PATH
    vectors = np.asarray(np.load(vp, mmap_mode="r"), dtype=np.float64)
    if vectors.ndim != 2 or vectors.shape[1] != 36:
        raise ValueError(f"expected crystal shape (N, 36), got {vectors.shape}")

    metadata: list[dict] = []
    with mp.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                metadata.append(json.loads(line))
    if len(metadata) != vectors.shape[0]:
        raise ValueError(
            f"crystal vector/metadata mismatch: {vectors.shape[0]} vs {len(metadata)}"
        )

    if sample is None or sample >= vectors.shape[0]:
        return np.array(vectors, copy=True), metadata
    if sample < 2:
        raise ValueError("sample must be at least 2")

    rng = np.random.default_rng(seed)
    indices = np.sort(rng.choice(vectors.shape[0], size=sample, replace=False))
    return np.array(vectors[indices], copy=True), [metadata[int(i)] for i in indices]


def phase_vectors_to_states(phase_vectors: np.ndarray) -> np.ndarray:
    """Convert N x 36 phase vectors into normalized complex phasor states."""

    phases = np.asarray(phase_vectors, dtype=np.float64)
    if phases.ndim != 2 or phases.shape[1] != 36:
        raise ValueError(f"expected shape (N, 36), got {phases.shape}")
    return np.exp(1j * phases) / np.sqrt(phases.shape[1])


def _fix_component_signs(basis: np.ndarray) -> np.ndarray:
    out = np.array(basis, copy=True)
    for column in range(out.shape[1]):
        pivot = int(np.argmax(np.abs(out[:, column])))
        if out[pivot, column] < 0.0:
            out[:, column] *= -1.0
    return out


def embed_poincare_disk(
    phase_vectors: np.ndarray,
    *,
    quantile: float = 0.99,
) -> PoincareEmbedding:
    """Embed the 36D phase crystal into the open Poincare disk.

    The phase torus is represented in R^72 by concatenated cosine and sine
    channels.  The two dominant centred singular directions are retained and
    radially compressed using tanh.  The construction is deterministic,
    preserves local directions in the selected plane, and guarantees |z| < 1.
    """

    if not 0.5 <= quantile < 1.0:
        raise ValueError("quantile must be in [0.5, 1)")
    phases = np.asarray(phase_vectors, dtype=np.float64)
    if phases.ndim != 2 or phases.shape[1] != 36:
        raise ValueError(f"expected shape (N, 36), got {phases.shape}")
    if phases.shape[0] < 2:
        raise ValueError("at least two facets are required for an embedding")

    features = np.concatenate((np.cos(phases), np.sin(phases)), axis=1)
    mean = features.mean(axis=0)
    centred = features - mean
    _, _, vt = np.linalg.svd(centred, full_matrices=False)
    basis = _fix_component_signs(vt[:2].T)
    plane = centred @ basis
    radii = np.linalg.norm(plane, axis=1)
    positive = radii[radii > _EPS]
    radial_scale = float(np.quantile(positive, quantile)) if positive.size else 1.0
    radial_scale = max(radial_scale, _EPS)

    compressed_radius = np.tanh(radii / radial_scale)
    directions = np.zeros_like(plane)
    nonzero = radii > _EPS
    directions[nonzero] = plane[nonzero] / radii[nonzero, None]
    xy = directions * compressed_radius[:, None]
    coordinates = xy[:, 0] + 1j * xy[:, 1]
    # tanh is strictly below one, but clip protects against platform rounding.
    moduli = np.abs(coordinates)
    too_close = moduli >= 1.0
    if np.any(too_close):
        coordinates[too_close] *= (1.0 - 1.0e-12) / moduli[too_close]

    return PoincareEmbedding(
        coordinates=np.asarray(coordinates, dtype=np.complex128),
        feature_mean=np.asarray(mean, dtype=np.float64),
        basis=np.asarray(basis, dtype=np.float64),
        radial_scale=radial_scale,
    )


def poincare_distance(u: complex | np.ndarray, v: complex | np.ndarray) -> np.ndarray:
    """Stable Poincare-disk geodesic distance with curvature -1."""

    ua = np.asarray(u, dtype=np.complex128)
    va = np.asarray(v, dtype=np.complex128)
    if np.any(np.abs(ua) >= 1.0) or np.any(np.abs(va) >= 1.0):
        raise ValueError("Poincare distance requires |z| < 1")
    ratio = np.abs(ua - va) / np.maximum(np.abs(1.0 - np.conj(ua) * va), _EPS)
    ratio = np.clip(ratio, 0.0, 1.0 - 1.0e-15)
    return 2.0 * np.arctanh(ratio)


def _robust_standardize(values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    scale = max(1.4826 * mad, float(np.std(arr)), _EPS)
    return (arr - median) / scale


def _metadata_field(metadata: Sequence[dict], key: str) -> np.ndarray:
    return np.asarray([float(item.get(key, 0.0) or 0.0) for item in metadata], dtype=np.float64)


def _target_phase_vector(target: str | Sequence[float] | np.ndarray) -> np.ndarray:
    if isinstance(target, str):
        phase = np.asarray(M_sentence_phase(target), dtype=np.float64)
    else:
        phase = np.asarray(target, dtype=np.float64)
    if phase.shape != (36,):
        raise ValueError(f"intention target must be 36D, got {phase.shape}")
    return phase % TAU


def build_intention_operator(
    phase_vectors: np.ndarray,
    target: str | Sequence[float] | np.ndarray,
) -> tuple[csr_matrix, csr_matrix, np.ndarray, np.ndarray]:
    """Construct a bounded Hermitian intention observable and its fluctuation.

    Resonance is R_a = |<a|I>|^2.  The bounded observable has eigenvalues
    i_a = 2 R_a - 1 in [-1, 1].  The fluctuation operator is

        Delta I = I - mean(i_a) 1.

    Both operators are real diagonal and therefore Hermitian.
    """

    states = phase_vectors_to_states(phase_vectors)
    target_state = np.exp(1j * _target_phase_vector(target)) / np.sqrt(36.0)
    resonance = np.abs(states.conj() @ target_state) ** 2
    resonance = np.clip(np.real(resonance), 0.0, 1.0)
    values = 2.0 * resonance - 1.0
    centred = values - float(values.mean())
    intention = sparse.diags(values, offsets=0, format="csr", dtype=np.complex128)
    fluctuation = sparse.diags(centred, offsets=0, format="csr", dtype=np.complex128)
    return intention, fluctuation, resonance, centred


def build_magnetic_poincare_laplacian(
    phase_vectors: np.ndarray,
    disk_coordinates: np.ndarray,
    *,
    neighbours: int = 8,
) -> csr_matrix:
    """Build a Hermitian magnetic graph Laplacian on the Poincare disk.

    Edge magnitudes are Gaussian functions of hyperbolic distance.  Edge phases
    are Pancharatnam phases arg <a|b>.  The reverse edge is inserted as the
    complex conjugate, so the resulting covariant Laplacian is Hermitian.
    """

    phases = np.asarray(phase_vectors, dtype=np.float64)
    z = np.asarray(disk_coordinates, dtype=np.complex128)
    n = phases.shape[0]
    if z.shape != (n,):
        raise ValueError("disk coordinate count must match phase-vector count")
    if n < 2:
        raise ValueError("at least two facets are required")
    k = min(max(1, int(neighbours)), n - 1)

    xy = np.column_stack((z.real, z.imag))
    tree = cKDTree(xy)
    _, neighbour_ids = tree.query(xy, k=k + 1)
    states = phase_vectors_to_states(phases)

    pair_distance: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j_raw in np.atleast_1d(neighbour_ids[i])[1:]:
            j = int(j_raw)
            if i == j:
                continue
            a, b = (i, j) if i < j else (j, i)
            if (a, b) not in pair_distance:
                pair_distance[(a, b)] = float(poincare_distance(z[a], z[b]))

    positive = np.asarray([d for d in pair_distance.values() if d > _EPS], dtype=np.float64)
    bandwidth = float(np.median(positive)) if positive.size else 1.0
    bandwidth = max(bandwidth, _EPS)

    rows: list[int] = []
    cols: list[int] = []
    data: list[complex] = []
    degree = np.zeros(n, dtype=np.float64)
    for (i, j), distance in pair_distance.items():
        magnitude = float(np.exp(-0.5 * (distance / bandwidth) ** 2))
        overlap = np.vdot(states[i], states[j])
        phase = float(np.angle(overlap)) if abs(overlap) > _EPS else 0.0
        link = magnitude * np.exp(1j * phase)
        rows.extend((i, j))
        cols.extend((j, i))
        data.extend((-link, -np.conj(link)))
        degree[i] += magnitude
        degree[j] += magnitude

    rows.extend(range(n))
    cols.extend(range(n))
    data.extend(degree.astype(np.complex128))
    return sparse.coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()


def build_crystal_potential(
    disk_coordinates: np.ndarray,
    metadata: Sequence[dict],
    resonance: np.ndarray,
    config: HypercrystalConfig,
) -> np.ndarray:
    """Evaluate the real diagonal potential on crystal facets.

    V combines Poincare radius, informational curvature, Tensor-of-Thought score,
    memory density, and target-intention resonance.  Metadata terms are robustly
    standardized so no source field silently dominates because of scale alone.
    """

    z = np.asarray(disk_coordinates, dtype=np.complex128)
    if len(metadata) != z.shape[0] or resonance.shape != (z.shape[0],):
        raise ValueError("potential inputs must have aligned facet counts")

    radius = poincare_distance(z, np.zeros_like(z))
    curvature = _robust_standardize(_metadata_field(metadata, "kappa_i"))
    tensor_score = _robust_standardize(_metadata_field(metadata, "t_score"))
    memory_density = _robust_standardize(_metadata_field(metadata, "memory_density"))
    resonance_cost = -np.log(np.clip(resonance, _EPS, 1.0))

    potential = config.energy_scale * (
        config.poincare_coupling * radius**2
        + config.curvature_coupling * curvature**2
        - config.tensor_well_coupling * tensor_score
        - config.memory_well_coupling * memory_density
        + config.resonance_coupling * resonance_cost
    )
    return np.asarray(potential, dtype=np.float64)


def build_temporal_operators(config: HypercrystalConfig) -> tuple[np.ndarray, csr_matrix, csr_matrix]:
    """Construct internal-time coordinates, momentum, and Hamiltonian."""

    nt = config.time_slices
    centre = 0.5 * (nt - 1)
    tau = (np.arange(nt, dtype=np.float64) - centre) * config.delta_tau

    if nt == 1:
        zero = sparse.csr_matrix((1, 1), dtype=np.complex128)
        potential = sparse.csr_matrix([[0.0]], dtype=np.complex128)
        return tau, zero, potential

    derivative = sparse.diags(
        diagonals=(
            -np.ones(nt - 1) / (2.0 * config.delta_tau),
            np.ones(nt - 1) / (2.0 * config.delta_tau),
        ),
        offsets=(-1, 1),
        shape=(nt, nt),
        format="csr",
        dtype=np.float64,
    )
    momentum = (-1j * derivative).tocsr()
    kinetic = config.temporal_kinetic_coupling * (momentum @ momentum)
    harmonic = sparse.diags(
        0.5 * (config.temporal_frequency**2) * tau**2,
        offsets=0,
        format="csr",
        dtype=np.complex128,
    )
    temporal_hamiltonian = config.energy_scale * (kinetic + harmonic)
    return tau, momentum, temporal_hamiltonian.tocsr()


def build_htri_hypercrystal(
    phase_vectors: np.ndarray,
    metadata: Sequence[dict],
    intention_target: str | Sequence[float] | np.ndarray,
    config: HypercrystalConfig | None = None,
) -> tuple[PoincareEmbedding, HypercrystalOperators]:
    """Build the complete sparse Hermitian HTRI time-hypercrystal Hamiltonian."""

    cfg = config or HypercrystalConfig()
    phases = np.asarray(phase_vectors, dtype=np.float64)
    if phases.ndim != 2 or phases.shape[1] != 36:
        raise ValueError(f"expected phase vectors of shape (N, 36), got {phases.shape}")
    if len(metadata) != phases.shape[0]:
        raise ValueError("metadata count must match phase-vector count")

    embedding = embed_poincare_disk(phases, quantile=cfg.embedding_quantile)
    magnetic_laplacian = build_magnetic_poincare_laplacian(
        phases,
        embedding.coordinates,
        neighbours=cfg.neighbours,
    )
    intention, fluctuation, resonance, centred = build_intention_operator(
        phases, intention_target
    )
    base_potential = build_crystal_potential(
        embedding.coordinates, metadata, resonance, cfg
    )

    fluctuation_energy = (
        cfg.energy_scale
        * KAPPA
        * cfg.intention_fluctuation_coupling
        * (fluctuation @ fluctuation)
    )
    spatial_hamiltonian = (
        cfg.energy_scale * cfg.spatial_coupling * magnetic_laplacian
        + sparse.diags(base_potential, offsets=0, format="csr", dtype=np.complex128)
        + fluctuation_energy
    ).tocsr()

    tau, temporal_momentum, temporal_hamiltonian = build_temporal_operators(cfg)
    n = phases.shape[0]
    nt = cfg.time_slices
    eye_space = sparse.identity(n, format="csr", dtype=np.complex128)
    eye_time = sparse.identity(nt, format="csr", dtype=np.complex128)

    total = sparse.kron(eye_time, spatial_hamiltonian, format="csr")
    total += sparse.kron(temporal_hamiltonian, eye_space, format="csr")
    if nt > 1 and cfg.shear_coupling != 0.0:
        # Delta I and P_tau act on different tensor factors and commute.  Their
        # Kronecker product is therefore Hermitian; this is the finite temporal-
        # shear coupling between internal time flow and intention fluctuation.
        total += (
            cfg.energy_scale
            * cfg.shear_coupling
            * sparse.kron(temporal_momentum, fluctuation, format="csr")
        )

    operators = HypercrystalOperators(
        disk_coordinates=embedding.coordinates,
        resonance=resonance,
        base_potential=base_potential,
        intention_values=centred,
        spatial_hamiltonian=spatial_hamiltonian,
        intention_operator=intention,
        intention_fluctuation=fluctuation,
        time_coordinates=tau,
        temporal_momentum=temporal_momentum,
        temporal_hamiltonian=temporal_hamiltonian,
        hamiltonian=total.tocsr(),
    )
    return embedding, operators


def hermiticity_error(operator: sparse.spmatrix | np.ndarray) -> float:
    """Return ||A - A^dagger||_F for dense or sparse operators."""

    if sparse.issparse(operator):
        delta = (operator - operator.getH()).tocsr()
        return float(np.sqrt(np.sum(np.abs(delta.data) ** 2)))
    dense = np.asarray(operator, dtype=np.complex128)
    return float(np.linalg.norm(dense - dense.conj().T))


def schrodinger_lagrangian(
    psi: np.ndarray,
    psi_dot: np.ndarray,
    hamiltonian: sparse.spmatrix | np.ndarray,
    *,
    hbar: float = 1.0,
    normalize: bool = False,
) -> LagrangianEvaluation:
    """Evaluate the real finite-dimensional Schrodinger Lagrangian."""

    state = np.asarray(psi, dtype=np.complex128).reshape(-1)
    velocity = np.asarray(psi_dot, dtype=np.complex128).reshape(-1)
    if state.shape != velocity.shape:
        raise ValueError("psi and psi_dot must have the same shape")
    if hamiltonian.shape != (state.size, state.size):
        raise ValueError("Hamiltonian shape does not match state dimension")
    norm = float(np.linalg.norm(state))
    if normalize:
        if norm <= _EPS:
            raise ValueError("cannot normalize a zero state")
        state = state / norm
        velocity = velocity / norm
        norm = 1.0

    h_psi = hamiltonian @ state
    energy_complex = np.vdot(state, h_psi)
    symplectic_complex = 0.5j * hbar * (
        np.vdot(state, velocity) - np.vdot(velocity, state)
    )
    symplectic = float(np.real_if_close(symplectic_complex).real)
    energy = float(np.real_if_close(energy_complex).real)
    return LagrangianEvaluation(
        lagrangian=symplectic - energy,
        symplectic_term=symplectic,
        energy_expectation=energy,
        norm=norm,
    )


def schrodinger_velocity(
    psi: np.ndarray,
    hamiltonian: sparse.spmatrix | np.ndarray,
    *,
    hbar: float = 1.0,
) -> np.ndarray:
    """Return Psi_dot = -i H Psi / hbar."""

    state = np.asarray(psi, dtype=np.complex128).reshape(-1)
    return (-1j / hbar) * (hamiltonian @ state)


def evolve_state(
    psi: np.ndarray,
    hamiltonian: sparse.spmatrix | np.ndarray,
    dt: float,
    *,
    hbar: float = 1.0,
) -> np.ndarray:
    """Apply exp(-i H dt / hbar) without forming a dense propagator."""

    if dt < 0.0:
        raise ValueError("dt must be non-negative")
    state = np.asarray(psi, dtype=np.complex128).reshape(-1)
    if sparse.issparse(hamiltonian):
        return np.asarray(expm_multiply((-1j * dt / hbar) * hamiltonian, state))
    eigenvalues, eigenvectors = np.linalg.eigh(np.asarray(hamiltonian, dtype=np.complex128))
    coefficients = eigenvectors.conj().T @ state
    return eigenvectors @ (np.exp(-1j * eigenvalues * dt / hbar) * coefficients)


def localized_state(
    facet_count: int,
    time_slices: int,
    *,
    facet_index: int = 0,
    time_index: int | None = None,
) -> np.ndarray:
    """Create a normalized basis state |tau_n> tensor |facet_a>."""

    if not 0 <= facet_index < facet_count:
        raise IndexError("facet_index out of range")
    if time_index is None:
        time_index = time_slices // 2
    if not 0 <= time_index < time_slices:
        raise IndexError("time_index out of range")
    state = np.zeros(facet_count * time_slices, dtype=np.complex128)
    state[time_index * facet_count + facet_index] = 1.0
    return state


__all__ = [
    "HypercrystalConfig",
    "PoincareEmbedding",
    "HypercrystalOperators",
    "LagrangianEvaluation",
    "load_crystal_arrays",
    "phase_vectors_to_states",
    "embed_poincare_disk",
    "poincare_distance",
    "build_intention_operator",
    "build_magnetic_poincare_laplacian",
    "build_crystal_potential",
    "build_temporal_operators",
    "build_htri_hypercrystal",
    "hermiticity_error",
    "schrodinger_lagrangian",
    "schrodinger_velocity",
    "evolve_state",
    "localized_state",
]
