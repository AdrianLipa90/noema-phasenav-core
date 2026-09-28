import math
import numpy as np
import pytest

from mixed_representation import (
    QuadraticPhasePolynomial,
    AbelianChargeRule,
    BlockSparseTensor,
    clifford_unitary,
    matchgate_unitary,
    polar_decompose,
    schur_complement,
    AtomFeatures,
    route_atom,
    TensorNode,
    TensorNetworkSpec,
    greedy_contraction_plan,
    slice_to_memory_budget,
    min_fill_graph_width,
    min_degree_graph_width,
    content_digest,
    plan_disk_shards,
    MixedRepresentationError,
)


def cz():
    return np.diag([1, 1, 1, -1]).astype(complex)


def cnot():
    return np.array([
        [1,0,0,0],
        [0,1,0,0],
        [0,0,0,1],
        [0,0,1,0],
    ], dtype=complex)


def h():
    return np.array([[1,1],[1,-1]], dtype=complex) / math.sqrt(2)


def rz(theta):
    return np.diag([np.exp(-0.5j*theta), np.exp(0.5j*theta)])


def fswap():
    return np.array([
        [1,0,0,0],
        [0,0,1,0],
        [0,1,0,0],
        [0,0,0,-1],
    ], dtype=complex)


def test_phase_polynomial_cz_truth_table():
    p = QuadraticPhasePolynomial.from_cz_edges(2, [(0,1)])
    vals = [p.amplitude(bits) for bits in [(0,0),(0,1),(1,0),(1,1)]]
    assert np.allclose(vals, [1,1,1,-1], atol=1e-12)


def test_phase_polynomial_rz_exact():
    theta = 0.731
    p = QuadraticPhasePolynomial.identity(1).with_rz(0, theta)
    got = np.array([p.amplitude((0,)), p.amplitude((1,))])
    assert np.allclose(got, np.diag(rz(theta)), atol=1e-12)


def test_phase_polynomial_restrict():
    p = QuadraticPhasePolynomial.from_cz_edges(3, [(0,1),(1,2)]).with_rz(2, 0.2)
    q = p.restrict({1:1})
    for x0 in (0,1):
        for x2 in (0,1):
            assert abs(p.amplitude((x0,1,x2)) - q.amplitude((x0,x2))) < 1e-12


def test_block_sparse_z2_roundtrip():
    # 2x2 matrix preserving Z2 charge equality: only |0><0| and |1><1|.
    dense = np.diag([2+0j, 3+0j])
    rule = AbelianChargeRule(modulus=2, target=0)
    bs = BlockSparseTensor.from_dense(dense, ((0,1),(0,1)), rule)
    assert np.allclose(bs.to_dense(), dense)
    assert bs.storage_fraction == 0.5


def test_block_sparse_fail_closed_on_forbidden_weight():
    dense = np.array([[1, 0.1],[0,1]], dtype=complex)
    rule = AbelianChargeRule(modulus=2, target=0)
    with pytest.raises(MixedRepresentationError):
        BlockSparseTensor.from_dense(dense, ((0,1),(0,1)), rule, zero_atol=0.0)


def test_cz_and_cnot_are_clifford():
    assert clifford_unitary(cz()).is_clifford
    assert clifford_unitary(cnot()).is_clifford


def test_h_and_generic_rz_classifier():
    assert clifford_unitary(h()).is_clifford
    assert not clifford_unitary(rz(0.317)).is_clifford


def test_fswap_is_matchgate_cz_is_not():
    assert matchgate_unitary(fswap()).is_matchgate
    assert not matchgate_unitary(cz()).is_matchgate


def test_polar_reconstructs():
    a = np.array([[1+1j, 2-0.2j],[0.5j, 3]], dtype=complex)
    rec = polar_decompose(a)
    assert rec.reconstruction_residual < 1e-12
    assert rec.unitarity_residual < 1e-12


def test_schur_complement_known_control():
    m = np.array([[4., 1.],[2., 3.]])
    rec = schur_complement(m, [0])
    assert rec.complement.shape == (1,1)
    assert abs(rec.complement[0,0] - (4 - 1*2/3)) < 1e-12


def test_schur_fails_on_singular_eliminated_block():
    m = np.array([[1., 2.],[3., 0.]])
    with pytest.raises(MixedRepresentationError):
        schur_complement(m, [0])


