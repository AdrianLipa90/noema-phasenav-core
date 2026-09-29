from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Mapping, Sequence, Iterable
import numpy as np
from global_support_transfer import support_gate_tensor, GlobalSupportError


@dataclass(frozen=True)
class RowBlockReceipt:
    depth:int
    layers_completed:int
    cycles_completed:int
    peak_bond:int
    peak_svd_matrix_elements:int
    normalization:float
    total_discarded_l2:float
    bond_history:tuple[tuple[int,...],...]
    aborted:bool
    abort_reason:str|None
    row_sizes:tuple[int,...]
    row_labels:tuple[tuple[int,...],...]


def _apply_two_axis_gate(arr:np.ndarray,axis1:int,axis2:int,gate:np.ndarray)->np.ndarray:
    if axis1==axis2: raise GlobalSupportError('axes must differ')
    if axis1>axis2: axis1,axis2=axis2,axis1
    n=arr.ndim
    if arr.shape[axis1]!=2 or arr.shape[axis2]!=2: raise GlobalSupportError('gate axes must be binary')
    remaining=[p for p in range(n) if p not in (axis1,axis2)]
    out=np.tensordot(gate,arr,axes=([2,3],[axis1,axis2]))
    perm=[]
    for p in range(n):
        if p==axis1: perm.append(0)
        elif p==axis2: perm.append(1)
        else: perm.append(2+remaining.index(p))
    return np.transpose(out,perm)


def _stable_svd(mat):
    if not np.all(np.isfinite(mat)): raise GlobalSupportError('non-finite SVD matrix')
    try:return np.linalg.svd(mat,full_matrices=False)
    except np.linalg.LinAlgError:
        from scipy.linalg import svd
        return svd(mat,full_matrices=False,lapack_driver='gesvd',check_finite=True)


