"""PhaseNav mixed-representation, symmetry and contraction primitives v0.16.

This candidate layer extends PhaseNav with exact typed fast paths for diagonal
phase polynomials, finite-dimensional symmetry sectors, Clifford/matchgate
classification, polar/Schur boundary reduction, representation routing and
small/medium tensor-network contraction planning.

The module is substrate-neutral.  It does not claim a physical quantum
computer, physical spacetime realization, generic low-entanglement structure,
or automatic quantum advantage.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

SCHEMA = "phasenav.mixed-representation-contraction/v0.16"
EPISTEMIC = "CANDIDATE_ONLY"
CANON_ALLOWED = False


class MixedRepresentationError(ValueError):
    pass


def _finite_array(value, *, name: str, ndim: int | None = None) -> np.ndarray:
    arr = np.asarray(value)
    if ndim is not None and arr.ndim != ndim:
        raise MixedRepresentationError(f"{name} must have ndim={ndim}, got {arr.ndim}")
    if not np.all(np.isfinite(arr)):
        raise MixedRepresentationError(f"{name} must be finite")
    return arr


def _positive_int(name: str, value: int) -> int:
    value = int(value)
    if value <= 0:
        raise MixedRepresentationError(f"{name} must be > 0")
    return value


def _prod(values: Iterable[int]) -> int:
    out = 1
    for value in values:
        out *= int(value)
    return int(out)


def _log2_int(value: int) -> float:
    if value <= 0:
        raise MixedRepresentationError("log2 input must be positive")
    return float(math.log2(value))


def _phase_wrap(x: float) -> float:
    return float((x + math.pi) % (2.0 * math.pi) - math.pi)


# ---------------------------------------------------------------------------
# Exact diagonal phase polynomial
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QuadraticPhasePolynomial:
    """Phase function on computational bits up to quadratic degree.

    phase(x) = constant + sum_i linear_i*x_i + sum_{i<j} quadratic_ij*x_i*x_j

    Coefficients are real radians and are wrapped modulo 2*pi only for
    canonical storage/evaluation.  This exactly represents CZ layers and RZ
    factors (up to their global phase, which is retained in ``constant``).
    """

    num_bits: int
    constant: float = 0.0
    linear: tuple[float, ...] = ()
    quadratic: tuple[tuple[int, int, float], ...] = ()

    def __post_init__(self):
        n = _positive_int("num_bits", self.num_bits)
        linear = tuple(float(x) for x in (self.linear or (0.0,) * n))
        if len(linear) != n:
            raise MixedRepresentationError("linear coefficient count must equal num_bits")
        if not all(math.isfinite(x) for x in linear):
            raise MixedRepresentationError("linear coefficients must be finite")
        q = []
        seen = set()
        for i, j, theta in self.quadratic:
            i = int(i); j = int(j); theta = float(theta)
            if not (0 <= i < n and 0 <= j < n) or i == j:
                raise MixedRepresentationError("quadratic indices must be distinct valid bits")
            if j < i:
                i, j = j, i
            if (i, j) in seen:
                raise MixedRepresentationError("duplicate quadratic term")
            if not math.isfinite(theta):
                raise MixedRepresentationError("quadratic coefficients must be finite")
            seen.add((i, j))
            q.append((i, j, _phase_wrap(theta)))
        object.__setattr__(self, "num_bits", n)
        object.__setattr__(self, "constant", _phase_wrap(float(self.constant)))
        object.__setattr__(self, "linear", tuple(_phase_wrap(x) for x in linear))
        object.__setattr__(self, "quadratic", tuple(sorted(q)))

    @classmethod
    def identity(cls, num_bits: int) -> "QuadraticPhasePolynomial":
        return cls(num_bits=num_bits)

    @classmethod
    def from_cz_edges(
        cls,
        num_bits: int,
        edges: Iterable[tuple[int, int]],
    ) -> "QuadraticPhasePolynomial":
        accum: dict[tuple[int, int], float] = {}
        for i, j in edges:
            i = int(i); j = int(j)
            if i == j:
                raise MixedRepresentationError("CZ self-edge is invalid")
            if j < i:
                i, j = j, i
            accum[(i, j)] = accum.get((i, j), 0.0) + math.pi
        return cls(
            num_bits=num_bits,
            quadratic=tuple((i, j, theta) for (i, j), theta in accum.items()),
        )

    def with_rz(self, bit: int, theta: float) -> "QuadraticPhasePolynomial":
        """Compose RZ(theta) on one bit.

        RZ(theta)|x> = exp(-i theta/2) * exp(i theta*x)|x>.
        """
        bit = int(bit)
        if not 0 <= bit < self.num_bits:
            raise MixedRepresentationError("bit out of range")
        lin = list(self.linear)
        lin[bit] += float(theta)
        return QuadraticPhasePolynomial(
            self.num_bits,
            constant=self.constant - 0.5 * float(theta),
            linear=tuple(lin),
            quadratic=self.quadratic,
        )

    def compose(self, other: "QuadraticPhasePolynomial") -> "QuadraticPhasePolynomial":
        if self.num_bits != other.num_bits:
            raise MixedRepresentationError("phase polynomial bit counts differ")
        lin = tuple(a + b for a, b in zip(self.linear, other.linear))
        terms: dict[tuple[int, int], float] = {}
        for i, j, t in self.quadratic + other.quadratic:
            terms[(i, j)] = terms.get((i, j), 0.0) + t
        return QuadraticPhasePolynomial(
            self.num_bits,
            constant=self.constant + other.constant,
            linear=lin,
            quadratic=tuple((i, j, t) for (i, j), t in terms.items()),
        )

    def restrict(self, fixed: Mapping[int, int]) -> "QuadraticPhasePolynomial":
        """Fix selected bits and exactly eliminate them from the phase function."""
        fixed2 = {}
        for k, v in fixed.items():
            k = int(k); v = int(v)
            if not 0 <= k < self.num_bits:
                raise MixedRepresentationError("fixed bit out of range")
            if v not in (0, 1):
                raise MixedRepresentationError("fixed values must be 0 or 1")
            fixed2[k] = v

        survivors = [i for i in range(self.num_bits) if i not in fixed2]
        remap = {old: new for new, old in enumerate(survivors)}
        const = self.constant
        lin = [0.0] * len(survivors)
        for i, theta in enumerate(self.linear):
            if i in fixed2:
                const += theta * fixed2[i]
            else:
                lin[remap[i]] += theta

        quad: dict[tuple[int, int], float] = {}
        for i, j, theta in self.quadratic:
            fi = i in fixed2
            fj = j in fixed2
            if fi and fj:
                const += theta * fixed2[i] * fixed2[j]
            elif fi:
                lin[remap[j]] += theta * fixed2[i]
            elif fj:
                lin[remap[i]] += theta * fixed2[j]
            else:
                quad[(remap[i], remap[j])] = quad.get((remap[i], remap[j]), 0.0) + theta
        return QuadraticPhasePolynomial(
            num_bits=len(survivors),
            constant=const,
            linear=tuple(lin),
            quadratic=tuple((i, j, t) for (i, j), t in quad.items()),
        )

    def phase(self, bits: Sequence[int]) -> float:
        if len(bits) != self.num_bits:
            raise MixedRepresentationError("bitstring length mismatch")
        x = tuple(int(v) for v in bits)
        if any(v not in (0, 1) for v in x):
            raise MixedRepresentationError("bits must be 0/1")
        value = self.constant
        value += math.fsum(theta * x[i] for i, theta in enumerate(self.linear))
        value += math.fsum(theta * x[i] * x[j] for i, j, theta in self.quadratic)
        return _phase_wrap(value)

    def amplitude(self, bits: Sequence[int]) -> complex:
        return complex(np.exp(1j * self.phase(bits)))

    def support_counts(self) -> dict[str, int]:
        return {
            "constant": int(abs(self.constant) > 0.0),
            "linear": sum(abs(x) > 0.0 for x in self.linear),
            "quadratic": sum(abs(t) > 0.0 for _, _, t in self.quadratic),
        }


# ---------------------------------------------------------------------------
# Abelian charge sectors / block-sparse tensors
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AbelianChargeRule:
    modulus: int | None = None
    target: int = 0

    def __post_init__(self):
        if self.modulus is not None and int(self.modulus) <= 1:
            raise MixedRepresentationError("modulus must be > 1 or None")
        object.__setattr__(self, "modulus", None if self.modulus is None else int(self.modulus))
        object.__setattr__(self, "target", int(self.target))

    def reduce(self, value: int) -> int:
        value = int(value)
        return value if self.modulus is None else value % self.modulus

    def allowed(self, charges: Sequence[int]) -> bool:
        return self.reduce(sum(int(c) for c in charges)) == self.reduce(self.target)


@dataclass
class BlockSparseTensor:
    shape: tuple[int, ...]
    axis_charges: tuple[tuple[int, ...], ...]
    rule: AbelianChargeRule
    blocks: dict[tuple[int, ...], np.ndarray]
    zero_atol: float = 0.0

    def __post_init__(self):
        self.shape = tuple(_positive_int("shape entry", x) for x in self.shape)
        if len(self.axis_charges) != len(self.shape):
            raise MixedRepresentationError("axis_charges rank mismatch")
        normalized = []
        for dim, charges in zip(self.shape, self.axis_charges):
            charges = tuple(int(c) for c in charges)
            if len(charges) != dim:
                raise MixedRepresentationError("axis charge count must match dimension")
            normalized.append(charges)
        self.axis_charges = tuple(normalized)
        self.zero_atol = float(self.zero_atol)
        if self.zero_atol < 0.0 or not math.isfinite(self.zero_atol):
            raise MixedRepresentationError("zero_atol must be finite and >= 0")

        charge_groups = []
        for charges in self.axis_charges:
            groups: dict[int, list[int]] = {}
            for idx, charge in enumerate(charges):
                charge = self.rule.reduce(charge)
                groups.setdefault(charge, []).append(idx)
            charge_groups.append(groups)

        checked = {}
        for key, block in self.blocks.items():
            key = tuple(self.rule.reduce(c) for c in key)
            if len(key) != len(self.shape):
                raise MixedRepresentationError("block charge key rank mismatch")
            if not self.rule.allowed(key):
                raise MixedRepresentationError(f"forbidden charge block {key}")
            expected = tuple(len(charge_groups[axis].get(key[axis], ())) for axis in range(len(key)))
            arr = np.asarray(block)
            if arr.shape != expected:
                raise MixedRepresentationError(f"block {key} shape {arr.shape} != {expected}")
            if not np.all(np.isfinite(arr)):
                raise MixedRepresentationError("block values must be finite")
            checked[key] = np.asarray(arr, dtype=np.complex128)
        self.blocks = checked

    @classmethod
    def from_dense(
        cls,
        tensor,
        axis_charges: Sequence[Sequence[int]],
        rule: AbelianChargeRule,
        *,
        zero_atol: float = 0.0,
    ) -> "BlockSparseTensor":
        arr = np.asarray(tensor, dtype=np.complex128)
        if arr.ndim == 0:
            raise MixedRepresentationError("tensor must have rank >= 1")
        if not np.all(np.isfinite(arr)):
            raise MixedRepresentationError("tensor values must be finite")
        axis_charges = tuple(tuple(int(c) for c in ch) for ch in axis_charges)
        if len(axis_charges) != arr.ndim:
            raise MixedRepresentationError("axis_charges rank mismatch")
        for dim, charges in zip(arr.shape, axis_charges):
            if len(charges) != dim:
                raise MixedRepresentationError("axis charge count must match dimension")

        groups = []
        for charges in axis_charges:
            d: dict[int, list[int]] = {}
            for idx, charge in enumerate(charges):
                c = rule.reduce(charge)
                d.setdefault(c, []).append(idx)
            groups.append(d)

        atol = float(zero_atol)
        if atol < 0 or not math.isfinite(atol):
            raise MixedRepresentationError("zero_atol must be finite and >= 0")

        # Fail closed if forbidden entries contain non-negligible weight.
        for coord in np.ndindex(arr.shape):
            charges = tuple(axis_charges[a][coord[a]] for a in range(arr.ndim))
            if not rule.allowed(charges) and abs(arr[coord]) > atol:
                raise MixedRepresentationError(
                    f"dense tensor violates charge rule at {coord}: |value|={abs(arr[coord])}"
                )

        blocks: dict[tuple[int, ...], np.ndarray] = {}
        charge_values = [tuple(sorted(g)) for g in groups]
        for key in itertools.product(*charge_values):
            if not rule.allowed(key):
                continue
            indices = [groups[a][key[a]] for a in range(arr.ndim)]
            block = arr[np.ix_(*indices)]
            if np.any(np.abs(block) > atol):
                blocks[tuple(key)] = np.array(block, copy=True)

        return cls(
            shape=tuple(arr.shape),
            axis_charges=axis_charges,
            rule=rule,
            blocks=blocks,
            zero_atol=atol,
        )

    def to_dense(self) -> np.ndarray:
        out = np.zeros(self.shape, dtype=np.complex128)
        groups = []
        for charges in self.axis_charges:
            d: dict[int, list[int]] = {}
            for idx, charge in enumerate(charges):
                d.setdefault(self.rule.reduce(charge), []).append(idx)
            groups.append(d)
        for key, block in self.blocks.items():
            indices = [groups[a][key[a]] for a in range(len(key))]
            out[np.ix_(*indices)] = block
        return out

    @property
    def dense_elements(self) -> int:
        return _prod(self.shape)

    @property
    def stored_elements(self) -> int:
        return sum(int(block.size) for block in self.blocks.values())

    @property
    def storage_fraction(self) -> float:
        return float(self.stored_elements / self.dense_elements)


# ---------------------------------------------------------------------------
# Gate-family classifiers
# ---------------------------------------------------------------------------

_PAULI = (
    np.eye(2, dtype=np.complex128),
    np.array([[0, 1], [1, 0]], dtype=np.complex128),
    np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
    np.array([[1, 0], [0, -1]], dtype=np.complex128),
)


def _num_qubits_from_square(unitary: np.ndarray) -> int:
    if unitary.ndim != 2 or unitary.shape[0] != unitary.shape[1]:
        raise MixedRepresentationError("unitary must be square")
    d = unitary.shape[0]
    n = int(round(math.log2(d)))
    if 2**n != d:
        raise MixedRepresentationError("unitary dimension must be a power of two")
    return n


def _is_unitary(unitary: np.ndarray, atol: float) -> float:
    ident = np.eye(unitary.shape[0], dtype=np.complex128)
    return float(np.linalg.norm(unitary.conj().T @ unitary - ident, ord="fro"))


def _kron_all(mats: Sequence[np.ndarray]) -> np.ndarray:
    out = np.array([[1.0 + 0.0j]])
    for m in mats:
        out = np.kron(out, m)
    return out


@dataclass(frozen=True)
class CliffordReceipt:
    num_qubits: int
    is_clifford: bool
    unitary_residual: float
    max_pauli_residual: float
    atol: float


def clifford_unitary(unitary, *, atol: float = 1e-10, max_qubits: int = 4) -> CliffordReceipt:
    u = np.asarray(unitary, dtype=np.complex128)
    n = _num_qubits_from_square(u)
    if n > max_qubits:
        raise MixedRepresentationError(
            f"Clifford classifier bounded to <= {max_qubits} qubits per gate"
        )
    atol = float(atol)
    if atol <= 0 or not math.isfinite(atol):
        raise MixedRepresentationError("atol must be finite and > 0")
    ures = _is_unitary(u, atol)
    if ures > atol:
        return CliffordReceipt(n, False, ures, math.inf, atol)

    basis = []
    labels = list(itertools.product(range(4), repeat=n))
    for label in labels:
        basis.append(_kron_all([_PAULI[i] for i in label]))
    d = 2**n

    generators = []
    for q in range(n):
        for pidx in (1, 3):  # X_q and Z_q
            label = [0] * n
            label[q] = pidx
            generators.append(_kron_all([_PAULI[i] for i in label]))

    worst = 0.0
    for g in generators:
        image = u @ g @ u.conj().T
        coeff = np.array([np.trace(p.conj().T @ image) / d for p in basis])
        best = int(np.argmax(np.abs(coeff)))
        phase = coeff[best]
        if abs(phase) == 0:
            residual = float(np.linalg.norm(image, ord="fro"))
        else:
            phase /= abs(phase)
            residual = float(
                np.linalg.norm(image - phase * basis[best], ord="fro") / math.sqrt(d)
            )
        worst = max(worst, residual)
    return CliffordReceipt(n, bool(worst <= atol), ures, worst, atol)


@dataclass(frozen=True)
class MatchgateReceipt:
    is_matchgate: bool
    unitary_residual: float
    parity_mixing_residual: float
    determinant_residual: float
    atol: float


def matchgate_unitary(unitary, *, atol: float = 1e-10) -> MatchgateReceipt:
    """Classify a 2-qubit matchgate in the computational parity basis.

    A matchgate is parity preserving and its even/odd 2x2 blocks have equal
    determinant.  This is a finite numerical classifier, not a simulator.
    """
    u = np.asarray(unitary, dtype=np.complex128)
    if u.shape != (4, 4):
        raise MixedRepresentationError("matchgate classifier requires a 4x4 unitary")
    atol = float(atol)
    if atol <= 0 or not math.isfinite(atol):
        raise MixedRepresentationError("atol must be finite and > 0")
    ures = _is_unitary(u, atol)

    even = (0, 3)
    odd = (1, 2)
    parity_mixing = 0.0
    for i in even:
        for j in odd:
            parity_mixing += abs(u[i, j]) ** 2 + abs(u[j, i]) ** 2
    parity_mixing = float(math.sqrt(parity_mixing))

    a = u[np.ix_(even, even)]
    b = u[np.ix_(odd, odd)]
    det_res = float(abs(np.linalg.det(a) - np.linalg.det(b)))
    ok = bool(ures <= atol and parity_mixing <= atol and det_res <= atol)
    return MatchgateReceipt(ok, ures, parity_mixing, det_res, atol)


# ---------------------------------------------------------------------------
# Polar and Schur boundary primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PolarReceipt:
    unitary_factor: np.ndarray
    positive_factor: np.ndarray
    singular_values: tuple[float, ...]
    reconstruction_residual: float
    unitarity_residual: float


def polar_decompose(matrix) -> PolarReceipt:
    a = np.asarray(matrix, dtype=np.complex128)
    if a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise MixedRepresentationError("polar_decompose currently requires a square matrix")
    if not np.all(np.isfinite(a)):
        raise MixedRepresentationError("matrix must be finite")
    u, s, vh = np.linalg.svd(a, full_matrices=False)
    unitary = u @ vh
    positive = (vh.conj().T * s) @ vh
    recon = float(np.linalg.norm(a - unitary @ positive, ord="fro"))
    ident = np.eye(a.shape[0], dtype=np.complex128)
    ures = float(np.linalg.norm(unitary.conj().T @ unitary - ident, ord="fro"))
    return PolarReceipt(
        unitary_factor=unitary,
        positive_factor=positive,
        singular_values=tuple(float(x) for x in s),
        reconstruction_residual=recon,
        unitarity_residual=ures,
    )


@dataclass(frozen=True)
class SchurReceipt:
    complement: np.ndarray
    eliminated_size: int
    retained_size: int
    condition_number: float
    reconstruction_residual: float


def schur_complement(matrix, retained: Sequence[int], *, condition_limit: float = 1e12) -> SchurReceipt:
    """Eliminate the complement of ``retained`` using an exact solve.

    For M = [[A,B],[C,D]], returns A - B D^{-1} C.  Singular or excessively
    ill-conditioned D fails closed; no pseudoinverse is silently substituted.
    """
    m = np.asarray(matrix, dtype=np.complex128)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise MixedRepresentationError("Schur complement requires a square matrix")
    if not np.all(np.isfinite(m)):
        raise MixedRepresentationError("matrix must be finite")
    n = m.shape[0]
    retained = tuple(sorted(set(int(i) for i in retained)))
    if not retained or any(i < 0 or i >= n for i in retained):
        raise MixedRepresentationError("retained indices must be a non-empty subset")
    eliminated = tuple(i for i in range(n) if i not in retained)
    if not eliminated:
        return SchurReceipt(np.array(m, copy=True), 0, n, 1.0, 0.0)

    a = m[np.ix_(retained, retained)]
    b = m[np.ix_(retained, eliminated)]
    c = m[np.ix_(eliminated, retained)]
    d = m[np.ix_(eliminated, eliminated)]
    cond = float(np.linalg.cond(d))
    if not math.isfinite(cond) or cond > float(condition_limit):
        raise MixedRepresentationError(
            f"eliminated block condition number {cond} exceeds limit {condition_limit}"
        )
    x = np.linalg.solve(d, c)
    complement = a - b @ x
    solve_res = float(np.linalg.norm(d @ x - c, ord="fro"))
    return SchurReceipt(
        complement=complement,
        eliminated_size=len(eliminated),
        retained_size=len(retained),
        condition_number=cond,
        reconstruction_residual=solve_res,
    )


# ---------------------------------------------------------------------------
# Representation router
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AtomFeatures:
    num_qubits: int
    gate_count: int
    clifford_only: bool = False
    matchgate_only: bool = False
    diagonal_quadratic_phase: bool = False
    symmetry_storage_fraction: float | None = None
    max_schmidt_rank: int | None = None
    multilinear_ranks: tuple[int, ...] | None = None
    one_dimensional_locality: bool = False
    exact_required: bool = True

    def __post_init__(self):
        _positive_int("num_qubits", self.num_qubits)
        if int(self.gate_count) < 0:
            raise MixedRepresentationError("gate_count must be >= 0")
        if self.symmetry_storage_fraction is not None:
            f = float(self.symmetry_storage_fraction)
            if not 0.0 <= f <= 1.0:
                raise MixedRepresentationError("symmetry_storage_fraction must be in [0,1]")
        if self.max_schmidt_rank is not None:
            _positive_int("max_schmidt_rank", self.max_schmidt_rank)
        if self.multilinear_ranks is not None:
            if not self.multilinear_ranks:
                raise MixedRepresentationError("multilinear_ranks cannot be empty")
            for r in self.multilinear_ranks:
                _positive_int("multilinear rank", r)


@dataclass(frozen=True)
class RepresentationRoute:
    primary: str
    overlays: tuple[str, ...]
    exact: bool
    reason: str
    thresholds: tuple[tuple[str, float], ...]


def route_atom(
    features: AtomFeatures,
    *,
    dense_qubit_limit: int = 24,
    mps_rank_limit: int = 1024,
    tucker_rank_limit: int = 128,
    symmetry_fraction_limit: float = 0.5,
) -> RepresentationRoute:
    """Deterministic routing with every policy threshold explicit in the receipt."""
    dense_qubit_limit = _positive_int("dense_qubit_limit", dense_qubit_limit)
    mps_rank_limit = _positive_int("mps_rank_limit", mps_rank_limit)
    tucker_rank_limit = _positive_int("tucker_rank_limit", tucker_rank_limit)
    symmetry_fraction_limit = float(symmetry_fraction_limit)
    if not 0 < symmetry_fraction_limit <= 1:
        raise MixedRepresentationError("symmetry_fraction_limit must be in (0,1]")

    overlays = []
    if (
        features.symmetry_storage_fraction is not None
        and features.symmetry_storage_fraction <= symmetry_fraction_limit
    ):
        overlays.append("BLOCK_SPARSE_SYMMETRY")

    if features.diagonal_quadratic_phase:
        primary = "QUADRATIC_PHASE_POLYNOMIAL"
        reason = "atom is exactly diagonal with degree<=2 computational-bit phase"
    elif features.clifford_only:
        primary = "STABILIZER"
        reason = "all gates classified Clifford"
    elif features.matchgate_only:
        primary = "FERMIONIC_GAUSSIAN"
        reason = "all two-qubit gates classified matchgate/Gaussian-compatible"
    elif (
        features.one_dimensional_locality
        and features.max_schmidt_rank is not None
        and features.max_schmidt_rank <= mps_rank_limit
    ):
        primary = "MPS_TT"
        reason = "1D-local atom with measured Schmidt rank inside explicit limit"
    elif (
        features.multilinear_ranks is not None
        and max(features.multilinear_ranks) <= tucker_rank_limit
    ):
        primary = "TUCKER_HOSVD"
        reason = "measured multilinear ranks inside explicit limit"
    elif features.num_qubits <= dense_qubit_limit:
        primary = "DENSE"
        reason = "atom fits explicit dense-qubit policy limit"
    else:
        primary = "TENSOR_NETWORK"
        reason = "no certified structured fast path satisfied"

    return RepresentationRoute(
        primary=primary,
        overlays=tuple(overlays),
        exact=bool(features.exact_required),
        reason=reason,
        thresholds=(
            ("dense_qubit_limit", float(dense_qubit_limit)),
            ("mps_rank_limit", float(mps_rank_limit)),
            ("tucker_rank_limit", float(tucker_rank_limit)),
            ("symmetry_fraction_limit", float(symmetry_fraction_limit)),
        ),
    )


# ---------------------------------------------------------------------------
# Pairwise tensor-network planner
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TensorNode:
    name: str
    indices: tuple[str, ...]

    def __post_init__(self):
        if not str(self.name):
            raise MixedRepresentationError("tensor node name cannot be empty")
        if len(set(self.indices)) != len(self.indices):
            raise MixedRepresentationError("a node cannot repeat an index in this planner")
        if not all(str(i) for i in self.indices):
            raise MixedRepresentationError("indices must be non-empty strings")


@dataclass(frozen=True)
class TensorNetworkSpec:
    nodes: tuple[TensorNode, ...]
    index_dims: tuple[tuple[str, int], ...]

    def __post_init__(self):
        if not self.nodes:
            raise MixedRepresentationError("tensor network requires at least one node")
        names = [n.name for n in self.nodes]
        if len(set(names)) != len(names):
            raise MixedRepresentationError("tensor node names must be unique")
        dims = dict(self.index_dims)
        if len(dims) != len(self.index_dims):
            raise MixedRepresentationError("duplicate index dimension records")
        for idx, dim in self.index_dims:
            if not str(idx):
                raise MixedRepresentationError("index names cannot be empty")
            _positive_int(f"dimension[{idx}]", dim)
        used = [idx for node in self.nodes for idx in node.indices]
        missing = sorted(set(used) - set(dims))
        if missing:
            raise MixedRepresentationError(f"missing index dimensions: {missing[:5]}")
        multiplicity = {idx: used.count(idx) for idx in set(used)}
        if any(v > 2 for v in multiplicity.values()):
            raise MixedRepresentationError(
                "pairwise planner requires every index to occur in at most two tensors"
            )

    @property
    def dims(self) -> dict[str, int]:
        return dict(self.index_dims)


@dataclass(frozen=True)
class ContractionStep:
    left: str
    right: str
    shared_indices: tuple[str, ...]
    result_name: str
    result_indices: tuple[str, ...]
    result_elements: int
    flop_estimate: int


@dataclass(frozen=True)
class ContractionPlan:
    steps: tuple[ContractionStep, ...]
    peak_elements: int
    peak_log2_elements: float
    peak_bytes: int
    total_flop_estimate: int
    total_flop_log10: float
    final_indices: tuple[str, ...]
    outer_products: int
    dtype_bytes: int


def _contract_index_sets(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    shared = tuple(sorted(set(left) & set(right)))
    result = tuple(sorted((set(left) | set(right)) - set(shared)))
    return shared, result


def greedy_contraction_plan(
    spec: TensorNetworkSpec,
    *,
    dtype_bytes: int = 16,
    allow_outer_products: bool = True,
) -> ContractionPlan:
    """Greedy exact-index planner minimizing immediate result size then FLOPs.

    The returned width is an upper bound for this explicit contraction order,
    not a proof of globally optimal treewidth.
    """
    dtype_bytes = _positive_int("dtype_bytes", dtype_bytes)
    dims = spec.dims
    active: dict[str, tuple[str, ...]] = {n.name: tuple(n.indices) for n in spec.nodes}
    steps = []
    peak = max(_prod(dims[i] for i in inds) for inds in active.values())
    total_flops = 0
    outer_products = 0
    counter = 0

    while len(active) > 1:
        names = sorted(active)
        best = None
        for ia, left_name in enumerate(names):
            for right_name in names[ia + 1:]:
                left = active[left_name]
                right = active[right_name]
                shared, result = _contract_index_sets(left, right)
                if not shared and not allow_outer_products:
                    continue
                result_elems = _prod(dims[i] for i in result) if result else 1
                union = tuple(sorted(set(left) | set(right)))
                flops = _prod(dims[i] for i in union)
                score = (
                    0 if shared else 1,
                    result_elems,
                    flops,
                    len(result),
                    left_name,
                    right_name,
                )
                if best is None or score < best[0]:
                    best = (score, left_name, right_name, shared, result, result_elems, flops)

        if best is None:
            raise MixedRepresentationError("network disconnected and outer products disabled")

        _, left_name, right_name, shared, result, result_elems, flops = best
        counter += 1
        new_name = f"_c{counter}"
        if not shared:
            outer_products += 1
        steps.append(
            ContractionStep(
                left=left_name,
                right=right_name,
                shared_indices=shared,
                result_name=new_name,
                result_indices=result,
                result_elements=result_elems,
                flop_estimate=flops,
            )
        )
        del active[left_name]
        del active[right_name]
        active[new_name] = result
        peak = max(peak, result_elems)
        total_flops += flops

    final_indices = next(iter(active.values()))
    return ContractionPlan(
        steps=tuple(steps),
        peak_elements=int(peak),
        peak_log2_elements=_log2_int(int(peak)),
        peak_bytes=int(peak) * dtype_bytes,
        total_flop_estimate=int(total_flops),
        total_flop_log10=float(math.log10(total_flops)) if total_flops else -math.inf,
        final_indices=tuple(final_indices),
        outer_products=outer_products,
        dtype_bytes=dtype_bytes,
    )


@dataclass(frozen=True)
class SlicePlan:
    sliced_indices: tuple[str, ...]
    slice_count: int
    per_slice_peak_bytes: int
    per_slice_peak_log2_elements: float
    per_slice_flop_estimate: int
    total_flop_estimate: int
    total_flop_log10: float
    memory_budget_bytes: int
    feasible: bool


def _spec_with_sliced_indices(spec: TensorNetworkSpec, sliced: set[str]) -> TensorNetworkSpec:
    nodes = []
    for node in spec.nodes:
        nodes.append(TensorNode(node.name, tuple(i for i in node.indices if i not in sliced)))
    dims = tuple((i, d) for i, d in spec.index_dims if i not in sliced)
    return TensorNetworkSpec(tuple(nodes), dims)


def slice_to_memory_budget(
    spec: TensorNetworkSpec,
    memory_budget_bytes: int,
    *,
    dtype_bytes: int = 16,
    candidate_indices: Sequence[str] | None = None,
) -> SlicePlan:
    """Greedily slice internal indices until the explicit plan fits memory.

    Slicing is exact: each sliced index is fixed and all its values are summed
    over externally.  The cost is multiplied by the product of sliced
    dimensions.  No claim of globally optimal slicing is made.
    """
    budget = _positive_int("memory_budget_bytes", memory_budget_bytes)
    dims = spec.dims
    used = [idx for node in spec.nodes for idx in node.indices]
    multiplicity = {idx: used.count(idx) for idx in set(used)}
    internal = [idx for idx, count in multiplicity.items() if count == 2]
    if candidate_indices is None:
        candidates = sorted(internal)
    else:
        candidates = []
        for idx in candidate_indices:
            if idx not in dims:
                raise MixedRepresentationError(f"unknown slice index {idx}")
            if multiplicity.get(idx, 0) != 2:
                raise MixedRepresentationError(f"slice index {idx} is not internal")
            candidates.append(idx)

    sliced: set[str] = set()
    slice_count = 1
    current = greedy_contraction_plan(spec, dtype_bytes=dtype_bytes)

    while current.peak_bytes > budget and candidates:
        best = None
        for idx in candidates:
            if idx in sliced:
                continue
            trial_sliced = set(sliced)
            trial_sliced.add(idx)
            trial_spec = _spec_with_sliced_indices(spec, trial_sliced)
            trial = greedy_contraction_plan(trial_spec, dtype_bytes=dtype_bytes)
            reduction = current.peak_bytes - trial.peak_bytes
            score = (
                reduction / math.log2(max(2, dims[idx])),
                reduction,
                -trial.total_flop_estimate,
                idx,
            )
            if best is None or score > best[0]:
                best = (score, idx, trial)
        if best is None or best[0][1] <= 0:
            break
        _, idx, current = best
        sliced.add(idx)
        slice_count *= dims[idx]
        candidates = [x for x in candidates if x != idx]

    total_flops = int(current.total_flop_estimate) * int(slice_count)
    return SlicePlan(
        sliced_indices=tuple(sorted(sliced)),
        slice_count=int(slice_count),
        per_slice_peak_bytes=current.peak_bytes,
        per_slice_peak_log2_elements=current.peak_log2_elements,
        per_slice_flop_estimate=current.total_flop_estimate,
        total_flop_estimate=total_flops,
        total_flop_log10=float(math.log10(total_flops)) if total_flops else -math.inf,
        memory_budget_bytes=budget,
        feasible=bool(current.peak_bytes <= budget),
    )


# ---------------------------------------------------------------------------
# Graph elimination width
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GraphWidthReceipt:
    elimination_order: tuple[str, ...]
    induced_width: int
    max_clique_size: int
    fill_edges_added: int


def min_fill_graph_width(adjacency: Mapping[str, Iterable[str]]) -> GraphWidthReceipt:
    """Min-fill elimination upper bound for an undirected graph."""
    graph: dict[str, set[str]] = {str(v): set(map(str, nbrs)) for v, nbrs in adjacency.items()}
    for v in list(graph):
        graph[v].discard(v)
        for u in tuple(graph[v]):
            graph.setdefault(u, set()).add(v)

    order = []
    width = 0
    fill_total = 0

    while graph:
        best = None
        for v in sorted(graph):
            nbrs = sorted(graph[v])
            missing = 0
            for i, a in enumerate(nbrs):
                ga = graph.get(a, set())
                for b in nbrs[i + 1:]:
                    if b not in ga:
                        missing += 1
            score = (missing, len(nbrs), v)
            if best is None or score < best[0]:
                best = (score, v, nbrs)
        _, v, nbrs = best
        width = max(width, len(nbrs))
        for i, a in enumerate(nbrs):
            for b in nbrs[i + 1:]:
                if b not in graph[a]:
                    graph[a].add(b)
                    graph[b].add(a)
                    fill_total += 1