def test_router_prefers_clifford():
    r = route_atom(AtomFeatures(50, 1000, clifford_only=True))
    assert r.primary == "STABILIZER"


def test_router_prefers_phase_polynomial():
    r = route_atom(AtomFeatures(100, 500, diagonal_quadratic_phase=True))
    assert r.primary == "QUADRATIC_PHASE_POLYNOMIAL"




def test_router_prefers_specialized_phase_over_clifford():
    r = route_atom(AtomFeatures(
        61, 29, clifford_only=True, diagonal_quadratic_phase=True
    ))
    assert r.primary == "QUADRATIC_PHASE_POLYNOMIAL"


def test_router_mps_and_symmetry_overlay():
    r = route_atom(AtomFeatures(
        60, 1000,
        one_dimensional_locality=True,
        max_schmidt_rank=64,
        symmetry_storage_fraction=0.2,
    ), mps_rank_limit=128)
    assert r.primary == "MPS_TT"
    assert "BLOCK_SPARSE_SYMMETRY" in r.overlays


def chain_spec(length=5, dim=2):
    # T0(a0,a1), T1(a1,a2), ...; open ends a0, aL.
    nodes = []
    dims = []
    for i in range(length + 1):
        dims.append((f"i{i}", dim))
    for i in range(length):
        nodes.append(TensorNode(f"T{i}", (f"i{i}", f"i{i+1}")))
    return TensorNetworkSpec(tuple(nodes), tuple(dims))


def test_greedy_chain_width_small():
    plan = greedy_contraction_plan(chain_spec(6))
    assert plan.peak_elements <= 4
    assert plan.outer_products == 0
    assert plan.final_indices == ("i0","i6")


def test_slice_memory_budget():
    # Square-ish network where slicing one internal dimension can reduce peak.
    spec = TensorNetworkSpec(
        nodes=(
            TensorNode("A", ("x","a","b")),
            TensorNode("B", ("x","c","d")),
            TensorNode("C", ("a","c")),
            TensorNode("D", ("b","d")),
        ),
        index_dims=(("x",8),("a",4),("b",4),("c",4),("d",4)),
    )
    raw = greedy_contraction_plan(spec)
    sliced = slice_to_memory_budget(spec, raw.peak_bytes // 2)
    assert sliced.slice_count >= 1
    assert sliced.per_slice_peak_bytes <= raw.peak_bytes
    assert sliced.total_flop_estimate >= sliced.per_slice_flop_estimate


def test_min_fill_cycle_width_two():
    adj = {
        "a":{"b","d"},
        "b":{"a","c"},
        "c":{"b","d"},
        "d":{"a","c"},
    }
    rec = min_fill_graph_width(adj)
    assert rec.induced_width == 2
    assert len(rec.elimination_order) == 4




def test_min_degree_cycle_width_two():
    adj = {
        "a":{"b","d"},
        "b":{"a","c"},
        "c":{"b","d"},
        "d":{"a","c"},
    }
    rec = min_degree_graph_width(adj)
    assert rec.induced_width == 2
    assert len(rec.elimination_order) == 4


def test_content_digest_deterministic():
    assert content_digest({"b":2,"a":1}) == content_digest({"a":1,"b":2})
    arr = np.arange(8, dtype=np.float64)
    assert content_digest(arr) == content_digest(arr.copy())


def test_disk_shard_plan_respects_ram_count():
    spec = chain_spec(5)
    raw = greedy_contraction_plan(spec)
    sp = slice_to_memory_budget(spec, raw.peak_bytes)
    dp = plan_disk_shards(sp, bytes_per_shard=1024, ram_budget_bytes=4096)
    assert dp.max_in_memory_shards == 4


def test_routing_thresholds_are_receipted():
    r = route_atom(AtomFeatures(30,10), dense_qubit_limit=20)
    d = dict(r.thresholds)
    assert d["dense_qubit_limit"] == 20.0
    assert r.primary == "TENSOR_NETWORK"


def test_generic_haar_1q_not_clifford():
    # Deterministic generic SU(2)
    theta, phi, lam = 0.71, 0.29, -0.43
    ry = np.array([[math.cos(theta/2), -math.sin(theta/2)],
                   [math.sin(theta/2), math.cos(theta/2)]], complex)
    rz1 = rz(phi)
    rz2 = rz(lam)
    u = rz1 @ ry @ rz2
    assert not clifford_unitary(u).is_clifford