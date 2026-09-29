from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

SCHEMA = "phasenav.global-support-transfer/v0.18"
EPISTEMIC = "CANDIDATE_ONLY"
CANON_ALLOWED = False


class GlobalSupportError(ValueError):
    pass


# Basis used by the analytic derivation: (00,10,01,11), columns=input, rows=output.
HAAR_CZ_SUPPORT_BASIS = ((0,0),(1,0),(0,1),(1,1))
HAAR_CZ_SUPPORT_TRANSFER = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0/3.0, 0.0, 2.0/9.0],
    [0.0, 0.0, 1.0/3.0, 2.0/9.0],
    [0.0, 2.0/3.0, 2.0/3.0, 5.0/9.0],
], dtype=np.float64)


def support_transfer_standard_basis() -> np.ndarray:
    """Return the local transfer in standard bit basis (00,01,10,11)."""
    # standard -> analytic basis indices
    p = [0,2,1,3]
    return HAAR_CZ_SUPPORT_TRANSFER[np.ix_(p,p)].copy()


def support_gate_tensor() -> np.ndarray:
    """G[o_i,o_j,i_i,i_j] for the local support Markov map."""
    return support_transfer_standard_basis().reshape(2,2,2,2)


def swap_gate_tensor() -> np.ndarray:
    m = np.zeros((4,4), dtype=np.float64)
    for a in (0,1):
        for b in (0,1):
            m[2*b+a, 2*a+b] = 1.0
    return m.reshape(2,2,2,2)


@dataclass(frozen=True)
class BondEvent:
    step: int
    kind: str
    left_label: int
    right_label: int
    bond_rank: int
    discarded_l2: float


@dataclass(frozen=True)
class SupportMPSReceipt:
    num_sites: int
    depth: int
    initial_active: tuple[int,...]
    initial_order: tuple[int,...]
    final_order: tuple[int,...]
    cycles_completed: int
    matching_layers_completed: int
    pair_updates: int
    reorder_swaps: int
    peak_bond: int
    peak_tensor_elements: int
    normalization: float
    numerical_rank_rtol: float
    total_discarded_l2: float
    exact_under_declared_rank_rule: bool
    aborted: bool
    abort_reason: str | None
    bond_by_cycle: tuple[int,...]


