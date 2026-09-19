"""Typed memory and information-exchange protocol for PhaseNav.

The protocol binds immutable information content to explicit causal lineage while
keeping route/relational phase separate from payload identity.

It is a software/memory contract only. It does not establish physical nonlocal
signalling, a physical communication channel, or canon authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from .u1_transport import finite_edge_potentials, u1_transport

MEMORY_EXCHANGE_VERSION = "0.1.0"
MEMORY_EXCHANGE_SCHEMA = "PHASENAV_MEMORY_INFORMATION_EXCHANGE_V0_1"
MEMORY_EXCHANGE_ACK_SCHEMA = "PHASENAV_MEMORY_INFORMATION_EXCHANGE_ACK_V0_1"
MEMORY_EXCHANGE_EPISTEMIC = "CHYBA"
MEMORY_EXCHANGE_AUTHORITY = "SHARED_COGNITION_ONLY"


class MemoryLayer(str, Enum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    RELATIONAL = "RELATIONAL"
    ARCHIVAL = "ARCHIVAL"


class ExchangeOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


_PROMOTION_NEXT = {
    MemoryLayer.WORKING: MemoryLayer.EPISODIC,
    MemoryLayer.EPISODIC: MemoryLayer.SEMANTIC,
    MemoryLayer.SEMANTIC: MemoryLayer.RELATIONAL,
    MemoryLayer.RELATIONAL: MemoryLayer.ARCHIVAL,
}


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("memory-exchange values must be finite JSON data") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    out = value.strip()
    if not out:
        raise ValueError(f"{field} must be non-empty")
    return out


def _strict_int(value: Any, field: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < minimum:
        raise ValueError(f"{field} must be >= {minimum}")
    return value


def _layer(value: MemoryLayer | str, field: str) -> MemoryLayer:
    if isinstance(value, MemoryLayer):
        return value
    try:
        return MemoryLayer(_text(value, field).upper())
    except ValueError as exc:
        raise ValueError(f"unsupported {field}") from exc


def _refs(values: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field} must be a sequence")
    out: list[str] = []
    for value in values:
        text = _text(value, field)
        if text not in out:
            out.append(text)
    return tuple(sorted(out))


def _transport(edge_potentials: Sequence[float]) -> tuple[tuple[float, ...], complex, float]:
    edges = finite_edge_potentials(edge_potentials)
    w = u1_transport(edges)
    return edges, w, math.atan2(w.imag, w.real)


@dataclass(frozen=True)
class InformationEnvelope:
    """Immutable content-addressed exchange unit.

    The payload hash identifies *what* information is carried. The envelope id
    also binds lineage, memory-layer endpoints and this hop's route phase data.
    Thus the same payload may traverse different relational routes without
    changing its content identity.
    """

    envelope_id: str
    subject_id: str
    producer_id: str
    generation_id: str
    sequence: int
    source_layer: MemoryLayer
    target_layer: MemoryLayer
    payload: Mapping[str, Any]
    payload_sha256: str
    parent_envelope_ids: tuple[str, ...]
    provenance: tuple[str, ...]
    dependencies: tuple[str, ...]
    route_edge_potentials: tuple[float, ...]
    transport_real: float
    transport_imag: float
    transport_phase: float
    hop_count: int
    hop_limit: int
    epistemic: str = MEMORY_EXCHANGE_EPISTEMIC
    authority: str = MEMORY_EXCHANGE_AUTHORITY
    canon_allowed: bool = False

    @classmethod
    def build(
        cls,
        *,
        subject_id: str,
        producer_id: str,
        generation_id: str,
        sequence: int,
        source_layer: MemoryLayer | str,
        target_layer: MemoryLayer | str,
        payload: Mapping[str, Any],
        parent_envelope_ids: Sequence[str] = (),
        provenance: Sequence[str] = (),
        dependencies: Sequence[str] = (),
        route_edge_potentials: Sequence[float] = (),
        hop_count: int = 0,
        hop_limit: int = 16,
    ) -> "InformationEnvelope":
        subject = _text(subject_id, "subject_id")
        producer = _text(producer_id, "producer_id")
        generation = _text(generation_id, "generation_id")
        seq = _strict_int(sequence, "sequence", minimum=0)
        source = _layer(source_layer, "source_layer")
        target = _layer(target_layer, "target_layer")
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be a mapping")
        payload_dict = dict(payload)
        payload_sha = _sha256(payload_dict)
        parents = _refs(parent_envelope_ids, "parent_envelope_ids")
        prov = _refs(provenance, "provenance")
        deps = _refs(dependencies, "dependencies")
        edges, w, phase = _transport(route_edge_potentials)
        hops = _strict_int(hop_count, "hop_count", minimum=0)
        limit = _strict_int(hop_limit, "hop_limit", minimum=1)
        if hops > limit:
            raise ValueError("hop_count cannot exceed hop_limit")

        core = {
            "schema": MEMORY_EXCHANGE_SCHEMA,
            "version": MEMORY_EXCHANGE_VERSION,
            "subject_id": subject,
            "producer_id": producer,
            "generation_id": generation,
            "sequence": seq,
            "source_layer": source.value,
            "target_layer": target.value,
            "payload_sha256": payload_sha,
            "parent_envelope_ids": list(parents),
            "provenance": list(prov),
            "dependencies": list(deps),
            "route_edge_potentials": list(edges),
            "hop_count": hops,
            "hop_limit": limit,
            "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
            "authority": MEMORY_EXCHANGE_AUTHORITY,
            "canon_allowed": False,
        }
        envelope_id = "px:" + _sha256(core)
        return cls(
            envelope_id=envelope_id,
            subject_id=subject,
            producer_id=producer,
            generation_id=generation,
            sequence=seq,
            source_layer=source,
            target_layer=target,
            payload=payload_dict,
            payload_sha256=payload_sha,
            parent_envelope_ids=parents,
            provenance=prov,
            dependencies=deps,
            route_edge_potentials=edges,
            transport_real=float(w.real),
            transport_imag=float(w.imag),
            transport_phase=float(phase),
            hop_count=hops,
            hop_limit=limit,
        )

    def to_packet(self) -> dict[str, Any]:
        return {
            "schema": MEMORY_EXCHANGE_SCHEMA,
            "version": MEMORY_EXCHANGE_VERSION,
            "envelope_id": self.envelope_id,
            "subject_id": self.subject_id,
            "producer_id": self.producer_id,
            "generation_id": self.generation_id,
            "sequence": self.sequence,
            "source_layer": self.source_layer.value,
            "target_layer": self.target_layer.value,
            "payload": dict(self.payload),
            "payload_sha256": self.payload_sha256,
            "parent_envelope_ids": list(self.parent_envelope_ids),
            "provenance": list(self.provenance),
            "dependencies": list(self.dependencies),
            "route_edge_potentials": list(self.route_edge_potentials),
            "transport": {
                "real": self.transport_real,
                "imag": self.transport_imag,
                "phase": self.transport_phase,
                "modulus": math.hypot(self.transport_real, self.transport_imag),
            },
            "hop_count": self.hop_count,
            "hop_limit": self.hop_limit,
            "epistemic": self.epistemic,
            "authority": self.authority,
            "canon_allowed": self.canon_allowed,
            "claims": {
                "content_addressed_payload": True,
                "causal_lineage": True,
                "computational_u1_route_phase": True,
                "physical_nonlocal_signalling": False,
                "physical_channel_identified": False,
                "canon_promoted": False,
            },
        }

    def forward(
        self,
        *,
        producer_id: str,
        target_layer: MemoryLayer | str,
        route_edge_potentials: Sequence[float] = (),
        provenance: Sequence[str] | None = None,
        dependencies: Sequence[str] | None = None,
    ) -> "InformationEnvelope":
        if self.hop_count >= self.hop_limit:
            raise RuntimeError("memory-exchange hop limit reached")
        return InformationEnvelope.build(
            subject_id=self.subject_id,
            producer_id=producer_id,
            generation_id=self.generation_id,
            sequence=self.sequence + 1,
            source_layer=self.target_layer,
            target_layer=target_layer,
            payload=self.payload,
            parent_envelope_ids=(self.envelope_id,),
            provenance=self.provenance if provenance is None else provenance,
            dependencies=self.dependencies if dependencies is None else dependencies,
            route_edge_potentials=route_edge_potentials,
            hop_count=self.hop_count + 1,
            hop_limit=self.hop_limit,
        )

    def transform(
        self,
        *,
        producer_id: str,
        target_layer: MemoryLayer | str,
        payload: Mapping[str, Any],
        route_edge_potentials: Sequence[float] = (),
        provenance: Sequence[str] | None = None,
        dependencies: Sequence[str] | None = None,
    ) -> "InformationEnvelope":
        if self.hop_count >= self.hop_limit:
            raise RuntimeError("memory-exchange hop limit reached")
        return InformationEnvelope.build(
            subject_id=self.subject_id,
            producer_id=producer_id,
            generation_id=self.generation_id,
            sequence=self.sequence + 1,
            source_layer=self.target_layer,
            target_layer=target_layer,
            payload=payload,
            parent_envelope_ids=(self.envelope_id,),
            provenance=self.provenance if provenance is None else provenance,
            dependencies=self.dependencies if dependencies is None else dependencies,
            route_edge_potentials=route_edge_potentials,
            hop_count=self.hop_count + 1,
            hop_limit=self.hop_limit,
        )

    def promote(
        self,
        *,
        producer_id: str,
        route_edge_potentials: Sequence[float] = (),
    ) -> "InformationEnvelope":
        expected = _PROMOTION_NEXT.get(self.target_layer)
        if expected is None:
            raise RuntimeError("ARCHIVAL is terminal for memory promotion")
        return self.forward(
            producer_id=producer_id,
            target_layer=expected,
            route_edge_potentials=route_edge_potentials,
        )


@dataclass(frozen=True)
class ExchangeAck:
    ack_id: str
    envelope_id: str
    payload_sha256: str
    consumer_id: str
    outcome: ExchangeOutcome
    reason_code: str
    epistemic: str = MEMORY_EXCHANGE_EPISTEMIC
    authority: str = MEMORY_EXCHANGE_AUTHORITY
    canon_allowed: bool = False

    @classmethod
    def build(
        cls,
        envelope: InformationEnvelope,
        *,
        consumer_id: str,
        outcome: ExchangeOutcome | str,
        reason_code: str = "OK",
    ) -> "ExchangeAck":
        consumer = _text(consumer_id, "consumer_id")
        reason = _text(reason_code, "reason_code")
        if isinstance(outcome, ExchangeOutcome):
            status = outcome
        else:
            try:
                status = ExchangeOutcome(_text(outcome, "outcome").upper())
            except ValueError as exc:
                raise ValueError("unsupported exchange outcome") from exc
        core = {
            "schema": MEMORY_EXCHANGE_ACK_SCHEMA,
            "version": MEMORY_EXCHANGE_VERSION,
            "envelope_id": envelope.envelope_id,
            "payload_sha256": envelope.payload_sha256,
            "consumer_id": consumer,
            "outcome": status.value,
            "reason_code": reason,
            "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
            "authority": MEMORY_EXCHANGE_AUTHORITY,
            "canon_allowed": False,
        }
        return cls(
            ack_id="pxa:" + _sha256(core),
            envelope_id=envelope.envelope_id,
            payload_sha256=envelope.payload_sha256,
            consumer_id=consumer,
            outcome=status,
            reason_code=reason,
        )

    def to_packet(self) -> dict[str, Any]:
        return {
            "schema": MEMORY_EXCHANGE_ACK_SCHEMA,
            "version": MEMORY_EXCHANGE_VERSION,
            "ack_id": self.ack_id,
            "envelope_id": self.envelope_id,
            "payload_sha256": self.payload_sha256,
            "consumer_id": self.consumer_id,
            "outcome": self.outcome.value,
            "reason_code": self.reason_code,
            "epistemic": self.epistemic,
            "authority": self.authority,
            "canon_allowed": self.canon_allowed,
        }


class MemoryExchangeLedger:
    """Append-only in-memory causal ledger for envelopes and acknowledgements."""

    def __init__(self) -> None:
        self._envelopes: dict[str, InformationEnvelope] = {}
        self._acks: dict[tuple[str, str], ExchangeAck] = {}

    @property
    def envelope_count(self) -> int:
        return len(self._envelopes)

    @property
    def ack_count(self) -> int:
        return len(self._acks)

    def append(self, envelope: InformationEnvelope) -> bool:
        existing = self._envelopes.get(envelope.envelope_id)
        if existing is not None:
            if existing.to_packet() != envelope.to_packet():
                raise RuntimeError("envelope id collision with different content")
            return False

        for parent_id in envelope.parent_envelope_ids:
            parent = self._envelopes.get(parent_id)
            if parent is None:
                raise RuntimeError("orphan memory-exchange envelope")
            if envelope.sequence <= parent.sequence:
                raise RuntimeError("child sequence must be greater than parent sequence")
            if envelope.generation_id != parent.generation_id:
                raise RuntimeError("child and parent generation_id must match")
        self._envelopes[envelope.envelope_id] = envelope
        return True

    def record_ack(self, ack: ExchangeAck) -> bool:
        envelope = self._envelopes.get(ack.envelope_id)
        if envelope is None:
            raise RuntimeError("ack references unknown envelope")
        if ack.payload_sha256 != envelope.payload_sha256:
            raise RuntimeError("ack payload commitment mismatch")
        key = (ack.envelope_id, ack.consumer_id)
        existing = self._acks.get(key)
        if existing is not None:
            if existing == ack:
                return False
            raise RuntimeError("consumer already acknowledged envelope with different outcome")
        self._acks[key] = ack
        return True

    def lineage(self, envelope_id: str) -> tuple[InformationEnvelope, ...]:
        target = self._envelopes.get(_text(envelope_id, "envelope_id"))
        if target is None:
            raise KeyError("unknown envelope_id")
        seen: dict[str, InformationEnvelope] = {}

        def visit(node: InformationEnvelope) -> None:
            if node.envelope_id in seen:
                return
            for parent_id in node.parent_envelope_ids:
                visit(self._envelopes[parent_id])
            seen[node.envelope_id] = node

        visit(target)
        return tuple(sorted(seen.values(), key=lambda item: (item.sequence, item.envelope_id)))

    def snapshot(self) -> dict[str, Any]:
        parent_refs = {
            parent
            for envelope in self._envelopes.values()
            for parent in envelope.parent_envelope_ids
        }
        heads = sorted(
            envelope_id
            for envelope_id in self._envelopes
            if envelope_id not in parent_refs
        )
        core = {
            "schema": "PHASENAV_MEMORY_INFORMATION_EXCHANGE_LEDGER_V0_1",
            "envelope_ids": sorted(self._envelopes),
            "ack_ids": sorted(ack.ack_id for ack in self._acks.values()),
            "head_envelope_ids": heads,
        }
        return {
            **core,
            "envelope_count": self.envelope_count,
            "ack_count": self.ack_count,
            "ledger_sha256": _sha256(core),
            "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
            "authority": MEMORY_EXCHANGE_AUTHORITY,
            "canon_allowed": False,
        }


__all__ = [
    "MEMORY_EXCHANGE_ACK_SCHEMA",
    "MEMORY_EXCHANGE_AUTHORITY",
    "MEMORY_EXCHANGE_EPISTEMIC",
    "MEMORY_EXCHANGE_SCHEMA",
    "MEMORY_EXCHANGE_VERSION",
    "ExchangeAck",
    "ExchangeOutcome",
    "InformationEnvelope",
    "MemoryExchangeLedger",
    "MemoryLayer",
]
