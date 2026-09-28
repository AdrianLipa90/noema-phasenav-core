"""Result-directed quantum gate IR for PhaseNav.

Candidate-only execution contract:
- backend-neutral logical circuit representation;
- exact backward causal-cone selection before hydration;
- compact logical->workspace remapping;
- deterministic lowering to the current Q28 native gate set.

This module does not claim physical-QPU execution or quantum advantage.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable

QIR_SCHEMA = "PHASENAV_QUANTUM_GATE_IR_V1"
PLAN_SCHEMA = "PHASENAV_RESULT_DIRECTED_PLAN_V1"
Q28_LOWERING_SCHEMA = "PHASENAV_Q28_LOWERING_V1"
Q28_ADDRESS_QUBITS = 6
Q28_WORKSPACE_QUBITS = 22

_GATE_ARITY = {
    "H": 1,
    "X": 1,
    "RZ": 1,
    "PHASE": 1,
    "CNOT": 2,
    "CZ": 2,
}
_ANGLED_GATES = {"RZ", "PHASE"}
_Q28_NATIVE = {"H", "X", "RZ", "PHASE", "CNOT"}


class QuantumGateIRError(ValueError):
    pass


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _require_qubit(q: int) -> int:
    if isinstance(q, bool) or not isinstance(q, int) or q < 0:
        raise QuantumGateIRError("qubit index must be a non-negative integer")
    return q


@dataclass(frozen=True)
class Gate:
    op: str
    qubits: tuple[int, ...]
    angle: float | None = None

    def __post_init__(self) -> None:
        op = str(self.op).upper()
        object.__setattr__(self, "op", op)
        if op not in _GATE_ARITY:
            raise QuantumGateIRError(f"unsupported gate: {op}")
        qs = tuple(_require_qubit(q) for q in self.qubits)
        if len(qs) != _GATE_ARITY[op]:
            raise QuantumGateIRError(f"{op} requires {_GATE_ARITY[op]} qubit(s)")
        if len(set(qs)) != len(qs):
            raise QuantumGateIRError("a gate cannot reference the same qubit twice")
        object.__setattr__(self, "qubits", qs)
        if op in _ANGLED_GATES:
            if self.angle is None:
                raise QuantumGateIRError(f"{op} requires an angle")
            a = float(self.angle)
            if not math.isfinite(a):
                raise QuantumGateIRError("gate angle must be finite")
            object.__setattr__(self, "angle", a)
        elif self.angle is not None:
            raise QuantumGateIRError(f"{op} does not accept an angle")

    def to_dict(self) -> dict:
        out = {"op": self.op, "qubits": list(self.qubits)}
        if self.angle is not None:
            out["angle"] = self.angle
        return out


@dataclass(frozen=True)
class Observable:
    pauli: str
    qubits: tuple[int, ...]

    def __post_init__(self) -> None:
        word = str(self.pauli).upper()
        qs = tuple(_require_qubit(q) for q in self.qubits)
        if not word or any(ch not in "IXYZ" for ch in word):
            raise QuantumGateIRError("observable must be a non-empty Pauli word")
        if len(word) != len(qs):
            raise QuantumGateIRError("Pauli word length must equal observable qubit count")
        if len(set(qs)) != len(qs):
            raise QuantumGateIRError("observable qubits must be unique")
        object.__setattr__(self, "pauli", word)
        object.__setattr__(self, "qubits", qs)

    @property
    def support(self) -> tuple[int, ...]:
        return tuple(q for p, q in zip(self.pauli, self.qubits) if p != "I")

    def to_dict(self) -> dict:
        return {"pauli": self.pauli, "qubits": list(self.qubits)}


@dataclass(frozen=True)
class Circuit:
    logical_qubits: int
    gates: tuple[Gate, ...]
    observable: Observable
    mode: str = "RESULT_DIRECTED"

    def __post_init__(self) -> None:
        n = self.logical_qubits
        if isinstance(n, bool) or not isinstance(n, int) or n < 1:
            raise QuantumGateIRError("logical_qubits must be a positive integer")
        gates = tuple(self.gates)
        object.__setattr__(self, "gates", gates)
        mode = str(self.mode).upper()
        if mode not in {"RESULT_DIRECTED", "FULL_STATE"}:
            raise QuantumGateIRError("unsupported execution mode")
        object.__setattr__(self, "mode", mode)
        for gate in gates:
            for q in gate.qubits:
                if q >= n:
                    raise QuantumGateIRError("gate qubit exceeds logical extent")
        for q in self.observable.qubits:
            if q >= n:
                raise QuantumGateIRError("observable qubit exceeds logical extent")
        if not self.observable.support:
            raise QuantumGateIRError("observable support cannot be empty")

    def to_dict(self) -> dict:
        return {
            "schema": QIR_SCHEMA,
            "logical_qubits": self.logical_qubits,
            "mode": self.mode,
            "gates": [gate.to_dict() for gate in self.gates],
            "observable": self.observable.to_dict(),
        }

    @property
    def sha256(self) -> str:
        return _sha256(self.to_dict())


@dataclass(frozen=True)
class ResultDirectedPlan:
    source_circuit_sha256: str
    logical_qubits: int
    active_logical_qubits: tuple[int, ...]
    logical_gates: tuple[Gate, ...]
    compact_gates: tuple[Gate, ...]
    compact_observable: Observable

    @property
    def workspace_qubits(self) -> int:
        return len(self.active_logical_qubits)

    @property
    def remap(self) -> dict[int, int]:
        return {q: i for i, q in enumerate(self.active_logical_qubits)}

    def to_dict(self) -> dict:
        return {
            "schema": PLAN_SCHEMA,
            "source_circuit_sha256": self.source_circuit_sha256,
            "logical_qubits": self.logical_qubits,
            "active_logical_qubits": list(self.active_logical_qubits),
            "workspace_qubits": self.workspace_qubits,
            "logical_gates": [g.to_dict() for g in self.logical_gates],
            "compact_gates": [g.to_dict() for g in self.compact_gates],
            "compact_observable": self.compact_observable.to_dict(),
        }

    @property
    def sha256(self) -> str:
        return _sha256(self.to_dict())


def plan_result_directed(circuit: Circuit) -> ResultDirectedPlan:
    """Compute an exact conservative backward causal cone for a local observable.

    A gate is retained iff at least one of its operands is currently in the
    backward support. Multi-qubit retained gates expand support to all operands.
    This may over-retain gates that commute with a particular observable, but it
    never drops an operator merely because of an unproven algebraic shortcut.
    """
    if circuit.mode != "RESULT_DIRECTED":
        raise QuantumGateIRError("result-directed planning requires RESULT_DIRECTED mode")

    active = set(circuit.observable.support)
    selected_rev: list[Gate] = []
    for gate in reversed(circuit.gates):
        gate_support = set(gate.qubits)
        if active.intersection(gate_support):
            selected_rev.append(gate)
            active.update(gate_support)

    logical_gates = tuple(reversed(selected_rev))
    active_logical = tuple(sorted(active))
    remap = {q: i for i, q in enumerate(active_logical)}

    compact_gates = tuple(
        Gate(g.op, tuple(remap[q] for q in g.qubits), g.angle)
        for g in logical_gates
    )
    compact_observable = Observable(
        circuit.observable.pauli,
        tuple(remap[q] for q in circuit.observable.qubits),
    )

    return ResultDirectedPlan(
        source_circuit_sha256=circuit.sha256,
        logical_qubits=circuit.logical_qubits,
        active_logical_qubits=active_logical,
        logical_gates=logical_gates,
        compact_gates=compact_gates,
        compact_observable=compact_observable,
    )


@dataclass(frozen=True)
class Q28LoweringReceipt:
    source_plan_sha256: str
    workspace_qubits: int
    address_qubits: int
    total_materialized_qubits: int
    native_gates: tuple[Gate, ...]
    observable: Observable

    def to_dict(self) -> dict:
        return {
            "schema": Q28_LOWERING_SCHEMA,
            "source_plan_sha256": self.source_plan_sha256,
            "workspace_qubits": self.workspace_qubits,
            "address_qubits": self.address_qubits,
            "total_materialized_qubits": self.total_materialized_qubits,
            "native_gate_set": sorted(_Q28_NATIVE),
            "native_gates": [g.to_dict() for g in self.native_gates],
            "observable": self.observable.to_dict(),
            "physical_qpu_claim": False,
        }

    @property
    def sha256(self) -> str:
        return _sha256(self.to_dict())


def _lower_gate_q28(gate: Gate) -> tuple[Gate, ...]:
    if gate.op in _Q28_NATIVE:
        return (gate,)
    if gate.op == "CZ":
        control, target = gate.qubits
        return (
            Gate("H", (target,)),
            Gate("CNOT", (control, target)),
            Gate("H", (target,)),
        )
    raise QuantumGateIRError(f"no exact Q28 lowering for {gate.op}")


def lower_plan_to_q28(
    plan: ResultDirectedPlan,
    *,
    workspace_limit: int = Q28_WORKSPACE_QUBITS,
    address_qubits: int = Q28_ADDRESS_QUBITS,
) -> Q28LoweringReceipt:
    if isinstance(workspace_limit, bool) or workspace_limit < 1:
        raise QuantumGateIRError("workspace_limit must be positive")
    if plan.workspace_qubits > workspace_limit:
        raise QuantumGateIRError(
            f"causal cone requires {plan.workspace_qubits} workspace qubits; "
            f"Q28 budget is {workspace_limit}"
        )
    native: list[Gate] = []
    for gate in plan.compact_gates:
        native.extend(_lower_gate_q28(gate))
    return Q28LoweringReceipt(
        source_plan_sha256=plan.sha256,
        workspace_qubits=plan.workspace_qubits,
        address_qubits=int(address_qubits),
        total_materialized_qubits=int(address_qubits) + plan.workspace_qubits,
        native_gates=tuple(native),
        observable=plan.compact_observable,
    )


def circuit_from_dict(payload: dict) -> Circuit:
    if payload.get("schema") != QIR_SCHEMA:
        raise QuantumGateIRError("unsupported QIR schema")
    gates = tuple(
        Gate(
            item["op"],
            tuple(item["qubits"]),
            item.get("angle"),
        )
        for item in payload.get("gates", ())
    )
    observable_raw = payload["observable"]
    observable = Observable(
        observable_raw["pauli"],
        tuple(observable_raw["qubits"]),
    )
    return Circuit(
        logical_qubits=int(payload["logical_qubits"]),
        gates=gates,
        observable=observable,
        mode=payload.get("mode", "RESULT_DIRECTED"),
    )


__all__ = [
    "QIR_SCHEMA",
    "PLAN_SCHEMA",
    "Q28_LOWERING_SCHEMA",
    "Q28_ADDRESS_QUBITS",
    "Q28_WORKSPACE_QUBITS",
    "QuantumGateIRError",
    "Gate",
    "Observable",
    "Circuit",
    "ResultDirectedPlan",
    "Q28LoweringReceipt",
    "plan_result_directed",
    "lower_plan_to_q28",
    "circuit_from_dict",
]
