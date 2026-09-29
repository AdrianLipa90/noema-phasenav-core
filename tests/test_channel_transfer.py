import math
import numpy as np
import pytest

from channel_transfer import (
    normalize_state,
    density_matrix,
    partial_trace,
    entropy_receipt,
    mutual_information,
    apply_channel,
    choi_from_kraus,
    kraus_from_choi,
    superoperator_from_kraus,
    channel_receipt,
    pauli_transfer_matrix,
    ptm_receipt,
    pauli_second_moment_transition,
    haar_local_cz_support_transition,
    transfer_spectrum,
    channel_fixed_point,
    woodbury_inverse_update,
    lanczos_hermitian,
    ChannelPrimitiveError,
)


I=np.eye(2,dtype=complex)
X=np.array([[0,1],[1,0]],complex)
Y=np.array([[0,-1j],[1j,0]],complex)
Z=np.array([[1,0],[0,-1]],complex)
H=np.array([[1,1],[1,-1]],complex)/math.sqrt(2)
CZ=np.diag([1,1,1,-1]).astype(complex)


def amplitude_damping(gamma):
    g=float(gamma)
    return (
        np.array([[1,0],[0,math.sqrt(1-g)]],complex),
        np.array([[0,math.sqrt(g)],[0,0]],complex),
    )


def test_normalize_state():
    psi=normalize_state([3,4])
    assert abs(np.linalg.norm(psi)-1)<1e-14


def test_bell_partial_trace_maximally_mixed():
    psi=np.array([1,0,0,1],complex)/math.sqrt(2)
    rho=density_matrix(psi)
    ra=partial_trace(rho,(2,2),(0,))
    assert np.allclose(ra,np.eye(2)/2,atol=1e-12)


def test_bell_entropy_one_bit():
    psi=np.array([1,0,0,1],complex)/math.sqrt(2)
    ra=partial_trace(density_matrix(psi),(2,2),(0,))
    rec=entropy_receipt(ra)
    assert abs(rec.von_neumann_bits-1)<1e-12
    assert abs(rec.purity-0.5)<1e-12


def test_pure_entropy_zero():
    rec=entropy_receipt(density_matrix([1,0]))
    assert abs(rec.von_neumann_bits)<1e-12
    assert abs(rec.purity-1)<1e-12


def test_bell_mutual_information_two_bits():
    psi=np.array([1,0,0,1],complex)/math.sqrt(2)
    rec=mutual_information(density_matrix(psi),(2,2),(0,),(1,))
    assert abs(rec.mutual_information_bits-2)<1e-12


def test_identity_channel():
    rho=density_matrix([1,1j])
    out=apply_channel(rho,(I,))
    assert np.allclose(out,rho)


def test_identity_choi_rank_one():
    j=choi_from_kraus((I,))
    vals=np.linalg.eigvalsh(j)
    assert np.count_nonzero(vals>1e-12)==1
    assert abs(vals[-1]-2)<1e-12


def test_kraus_roundtrip_identity_choi():
    j=choi_from_kraus((I,))
    ks=kraus_from_choi(j,2,2)
    j2=choi_from_kraus(ks)
    assert np.allclose(j2,j,atol=1e-10)


def test_amplitude_damping_channel_receipt_tp_not_unital():
    rec=channel_receipt(amplitude_damping(0.3))
    assert rec.cp_residual < 1e-12
    assert rec.tp_residual < 1e-12
    assert rec.unital_residual > 0.1
    assert rec.kraus_rank==2


def test_amplitude_damping_choi_kraus_roundtrip():
    ks=amplitude_damping(0.2)
    j=choi_from_kraus(ks)
    ks2=kraus_from_choi(j,2,2)
    j2=choi_from_kraus(ks2)
    assert np.allclose(j2,j,atol=1e-10)


def test_superoperator_identity():
    s=superoperator_from_kraus((I,))
    assert np.allclose(s,np.eye(4))


def test_hadamard_ptm_signed_permutation():
    r=pauli_transfer_matrix((H,))
    rec=ptm_receipt(r)
    assert rec.signed_permutation
    assert rec.nonzero_count==4


def test_generic_rotation_ptm_not_signed_permutation():
    theta=0.37
    rz=np.diag([np.exp(-0.5j*theta),np.exp(0.5j*theta)])
    r=pauli_transfer_matrix((rz,))
    assert not ptm_receipt(r).signed_permutation


def test_unitary_second_moment_columns_sum_one():
    r=pauli_transfer_matrix((H,))
    t=pauli_second_moment_transition(r)
    assert np.allclose(t.sum(axis=0),1.0,atol=1e-12)


def test_cz_ptm_signed_permutation():
    r=pauli_transfer_matrix((CZ,),max_qubits=2)
    assert ptm_receipt(r).signed_permutation


def test_haar_cz_support_transition_exact_entries():
    t=haar_local_cz_support_transition()
    assert np.allclose(t.sum(axis=0),1.0)
    assert np.allclose(t[:,1],[0,1/3,0,2/3])
    assert np.allclose(t[:,3],[0,2/9,2/9,5/9])


def test_transfer_spectrum_simple():
    a=np.diag([1.0,0.75,0.2])
    rec=transfer_spectrum(a)
    assert abs(rec.spectral_radius-1)<1e-12
    assert abs(rec.subleading_magnitude-0.75)<1e-12
    assert abs(rec.gap-0.25)<1e-12


def test_depolarizing_like_fixed_point_identity():
    p=0.2
    ks=(
        math.sqrt(1-3*p/4)*I,
        math.sqrt(p/4)*X,
        math.sqrt(p/4)*Y,
        math.sqrt(p/4)*Z,
    )
    rec=channel_fixed_point(ks)
    assert rec.residual < 1e-10
    assert np.allclose(rec.density,np.eye(2)/2,atol=1e-8)


def test_amplitude_damping_fixed_point_ground_state():
    rec=channel_fixed_point(amplitude_damping(0.3))
    assert rec.residual < 1e-10
    assert np.allclose(rec.density,np.array([[1,0],[0,0]],complex),atol=1e-8)


def test_woodbury_matches_direct_inverse():
    a=np.array([[4.,1.],[1.,3.]],complex)
    ai=np.linalg.inv(a)
    u=np.array([[1.],[2.]],complex)
    c=np.array([[0.2]],complex)
    v=np.array([[1.,-1.]],complex)
    rec=woodbury_inverse_update(ai,u,c,v)
    direct=np.linalg.inv(a+u@c@v)
    assert np.allclose(rec.inverse,direct,atol=1e-12)
    assert rec.inverse_residual < 1e-12


def test_lanczos_orthogonality():
    a=np.diag([1.,2.,3.,4.])
    rec=lanczos_hermitian(a,[1,1,1,1],4)
    assert rec.orthogonality_residual < 1e-10
    ev=np.linalg.eigvalsh(rec.tridiagonal)
    assert np.allclose(np.sort(ev),[1,2,3,4],atol=1e-10)


def test_partial_trace_dimension_error():
    with pytest.raises(ChannelPrimitiveError):
        partial_trace(np.eye(4)/4,(2,3),(0,))


def test_invalid_density_rejected():
    with pytest.raises(ChannelPrimitiveError):
        entropy_receipt(np.array([[1,1],[0,0]],complex))


def test_non_tp_channel_detected():
    rec=channel_receipt((0.5*I,))
    assert rec.tp_residual > 0.5