class SupportMPS:
    """MPS representation of a probability vector on labelled support bits.

    Adjacent variable reordering is performed by an exact SWAP map and an update
    of the label order. Two-site updates are factored by SVD. The default rank
    threshold is machine precision * max(shape) * sigma_max, i.e. a numerical
    rank rule rather than a fitted physical cutoff.
    """

    def __init__(self, tensors: Sequence[np.ndarray], order: Sequence[int]):
        self.tensors=[np.asarray(t,dtype=np.float64) for t in tensors]
        self.order=list(map(int,order))
        if len(self.tensors)!=len(self.order):
            raise GlobalSupportError("tensor/order length mismatch")
        for k,t in enumerate(self.tensors):
            if t.ndim!=3 or t.shape[1]!=2:
                raise GlobalSupportError("each MPS tensor must be Dl x 2 x Dr")
            if k==0 and t.shape[0]!=1:
                raise GlobalSupportError("left boundary dimension must be 1")
            if k==len(self.tensors)-1 and t.shape[2]!=1:
                raise GlobalSupportError("right boundary dimension must be 1")
            if k+1<len(self.tensors) and t.shape[2]!=self.tensors[k+1].shape[0]:
                raise GlobalSupportError("adjacent bond mismatch")
        if len(set(self.order))!=len(self.order):
            raise GlobalSupportError("order labels must be unique")
        self.total_discarded_l2=0.0
        self.peak_bond=max([1]+[t.shape[2] for t in self.tensors[:-1]])
        self.peak_tensor_elements=max(int(t.size) for t in self.tensors)
        self.events=[]

    @classmethod
    def product_state(cls, num_sites:int, active: Iterable[int]=(), order: Sequence[int]|None=None):
        n=int(num_sites)
        if n<=0: raise GlobalSupportError("num_sites must be positive")
        order=list(range(n)) if order is None else list(map(int,order))
        if sorted(order)!=list(range(n)):
            raise GlobalSupportError("order must be a permutation of site labels")
        active=set(map(int,active))
        if any(q<0 or q>=n for q in active):
            raise GlobalSupportError("active label out of range")
        tensors=[]
        for label in order:
            v=np.zeros((1,2,1),dtype=np.float64)
            v[0,1 if label in active else 0,0]=1.0
            tensors.append(v)
        return cls(tensors,order)

    def position(self,label:int)->int:
        try: return self.order.index(int(label))
        except ValueError as e: raise GlobalSupportError(f"unknown label {label}") from e

    def _apply_adjacent(self,pos:int,gate:np.ndarray,*,rtol:float,max_bond:int|None,kind:str,labels:tuple[int,int],step:int)->int:
        if not (0<=pos<len(self.tensors)-1):
            raise GlobalSupportError("adjacent position out of range")
        a=self.tensors[pos]; b=self.tensors[pos+1]
        dl,_,dm=a.shape; dm2,_,dr=b.shape
        if dm!=dm2: raise GlobalSupportError("bond mismatch")
        theta=np.einsum('lar,rbs->labs',a,b,optimize=True)  # Dl,ai,bi,Dr
        out=np.einsum('ABab,labs->lABs',gate,theta,optimize=True)
        mat=out.reshape(dl*2,2*dr)
        if not np.all(np.isfinite(mat)):
            raise GlobalSupportError("non-finite MPS two-site matrix")
        try:
            u,s,vh=np.linalg.svd(mat,full_matrices=False)
        except np.linalg.LinAlgError:
            # More conservative LAPACK driver fallback for ill-conditioned
            # probability-transfer factorizations.  This changes no cutoff.
            from scipy.linalg import svd as _scipy_svd
            u,s,vh=_scipy_svd(mat,full_matrices=False,lapack_driver="gesvd",check_finite=True)
        if s.size:
            threshold=float(rtol)*max(mat.shape)*float(s[0])
            rank=int(np.count_nonzero(s>threshold))
        else:
            threshold=0.0; rank=0
        rank=max(rank,1)
        if max_bond is not None and rank>int(max_bond):
            raise MemoryError(f"required bond rank {rank} exceeds max_bond={max_bond}")
        discarded=float(np.linalg.norm(s[rank:])) if rank<s.size else 0.0
        self.total_discarded_l2 += discarded
        u=u[:,:rank]; s=s[:rank]; vh=vh[:rank,:]
        self.tensors[pos]=u.reshape(dl,2,rank)
        self.tensors[pos+1]=(s[:,None]*vh).reshape(rank,2,dr)
        self.peak_bond=max(self.peak_bond,rank)
        self.peak_tensor_elements=max(self.peak_tensor_elements,int(self.tensors[pos].size),int(self.tensors[pos+1].size))
        self.events.append(BondEvent(step,kind,labels[0],labels[1],rank,discarded))
        return rank

    def reorder_adjacent(self,pos:int,*,rtol:float,max_bond:int|None,step:int):
        labels=(self.order[pos],self.order[pos+1])
        self._apply_adjacent(pos,swap_gate_tensor(),rtol=rtol,max_bond=max_bond,kind="REORDER_SWAP",labels=labels,step=step)
        self.order[pos],self.order[pos+1]=self.order[pos+1],self.order[pos]

    def bring_adjacent(self,a:int,b:int,*,rtol:float,max_bond:int|None,step:int)->int:
        """Bring b next to a by shortest bubble movement; return swap count."""
        pa=self.position(a); pb=self.position(b)
        swaps=0
        if abs(pa-pb)==1: return 0
        if pb>pa:
            # move b left until directly after a
            while pb>pa+1:
                self.reorder_adjacent(pb-1,rtol=rtol,max_bond=max_bond,step=step)
                pb-=1; swaps+=1
        else:
            # move b right until directly before a
            while pb<pa-1:
                self.reorder_adjacent(pb,rtol=rtol,max_bond=max_bond,step=step)
                pb+=1; swaps+=1
        return swaps

    def apply_pair(self,a:int,b:int,gate:np.ndarray,*,rtol:float,max_bond:int|None,step:int)->tuple[int,int]:
        swaps=self.bring_adjacent(a,b,rtol=rtol,max_bond=max_bond,step=step)
        pa=self.position(a); pb=self.position(b)
        if abs(pa-pb)!=1: raise GlobalSupportError("failed to make pair adjacent")
        if pa<pb:
            pos=pa; labels=(a,b); g=gate
        else:
            # Gate is symmetric under site exchange for this support transition.
            pos=pb; labels=(b,a); g=gate
        rank=self._apply_adjacent(pos,g,rtol=rtol,max_bond=max_bond,kind="SUPPORT_TRANSFER",labels=labels,step=step)
        return swaps,rank

    def total_mass(self)->float:
        # Contract physical legs against ones.
        env=np.array([1.0])
        for t in self.tensors:
            m=t[:,0,:]+t[:,1,:]
            env=env@m
        return float(env[0])

    def to_dense(self,*,max_sites:int=20)->np.ndarray:
        n=len(self.tensors)
        if n>max_sites: raise GlobalSupportError("dense materialization refused")
        cur=self.tensors[0]
        # cur 1,2,D
        arr=cur[0]
        # arr physical_flat,D
        for t in self.tensors[1:]:
            arr=np.einsum('xd,day->xay',arr,t,optimize=True)
            arr=arr.reshape(arr.shape[0]*2,arr.shape[-1])
        return arr[:,0]


