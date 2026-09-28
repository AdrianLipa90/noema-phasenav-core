"""Candidate orbital/scalar/tensor primitives for PhaseNav v0.15.

The layer is intentionally substrate-neutral.  It provides finite numerical
geometry, rank diagnostics, tensor factorizations and exact/controlled
boundary compression primitives.  It does not claim a physical quantum
computer, physical spacetime identification, or automatic canon promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np

SCHEMA = "phasenav.orbital-scalar-tensor-primitives/v0.15"
EPISTEMIC = "CANDIDATE_ONLY"
CANON_ALLOWED = False


def _finite_array(value, *, name: str, ndim: int | None = None, complex_ok: bool = True) -> np.ndarray:
    arr = np.asarray(value, dtype=np.complex128 if complex_ok else np.float64)
    if ndim is not None and arr.ndim != ndim:
        raise ValueError(f"{name} must have ndim={ndim}, got {arr.ndim}")
    if arr.size == 0:
        raise ValueError(f"{name} must be non-empty")
    if not np.all(np.isfinite(arr.real)) or not np.all(np.isfinite(arr.imag)):
        raise ValueError(f"{name} must be finite")
    return arr


def _rank_threshold(singular_values: np.ndarray, shape: Sequence[int], *, rtol: float | None, atol: float) -> float:
    atol = float(atol)
    if not math.isfinite(atol) or atol < 0.0:
        raise ValueError("atol must be finite and >= 0")
    if singular_values.size == 0:
        return atol
    if rtol is None:
        rtol_value = np.finfo(float).eps * max(int(x) for x in shape)
    else:
        rtol_value = float(rtol)
        if not math.isfinite(rtol_value) or rtol_value < 0.0:
            raise ValueError("rtol must be finite and >= 0")
    return max(atol, rtol_value * float(singular_values[0]))


@dataclass(frozen=True)
class SpectralScalars:
    shape: tuple[int, int]
    singular_values: tuple[float, ...]
    numerical_rank: int
    nullity: int
    threshold: float
    spectral_norm: float
    frobenius_norm: float
    nuclear_norm: float
    stable_rank: float
    entropy_rank: float
    condition_number_nonzero: float
    log_singular_volume: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def spectral_scalars(matrix, *, rtol: float | None = None, atol: float = 0.0) -> SpectralScalars:
    """Return scale/rank invariants from the singular spectrum.

    `entropy_rank = exp(-sum p log p)` with p_i = s_i^2 / sum_j s_j^2.
    `stable_rank = ||A||_F^2 / ||A||_2^2`.
    The default numerical-rank tolerance is the machine-epsilon rule
    `eps * max(shape) * sigma_max`, not a fitted model coefficient.
    """
    a = _finite_array(matrix, name="matrix", ndim=2)
    s = np.linalg.svd(a, compute_uv=False)
    threshold = _rank_threshold(s, a.shape, rtol=rtol, atol=atol)
    rank = int(np.count_nonzero(s > threshold))
    # Right-nullity: dimension of ker(A), aligned with GREMLIN column-nullity semantics.
    nullity = int(a.shape[1] - rank)
    spectral = float(s[0]) if s.size else 0.0
    fro = float(np.linalg.norm(s))
    nuclear = float(np.sum(s))
    stable = 0.0 if spectral == 0.0 else float((fro * fro) / (spectral * spectral))
    if fro == 0.0:
        entropy_rank = 0.0
    else:
        p = (s * s) / (fro * fro)
        nz = p[p > 0.0]
        entropy_rank = float(math.exp(-float(np.sum(nz * np.log(nz)))))
    if rank == 0:
        condition = math.inf
        log_volume = -math.inf
    else:
        condition = float(s[0] / s[rank - 1])
        log_volume = float(np.sum(np.log(s[:rank])))
    return SpectralScalars(
        shape=(int(a.shape[0]), int(a.shape[1])),
        singular_values=tuple(float(x) for x in s),
        numerical_rank=rank,
        nullity=nullity,
        threshold=float(threshold),
        spectral_norm=spectral,
        frobenius_norm=fro,
        nuclear_norm=nuclear,
        stable_rank=stable,
        entropy_rank=entropy_rank,
        condition_number_nonzero=condition,
        log_singular_volume=log_volume,
    )


@dataclass(frozen=True)
class ProjectiveOrbitReceipt:
    overlap_abs: float
    fidelity: float
    fubini_study_distance: float
    pancharatnam_phase: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def projective_orbit(a, b) -> ProjectiveOrbitReceipt:
    """Complex-projective overlap on CP^(n-1).

    Fubini-Study distance is arccos(|<a|b>|) after normalization.  The open-path
    Pancharatnam phase is reported separately; it is common-gauge invariant but
    changes under independent endpoint gauges.
    """
    va = _finite_array(a, name="a", ndim=1)
    vb = _finite_array(b, name="b", ndim=1)
    if va.shape != vb.shape:
        raise ValueError("a and b must have equal shape")
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        raise ValueError("projective vectors must be non-zero")
    overlap = complex(np.vdot(va, vb) / (na * nb))
    mag = min(1.0, max(0.0, abs(overlap)))
    return ProjectiveOrbitReceipt(
        overlap_abs=float(mag),
        fidelity=float(mag * mag),
        fubini_study_distance=float(math.acos(mag)),
        pancharatnam_phase=float(math.atan2(overlap.imag, overlap.real)),
    )


PAIR_BASIS_4D = ((0, 1), (0, 2), (0, 3), (2, 3), (3, 1), (1, 2))


def wedge2_4d(u, v) -> tuple[float, ...]:
    """Exterior product u wedge v in the canonical 01,02,03,23,31,12 basis."""
    a = _finite_array(u, name="u", ndim=1, complex_ok=False)
    b = _finite_array(v, name="v", ndim=1, complex_ok=False)
    if a.size != 4 or b.size != 4:
        raise ValueError("wedge2_4d requires two four-component vectors")
    return tuple(float(a[i] * b[j] - a[j] * b[i]) for i, j in PAIR_BASIS_4D)


@dataclass(frozen=True)
class PluckerReceipt:
    relation_value: float
    normalized_residual: float
    simple: bool
    tolerance: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def plucker_simplicity(bivector6, *, tolerance: float | None = None) -> PluckerReceipt:
    """Test decomposability of a 4D bivector in the 01,02,03,23,31,12 basis.

    The Pluecker relation is
        p01*p23 + p02*p31 + p03*p12 = 0.
    This is a finite algebraic simplicity gate, not a physical binding claim.
    """
    b = _finite_array(bivector6, name="bivector6", ndim=1, complex_ok=False)
    if b.size != 6:
        raise ValueError("bivector6 must contain six coefficients")
    if tolerance is None:
        # Six-coordinate algebraic residual: machine precision scaled by carrier size.
        tolerance = np.finfo(float).eps * float(b.size)
    tolerance = float(tolerance)
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("tolerance must be finite and >= 0")
    relation = float(b[0] * b[3] + b[1] * b[4] + b[2] * b[5])
    scale = max(float(np.dot(b, b)), np.finfo(float).tiny)
    residual = abs(relation) / scale
    return PluckerReceipt(relation, residual, residual <= tolerance, tolerance)


@dataclass(frozen=True)
class HodgeSplit4D:
    self_dual: tuple[float, ...]
    anti_self_dual: tuple[float, ...]
    self_dual_norm: float
    anti_self_dual_norm: float
    reconstruction_residual: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def hodge_split_euclidean_4d(bivector6) -> HodgeSplit4D:
    """Euclidean Hodge decomposition Lambda^2 = Lambda^2_+ direct-sum Lambda^2_-."""
    b = _finite_array(bivector6, name="bivector6", ndim=1, complex_ok=False)
    if b.size != 6:
        raise ValueError("bivector6 must contain six coefficients")
    star = np.array((b[3], b[4], b[5], b[0], b[1], b[2]), dtype=float)
    plus = 0.5 * (b.real + star)
    minus = 0.5 * (b.real - star)
    reconstruction = plus + minus
    residual = float(np.linalg.norm(reconstruction - b.real))
    return HodgeSplit4D(
        self_dual=tuple(float(x) for x in plus),
        anti_self_dual=tuple(float(x) for x in minus),
        self_dual_norm=float(np.linalg.norm(plus)),
        anti_self_dual_norm=float(np.linalg.norm(minus)),
        reconstruction_residual=residual,
    )


def _column_space_basis(matrix: np.ndarray) -> np.ndarray:
    """Numerical orthonormal basis of the column span with a machine-epsilon rank gate."""
    u, s, _ = np.linalg.svd(matrix, full_matrices=False)
    threshold = _rank_threshold(s, matrix.shape, rtol=None, atol=0.0)
    rank = int(np.count_nonzero(s > threshold))
    if rank == 0:
        return np.zeros((matrix.shape[0], 0), dtype=np.complex128)
    return u[:, :rank]


def principal_angles(subspace_a, subspace_b) -> tuple[float, ...]:
    """Principal angles between numerical column spans of two finite matrices."""
    a = _finite_array(subspace_a, name="subspace_a", ndim=2)
    b = _finite_array(subspace_b, name="subspace_b", ndim=2)
    if a.shape[0] != b.shape[0]:
        raise ValueError("subspaces must live in the same ambient dimension")
    qa = _column_space_basis(a)
    qb = _column_space_basis(b)
    if qa.shape[1] == 0 or qb.shape[1] == 0:
        return tuple()
    s = np.linalg.svd(qa.conj().T @ qb, compute_uv=False)
    s = np.clip(s.real, 0.0, 1.0)
    return tuple(float(math.acos(float(x))) for x in s)


@dataclass(frozen=True)
class BargmannTriangleReceipt:
    phase: float
    strength: float
    overlap_ab: float
    overlap_bc: float
    overlap_ca: float
    fubini_study_perimeter: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def bargmann_triangle(a, b, c) -> BargmannTriangleReceipt:
    """Gauge-invariant three-point Bargmann phase on complex projective space."""
    vectors=[]
    for name, raw in (("a", a), ("b", b), ("c", c)):
        v=_finite_array(raw, name=name, ndim=1)
        n=float(np.linalg.norm(v))
        if n==0.0:
            raise ValueError("Bargmann vectors must be non-zero")
        vectors.append(v/n)
    va,vb,vc=vectors
    if not (va.shape==vb.shape==vc.shape):
        raise ValueError("Bargmann vectors must have equal shape")
    zab=complex(np.vdot(va,vb)); zbc=complex(np.vdot(vb,vc)); zca=complex(np.vdot(vc,va))
    product=zab*zbc*zca
    if abs(product)==0.0:
        raise ValueError("Bargmann phase is undefined for zero closed-overlap product")
    mags=[min(1.0,max(0.0,abs(z))) for z in (zab,zbc,zca)]
    return BargmannTriangleReceipt(
        phase=float(math.atan2(product.imag,product.real)),
        strength=float(abs(product)),
        overlap_ab=float(mags[0]), overlap_bc=float(mags[1]), overlap_ca=float(mags[2]),
        fubini_study_perimeter=float(math.fsum(math.acos(x) for x in mags)),
    )


@dataclass(frozen=True)
class GrassmannReceipt:
    rank_a: int
    rank_b: int
    principal_angles: tuple[float, ...]
    chordal_distance: float
    geodesic_distance: float
    projector_frobenius_distance: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def grassmann_distance(subspace_a, subspace_b) -> GrassmannReceipt:
    """Basis-independent finite-subspace distances from principal angles."""
    a=_finite_array(subspace_a,name="subspace_a",ndim=2)
    b=_finite_array(subspace_b,name="subspace_b",ndim=2)
    if a.shape[0]!=b.shape[0]:
        raise ValueError("subspaces must live in the same ambient dimension")
    qa=_column_space_basis(a); qb=_column_space_basis(b)
    ra,rb=qa.shape[1],qb.shape[1]
    if ra==0 or rb==0:
        angles=np.zeros(0,dtype=float)
        cos2_sum=0.0
    else:
        sv=np.clip(np.linalg.svd(qa.conj().T@qb,compute_uv=False).real,0.0,1.0)
        angles=np.arccos(sv)
        cos2_sum=float(np.dot(sv,sv))
    chordal=float(math.sqrt(max(0.0,min(ra,rb)-cos2_sum)))
    geodesic=float(np.linalg.norm(angles))
    projector=float(math.sqrt(max(0.0,ra+rb-2.0*cos2_sum)))
    return GrassmannReceipt(ra,rb,tuple(float(x) for x in angles),chordal,geodesic,projector)


def unfold(tensor, mode: int) -> np.ndarray:
    t = _finite_array(tensor, name="tensor")
    mode = int(mode)
    if mode < 0 or mode >= t.ndim:
        raise ValueError("mode outside tensor rank")
    return np.moveaxis(t, mode, 0).reshape(t.shape[mode], -1)


def fold(matrix, shape: Sequence[int], mode: int) -> np.ndarray:
    shape = tuple(int(x) for x in shape)
    if not shape or any(x <= 0 for x in shape):
        raise ValueError("shape must contain positive dimensions")
    mode = int(mode)
    if mode < 0 or mode >= len(shape):
        raise ValueError("mode outside tensor rank")
    m = _finite_array(matrix, name="matrix", ndim=2)
    expected = (shape[mode], int(np.prod(shape) // shape[mode]))
    if m.shape != expected:
        raise ValueError(f"matrix shape must be {expected}, got {m.shape}")
    moved_shape = (shape[mode],) + tuple(shape[i] for i in range(len(shape)) if i != mode)
    moved = m.reshape(moved_shape)
    return np.moveaxis(moved, 0, mode)


def mode_product(tensor, matrix, mode: int) -> np.ndarray:
    """n-mode product: matrix(out_dim, tensor.shape[mode]) times tensor."""
    t = _finite_array(tensor, name="tensor")
    m = _finite_array(matrix, name="matrix", ndim=2)
    mode = int(mode)
    if mode < 0 or mode >= t.ndim:
        raise ValueError("mode outside tensor rank")
    if m.shape[1] != t.shape[mode]:
        raise ValueError("matrix input dimension must match selected tensor mode")
    out = m @ unfold(t, mode)
    new_shape = list(t.shape)
    new_shape[mode] = m.shape[0]
    return fold(out, new_shape, mode)


@dataclass(frozen=True)
class SchmidtReceipt:
    singular_values: tuple[float, ...]
    numerical_rank: int
    retained_rank: int
    threshold: float
    discarded_l2: float
    exact_within_numerical_rank: bool
    left_dim: int
    right_dim: int
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def _retained_rank(s: np.ndarray, shape: Sequence[int], *, rtol: float | None, atol: float, max_rank: int | None) -> tuple[int, int, float]:
    threshold = _rank_threshold(s, shape, rtol=rtol, atol=atol)
    numerical_rank = int(np.count_nonzero(s > threshold))
    retained = numerical_rank
    if max_rank is not None:
        max_rank = int(max_rank)
        if max_rank < 1:
            raise ValueError("max_rank must be >= 1")
        retained = min(retained, max_rank)
    return numerical_rank, retained, threshold


def schmidt_decompose(state, dims: Sequence[int], cut: int, *, rtol: float | None = None, atol: float = 0.0, max_rank: int | None = None):
    """Schmidt/SVD decomposition across a declared tensor-product cut.

    Returns `(U, s, Vh, receipt)` with only retained components.  A rank cap is
    explicitly reported as truncation; no truncated result is labelled exact.
    """
    dims = tuple(int(x) for x in dims)
    if len(dims) < 2 or any(x <= 0 for x in dims):
        raise ValueError("dims must contain at least two positive dimensions")
    cut = int(cut)
    if cut <= 0 or cut >= len(dims):
        raise ValueError("cut must split dims into two non-empty parts")
    v = _finite_array(state, name="state")
    if int(v.size) != int(np.prod(dims)):
        raise ValueError("state size does not match dims")
    left = int(np.prod(dims[:cut]))
    right = int(np.prod(dims[cut:]))
    mat = v.reshape(left, right)
    u, s, vh = np.linalg.svd(mat, full_matrices=False)
    numerical_rank, retained, threshold = _retained_rank(s, mat.shape, rtol=rtol, atol=atol, max_rank=max_rank)
    discarded = float(np.linalg.norm(s[retained:]))
    receipt = SchmidtReceipt(
        singular_values=tuple(float(x) for x in s),
        numerical_rank=numerical_rank,
        retained_rank=retained,
        threshold=float(threshold),
        discarded_l2=discarded,
        exact_within_numerical_rank=(retained == numerical_rank),
        left_dim=left,
        right_dim=right,
    )
    return u[:, :retained], s[:retained], vh[:retained, :], receipt


@dataclass(frozen=True)
class SchmidtEntropyReceipt:
    numerical_rank: int
    threshold: float
    purity: float
    participation_ratio: float
    von_neumann_nats: float
    von_neumann_bits: float
    renyi2_bits: float
    min_entropy_bits: float
    max_weight: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def schmidt_entropy(singular_values, *, rtol: float | None = None, atol: float = 0.0) -> SchmidtEntropyReceipt:
    """Scalar information invariants of a Schmidt spectrum.

    The coefficients are normalized internally through p_i=s_i^2/sum_j s_j^2.
    Rank uses the same declared numerical threshold as the tensor primitives.
    """
    svals=np.asarray(singular_values,dtype=float).reshape(-1)
    if svals.size==0 or not np.all(np.isfinite(svals)) or np.any(svals<0.0):
        raise ValueError("singular_values must be a non-empty finite nonnegative vector")
    total=float(np.dot(svals,svals))
    if total==0.0:
        raise ValueError("Schmidt spectrum must have non-zero norm")
    threshold=_rank_threshold(svals,(svals.size,svals.size),rtol=rtol,atol=atol)
    rank=int(np.count_nonzero(svals>threshold))
    p=(svals*svals)/total
    nz=p[p>0.0]
    purity=float(np.dot(p,p))
    svn_nats=-float(np.sum(nz*np.log(nz)))
    maxw=float(np.max(p))
    return SchmidtEntropyReceipt(
        numerical_rank=rank, threshold=float(threshold), purity=purity,
        participation_ratio=float(1.0/purity),
        von_neumann_nats=svn_nats,
        von_neumann_bits=float(svn_nats/math.log(2.0)),
        renyi2_bits=float(-math.log2(purity)),
        min_entropy_bits=float(-math.log2(maxw)),
        max_weight=maxw,
    )


@dataclass(frozen=True)
class OperatorSchmidtReceipt:
    singular_values: tuple[float, ...]
    numerical_rank: int
    retained_rank: int
    threshold: float
    discarded_frobenius: float
    exact_within_numerical_rank: bool
    dims: tuple[int, int]
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def operator_schmidt_decompose(operator, dims: tuple[int, int] = (2, 2), *, rtol: float | None = None, atol: float = 0.0, max_rank: int | None = None):
    """Operator-Schmidt decomposition for a bipartite linear operator.

    Returns `(A_factors, singular_values, B_factors, receipt)` where
    `O = sum_k s_k A_k tensor B_k` up to the declared truncation.
    """
    da, db = (int(dims[0]), int(dims[1]))
    if da <= 0 or db <= 0:
        raise ValueError("operator dims must be positive")
    op = _finite_array(operator, name="operator", ndim=2)
    dim = da * db
    if op.shape != (dim, dim):
        raise ValueError(f"operator shape must be {(dim, dim)}")
    t = op.reshape(da, db, da, db)
    reshuffled = np.transpose(t, (0, 2, 1, 3)).reshape(da * da, db * db)
    u, s, vh = np.linalg.svd(reshuffled, full_matrices=False)
    numerical_rank, retained, threshold = _retained_rank(s, reshuffled.shape, rtol=rtol, atol=atol, max_rank=max_rank)
    a_factors = tuple(u[:, k].reshape(da, da) for k in range(retained))
    b_factors = tuple(vh[k, :].reshape(db, db) for k in range(retained))
    discarded = float(np.linalg.norm(s[retained:]))
    receipt = OperatorSchmidtReceipt(
        singular_values=tuple(float(x) for x in s),
        numerical_rank=numerical_rank,
        retained_rank=retained,
        threshold=float(threshold),
        discarded_frobenius=discarded,
        exact_within_numerical_rank=(retained == numerical_rank),
        dims=(da, db),
    )
    return a_factors, s[:retained], b_factors, receipt


def reconstruct_operator_schmidt(a_factors, singular_values, b_factors) -> np.ndarray:
    a_factors = tuple(np.asarray(x, dtype=np.complex128) for x in a_factors)
    b_factors = tuple(np.asarray(x, dtype=np.complex128) for x in b_factors)
    s = np.asarray(singular_values, dtype=float)
    if not (len(a_factors) == len(b_factors) == s.size):
        raise ValueError("factor counts must match singular values")
    if not a_factors:
        raise ValueError("at least one factor is required")
    out = np.zeros((a_factors[0].shape[0] * b_factors[0].shape[0], a_factors[0].shape[1] * b_factors[0].shape[1]), dtype=np.complex128)
    for ak, sk, bk in zip(a_factors, s, b_factors):
        out += float(sk) * np.kron(ak, bk)
    return out


@dataclass(frozen=True)
class TensorTrainReceipt:
    original_shape: tuple[int, ...]
    ranks: tuple[int, ...]
    discarded_l2_upper_bound: float
    exact_within_numerical_rank: bool
    storage_elements: int
    dense_elements: int
    compression_ratio_elements: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def tensor_train_svd(tensor, *, rtol: float | None = None, atol: float = 0.0, max_rank: int | Sequence[int] | None = None):
    """TT-SVD/MPS factorization with explicit truncation accounting."""
    t = _finite_array(tensor, name="tensor")
    if t.ndim < 2:
        raise ValueError("tensor_train_svd requires tensor rank >= 2")
    shape = tuple(int(x) for x in t.shape)
    if isinstance(max_rank, Sequence) and not isinstance(max_rank, (str, bytes)):
        caps = tuple(int(x) for x in max_rank)
        if len(caps) != t.ndim - 1:
            raise ValueError("max_rank sequence must have ndim-1 entries")
    elif max_rank is None:
        caps = (None,) * (t.ndim - 1)
    else:
        caps = (int(max_rank),) * (t.ndim - 1)

    cores = []
    ranks = [1]
    work = t.copy()
    discarded_sq = 0.0
    exact = True
    r_prev = 1
    for mode in range(t.ndim - 1):
        work = work.reshape(r_prev * shape[mode], -1)
        u, s, vh = np.linalg.svd(work, full_matrices=False)
        numerical_rank, retained, _ = _retained_rank(s, work.shape, rtol=rtol, atol=atol, max_rank=caps[mode])
        if retained < numerical_rank:
            exact = False
        discarded_sq += float(np.dot(s[retained:], s[retained:]))
        core = u[:, :retained].reshape(r_prev, shape[mode], retained)
        cores.append(core)
        work = s[:retained, None] * vh[:retained, :]
        r_prev = retained
        ranks.append(retained)
    cores.append(work.reshape(r_prev, shape[-1], 1))
    ranks.append(1)
    storage = int(sum(core.size for core in cores))
    dense = int(np.prod(shape))
    receipt = TensorTrainReceipt(
        original_shape=shape,
        ranks=tuple(int(x) for x in ranks),
        discarded_l2_upper_bound=float(math.sqrt(discarded_sq)),
        exact_within_numerical_rank=exact,
        storage_elements=storage,
        dense_elements=dense,
        compression_ratio_elements=float(dense / storage),
    )
    return tuple(cores), receipt


def reconstruct_tensor_train(cores: Sequence[np.ndarray]) -> np.ndarray:
    cores = tuple(np.asarray(c, dtype=np.complex128) for c in cores)
    if len(cores) < 2:
        raise ValueError("at least two TT cores are required")
    if cores[0].ndim != 3 or cores[0].shape[0] != 1:
        raise ValueError("first core must have shape (1,n,r)")
    current = cores[0]
    for nxt in cores[1:]:
        if nxt.ndim != 3 or current.shape[-1] != nxt.shape[0]:
            raise ValueError("adjacent TT ranks do not match")
        current = np.tensordot(current, nxt, axes=([-1], [0]))
    if current.shape[0] != 1 or current.shape[-1] != 1:
        raise ValueError("terminal TT ranks must be one")
    return np.squeeze(current, axis=(0, -1))


@dataclass(frozen=True)
class TuckerReceipt:
    original_shape: tuple[int, ...]
    mode_ranks: tuple[int, ...]
    thresholds: tuple[float, ...]
    discarded_l2_upper_bound: float
    exact_within_numerical_rank: bool
    core_elements: int
    factor_elements: int
    dense_elements: int
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def tucker_hosvd(tensor, *, rtol: float | None = None, atol: float = 0.0, max_ranks: Sequence[int] | None = None):
    """HOSVD/Tucker factorization with per-mode rank receipts.

    The square root of the summed discarded mode-spectrum energies is a standard
    HOSVD reconstruction-error upper bound, not a claim of optimal multilinear rank.
    """
    t=_finite_array(tensor,name="tensor")
    if t.ndim<2:
        raise ValueError("tucker_hosvd requires tensor rank >= 2")
    if max_ranks is None:
        caps=(None,)*t.ndim
    else:
        caps=tuple(int(x) for x in max_ranks)
        if len(caps)!=t.ndim or any(x<1 for x in caps):
            raise ValueError("max_ranks must contain one positive rank per tensor mode")
    factors=[]; ranks=[]; thresholds=[]; discarded_sq=0.0; exact=True
    for mode in range(t.ndim):
        mat=unfold(t,mode)
        u,svals,_=np.linalg.svd(mat,full_matrices=False)
        numerical,retained,threshold=_retained_rank(svals,mat.shape,rtol=rtol,atol=atol,max_rank=caps[mode])
        if retained<numerical:
            exact=False
        discarded_sq+=float(np.dot(svals[retained:],svals[retained:]))
        factors.append(u[:,:retained]); ranks.append(retained); thresholds.append(float(threshold))
    core=t.copy()
    for mode,factor in enumerate(factors):
        core=mode_product(core,factor.conj().T,mode)
    return core,tuple(factors),TuckerReceipt(
        original_shape=tuple(int(x) for x in t.shape), mode_ranks=tuple(ranks), thresholds=tuple(thresholds),
        discarded_l2_upper_bound=float(math.sqrt(discarded_sq)), exact_within_numerical_rank=exact,
        core_elements=int(core.size), factor_elements=int(sum(f.size for f in factors)), dense_elements=int(t.size),
    )


def reconstruct_tucker(core, factors: Sequence[np.ndarray]) -> np.ndarray:
    out=_finite_array(core,name="core")
    factors=tuple(_finite_array(f,name="factor",ndim=2) for f in factors)
    if len(factors)!=out.ndim:
        raise ValueError("one Tucker factor is required per core mode")
    for mode,factor in enumerate(factors):
        if factor.shape[1]!=out.shape[mode]:
            raise ValueError("Tucker factor input rank does not match core mode")
        out=mode_product(out,factor,mode)
    return out


@dataclass(frozen=True)
class BoundaryBasisReceipt:
    ambient_dim: int
    branch_count: int
    numerical_rank: int
    threshold: float
    reconstruction_residual_frobenius: float
    branch_to_rank_ratio: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def compress_boundary_states(states, *, rtol: float | None = None, atol: float = 0.0):
    """Rank-revealing compression of boundary-state columns.

    This finds linear dependence rather than merely duplicate/projective-equal
    branches.  Returns `(basis, coefficients, receipt)` with
    `states ~= basis @ coefficients`.
    """
    x = _finite_array(states, name="states", ndim=2)
    u, s, vh = np.linalg.svd(x, full_matrices=False)
    numerical_rank, retained, threshold = _retained_rank(s, x.shape, rtol=rtol, atol=atol, max_rank=None)
    basis = u[:, :retained]
    coefficients = s[:retained, None] * vh[:retained, :]
    residual = float(np.linalg.norm(x - basis @ coefficients))
    receipt = BoundaryBasisReceipt(
        ambient_dim=int(x.shape[0]),
        branch_count=int(x.shape[1]),
        numerical_rank=numerical_rank,
        threshold=float(threshold),
        reconstruction_residual_frobenius=residual,
        branch_to_rank_ratio=float(x.shape[1] / max(1, numerical_rank)),
    )
    return basis, coefficients, receipt


@dataclass(frozen=True)
class BoundaryCapacityReceipt:
    event_count: int
    raw_log2_branches: float
    left_log2_dimension: float
    right_log2_dimension: float
    rank_cap_log2: float
    effective_log2_upper_bound: float
    schema: str = SCHEMA
    epistemic: str = EPISTEMIC
    canon_allowed: bool = CANON_ALLOWED


def boundary_capacity(operator_schmidt_ranks: Iterable[int], *, left_dimension: int, right_dimension: int) -> BoundaryCapacityReceipt:
    """Upper-bound boundary branch/rank growth without enumerating branches."""
    ranks = tuple(int(r) for r in operator_schmidt_ranks)
    if any(r < 1 for r in ranks):
        raise ValueError("operator Schmidt ranks must be positive")
    left_dimension = int(left_dimension)
    right_dimension = int(right_dimension)
    if left_dimension < 1 or right_dimension < 1:
        raise ValueError("boundary Hilbert dimensions must be positive")
    raw = float(math.fsum(math.log2(r) for r in ranks))
    ll = float(math.log2(left_dimension))
    rr = float(math.log2(right_dimension))
    cap = min(ll, rr)
    return BoundaryCapacityReceipt(
        event_count=len(ranks),
        raw_log2_branches=raw,
        left_log2_dimension=ll,
        right_log2_dimension=rr,
        rank_cap_log2=cap,
        effective_log2_upper_bound=min(raw, cap),
    )


class IncrementalBoundaryBasis:
    """Streaming orthonormal boundary basis with explicit numerical threshold.

    The class is intended for atomized contraction pipelines where branch states
    arrive incrementally.  It never treats numerical near-dependence as exact
    without recording the threshold used.
    """

    def __init__(self, ambient_dim: int, *, rtol: float | None = None, atol: float = 0.0):
        ambient_dim = int(ambient_dim)
        if ambient_dim < 1:
            raise ValueError("ambient_dim must be positive")
        self.ambient_dim = ambient_dim
        self.rtol = rtol
        self.atol = float(atol)
        if not math.isfinite(self.atol) or self.atol < 0.0:
            raise ValueError("atol must be finite and >= 0")
        self._basis = np.zeros((ambient_dim, 0), dtype=np.complex128)

    @property
    def rank(self) -> int:
        return int(self._basis.shape[1])

    @property
    def basis(self) -> np.ndarray:
        return self._basis.copy()

    def add(self, vector) -> dict[str, float | int | bool | str]:
        v = _finite_array(vector, name="vector", ndim=1)
        if v.size != self.ambient_dim:
            raise ValueError("vector length does not match ambient_dim")
        norm = float(np.linalg.norm(v))
        if norm == 0.0:
            return {
                "schema": SCHEMA,
                "accepted": False,
                "rank_before": self.rank,
                "rank_after": self.rank,
                "residual_norm": 0.0,
                "threshold": 0.0,
                "reason": "ZERO_VECTOR",
            }
        if self.rtol is None:
            rel = np.finfo(float).eps * max(self.ambient_dim, self.rank + 1)
        else:
            rel = float(self.rtol)
            if not math.isfinite(rel) or rel < 0.0:
                raise ValueError("rtol must be finite and >= 0")
        threshold = max(self.atol, rel * norm)
        before = self.rank
        residual = v.astype(np.complex128, copy=True)
        if before:
            coeff = self._basis.conj().T @ residual
            residual -= self._basis @ coeff
            coeff2 = self._basis.conj().T @ residual
            residual -= self._basis @ coeff2
        residual_norm = float(np.linalg.norm(residual))
        accepted = residual_norm > threshold
        if accepted:
            q = residual / residual_norm
            self._basis = np.column_stack((self._basis, q))
        return {
            "schema": SCHEMA,
            "accepted": bool(accepted),
            "rank_before": before,
            "rank_after": self.rank,
            "residual_norm": residual_norm,
            "threshold": float(threshold),
            "reason": "NEW_DIRECTION" if accepted else "NUMERICALLY_DEPENDENT",
        }


__all__ = [
    "SCHEMA", "EPISTEMIC", "CANON_ALLOWED",
    "SpectralScalars", "spectral_scalars",
    "ProjectiveOrbitReceipt", "projective_orbit",
    "PAIR_BASIS_4D", "wedge2_4d", "PluckerReceipt", "plucker_simplicity",
    "HodgeSplit4D", "hodge_split_euclidean_4d", "principal_angles",
    "BargmannTriangleReceipt", "bargmann_triangle", "GrassmannReceipt", "grassmann_distance",
    "unfold", "fold", "mode_product",
    "SchmidtReceipt", "schmidt_decompose", "SchmidtEntropyReceipt", "schmidt_entropy",
    "OperatorSchmidtReceipt", "operator_schmidt_decompose", "reconstruct_operator_schmidt",
    "TensorTrainReceipt", "tensor_train_svd", "reconstruct_tensor_train",
    "TuckerReceipt", "tucker_hosvd", "reconstruct_tucker",
    "BoundaryBasisReceipt", "compress_boundary_states",
    "BoundaryCapacityReceipt", "boundary_capacity",
    "IncrementalBoundaryBasis",
]