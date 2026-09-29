from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

SCHEMA = "phasenav.adaptive-separator-tree/v0.19"
EPISTEMIC = "CANDIDATE_ONLY"
CANON_ALLOWED = False


class SeparatorError(ValueError):
    pass


def _edge(u:int,v:int)->tuple[int,int]:
    u=int(u);v=int(v)
    if u==v: raise SeparatorError("self edges are not allowed")
    return (u,v) if u<v else (v,u)


def canonical_edges(edges: Iterable[Sequence[int]]) -> tuple[tuple[int,int],...]:
    out=sorted({_edge(int(e[0]),int(e[1])) for e in edges})
    return tuple(out)


def schedule_occurrences(schedule: Sequence[str], depth:int)->dict[str,int]:
    if depth<0: raise SeparatorError("depth must be >= 0")
    schedule=tuple(str(x) for x in schedule)
    if not schedule: raise SeparatorError("schedule must be non-empty")
    counts={x:0 for x in schedule}
    for d in range(int(depth)):
        counts[schedule[d%len(schedule)]] += 1
    return counts


def dynamic_edge_weights(
    matchings: Mapping[str, Sequence[Sequence[int]]],
    schedule: Sequence[str],
    depth:int,
    *,
    operator_schmidt_rank: int | Mapping[tuple[int,int],int]=2,
)->dict[tuple[int,int],float]:
    """Return dynamic cut weights in log2 Schmidt-capacity units.

    Each use of an edge contributes log2(operator-Schmidt-rank). This is a
    structural upper-capacity accounting primitive, not actual Schmidt rank.
    """
    counts=schedule_occurrences(schedule,depth)
    owner={}
    for layer,es in matchings.items():
        if layer not in counts: continue
        for u,v in es:
            e=_edge(u,v)
            if e in owner and owner[e]!=layer:
                raise SeparatorError(f"edge {e} occurs in multiple matching labels")
            owner[e]=layer
    weights={}
    for e,layer in owner.items():
        if isinstance(operator_schmidt_rank,Mapping):
            r=int(operator_schmidt_rank[e])
        else:
            r=int(operator_schmidt_rank)
        if r<1: raise SeparatorError("operator Schmidt rank must be >= 1")
        weights[e]=float(counts[layer])*math.log2(r)
    return weights


@dataclass(frozen=True)
class FixedSizeCutReceipt:
    vertices: tuple[int,...]
    target_size: int
    complement_size: int
    left: tuple[int,...]
    right: tuple[int,...]
    cut_edges: tuple[tuple[int,int],...]
    edge_cut_count: int
    objective_weight: float
    imbalance: int
    solver_success: bool
    solver_message: str
    solver_optimal: bool
    time_limit_s: float | None


def minimum_fixed_size_cut(
    vertices: Iterable[int],
    edges: Iterable[Sequence[int]],
    target_size:int,
    *,
    edge_weights: Mapping[tuple[int,int],float] | None=None,
    time_limit_s: float | None=30.0,
)->FixedSizeCutReceipt:
    """Exact fixed-cardinality minimum cut via SciPy/HiGHS MILP.

    Binary x_v selects the target side. Continuous y_e is forced to |x_u-x_v|
    at optimum by the positive edge objective. No fitted coefficient is used.
    """
    from scipy.optimize import milp, LinearConstraint, Bounds

    verts=tuple(sorted(set(map(int,vertices))))
    if not verts: raise SeparatorError("vertices must be non-empty")
    index={v:i for i,v in enumerate(verts)}
    es=[]
    for raw in edges:
        e=_edge(raw[0],raw[1])
        if e[0] in index and e[1] in index: es.append(e)
    es=tuple(sorted(set(es)))
    n=len(verts);m=len(es);k=int(target_size)
    if not (1<=k<=n-1): raise SeparatorError("target_size must be between 1 and n-1")
    if k>n//2:
        raise SeparatorError("target_size should be the smaller/equal side (<= n//2)")

    weights=[]
    for e in es:
        w=1.0 if edge_weights is None else float(edge_weights.get(e,0.0))
        if not math.isfinite(w) or w<0: raise SeparatorError("edge weights must be finite and nonnegative")
        weights.append(w)
    N=n+m
    c=np.r_[np.zeros(n,dtype=float),np.asarray(weights,dtype=float)]
    rows=[];lower=[];upper=[]
    for ei,(u,v) in enumerate(es):
        iu=index[u];iv=index[v]
        # xu - xv - y <= 0
        row=np.zeros(N);row[iu]=1;row[iv]=-1;row[n+ei]=-1
        rows.append(row);lower.append(-np.inf);upper.append(0.0)
        # xv - xu - y <= 0
        row=np.zeros(N);row[iv]=1;row[iu]=-1;row[n+ei]=-1
        rows.append(row);lower.append(-np.inf);upper.append(0.0)
    row=np.zeros(N);row[:n]=1
    rows.append(row);lower.append(float(k));upper.append(float(k))
    A=np.vstack(rows)
    integrality=np.r_[np.ones(n,dtype=int),np.zeros(m,dtype=int)]
    options={}
    if time_limit_s is not None:
        if time_limit_s<=0 or not math.isfinite(float(time_limit_s)): raise SeparatorError("time_limit_s must be > 0")
        options['time_limit']=float(time_limit_s)
    res=milp(
        c,
        integrality=integrality,
        bounds=Bounds(np.zeros(N),np.ones(N)),
        constraints=LinearConstraint(A,np.asarray(lower),np.asarray(upper)),
        options=options,
    )
    if res.x is None:
        raise SeparatorError(f"MILP returned no solution: {res.message}")
    x=np.rint(res.x[:n]).astype(int)
    left=tuple(v for v in verts if x[index[v]]==1)
    right=tuple(v for v in verts if x[index[v]]==0)
    cut=tuple(e for e in es if x[index[e[0]]]!=x[index[e[1]]])
    obj=sum((1.0 if edge_weights is None else float(edge_weights.get(e,0.0))) for e in cut)
    # HiGHS reports status 0 for optimal in scipy OptimizeResult.
    optimal=bool(getattr(res,'status',None)==0 and bool(res.success))
    return FixedSizeCutReceipt(
        vertices=verts,target_size=k,complement_size=n-k,left=left,right=right,
        cut_edges=cut,edge_cut_count=len(cut),objective_weight=float(obj),
        imbalance=abs((n-k)-k),solver_success=bool(res.success),solver_message=str(res.message),
        solver_optimal=optimal,time_limit_s=None if time_limit_s is None else float(time_limit_s),
    )


