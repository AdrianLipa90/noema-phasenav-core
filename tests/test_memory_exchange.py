from __future__ import annotations

import math

import pytest

from ciel_geometry.phasenav.canon.memory_exchange import (
    ExchangeAck,
    InformationEnvelope,
    MemoryExchangeLedger,
    MemoryLayer,
)


def _root(**overrides):
    kwargs = {
        "subject_id": "spectroscopy:ring-6",
        "producer_id": "PHASENAV",
        "generation_id": "gen-001",
        "sequence": 0,
        "source_layer": MemoryLayer.WORKING,
        "target_layer": MemoryLayer.EPISODIC,
        "payload": {"kind": "OBSERVATION", "value": 3, "nested": {"a": 1}},
        "provenance": ("run:123",),
        "dependencies": ("model:ring6",),
        "route_edge_potentials": (0.20, -0.05),
        "hop_limit": 4,
    }
    kwargs.update(overrides)
    return InformationEnvelope.build(**kwargs)


def test_payload_commitment_is_canonical_and_separate_from_route() -> None:
    first = _root(payload={"b": 2, "a": 1}, route_edge_potentials=(0.1,))
    same_content = _root(payload={"a": 1, "b": 2}, route_edge_potentials=(0.7,))
    assert first.payload_sha256 == same_content.payload_sha256
    assert first.envelope_id != same_content.envelope_id
    assert abs(first.to_packet()["transport"]["modulus"] - 1.0) < 1.0e-12


def test_forward_preserves_payload_and_creates_causal_child() -> None:
    root = _root()
    child = root.forward(
        producer_id="GREMLIN",
        target_layer=MemoryLayer.SEMANTIC,
        route_edge_potentials=(0.30, 0.10),
    )
    assert child.payload_sha256 == root.payload_sha256
    assert child.parent_envelope_ids == (root.envelope_id,)
    assert child.sequence == root.sequence + 1
    assert child.hop_count == 1
    assert child.source_layer == MemoryLayer.EPISODIC
    assert child.target_layer == MemoryLayer.SEMANTIC


def test_transform_changes_payload_but_preserves_parent_lineage() -> None:
    root = _root()
    child = root.transform(
        producer_id="MOLE",
        target_layer=MemoryLayer.SEMANTIC,
        payload={"kind": "DERIVED", "value": 4},
    )
    assert child.payload_sha256 != root.payload_sha256
    assert child.parent_envelope_ids == (root.envelope_id,)


def test_monotonic_memory_promotion_chain() -> None:
    episodic = _root()
    semantic = episodic.promote(producer_id="RAVEN")
    relational = semantic.promote(producer_id="SPIDER")
    archival = relational.promote(producer_id="GREMLIN")
    assert [
        episodic.target_layer,
        semantic.target_layer,
        relational.target_layer,
        archival.target_layer,
    ] == [
        MemoryLayer.EPISODIC,
        MemoryLayer.SEMANTIC,
        MemoryLayer.RELATIONAL,
        MemoryLayer.ARCHIVAL,
    ]
    with pytest.raises(RuntimeError):
        archival.promote(producer_id="GREMLIN")


def test_hop_limit_fails_closed() -> None:
    root = _root(hop_limit=1)
    child = root.forward(
        producer_id="GREMLIN",
        target_layer=MemoryLayer.SEMANTIC,
    )
    with pytest.raises(RuntimeError):
        child.forward(
            producer_id="RAVEN",
            target_layer=MemoryLayer.RELATIONAL,
        )


def test_ledger_requires_parent_first_and_monotonic_sequence() -> None:
    ledger = MemoryExchangeLedger()
    root = _root()
    child = root.forward(
        producer_id="GREMLIN",
        target_layer=MemoryLayer.SEMANTIC,
    )
    with pytest.raises(RuntimeError):
        ledger.append(child)
    assert ledger.append(root) is True
    assert ledger.append(root) is False
    assert ledger.append(child) is True
    assert [row.envelope_id for row in ledger.lineage(child.envelope_id)] == [
        root.envelope_id,
        child.envelope_id,
    ]


