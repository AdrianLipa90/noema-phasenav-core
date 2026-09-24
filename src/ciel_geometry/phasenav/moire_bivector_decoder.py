"""Candidate moire -> bivector/coframe Lie decoder.

The decoder is a representation-level construction only. It maps relative
36D phase coordinates to a 6x6 real generator, decomposes Mat(6) into the
conformal-orthogonal geometric sector co(3,3) (dimension 16) plus a
20-dimensional simplicity-defect sector, and inverts the exterior-square Lie
representation to a 4x4 gl(4) coframe generator.

No physical gravity claim follows from this projection by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from .bivector36 import BivectorField36, PAIR_BASIS, wedge_pairing
from .moire_hyperlayers import PhaseMatrix6, pair_hyperlayers

TAU = 2.0 * math.pi
J = wedge_pairing()


def _matmul(a, b):
    return tuple(
        tuple(
            math.fsum(a[i][k] * b[k][j] for k in range(len(b)))
            for j in range(len(b[0]))
        )
        for i in range(len(a))
    )


def _transpose(a):
    return tuple(
        tuple(a[j][i] for j in range(len(a)))
        for i in range(len(a[0]))
    )


def _add(a, b):
    return tuple(
        tuple(x + y for x, y in zip(ra, rb))
        for ra, rb in zip(a, b)
    )


def _sub(a, b):
    return tuple(
        tuple(x - y for x, y in zip(ra, rb))
        for ra, rb in zip(a, b)
    )


def _scale(a, scalar: float):
    return tuple(tuple(scalar * x for x in row) for row in a)


def _eye(n: int):
    return tuple(
        tuple(1.0 if i == j else 0.0 for j in range(n))
        for i in range(n)
    )


def _frob(a) -> float:
    return math.sqrt(math.fsum(x * x for row in a for x in row))


def _trace(a) -> float:
    return math.fsum(a[i][i] for i in range(len(a)))


def _j_adjoint(x):
    # theta_J(X) = J X^T J, with J^2 = I.
    return _matmul(_matmul(J, _transpose(x)), J)


def relative_phase_generator(
    left: PhaseMatrix6,
    right: PhaseMatrix6,
) -> BivectorField36:
    """Return the signed shortest relative phase in each 6x6 channel.

    pair_hyperlayers stores half_delta = wrap(left-right)/2, so multiplying by
    two recovers the local Lie-coordinate Arg(exp(i(left-right))).
    This is invariant under a common U(1) phase shift and changes sign under
    layer exchange away from the unavoidable pi branch cut.
    """
    pair = pair_hyperlayers(left, right)
    return BivectorField36.from_flat36(
        tuple(2.0 * h for h in pair.half_delta36)
    )


@dataclass(frozen=True)
class Co33Decomposition:
    raw: BivectorField36
    geometric: BivectorField36
    defect: BivectorField36
    scalar_alpha: float
    defect_ratio: float
    co33_residual: float
    defect_symmetry_residual: float
    defect_trace: float

    @property
    def curvature_candidate(self) -> BivectorField36:
        """Preferred name for the 20D J-self-adjoint traceless sector.

        The historical `defect` field is retained for backward compatibility.
        Physical curvature still requires an independent differential gate.
        """
        return self.defect

    @property
    def curvature_candidate_ratio(self) -> float:
        """Frobenius-amplitude ratio of the 20D algebraic-curvature sector."""
        return self.defect_ratio


def decompose_co33(field: BivectorField36) -> Co33Decomposition:
    """Orthogonally decompose Mat(6) = co(3,3) + Q for the wedge pairing.

    theta_J(X) = J X^T J

    so(3,3) part: (X-theta_J(X))/2
    scalar conformal part: tr(X)/6 * I
    Q: J-self-adjoint traceless complement. Historically called a
       "simplicity defect"; the preferred representation-level interpretation
       is a 20D algebraic-curvature candidate after S=JQ.

    Dimensions:
        36 = 15 + 1 + 20.
    """
    x = field.matrix6
    theta = _j_adjoint(x)
    so_part = _scale(_sub(x, theta), 0.5)
    alpha = _trace(x) / 6.0
    geometric = _add(so_part, _scale(_eye(6), alpha))
    defect = _sub(x, geometric)

    lhs = _add(
        _matmul(_transpose(geometric), J),
        _matmul(J, geometric),
    )
    target = _scale(J, 2.0 * alpha)
    co_residual = _frob(_sub(lhs, target)) / max(1.0, _frob(target))

    symmetry_residual = _frob(
        _sub(_j_adjoint(defect), defect)
    ) / max(1.0, _frob(defect))

    defect_ratio = _frob(defect) / max(1e-300, _frob(x))

    return Co33Decomposition(
        raw=field,
        geometric=BivectorField36(geometric),
        defect=BivectorField36(defect),
        scalar_alpha=alpha,
        defect_ratio=defect_ratio,
        co33_residual=co_residual,
        defect_symmetry_residual=symmetry_residual,
        defect_trace=_trace(defect),
    )


def _pair_index_sign(i: int, j: int) -> tuple[int | None, float]:
    if i == j:
        return None, 0.0
    for index, (a, b) in enumerate(PAIR_BASIS):
        if (i, j) == (a, b):
            return index, 1.0
        if (i, j) == (b, a):
            return index, -1.0
    raise AssertionError((i, j))


def _bivector_component(
    matrix6,
    out_i: int,
    out_j: int,
    in_i: int,
    in_j: int,
) -> float:
    row, row_sign = _pair_index_sign(out_i, out_j)
    col, col_sign = _pair_index_sign(in_i, in_j)
    if row is None or col is None:
        return 0.0
    return row_sign * col_sign * matrix6[row][col]


def lie_exterior_square(
    generator4: Sequence[Sequence[float]],
) -> BivectorField36:
    """Differential of the exterior-square representation gl(4)->co(3,3)."""
    if len(generator4) != 4 or any(len(row) != 4 for row in generator4):
        raise ValueError("expected 4x4 generator")
    h = tuple(tuple(float(x) for x in row) for row in generator4)
    if not all(math.isfinite(x) for row in h for x in row):
        raise ValueError("generator entries must be finite")

    out = [[0.0] * 6 for _ in range(6)]
    for col, (i, j) in enumerate(PAIR_BASIS):
        for row, (k, ell) in enumerate(PAIR_BASIS):
            out[row][col] = (
                h[k][i] * (1.0 if ell == j else 0.0)
                - h[ell][i] * (1.0 if k == j else 0.0)
                + (1.0 if k == i else 0.0) * h[ell][j]
                - (1.0 if ell == i else 0.0) * h[k][j]
            )
    return BivectorField36(tuple(tuple(row) for row in out))


def inverse_lie_exterior_square(
    geometric: BivectorField36,
) -> tuple[tuple[float, ...], ...]:
    """Invert the local exterior-square Lie map on its geometric image.

    If A = d(Lambda^2)(H), contraction gives

        C^k_i = sum_j A^{k j}_{i j}
              = 2 H^k_i + delta^k_i tr(H)

    in four dimensions. Hence tr(H)=tr(C)/6 and H follows directly.
    """
    a = geometric.matrix6
    contracted = [[0.0] * 4 for _ in range(4)]
    for k in range(4):
        for i in range(4):
            contracted[k][i] = math.fsum(
                _bivector_component(a, k, j, i, j)
                for j in range(4)
            )

    tr_h = math.fsum(contracted[i][i] for i in range(4)) / 6.0
    h = [[0.0] * 4 for _ in range(4)]
    for k in range(4):
        for i in range(4):
            h[k][i] = 0.5 * (
                contracted[k][i]
                - (tr_h if k == i else 0.0)
            )
    return tuple(tuple(row) for row in h)


@dataclass(frozen=True)
class MoireCoframeGeneratorReceipt:
    relative_phase: BivectorField36
    geometric: BivectorField36
    defect: BivectorField36
    coframe_generator4: tuple[tuple[float, ...], ...]
    scalar_alpha: float
    defect_ratio: float
    co33_residual: float
    lie_roundtrip_residual: float
    candidate_only: bool = True
    physical_gravity_claim: bool = False


def decode_moire_to_coframe_generator(
    left: PhaseMatrix6,
    right: PhaseMatrix6,
) -> MoireCoframeGeneratorReceipt:
    raw = relative_phase_generator(left, right)
    decomposition = decompose_co33(raw)
    h = inverse_lie_exterior_square(decomposition.geometric)
    roundtrip = lie_exterior_square(h)
    residual = _frob(
        _sub(roundtrip.matrix6, decomposition.geometric.matrix6)
    ) / max(1.0, _frob(decomposition.geometric.matrix6))

    return MoireCoframeGeneratorReceipt(
        relative_phase=raw,
        geometric=decomposition.geometric,
        defect=decomposition.defect,
        coframe_generator4=h,
        scalar_alpha=decomposition.scalar_alpha,
        defect_ratio=decomposition.defect_ratio,
        co33_residual=decomposition.co33_residual,
        lie_roundtrip_residual=residual,
    )


@dataclass(frozen=True)
class GL4MetricSplit:
    lorentz_gauge4: tuple[tuple[float,...],...]
    metric_deformation4: tuple[tuple[float,...],...]
    first_metric_variation4: tuple[tuple[float,...],...]
    dimension_ledger: tuple[int,int,int]=(20,6,10)


def _inverse4_matrix(a):
    m=[list(map(float,row))+[1.0 if i==j else 0.0 for j in range(4)] for i,row in enumerate(a)]
    for col in range(4):
        pivot=max(range(col,4),key=lambda r:abs(m[r][col]))
        if abs(m[pivot][col])<1e-15:
            raise ValueError("metric must be invertible")
        m[col],m[pivot]=m[pivot],m[col]
        s=m[col][col]
        m[col]=[x/s for x in m[col]]
        for r in range(4):
            if r==col: continue
            f=m[r][col]
            m[r]=[x-f*y for x,y in zip(m[r],m[col])]
    return tuple(tuple(row[4:]) for row in m)


def split_gl4_lorentz_metric(
    generator4,
    metric4=((1.0,0.0,0.0,0.0),(0.0,-1.0/3.0,0.0,0.0),(0.0,0.0,-1.0/3.0,0.0),(0.0,0.0,0.0,-1.0/3.0)),
) -> GL4MetricSplit:
    h=tuple(tuple(float(x) for x in row) for row in generator4)
    g=tuple(tuple(float(x) for x in row) for row in metric4)
    if len(h)!=4 or any(len(r)!=4 for r in h) or len(g)!=4 or any(len(r)!=4 for r in g):
        raise ValueError("expected 4x4 generator and metric")
    ginv=_inverse4_matrix(g)
    hdag=_matmul(_matmul(ginv,_transpose(h)),g)
    gauge=_scale(_sub(h,hdag),0.5)
    metric=_scale(_add(h,hdag),0.5)
    delta_g=_scale(_add(_matmul(_transpose(h),g),_matmul(g,h)),-1.0)
    return GL4MetricSplit(gauge,metric,delta_g)