def _graph_adjacency(num_sites:int, matchings: Mapping[str, Sequence[Sequence[int]]]):
    adj=[set() for _ in range(num_sites)]
    for edges in matchings.values():
        for a,b in edges:
            a=int(a);b=int(b);adj[a].add(b);adj[b].add(a)
    return adj


def reverse_cuthill_mckee_order(num_sites:int, matchings: Mapping[str, Sequence[Sequence[int]]])->tuple[int,...]:
    try:
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import reverse_cuthill_mckee
    except Exception as e:
        raise GlobalSupportError("scipy is required for RCM ordering") from e
    adj=_graph_adjacency(num_sites,matchings)
    rows=[];cols=[]
    for i,nbrs in enumerate(adj):
        for j in nbrs: rows.append(i);cols.append(j)
    data=np.ones(len(rows),dtype=np.int8)
    mat=csr_matrix((data,(rows,cols)),shape=(num_sites,num_sites))
    return tuple(int(x) for x in reverse_cuthill_mckee(mat,symmetric_mode=True))


def evolve_support_mps(
    *,
    num_sites:int,
    matchings: Mapping[str, Sequence[Sequence[int]]],
    schedule: Sequence[str],
    depth:int,
    initial_active: Iterable[int],
    order: Sequence[int]|None=None,
    numerical_rank_rtol: float=np.finfo(np.float64).eps,
    max_bond:int|None=None,
)->SupportMPSReceipt:
    if depth<0: raise GlobalSupportError("depth must be >=0")
    if not schedule: raise GlobalSupportError("schedule must be non-empty")
    if order is None:
        order=reverse_cuthill_mckee_order(num_sites,matchings)
    mps=SupportMPS.product_state(num_sites,initial_active,order=order)
    gate=support_gate_tensor()
    swaps=0; updates=0; layers_done=0; cycles_done=0; bond_by_cycle=[]
    aborted=False; reason=None
    step=0
    try:
        for d in range(depth):
            layer=schedule[d%len(schedule)]
            if layer not in matchings: raise GlobalSupportError(f"unknown layer {layer}")
            # Greedy edge ordering: pick next pair minimizing current MPS distance.
            remaining=[tuple(map(int,e)) for e in matchings[layer]]
            while remaining:
                pair=min(remaining,key=lambda e:(abs(mps.position(e[0])-mps.position(e[1])),e))
                remaining.remove(pair)
                sw,_=mps.apply_pair(pair[0],pair[1],gate,rtol=numerical_rank_rtol,max_bond=max_bond,step=step)
                swaps+=sw;updates+=1;step+=1
            layers_done+=1
            if (d+1)%len(schedule)==0:
                cycles_done+=1
                bond_by_cycle.append(mps.peak_bond)
    except (MemoryError, np.linalg.LinAlgError) as e:
        aborted=True;reason=f"{type(e).__name__}:{e}"

    norm=mps.total_mass()
    return SupportMPSReceipt(
        num_sites=int(num_sites),depth=int(depth),initial_active=tuple(sorted(map(int,initial_active))),
        initial_order=tuple(map(int,order)),final_order=tuple(mps.order),cycles_completed=cycles_done,
        matching_layers_completed=layers_done,pair_updates=updates,reorder_swaps=swaps,
        peak_bond=int(mps.peak_bond),peak_tensor_elements=int(mps.peak_tensor_elements),
        normalization=float(norm),numerical_rank_rtol=float(numerical_rank_rtol),
        total_discarded_l2=float(mps.total_discarded_l2),
        exact_under_declared_rank_rule=bool(mps.total_discarded_l2==0.0 and not aborted),
        aborted=aborted,abort_reason=reason,bond_by_cycle=tuple(map(int,bond_by_cycle)),
    )


@dataclass(frozen=True)
class MonteCarloSupportReceipt:
    num_sites:int
    depth:int
    samples:int
    seed:int
    initial_active:tuple[int,...]
    mean_weight_by_layer:tuple[float,...]
    stderr_weight_by_layer:tuple[float,...]
    final_mean_weight:float
    final_std_weight:float
    final_min_weight:int
    final_max_weight:int
    final_site_active_probability:tuple[float,...]