def test_ack_is_content_bound_idempotent_and_conflict_closed() -> None:
    ledger = MemoryExchangeLedger()
    root = _root()
    ledger.append(root)
    accepted = ExchangeAck.build(
        root,
        consumer_id="GREMLIN-HIVE",
        outcome="ACCEPTED",
    )
    assert accepted.to_packet()["authentication"] == "UNSIGNED_CONTENT_COMMITMENT"
    assert ledger.record_ack(accepted) is True
    assert ledger.record_ack(accepted) is False

    rejected = ExchangeAck.build(
        root,
        consumer_id="GREMLIN-HIVE",
        outcome="REJECTED",
        reason_code="TEST_CONFLICT",
    )
    with pytest.raises(RuntimeError):
        ledger.record_ack(rejected)


def test_snapshot_is_deterministic_and_reports_current_heads() -> None:
    root = _root()
    child = root.forward(
        producer_id="GREMLIN",
        target_layer=MemoryLayer.SEMANTIC,
        route_edge_potentials=(math.pi / 7.0,),
    )
    ack = ExchangeAck.build(
        child,
        consumer_id="RAVEN",
        outcome="QUARANTINED",
        reason_code="AWAITING_AUDIT",
    )

    a = MemoryExchangeLedger()
    a.append(root)
    a.append(child)
    a.record_ack(ack)

    b = MemoryExchangeLedger()
    b.append(root)
    b.append(child)
    b.record_ack(ack)

    snap_a = a.snapshot()
    snap_b = b.snapshot()
    assert snap_a == snap_b
    assert snap_a["head_envelope_ids"] == [child.envelope_id]
    assert snap_a["envelope_count"] == 2
    assert snap_a["ack_count"] == 1
    assert len(snap_a["ledger_sha256"]) == 64



def test_lineage_bundle_carries_ancestor_envelopes_and_acks() -> None:
    episodic = _root()
    semantic = episodic.promote(producer_id="RAVEN")
    relational = semantic.promote(producer_id="SPIDER")

    ledger = MemoryExchangeLedger()
    for envelope in (episodic, semantic, relational):
        ledger.append(envelope)

    ledger.record_ack(
        ExchangeAck.build(
            episodic,
            consumer_id="EPISODIC-STORE",
            outcome="ACCEPTED",
            reason_code="EPISODIC_INGESTED",
        )
    )
    ledger.record_ack(
        ExchangeAck.build(
            semantic,
            consumer_id="SEMANTIC-STORE",
            outcome="ACCEPTED",
            reason_code="SEMANTIC_INGESTED",
        )
    )

    bundle = ledger.export_bundle(relational.envelope_id)
    assert bundle["schema"] == "PHASENAV_MEMORY_INFORMATION_EXCHANGE_BUNDLE_V0_1"
    assert bundle["target_envelope_id"] == relational.envelope_id
    assert [row["envelope_id"] for row in bundle["envelopes"]] == [
        episodic.envelope_id,
        semantic.envelope_id,
        relational.envelope_id,
    ]
    assert {row["envelope_id"] for row in bundle["acks"]} == {
        episodic.envelope_id,
        semantic.envelope_id,
    }
    assert len(bundle["bundle_sha256"]) == 64
    assert bundle["claims"]["causal_lineage_bundle"] is True
    assert bundle["claims"]["ack_origin_authenticated"] is False
    assert bundle["claims"]["physical_nonlocal_signalling"] is False


def test_lineage_bundle_is_deterministic() -> None:
    root = _root()
    child = root.promote(producer_id="RAVEN")

    a = MemoryExchangeLedger()
    a.append(root)
    a.append(child)
    a.record_ack(
        ExchangeAck.build(
            root,
            consumer_id="EPISODIC-STORE",
            outcome="ACCEPTED",
        )
    )

    b = MemoryExchangeLedger()
    b.append(root)
    b.append(child)
    b.record_ack(
        ExchangeAck.build(
            root,
            consumer_id="EPISODIC-STORE",
            outcome="ACCEPTED",
        )
    )

    assert a.export_bundle(child.envelope_id) == b.export_bundle(child.envelope_id)