class RowBlockMPS:
    def __init__(self,row_labels:Sequence[Sequence[int]],active:Iterable[int]):
        self.row_labels=tuple(tuple(map(int,row)) for row in row_labels)
        self.label_to_pos={q:(r,i) for r,row in enumerate(self.row_labels) for i,q in enumerate(row)}
        active=set(map(int,active))
        self.tensors=[]
        for row in self.row_labels:
            k=len(row);d=2**k
            bits=[1 if q in active else 0 for q in row]
            idx=sum(bit << (k-1-i) for i,bit in enumerate(bits))
            t=np.zeros((1,d,1),dtype=np.float64);t[0,idx,0]=1.0
            self.tensors.append(t)
        self.total_discarded_l2=0.0
        self.peak_bond=1
        self.peak_svd_matrix_elements=0

    def total_mass(self):
        env=np.array([1.0])
        for t in self.tensors:
            env=env@t.sum(axis=1)
        return float(env[0])

    def _apply_local_pairs(self,row:int,pairs:Sequence[tuple[int,int]],gate):
        if not pairs:return
        t=self.tensors[row]; dl,d,dr=t.shape;k=len(self.row_labels[row])
        arr=t.reshape((dl,)+((2,)*k)+(dr,))
        local={q:i for i,q in enumerate(self.row_labels[row])}
        for a,b in pairs:
            ia=1+local[a];ib=1+local[b]
            arr=_apply_two_axis_gate(arr,ia,ib,gate)
        self.tensors[row]=arr.reshape(dl,d,dr)

    def _apply_cross_pairs(self,r:int,pairs:Sequence[tuple[int,int]],gate,*,rtol,max_bond,max_matrix_elements):
        if not pairs:return
        if not (0<=r<len(self.tensors)-1):raise GlobalSupportError('row pair out of range')
        A=self.tensors[r];B=self.tensors[r+1]
        dl,dA,dm=A.shape;dm2,dB,dr=B.shape
        if dm!=dm2:raise GlobalSupportError('bond mismatch')
        kA=len(self.row_labels[r]);kB=len(self.row_labels[r+1])
        theta=np.einsum('lar,rbs->labs',A,B,optimize=True)
        arr=theta.reshape((dl,)+((2,)*kA)+((2,)*kB)+(dr,))
        locA={q:i for i,q in enumerate(self.row_labels[r])}
        locB={q:i for i,q in enumerate(self.row_labels[r+1])}
        for a,b in pairs:
            if a in locB and b in locA:a,b=b,a
            if a not in locA or b not in locB:raise GlobalSupportError(f'cross pair {a,b} not in row pair {r}')
            ia=1+locA[a];ib=1+kA+locB[b]
            arr=_apply_two_axis_gate(arr,ia,ib,gate)
        mat=arr.reshape(dl*dA,dB*dr)
        self.peak_svd_matrix_elements=max(self.peak_svd_matrix_elements,int(mat.size))
        if mat.size>max_matrix_elements:
            raise MemoryError(f'SVD matrix elements {mat.size} exceed budget {max_matrix_elements}')
        u,s,vh=_stable_svd(mat)
        threshold=float(rtol)*max(mat.shape)*float(s[0]) if s.size else 0.0
        rank=max(1,int(np.count_nonzero(s>threshold)))
        if max_bond is not None and rank>max_bond:
            raise MemoryError(f'required row bond rank {rank} exceeds max_bond={max_bond}')
        discarded=float(np.linalg.norm(s[rank:])) if rank<s.size else 0.0
        self.total_discarded_l2+=discarded
        u=u[:,:rank];s=s[:rank];vh=vh[:rank,:]
        self.tensors[r]=u.reshape(dl,dA,rank)
        self.tensors[r+1]=(s[:,None]*vh).reshape(rank,dB,dr)
        self.peak_bond=max(self.peak_bond,rank)

    def apply_layer(self,edges,gate,*,rtol,max_bond,max_matrix_elements):
        local=[[] for _ in self.tensors]
        cross={}
        for a,b in edges:
            ra,_=self.label_to_pos[a];rb,_=self.label_to_pos[b]
            if ra==rb:local[ra].append((a,b))
            else:
                if abs(ra-rb)!=1:raise GlobalSupportError(f'non-adjacent row edge {a,b}: {ra},{rb}')
                r=min(ra,rb);cross.setdefault(r,[]).append((a,b))
        for r,pairs in enumerate(local):self._apply_local_pairs(r,pairs,gate)
        # Cross row pairs in alternating order to reduce directional bias.
        for r in sorted(cross):self._apply_cross_pairs(r,cross[r],gate,rtol=rtol,max_bond=max_bond,max_matrix_elements=max_matrix_elements)

    def bond_dims(self):
        return tuple(int(t.shape[2]) for t in self.tensors[:-1])


def ibm61_rows(logical_to_physical:Sequence[int])->tuple[tuple[int,...],...]:
    groups={}
    for q,p in enumerate(logical_to_physical):groups.setdefault(int(p)//10,[]).append((int(p)%10,q))
    return tuple(tuple(q for _,q in sorted(groups[r])) for r in sorted(groups))


def evolve_row_block_mps(*,logical_to_physical,matchings:Mapping[str,Sequence[Sequence[int]]],schedule:Sequence[str],depth:int,initial_active:Iterable[int],numerical_rank_rtol=np.finfo(float).eps,max_bond=4096,max_matrix_elements=20_000_000)->RowBlockReceipt:
    rows=ibm61_rows(logical_to_physical);m=RowBlockMPS(rows,initial_active);g=support_gate_tensor();history=[];layers=0;cycles=0;aborted=False;reason=None
    try:
        for d in range(depth):
            m.apply_layer(matchings[schedule[d%len(schedule)]],g,rtol=numerical_rank_rtol,max_bond=max_bond,max_matrix_elements=max_matrix_elements)
            layers+=1;history.append(m.bond_dims())
            if (d+1)%len(schedule)==0:cycles+=1
    except (MemoryError,np.linalg.LinAlgError) as e:
        aborted=True;reason=f'{type(e).__name__}:{e}'
    return RowBlockReceipt(depth=int(depth),layers_completed=layers,cycles_completed=cycles,peak_bond=m.peak_bond,peak_svd_matrix_elements=m.peak_svd_matrix_elements,normalization=m.total_mass(),total_discarded_l2=m.total_discarded_l2,bond_history=tuple(history),aborted=aborted,abort_reason=reason,row_sizes=tuple(len(r) for r in rows),row_labels=rows)