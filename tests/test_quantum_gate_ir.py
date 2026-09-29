import math

import numpy as np
import pytest

from ciel_geometry.phasenav.quantum_gate_ir import (
    Circuit,
    Gate,
    Observable,
    QuantumGateIRError,
    lower_plan_to_q28,
    plan_result_directed,
)


def _apply_h(state, q, n):
    out = state.copy()
    step = 1 << q
    inv = 1.0 / math.sqrt(2.0)
    for base in range(0, len(state), step * 2):
        for off in range(step):
            i, j = base + off, base + off + step
            a, b = state[i], state[j]
            out[i] = (a + b) * inv
            out[j] = (a - b) * inv
    return out


def _apply_cnot(state, c, t, n):
    out = np.zeros_like(state)
    for i, amp in enumerate(state):
        j = i ^ (1 << t) if ((i >> c) & 1) else i
        out[j] += amp
    return out


def _apply_cz(state, c, t):
    out = state.copy()
    for i in range(len(state)):
        if ((i >> c) & 1) and ((i >> t) & 1):
            out[i] *= -1
    return out


def test_googol_logical_extent_reduces_to_eight_qubit_cone():
    n = 10**100
    gates = [Gate("H", (0,))]
    gates += [Gate("CZ", (i, i + 1)) for i in range(7)]
    gates += [Gate("H", (n - 1,))]  # provably irrelevant to Z(q7)
    circuit = Circuit(
        logical_qubits=n,
        gates=tuple(gates),
        observable=Observable("Z", (7,)),
    )
    plan = plan_result_directed(circuit)
    assert plan.active_logical_qubits == tuple(range(8))
    assert plan.workspace_qubits == 8
    assert all((n - 1) not in g.qubits for g in plan.logical_gates)

    receipt = lower_plan_to_q28(plan)
    assert receipt.workspace_qubits == 8
    assert receipt.address_qubits == 6
    assert receipt.total_materialized_qubits == 14
    assert len(receipt.native_gates) == 1 + 7 * 3


def test_cz_lowering_is_exact_up_to_numerical_precision():
    rng = np.random.default_rng(20260925)
    state = rng.normal(size=4) + 1j * rng.normal(size=4)
    state = state / np.linalg.norm(state)

    direct = _apply_cz(state, 0, 1)
    lowered = _apply_h(state, 1, 2)
    lowered = _apply_cnot(lowered, 0, 1, 2)
    lowered = _apply_h(lowered, 1, 2)

    assert np.max(np.abs(direct - lowered)) < 1e-12


def test_backward_cone_expands_only_when_dependency_touches_support():
    circuit = Circuit(
        logical_qubits=50,
        gates=(
            Gate("H", (20,)),
            Gate("CNOT", (20, 21)),
            Gate("H", (0,)),
            Gate("CNOT", (0, 1)),
            Gate("CNOT", (1, 2)),
        ),
        observable=Observable("Z", (2,)),
    )
    plan = plan_result_directed(circuit)
    assert plan.active_logical_qubits == (0, 1, 2)
    assert [g.op for g in plan.logical_gates] == ["H", "CNOT", "CNOT"]


def test_workspace_budget_fails_closed():
    gates = tuple(Gate("CNOT", (i, i + 1)) for i in range(22))
    circuit = Circuit(
        logical_qubits=23,
        gates=gates,
        observable=Observable("Z", (22,)),
    )
    plan = plan_result_directed(circuit)
    assert plan.workspace_qubits == 23
    with pytest.raises(QuantumGateIRError):
        lower_plan_to_q28(plan)


def test_hash_is_deterministic_and_sensitive_to_observable():
    gates = (Gate("H", (0,)), Gate("CZ", (0, 1)))
    a = Circuit(2, gates, Observable("Z", (0,)))
    b = Circuit(2, gates, Observable("Z", (0,)))
    c = Circuit(2, gates, Observable("Z", (1,)))
    assert a.sha256 == b.sha256
    assert a.sha256 != c.sha256
