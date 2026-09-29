import numpy as np
from row_block_support import _apply_two_axis_gate,RowBlockMPS,evolve_row_block_mps,ibm61_rows
from global_support_transfer import support_gate_tensor, exact_dense_support


def test_axis_gate_identity_shape():
    a=np.arange(16,dtype=float).reshape(2,2,2,2)
    g=np.eye(4).reshape(2,2,2,2)
    b=_apply_two_axis_gate(a,1,2,g)
    assert np.allclose(a,b)


def test_row_block_two_rows_matches_dense():
    rows=((0,1),(2,3));match={'A':((0,1),(2,3)),'B':((1,2),),'C':(),'D':()};sched='ABCD';depth=2
    dense=exact_dense_support(num_sites=4,matchings=match,schedule=sched,depth=depth,initial_active=(0,))
    m=RowBlockMPS(rows,(0,));g=support_gate_tensor()
    for d in range(depth):m.apply_layer(match[sched[d%4]],g,rtol=np.finfo(float).eps,max_bond=64,max_matrix_elements=100000)
    # Contract row-block MPS to dense row-order basis then map to little-endian logical.
    A,B=m.tensors
    x=np.einsum('lar,rbs->labs',A,B)[0,:,:,0].reshape(-1)
    remap=np.zeros_like(x)
    for idx,p in enumerate(x):
        bits=[(idx>>(3-k))&1 for k in range(4)]
        j=sum(bits[q]<<q for q in range(4));remap[j]=p
    assert np.allclose(remap,dense,atol=1e-12)
    assert abs(m.total_mass()-1)<1e-12


def test_ibm_rows_shape():
    phys=[12,13,14,15,16,18,19,22,23,24,25,26,27,28,29,32,33,34,35,36,37,38,39,42,43,44,45,46,47,48,49,52,53,54,56,57,58,59,63,64,65,66,67,68,69,72,73,74,75,76,77,78,79,82,83,84,85,86,87,88,89]
    rows=ibm61_rows(phys)
    assert tuple(map(len,rows))==(7,8,8,8,7,7,8,8)
    assert sum(map(len,rows))==61