def _sample_pair_update(a:np.ndarray,b:np.ndarray,rng:np.random.Generator)->tuple[np.ndarray,np.ndarray]:
    # Vectorized exact transition sampler from the rational probabilities.
    x=a.astype(np.int8)*2+b.astype(np.int8)  # standard basis 00,01,10,11
    u=rng.random(x.size)
    ao=np.empty_like(a);bo=np.empty_like(b)
    # 00 -> 00
    mask=x==0;ao[mask]=0;bo[mask]=0
    # 01 -> 01 with 1/3, 11 with 2/3
    mask=x==1; keep=u[mask]<(1/3); ao[mask]=np.where(keep,0,1);bo[mask]=1
    # 10 -> 10 with 1/3, 11 with 2/3
    mask=x==2; keep=u[mask]<(1/3); ao[mask]=1;bo[mask]=np.where(keep,0,1)
    # 11 -> 10 2/9, 01 2/9, 11 5/9
    mask=x==3; uu=u[mask]; ao[mask]=np.where(uu<2/9,1,np.where(uu<4/9,0,1));bo[mask]=np.where(uu<2/9,0,1)
    return ao,bo


def sample_support_trajectories(
    *,num_sites:int,matchings:Mapping[str,Sequence[Sequence[int]]],schedule:Sequence[str],depth:int,
    initial_active:Iterable[int],samples:int=10000,seed:int=0,
)->MonteCarloSupportReceipt:
    n=int(num_sites);ns=int(samples)
    if n<=0 or ns<=0 or depth<0: raise GlobalSupportError("invalid size/depth")
    rng=np.random.default_rng(int(seed))
    state=np.zeros((ns,n),dtype=np.int8)
    active=tuple(sorted(map(int,initial_active)))
    state[:,active]=1
    means=[];ses=[]
    for d in range(depth):
        layer=schedule[d%len(schedule)]
        for a,b in matchings[layer]:
            ao,bo=_sample_pair_update(state[:,a],state[:,b],rng)
            state[:,a]=ao;state[:,b]=bo
        w=state.sum(axis=1)
        means.append(float(w.mean()))
        ses.append(float(w.std(ddof=1)/math.sqrt(ns)) if ns>1 else 0.0)
    w=state.sum(axis=1)
    return MonteCarloSupportReceipt(
        num_sites=n,depth=int(depth),samples=ns,seed=int(seed),initial_active=active,
        mean_weight_by_layer=tuple(means),stderr_weight_by_layer=tuple(ses),
        final_mean_weight=float(w.mean()),final_std_weight=float(w.std(ddof=1)) if ns>1 else 0.0,
        final_min_weight=int(w.min()),final_max_weight=int(w.max()),
        final_site_active_probability=tuple(float(x) for x in state.mean(axis=0)),
    )


def exact_dense_support(
    *,num_sites:int,matchings:Mapping[str,Sequence[Sequence[int]]],schedule:Sequence[str],depth:int,initial_active:Iterable[int]
)->np.ndarray:
    """Exact dense control, refused above 20 sites."""
    n=int(num_sites)
    if n>20: raise GlobalSupportError("exact dense support refused above 20 sites")
    vec=np.zeros(2**n,dtype=np.float64)
    idx=sum(1<<q for q in initial_active)
    vec[idx]=1.0
    t=support_transfer_standard_basis()
    # bit q is little-endian in integer index; reshape with explicit loops for clarity.
    for d in range(depth):
        for a,b in matchings[schedule[d%len(schedule)]]:
            out=np.zeros_like(vec)
            for basis,p in enumerate(vec):
                if p==0: continue
                ai=(basis>>a)&1; bi=(basis>>b)&1
                inp=2*ai+bi
                for outp,prob in enumerate(t[:,inp]):
                    if prob==0: continue
                    ao=(outp>>1)&1; bo=outp&1
                    j=basis
                    if ao!=ai: j ^= (1<<a)
                    if bo!=bi: j ^= (1<<b)
                    out[j]+=p*prob
            vec=out
    return vec


__all__=[
    "SCHEMA","EPISTEMIC","CANON_ALLOWED","GlobalSupportError",
    "HAAR_CZ_SUPPORT_BASIS","HAAR_CZ_SUPPORT_TRANSFER","support_transfer_standard_basis","support_gate_tensor",
    "SupportMPS","BondEvent","SupportMPSReceipt","reverse_cuthill_mckee_order","evolve_support_mps",
    "MonteCarloSupportReceipt","sample_support_trajectories","exact_dense_support",
]