@dataclass(frozen=True)
class ParetoCutReceipt:
    candidates: tuple[FixedSizeCutReceipt,...]
    pareto_indices: tuple[int,...]

    @property
    def pareto(self)->tuple[FixedSizeCutReceipt,...]:
        return tuple(self.candidates[i] for i in self.pareto_indices)


def pareto_fixed_size_cuts(
    vertices:Iterable[int],edges:Iterable[Sequence[int]],target_sizes:Iterable[int],*,edge_weights=None,time_limit_s:float|None=30.0
)->ParetoCutReceipt:
    receipts=tuple(minimum_fixed_size_cut(vertices,edges,k,edge_weights=edge_weights,time_limit_s=time_limit_s) for k in sorted(set(map(int,target_sizes))))
    keep=[]
    for i,a in enumerate(receipts):
        dominated=False
        for j,b in enumerate(receipts):
            if i==j: continue
            if (b.objective_weight<=a.objective_weight+1e-12 and b.imbalance<=a.imbalance and
                (b.objective_weight<a.objective_weight-1e-12 or b.imbalance<a.imbalance)):
                dominated=True;break
        if not dominated: keep.append(i)
    return ParetoCutReceipt(receipts,tuple(keep))


@dataclass(frozen=True)
class SeparatorTreeNode:
    vertices: tuple[int,...]
    depth: int
    cut: FixedSizeCutReceipt | None
    left: "SeparatorTreeNode | None"
    right: "SeparatorTreeNode | None"

    @property
    def is_leaf(self)->bool: return self.cut is None


def build_balanced_separator_tree(
    vertices:Iterable[int],edges:Iterable[Sequence[int]],*,leaf_max:int,edge_weights=None,time_limit_s:float|None=30.0,root_cut:FixedSizeCutReceipt|None=None,_depth:int=0
)->SeparatorTreeNode:
    verts=tuple(sorted(set(map(int,vertices))))
    leaf_max=int(leaf_max)
    if leaf_max<=0: raise SeparatorError("leaf_max must be positive")
    es=canonical_edges(edges)
    if len(verts)<=leaf_max:
        return SeparatorTreeNode(verts,_depth,None,None,None)
    if root_cut is None:
        k=len(verts)//2
        cut=minimum_fixed_size_cut(verts,es,k,edge_weights=edge_weights,time_limit_s=time_limit_s)
    else:
        if set(root_cut.vertices)!=set(verts): raise SeparatorError("root_cut vertex set mismatch")
        cut=root_cut
    leftset=set(cut.left);rightset=set(cut.right)
    left_edges=[e for e in es if e[0] in leftset and e[1] in leftset]
    right_edges=[e for e in es if e[0] in rightset and e[1] in rightset]
    left=build_balanced_separator_tree(cut.left,left_edges,leaf_max=leaf_max,edge_weights=edge_weights,time_limit_s=time_limit_s,_depth=_depth+1)
    right=build_balanced_separator_tree(cut.right,right_edges,leaf_max=leaf_max,edge_weights=edge_weights,time_limit_s=time_limit_s,_depth=_depth+1)
    return SeparatorTreeNode(verts,_depth,cut,left,right)


@dataclass(frozen=True)
class SeparatorTreeSummary:
    vertex_count:int
    leaf_count:int
    max_leaf_size:int
    max_depth:int
    max_edge_cut_count:int
    max_cut_weight:float
    sum_edge_cut_count:int
    sum_cut_weight:float
    leaves:tuple[tuple[int,...],...]


def summarize_separator_tree(root:SeparatorTreeNode)->SeparatorTreeSummary:
    leaves=[];cuts=[]
    stack=[root]
    maxdepth=0
    while stack:
        node=stack.pop();maxdepth=max(maxdepth,node.depth)
        if node.is_leaf:leaves.append(node.vertices)
        else:
            cuts.append(node.cut);stack.extend([node.left,node.right])
    return SeparatorTreeSummary(
        vertex_count=len(root.vertices),leaf_count=len(leaves),max_leaf_size=max(map(len,leaves)),max_depth=maxdepth,
        max_edge_cut_count=max([0]+[c.edge_cut_count for c in cuts]),
        max_cut_weight=max([0.0]+[c.objective_weight for c in cuts]),
        sum_edge_cut_count=sum(c.edge_cut_count for c in cuts),
        sum_cut_weight=float(sum(c.objective_weight for c in cuts)),
        leaves=tuple(sorted((tuple(sorted(x)) for x in leaves),key=lambda x:(len(x),x))),
    )


__all__=[
    "SCHEMA","EPISTEMIC","CANON_ALLOWED","SeparatorError","canonical_edges","schedule_occurrences","dynamic_edge_weights",
    "FixedSizeCutReceipt","minimum_fixed_size_cut","ParetoCutReceipt","pareto_fixed_size_cuts","SeparatorTreeNode",
    "build_balanced_separator_tree","SeparatorTreeSummary","summarize_separator_tree",
]