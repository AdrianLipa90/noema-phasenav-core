"""PhaseNav channel, transfer, information and Krylov primitives v0.17.

This candidate layer adds density/channel observables, Choi/Kraus and Pauli
transfer representations, exact second-moment support transport controls,
transfer-spectrum diagnostics and low-rank/Krylov numerical primitives.

The layer is finite and substrate-neutral.  It does not identify software
channels with a physical QPU/noise process unless external calibration is
supplied.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Iterable, Sequence

import numpy as np

SCHEMA = "phasenav.channel-transfer-krylov/v0.17"
EPISTEMIC = "CANDIDATE_ONLY"
CANON_ALLOWED = False


class ChannelPrimitiveError(ValueError):
    pass


def _finite(a, *, name: str) -> np.ndarray:
    arr=np.asarray(a)
    if not np.all(np.isfinite(arr)):
        raise ChannelPrimitiveError(f"{name} must be finite")
    return arr


def _square(a, *, name: str) -> np.ndarray:
    arr=np.asarray(a,dtype=np.complex128)
    if arr.ndim!=2 or arr.shape[0]!=arr.shape[1]:
        raise ChannelPrimitiveError(f"{name} must be square")
    if not np.all(np.isfinite(arr)):
        raise ChannelPrimitiveError(f"{name} must be finite")
    return arr


def _power_of_two_qubits(dim:int)->int:
    dim=int(dim)
    if dim<=0:
        raise ChannelPrimitiveError("dimension must be positive")
    n=int(round(math.log2(dim)))
    if 2**n!=dim:
        raise ChannelPrimitiveError("dimension must be a power of two")
    return n


def normalize_state(state, *, atol:float=1e-15)->np.ndarray:
    psi=np.asarray(state,dtype=np.complex128).reshape(-1)
    if not np.all(np.isfinite(psi)):
        raise ChannelPrimitiveError("state must be finite")
    norm=float(np.linalg.norm(psi))
    if norm<=atol:
        raise ChannelPrimitiveError("state norm is zero")
    return psi/norm


def density_matrix(state)->np.ndarray:
    psi=normalize_state(state)
    return np.outer(psi,psi.conj())


def _validate_density(rho, *, atol:float=1e-10)->np.ndarray:
    r=_square(rho,name="density matrix")
    herm=float(np.linalg.norm(r-r.conj().T,ord="fro"))
    if herm>atol:
        raise ChannelPrimitiveError(f"density matrix not Hermitian: residual={herm}")
    tr=complex(np.trace(r))
    if abs(tr-1.0)>atol:
        raise ChannelPrimitiveError(f"density matrix trace must be 1, got {tr}")
    vals=np.linalg.eigvalsh((r+r.conj().T)/2)
    if float(vals.min()) < -atol:
        raise ChannelPrimitiveError(f"density matrix not positive semidefinite: min={vals.min()}")
    return r


def partial_trace(rho, dims:Sequence[int], keep:Sequence[int])->np.ndarray:
    """Trace out all subsystems not in ``keep``.

    Subsystem order follows tensor axis order in ``dims``.
    """
    dims=tuple(int(d) for d in dims)
    if not dims or any(d<=0 for d in dims):
        raise ChannelPrimitiveError("dims must be positive")
    r=_square(rho,name="rho")
    if r.shape[0]!=math.prod(dims):
        raise ChannelPrimitiveError("rho dimension does not match dims")
    keep=tuple(sorted(set(int(i) for i in keep)))
    if any(i<0 or i>=len(dims) for i in keep):
        raise ChannelPrimitiveError("keep indices out of range")
    traced=[i for i in range(len(dims)) if i not in keep]
    tensor=r.reshape(dims+dims)
    current_dims=list(dims)
    # Trace from highest subsystem down so axis numbering stays stable.
    for i in sorted(traced,reverse=True):
        nsub=len(current_dims)
        tensor=np.trace(tensor,axis1=i,axis2=i+nsub)
        current_dims.pop(i)
    out_dim=math.prod(current_dims) if current_dims else 1
    return np.asarray(tensor,dtype=np.complex128).reshape(out_dim,out_dim)


@dataclass(frozen=True)
class EntropyReceipt:
    eigenvalues: tuple[float,...]
    von_neumann_bits: float
    purity: float
    renyi2_bits: float
    min_entropy_bits: float


def entropy_receipt(rho, *, atol:float=1e-12)->EntropyReceipt:
    r=_validate_density(rho,atol=max(atol,1e-10))
    vals=np.linalg.eigvalsh((r+r.conj().T)/2).real
    vals=np.where(vals<0,0,vals)
    total=float(vals.sum())
    if total<=0:
        raise ChannelPrimitiveError("density spectrum vanished")
    vals=vals/total
    nz=vals[vals>atol]
    s=float(-np.sum(nz*np.log2(nz))) if nz.size else 0.0
    purity=float(np.sum(vals*vals))
    renyi2=float(-math.log2(purity)) if purity>0 else math.inf
    pmax=float(vals.max()) if vals.size else 0.0
    minent=float(-math.log2(pmax)) if pmax>0 else math.inf
    return EntropyReceipt(
        eigenvalues=tuple(float(x) for x in vals),
        von_neumann_bits=s,
        purity=purity,
        renyi2_bits=renyi2,
        min_entropy_bits=minent,
    )


@dataclass(frozen=True)
class MutualInformationReceipt:
    entropy_a_bits: float
    entropy_b_bits: float
    entropy_ab_bits: float
    mutual_information_bits: float


def mutual_information(rho_ab, dims:Sequence[int], a:Sequence[int], b:Sequence[int])->MutualInformationReceipt:
    dims=tuple(int(d) for d in dims)
    a=tuple(sorted(set(int(i) for i in a)))
    b=tuple(sorted(set(int(i) for i in b)))
    if set(a)&set(b):
        raise ChannelPrimitiveError("A and B must be disjoint")
    keep_ab=tuple(sorted(a+b))
    rab=partial_trace(rho_ab,dims,keep_ab)
    dims_ab=tuple(dims[i] for i in keep_ab)
    map_pos={orig:j for j,orig in enumerate(keep_ab)}
    ra=partial_trace(rab,dims_ab,[map_pos[i] for i in a])
    rb=partial_trace(rab,dims_ab,[map_pos[i] for i in b])
    sa=entropy_receipt(ra).von_neumann_bits
    sb=entropy_receipt(rb).von_neumann_bits
    sab=entropy_receipt(rab).von_neumann_bits
    return MutualInformationReceipt(sa,sb,sab,float(sa+sb-sab))


# ---------------------------------------------------------------------------
# Kraus / Choi / superoperator
# ---------------------------------------------------------------------------

def _validate_kraus(kraus:Iterable[np.ndarray])->tuple[np.ndarray,...]:
    ks=tuple(np.asarray(k,dtype=np.complex128) for k in kraus)
    if not ks:
        raise ChannelPrimitiveError("at least one Kraus operator is required")
    shape=ks[0].shape
    if len(shape)!=2 or any(k.shape!=shape for k in ks):
        raise ChannelPrimitiveError("all Kraus operators must have the same matrix shape")
    if not all(np.all(np.isfinite(k)) for k in ks):
        raise ChannelPrimitiveError("Kraus operators must be finite")
    return ks


def apply_channel(rho, kraus:Iterable[np.ndarray])->np.ndarray:
    ks=_validate_kraus(kraus)
    r=_square(rho,name="rho")
    din=ks[0].shape[1]
    if r.shape!=(din,din):
        raise ChannelPrimitiveError("rho dimension does not match Kraus input")
    return sum((k@r@k.conj().T for k in ks),np.zeros((ks[0].shape[0],ks[0].shape[0]),complex))


def choi_from_kraus(kraus:Iterable[np.ndarray])->np.ndarray:
    """Return Choi matrix in output⊗input ordering.

    J = sum_ij E(|i><j|) ⊗ |i><j|.
    """
    ks=_validate_kraus(kraus)
    dout,din=ks[0].shape
    jmat=np.zeros((dout*din,dout*din),dtype=np.complex128)
    for i in range(din):
        for j in range(din):
            eij=np.zeros((din,din),complex); eij[i,j]=1.0
            out=apply_channel(eij,ks)
            inp=np.zeros((din,din),complex); inp[i,j]=1.0
            jmat+=np.kron(out,inp)
    return jmat


def kraus_from_choi(choi, dout:int, din:int, *, atol:float=1e-12)->tuple[np.ndarray,...]:
    j=_square(choi,name="choi")
    dout=int(dout); din=int(din)
    if j.shape!=(dout*din,dout*din):
        raise ChannelPrimitiveError("Choi dimension mismatch")
    herm=(j+j.conj().T)/2
    vals,vecs=np.linalg.eigh(herm)
    if float(vals.min()) < -atol:
        raise ChannelPrimitiveError("Choi matrix is not positive semidefinite")
    ks=[]
    for lam,vec in zip(vals,vecs.T):
        if lam>atol:
            # For output⊗input Choi ordering constructed above, vec is C-order
            # flattening of K columns interleaved by input in the Kronecker basis.
            # Reshape to (dout,din) in C-order.
            ks.append(math.sqrt(float(lam))*vec.reshape(dout,din))
    return tuple(ks)


def superoperator_from_kraus(kraus:Iterable[np.ndarray])->np.ndarray:
    """Column-vectorization superoperator: vec(E(rho)) = S vec(rho)."""
    ks=_validate_kraus(kraus)
    return sum((np.kron(k.conj(),k) for k in ks),np.zeros((ks[0].shape[0]**2,ks[0].shape[1]**2),complex))


@dataclass(frozen=True)
class ChannelReceipt:
    input_dim: int
    output_dim: int
    kraus_rank: int
    choi_min_eigenvalue: float
    cp_residual: float
    tp_residual: float
    unital_residual: float


def channel_receipt(kraus:Iterable[np.ndarray], *, atol:float=1e-12)->ChannelReceipt:
    ks=_validate_kraus(kraus)
    dout,din=ks[0].shape
    j=choi_from_kraus(ks)
    eig=np.linalg.eigvalsh((j+j.conj().T)/2).real
    mine=float(eig.min())
    cp_res=max(0.0,-mine)
    tp=sum((k.conj().T@k for k in ks),np.zeros((din,din),complex))
    unital=sum((k@k.conj().T for k in ks),np.zeros((dout,dout),complex))
    return ChannelReceipt(
        input_dim=din,
        output_dim=dout,
        kraus_rank=len(ks),
        choi_min_eigenvalue=mine,
        cp_residual=float(cp_res),
        tp_residual=float(np.linalg.norm(tp-np.eye(din),ord="fro")),
        unital_residual=float(np.linalg.norm(unital-np.eye(dout),ord="fro")) if din==dout else math.nan,
    )


# ---------------------------------------------------------------------------
# Pauli transfer / second moments
# ---------------------------------------------------------------------------

I2=np.eye(2,dtype=np.complex128)
X=np.array([[0,1],[1,0]],dtype=np.complex128)
Y=np.array([[0,-1j],[1j,0]],dtype=np.complex128)
Z=np.array([[1,0],[0,-1]],dtype=np.complex128)
PAULI_SINGLE=(I2,X,Y,Z)


def pauli_basis(num_qubits:int)->tuple[np.ndarray,...]:
    n=int(num_qubits)
    if n<1 or n>4:
        raise ChannelPrimitiveError("pauli_basis is bounded to 1..4 qubits")
    out=[]
    for label in itertools.product(range(4),repeat=n):
        m=np.array([[1+0j]])
        for idx in label:
            m=np.kron(m,PAULI_SINGLE[idx])
        out.append(m)
    return tuple(out)


def pauli_transfer_matrix(kraus:Iterable[np.ndarray], *, max_qubits:int=3)->np.ndarray:
    ks=_validate_kraus(kraus)
    dout,din=ks[0].shape
    if dout!=din:
        raise ChannelPrimitiveError("PTM currently requires equal input/output dimension")
    n=_power_of_two_qubits(din)
    if n>max_qubits:
        raise ChannelPrimitiveError(f"PTM bounded to <= {max_qubits} qubits")
    basis=pauli_basis(n)
    d=din
    r=np.zeros((len(basis),len(basis)),dtype=np.float64)
    for j,p in enumerate(basis):
        ep=apply_channel(p,ks)
        for i,q in enumerate(basis):
            value=np.trace(q.conj().T@ep)/d
            if abs(value.imag)>1e-10:
                raise ChannelPrimitiveError("Hermiticity-preserving channel produced complex PTM coefficient")
            r[i,j]=float(value.real)
    return r


@dataclass(frozen=True)
class PTMReceipt:
    rows: int
    cols: int
    nonzero_count: int
    density: float
    signed_permutation: bool
    column_norm_residual: float


def ptm_receipt(ptm, *, atol:float=1e-10)->PTMReceipt:
    r=np.asarray(ptm,dtype=float)
    if r.ndim!=2 or not np.all(np.isfinite(r)):
        raise ChannelPrimitiveError("PTM must be a finite matrix")
    nonzero=int(np.count_nonzero(np.abs(r)>atol))
    signed=False
    norm_res=math.inf
    if r.shape[0]==r.shape[1]:
        absr=np.abs(r)
        row_hits=np.sum(absr>atol,axis=1)
        col_hits=np.sum(absr>atol,axis=0)
        vals=absr[absr>atol]
        signed=bool(np.all(row_hits==1) and np.all(col_hits==1) and np.all(np.abs(vals-1.0)<=atol))
        norms=np.sum(r*r,axis=0)
        norm_res=float(np.max(np.abs(norms-1.0)))
    return PTMReceipt(r.shape[0],r.shape[1],nonzero,float(nonzero/r.size),signed,norm_res)


def pauli_second_moment_transition(ptm)->np.ndarray:
    """Square PTM entries columnwise.

    For a unitary channel this is column stochastic and gives the transition of
    squared Pauli amplitudes in the normalized Pauli basis.
    """
    r=np.asarray(ptm,dtype=float)
    if r.ndim!=2 or not np.all(np.isfinite(r)):
        raise ChannelPrimitiveError("PTM must be finite")
    return r*r


def haar_local_cz_support_transition()->np.ndarray:
    """Exact local-Haar-twirled support transition for one CZ edge.

    Basis order for both rows/columns: 00,10,01,11.
    Columns are input support classes; rows are output support classes.
    """
    return np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0/3.0, 0.0, 2.0/9.0],
        [0.0, 0.0, 1.0/3.0, 2.0/9.0],
        [0.0, 2.0/3.0, 2.0/3.0, 5.0/9.0],
    ],dtype=float)


# ---------------------------------------------------------------------------
# Transfer spectrum / fixed points
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TransferSpectrumReceipt:
    eigenvalues: tuple[complex,...]
    spectral_radius: float
    subleading_magnitude: float
    gap: float


def transfer_spectrum(operator)->TransferSpectrumReceipt:
    a=_square(operator,name="transfer operator")
    vals=np.linalg.eigvals(a)
    order=np.argsort(-np.abs(vals))
    vals=vals[order]
    mags=np.abs(vals)
    radius=float(mags[0]) if mags.size else 0.0
    sub=float(mags[1]) if mags.size>1 else 0.0
    return TransferSpectrumReceipt(
        eigenvalues=tuple(complex(x) for x in vals),
        spectral_radius=radius,
        subleading_magnitude=sub,
        gap=float(radius-sub),
    )


@dataclass(frozen=True)
class FixedPointReceipt:
    density: np.ndarray
    eigenvalue: complex
    residual: float
    hermiticity_residual: float
    trace_residual: float


def channel_fixed_point(kraus:Iterable[np.ndarray], *, atol:float=1e-10)->FixedPointReceipt:
    ks=_validate_kraus(kraus)
    dout,din=ks[0].shape
    if dout!=din:
        raise ChannelPrimitiveError("fixed point requires square channel")
    s=superoperator_from_kraus(ks)
    vals,vecs=np.linalg.eig(s)
    idx=int(np.argmin(np.abs(vals-1.0)))
    lam=complex(vals[idx])
    raw=vecs[:,idx].reshape(din,din,order="F")
    rho=(raw+raw.conj().T)/2
    tr=complex(np.trace(rho))
    if abs(tr)<=atol:
        raise ChannelPrimitiveError("candidate fixed point has zero trace")
    rho=rho/tr
    # If numerical eigenvector sign makes it negative, flip is not allowed after trace=1;
    # check PSD and fail if channel is pathological for this simple extractor.
    ev=np.linalg.eigvalsh((rho+rho.conj().T)/2).real
    if float(ev.min()) < -1e-8:
        raise ChannelPrimitiveError("dominant unit-eigenvalue vector is not a density matrix")
    residual=float(np.linalg.norm(apply_channel(rho,ks)-rho,ord="fro"))
    return FixedPointReceipt(
        density=rho,
        eigenvalue=lam,
        residual=residual,
        hermiticity_residual=float(np.linalg.norm(rho-rho.conj().T,ord="fro")),
        trace_residual=float(abs(np.trace(rho)-1.0)),
    )


# ---------------------------------------------------------------------------
# Low-rank updates / Krylov
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WoodburyReceipt:
    inverse: np.ndarray
    middle_condition_number: float
    inverse_residual: float


def woodbury_inverse_update(a_inverse, u, c, v, *, condition_limit:float=1e12)->WoodburyReceipt:
    ai=_square(a_inverse,name="A inverse")
    u=np.asarray(u,dtype=np.complex128)
    c=_square(c,name="C")
    v=np.asarray(v,dtype=np.complex128)
    n=ai.shape[0]
    k=c.shape[0]
    if u.shape!=(n,k) or v.shape!=(k,n):
        raise ChannelPrimitiveError("Woodbury dimensions are inconsistent")
    cinv=np.linalg.inv(c)
    middle=cinv+v@ai@u
    cond=float(np.linalg.cond(middle))
    if not math.isfinite(cond) or cond>condition_limit:
        raise ChannelPrimitiveError("Woodbury middle matrix is singular/ill-conditioned")
    updated=ai-ai@u@np.linalg.solve(middle,v@ai)
    # Reconstruct A from A^-1 only for validation; fail closed if singular.
    a=np.linalg.inv(ai)
    target=a+u@c@v
    residual=float(np.linalg.norm(target@updated-np.eye(n),ord="fro"))
    return WoodburyReceipt(updated,cond,residual)


@dataclass(frozen=True)
class LanczosReceipt:
    alpha: tuple[float,...]
    beta: tuple[float,...]
    basis: np.ndarray
    tridiagonal: np.ndarray
    orthogonality_residual: float
    recurrence_residual: float


def lanczos_hermitian(matrix, start, steps:int, *, atol:float=1e-14)->LanczosReceipt:
    a=_square(matrix,name="Hermitian matrix")
    herm=float(np.linalg.norm(a-a.conj().T,ord="fro"))
    if herm>1e-10:
        raise ChannelPrimitiveError(f"matrix is not Hermitian: {herm}")
    n=a.shape[0]
    k=min(int(steps),n)
    if k<=0:
        raise ChannelPrimitiveError("steps must be positive")
    q=np.asarray(start,dtype=np.complex128).reshape(-1)
    if q.size!=n:
        raise ChannelPrimitiveError("start vector dimension mismatch")
    norm=float(np.linalg.norm(q))
    if norm<=atol:
        raise ChannelPrimitiveError("start vector has zero norm")
    q=q/norm

    qs=[]
    alpha=[]
    beta=[]
    qprev=np.zeros_like(q)
    bprev=0.0
    for j in range(k):
        qs.append(q.copy())
        z=a@q-bprev*qprev
        aj=float(np.vdot(q,z).real)
        z=z-aj*q
        # Full reorthogonalization for deterministic numerical stability.
        for qi in qs:
            z=z-np.vdot(qi,z)*qi
        bj=float(np.linalg.norm(z))
        alpha.append(aj)
        if j<k-1:
            beta.append(bj)
        if bj<=atol or j==k-1:
            break
        qprev,q=q,z/bj
        bprev=bj

    qmat=np.column_stack(qs)
    m=len(alpha)
    t=np.zeros((m,m),dtype=float)
    for i,a0 in enumerate(alpha):
        t[i,i]=a0
    for i,b0 in enumerate(beta[:m-1]):
        t[i,i+1]=b0
        t[i+1,i]=b0
    orth=float(np.linalg.norm(qmat.conj().T@qmat-np.eye(m),ord="fro"))
    rec=float(np.linalg.norm(a@qmat-qmat@t,ord="fro"))
    # The recurrence residual includes the final unreduced beta*q_{m+1}; report it
    # rather than pretending exact closure.
    return LanczosReceipt(
        alpha=tuple(alpha),
        beta=tuple(beta[:max(0,m-1)]),
        basis=qmat,
        tridiagonal=t,
        orthogonality_residual=orth,
        recurrence_residual=rec,
    )


__all__=[
    "SCHEMA","EPISTEMIC","CANON_ALLOWED","ChannelPrimitiveError",
    "normalize_state","density_matrix","partial_trace","EntropyReceipt","entropy_receipt",
    "MutualInformationReceipt","mutual_information","apply_channel","choi_from_kraus",
    "kraus_from_choi","superoperator_from_kraus","ChannelReceipt","channel_receipt",
    "PAULI_SINGLE","pauli_basis","pauli_transfer_matrix","PTMReceipt","ptm_receipt",
    "pauli_second_moment_transition","haar_local_cz_support_transition",
    "TransferSpectrumReceipt","transfer_spectrum","FixedPointReceipt","channel_fixed_point",
    "WoodburyReceipt","woodbury_inverse_update","LanczosReceipt","lanczos_hermitian",
]