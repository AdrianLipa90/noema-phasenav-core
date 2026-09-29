import numpy as np
from global_support_transfer import (
    HAAR_CZ_SUPPORT_TRANSFER,support_transfer_standard_basis,SupportMPS,
    exact_dense_support,evolve_support_mps,sample_support_trajectories,
    reverse_cuthill_mckee_order,
)


def small_matchings():
    return {"A":((0,1),(2,3)),"B":((1,2),),"C":((0,2),(1,3)),"D":((0,3),)}


def test_local_transfer_column_stochastic():
    assert np.allclose(HAAR_CZ_SUPPORT_TRANSFER.sum(axis=0),1.0)


def test_standard_basis_reorder_preserves_spectrum():
    a=np.sort_complex(np.linalg.eigvals(HAAR_CZ_SUPPORT_TRANSFER))
    b=np.sort_complex(np.linalg.eigvals(support_transfer_standard_basis()))
    assert np.allclose(a,b)


def test_exact_dense_mass():
    v=exact_dense_support(num_sites=4,matchings=small_matchings(),schedule="ABCD",depth=4,initial_active=(0,))
    assert abs(v.sum()-1.0)<1e-12


def test_mps_matches_dense_control():
    match=small_matchings(); schedule="ABCD"; depth=4
    dense=exact_dense_support(num_sites=4,matchings=match,schedule=schedule,depth=depth,initial_active=(0,))
    order=reverse_cuthill_mckee_order(4,match)
    mps=SupportMPS.product_state(4,(0,),order=order)
    g=__import__('global_support_transfer').support_gate_tensor()
    step=0
    for d in range(depth):
        for a,b in match[schedule[d%4]]:
            mps.apply_pair(a,b,g,rtol=np.finfo(float).eps,max_bond=None,step=step);step+=1
    got=mps.to_dense(max_sites=10)
    # MPS dense is in current variable order, so remap to logical integer order.
    remapped=np.zeros_like(got)
    for pos_index,p in enumerate(got):
        bits=[(pos_index>>(3-k))&1 for k in range(4)]  # MPS flatten big-endian position bits
        logical=[0]*4
        for k,label in enumerate(mps.order): logical[label]=bits[k]
        j=sum(logical[q]<<q for q in range(4))
        remapped[j]=p
    assert np.allclose(remapped,dense,atol=1e-12)
    assert abs(mps.total_mass()-1.0)<1e-12


def test_evolve_receipt_normalized():
    r=evolve_support_mps(num_sites=4,matchings=small_matchings(),schedule="ABCD",depth=4,initial_active=(0,),max_bond=64)
    assert not r.aborted
    assert abs(r.normalization-1.0)<1e-12
    assert r.pair_updates==6


def test_mc_agrees_with_exact_weight_mean():
    match=small_matchings();schedule="ABCD";depth=4
    v=exact_dense_support(num_sites=4,matchings=match,schedule=schedule,depth=depth,initial_active=(0,))
    exact=0.0
    for j,p in enumerate(v): exact += p*int(j).bit_count()
    mc=sample_support_trajectories(num_sites=4,matchings=match,schedule=schedule,depth=depth,initial_active=(0,),samples=50000,seed=123)
    assert abs(mc.final_mean_weight-exact) < 5*mc.stderr_weight_by_layer[-1] + 0.01