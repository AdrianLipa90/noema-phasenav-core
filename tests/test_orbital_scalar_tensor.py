import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from orbital_scalar_tensor import (
    IncrementalBoundaryBasis,
    boundary_capacity,
    compress_boundary_states,
    fold,
    hodge_split_euclidean_4d,
    mode_product,
    operator_schmidt_decompose,
    plucker_simplicity,
    principal_angles,
    projective_orbit,
    reconstruct_operator_schmidt,
    reconstruct_tensor_train,
    schmidt_decompose,
    spectral_scalars,
    tensor_train_svd,
    unfold,
)


def test_spectral_scalars_rank_and_effective_ranks():
    a=np.diag([4.0,2.0,0.0])
    r=spectral_scalars(a)
    assert r.numerical_rank==2
    assert r.nullity==1
    assert math.isclose(r.stable_rank,1.25,rel_tol=1e-12)
    assert 1.0 < r.entropy_rank <= 2.0
    assert math.isclose(r.condition_number_nonzero,2.0,rel_tol=1e-12)



def test_spectral_scalars_rectangular_right_nullity():
    a=np.array([[1.,0.,0.],[0.,1.,0.]])
    r=spectral_scalars(a)
    assert r.numerical_rank==2
    assert r.nullity==1


def test_principal_angles_ignore_dependent_columns():
    a=np.array([[1.,2.,0.],[0.,0.,1.],[0.,0.,0.]])
    b=np.array([[1.,0.],[0.,1.],[0.,0.]])
    angles=principal_angles(a,b)
    assert len(angles)==2
    assert max(abs(x) for x in angles) < 1e-7

def test_projective_orbit_common_gauge_invariant():
    a=np.array([1,1j],dtype=complex)
    b=np.array([1,1],dtype=complex)
    r1=projective_orbit(a,b)
    phase=np.exp(0.713j)
    r2=projective_orbit(phase*a,phase*b)
    assert math.isclose(r1.fidelity,r2.fidelity,abs_tol=1e-14)
    assert math.isclose(r1.fubini_study_distance,r2.fubini_study_distance,abs_tol=1e-14)
    assert math.isclose(r1.pancharatnam_phase,r2.pancharatnam_phase,abs_tol=1e-14)


def test_plucker_simple_wedge_and_generic_failure():
    u=np.array([1.0,2.0,-1.0,0.5])
    v=np.array([0.2,-0.7,1.1,3.0])
    b=[]
    for i,j in ((0,1),(0,2),(0,3),(2,3),(3,1),(1,2)):
        b.append(u[i]*v[j]-u[j]*v[i])
    rec=plucker_simplicity(b)
    assert rec.simple
    bad=np.array(b); bad[0]+=0.3
    assert not plucker_simplicity(bad,tolerance=1e-14).simple


def test_hodge_split_reconstructs_and_self_dual_pieces():
    b=np.array([1.,2.,3.,4.,5.,6.])
    r=hodge_split_euclidean_4d(b)
    plus=np.array(r.self_dual); minus=np.array(r.anti_self_dual)
    assert np.allclose(plus+minus,b)
    star_plus=np.array([plus[3],plus[4],plus[5],plus[0],plus[1],plus[2]])
    star_minus=np.array([minus[3],minus[4],minus[5],minus[0],minus[1],minus[2]])
    assert np.allclose(star_plus,plus)
    assert np.allclose(star_minus,-minus)


def test_principal_angles_identical_subspace_zero():
    a=np.array([[1.,0.],[0.,1.],[0.,0.]])
    angles=principal_angles(a,a)
    assert max(abs(x) for x in angles) < 1e-8


def test_unfold_fold_roundtrip_and_mode_product():
    t=np.arange(24,dtype=float).reshape(2,3,4)
    for mode in range(3):
        assert np.allclose(fold(unfold(t,mode),t.shape,mode),t)
    m=np.eye(3)*2
    out=mode_product(t,m,1)
    assert np.allclose(out,2*t)


def test_schmidt_product_and_bell():
    prod=np.array([1,0,0,0],dtype=complex)
    _,_,_,rp=schmidt_decompose(prod,(2,2),1)
    assert rp.numerical_rank==1
    bell=np.array([1,0,0,1],dtype=complex)/math.sqrt(2)
    u,s,vh,rb=schmidt_decompose(bell,(2,2),1)
    assert rb.numerical_rank==2
    assert np.allclose(s,[1/math.sqrt(2)]*2)
    assert rb.exact_within_numerical_rank


def test_operator_schmidt_cz_rank2_and_reconstruction():
    cz=np.diag([1,1,1,-1]).astype(complex)
    a,s,b,r=operator_schmidt_decompose(cz)
    rec=reconstruct_operator_schmidt(a,s,b)
    assert r.numerical_rank==2
    assert np.allclose(rec,cz,atol=1e-12)


def test_operator_schmidt_swap_rank4():
    swap=np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]],dtype=complex)
    *_,r=operator_schmidt_decompose(swap)
    assert r.numerical_rank==4


def test_tensor_train_exact_reconstruction():
    rng=np.random.default_rng(123)
    t=rng.normal(size=(2,3,2,2))+1j*rng.normal(size=(2,3,2,2))
    cores,r=tensor_train_svd(t)
    rec=reconstruct_tensor_train(cores)
    assert r.exact_within_numerical_rank
    assert np.allclose(rec,t,atol=1e-12)


def test_boundary_compression_linear_dependence_not_duplicates():
    rng=np.random.default_rng(7)
    left=rng.normal(size=(40,7))+1j*rng.normal(size=(40,7))
    coeff=rng.normal(size=(7,100))+1j*rng.normal(size=(7,100))
    x=left@coeff
    basis,c,receipt=compress_boundary_states(x,rtol=1e-12)
    assert receipt.numerical_rank==7
    assert np.linalg.norm(x-basis@c) < 1e-9
    assert receipt.branch_count==100


def test_boundary_capacity_100q_center_cut():
    r=boundary_capacity([2]*90,left_dimension=2**50,right_dimension=2**50)
    assert r.raw_log2_branches==90.0
    assert r.rank_cap_log2==50.0
    assert r.effective_log2_upper_bound==50.0


def test_incremental_boundary_basis_detects_dependence():
    b=IncrementalBoundaryBasis(4,rtol=1e-12)
    assert b.add([1,0,0,0])["accepted"]
    assert b.add([0,1,0,0])["accepted"]
    dep=b.add([2,3,0,0])
    assert not dep["accepted"]
    assert b.rank==2