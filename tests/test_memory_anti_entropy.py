from __future__ import annotations

import copy

import pytest

from ciel_geometry.phasenav.canon.memory_anti_entropy import (
    apply_delta,
    build_bucket_manifest,
    build_inventory,
    divergent_buckets,
    export_delta,
    plan_delta,
    validate_bucket_manifest,
    validate_delta,
    validate_inventory,
    validate_plan,
)
from ciel_geometry.phasenav.canon.memory_exchange import (
    ExchangeAck,
    InformationEnvelope,
    MemoryExchangeLedger,
    MemoryLayer,
)


def _root(subject: str = "spectroscopy:ring-6") -> InformationEnvelope:
    return InformationEnvelope.build(
        subject_id=subject,
        producer_id="PHASENAV",
        generation_id="gen-001",
        sequence=0,
        source_layer=MemoryLayer.WORKING,
        target_layer=MemoryLayer.EPISODIC,
        payload={"kind": "OBSERVATION", "subject": subject, "value": 3},
        provenance=("run:123",),
        dependencies=("model:ring6",),
        route_edge_potentials=(0.20, -0.05),
        hop_limit=8,
    )


def _chain() -> tuple[InformationEnvelope, InformationEnvelope, InformationEnvelope]:
    episodic = _root()
    semantic = episodic.promote(
        producer_id="RAVEN",
        route_edge_potentials=(0.30,),
    )
    relational = semantic.promote(
        producer_id="SPIDER",
        route_edge_potentials=(0.40, -0.10),
    )
    return episodic, semantic, relational


def _ledger(
    envelopes: tuple[InformationEnvelope, ...],
    *,
    ack_envelopes: tuple[InformationEnvelope, ...] = (),
) -> MemoryExchangeLedger:
    ledger = MemoryExchangeLedger()
    for envelope in envelopes:
        ledger.append(envelope)
    for envelope in ack_envelopes:
        ledger.record_ack(
            ExchangeAck.build(
                envelope,
                consumer_id=f"STORE-{envelope.target_layer.value}",
                outcome="ACCEPTED",
                reason_code="INGESTED",
            )
        )
    return ledger


def _sync(sender: MemoryExchangeLedger, receiver: MemoryExchangeLedger):
    sender_inventory = build_inventory(sender, node_id="NODE-A")
    receiver_inventory = build_inventory(receiver, node_id="NODE-B")
    prefixes = divergent_buckets(sender_inventory, receiver_inventory)
    sender_manifest = build_bucket_manifest(
        sender,
        node_id="NODE-A",
        prefixes=prefixes,
    )
    receiver_manifest = build_bucket_manifest(
        receiver,
        node_id="NODE-B",
        prefixes=prefixes,
    )
    plan = plan_delta(
        sender_inventory,
        receiver_inventory,
        sender_manifest,
        receiver_manifest,
    )
    delta = export_delta(sender, plan)
    return sender_inventory, receiver_inventory, prefixes, sender_manifest, receiver_manifest, plan, delta


def test_inventory_is_deterministic_and_identity_is_explicitly_unsigned() -> None:
    episodic, semantic, relational = _chain()
    a = _ledger((episodic, semantic, relational), ack_envelopes=(episodic, semantic))
    b = _ledger((episodic, semantic, relational), ack_envelopes=(semantic, episodic))

    inv_a = build_inventory(a, node_id="NODE-A")
    inv_b = build_inventory(b, node_id="NODE-B")

    assert inv_a["content_root_sha256"] == inv_b["content_root_sha256"]
    assert inv_a["ledger_sha256"] == inv_b["ledger_sha256"]
    assert inv_a["inventory_sha256"] != inv_b["inventory_sha256"]
    assert inv_a["authentication"] == "UNSIGNED_CONTENT_COMMITMENT"
    assert inv_a["claims"]["node_identity_authenticated"] is False
    assert divergent_buckets(inv_a, inv_b) == ()
    assert validate_inventory(inv_a)["inventory_sha256"] == inv_a["inventory_sha256"]


def test_manifest_discloses_only_metadata_for_divergent_buckets() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger((episodic, semantic, relational), ack_envelopes=(episodic,))
    receiver = _ledger((episodic,))
    sender_inv = build_inventory(sender, node_id="NODE-A")
    receiver_inv = build_inventory(receiver, node_id="NODE-B")
    prefixes = divergent_buckets(sender_inv, receiver_inv)

    manifest = build_bucket_manifest(sender, node_id="NODE-A", prefixes=prefixes)
    validated = validate_bucket_manifest(manifest, sender_inv)

    assert validated["claims"]["metadata_only"] is True
    assert validated["claims"]["payload_transferred"] is False
    serialized = repr(validated)
    assert "'payload':" not in serialized
    assert set(validated["prefixes"]) == set(prefixes)


def test_delta_plan_contains_only_sender_items_missing_at_receiver() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger(
        (episodic, semantic, relational),
        ack_envelopes=(episodic, semantic, relational),
    )
    receiver = _ledger((episodic,), ack_envelopes=(episodic,))

    _, _, _, _, _, plan, delta = _sync(sender, receiver)
    validated_plan = validate_plan(plan)

    assert episodic.envelope_id not in validated_plan["send_envelope_ids"]
    assert semantic.envelope_id in validated_plan["send_envelope_ids"]
    assert relational.envelope_id in validated_plan["send_envelope_ids"]
    assert len(validated_plan["send_ack_ids"]) == 2
    assert validated_plan["claims"]["delete_receiver_only_items"] is False
    assert validated_plan["claims"]["overwrite_receiver_items"] is False
    assert validate_delta(delta)["delta_sha256"] == delta["delta_sha256"]


def test_apply_delta_reaches_sender_content_without_copying_existing_items() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger(
        (episodic, semantic, relational),
        ack_envelopes=(episodic, semantic, relational),
    )
    receiver = _ledger((episodic,), ack_envelopes=(episodic,))

    sender_inv, _, _, _, _, _, delta = _sync(sender, receiver)
    result = apply_delta(receiver, delta, receiver_node_id="NODE-B")
    after = build_inventory(receiver, node_id="NODE-B")

    assert result["status"] == "APPLIED"
    assert result["created_envelopes"] == 2
    assert result["created_acks"] == 2
    assert after["content_root_sha256"] == sender_inv["content_root_sha256"]
    assert receiver.envelope_count == sender.envelope_count
    assert receiver.ack_count == sender.ack_count


def test_exact_delta_retry_is_idempotent_even_after_receiver_inventory_changes() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger((episodic, semantic, relational), ack_envelopes=(episodic, semantic))
    receiver = _ledger((episodic,))

    *_, delta = _sync(sender, receiver)
    first = apply_delta(receiver, delta, receiver_node_id="NODE-B")
    second = apply_delta(receiver, delta, receiver_node_id="NODE-B")

    assert first["status"] == "APPLIED"
    assert second["status"] == "ALREADY_APPLIED"
    assert second["created_envelopes"] == 0
    assert second["created_acks"] == 0


def test_stale_delta_is_rejected_before_mutation() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger((episodic, semantic, relational), ack_envelopes=(episodic,))
    receiver = _ledger((episodic,))
    *_, delta = _sync(sender, receiver)

    independent = _root("receiver-local")
    receiver.append(independent)
    before = receiver.snapshot()

    with pytest.raises(RuntimeError, match="inventory changed"):
        apply_delta(receiver, delta, receiver_node_id="NODE-B")

    assert receiver.snapshot() == before


def test_receiver_only_items_are_never_deleted() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger((episodic, semantic, relational), ack_envelopes=(episodic,))
    receiver_local = _root("receiver-local")
    receiver = _ledger((episodic, receiver_local))

    *_, plan, delta = _sync(sender, receiver)
    assert receiver_local.envelope_id in plan["receiver_only_envelope_ids"]

    result = apply_delta(receiver, delta, receiver_node_id="NODE-B")
    assert result["status"] == "APPLIED"
    assert receiver.get_envelope(receiver_local.envelope_id) == receiver_local


def test_delta_preflight_prevents_partial_apply_on_tamper() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger((episodic, semantic, relational), ack_envelopes=(semantic,))
    receiver = _ledger((episodic,))
    *_, delta = _sync(sender, receiver)

    tampered = copy.deepcopy(delta)
    tampered["envelopes"][-1]["payload"]["value"] = 999
    before = receiver.snapshot()

    with pytest.raises(ValueError):
        apply_delta(receiver, tampered, receiver_node_id="NODE-B")

    assert receiver.snapshot() == before


def test_manifest_tamper_and_wrong_inventory_binding_fail_closed() -> None:
    episodic, semantic, relational = _chain()
    sender = _ledger((episodic, semantic, relational))
    receiver = _ledger((episodic,))
    sender_inv = build_inventory(sender, node_id="NODE-A")
    receiver_inv = build_inventory(receiver, node_id="NODE-B")
    prefixes = divergent_buckets(sender_inv, receiver_inv)
    manifest = build_bucket_manifest(sender, node_id="NODE-A", prefixes=prefixes)

    with pytest.raises(ValueError):
        validate_bucket_manifest(manifest, receiver_inv)

    bad = copy.deepcopy(manifest)
    prefix = bad["prefixes"][0]
    bad["buckets"][prefix]["root_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="root"):
        validate_bucket_manifest(bad, sender_inv)


def test_empty_delta_when_receiver_is_strict_superset_is_non_destructive() -> None:
    sender_root = _root()
    receiver_extra = _root("receiver-extra")
    sender = _ledger((sender_root,))
    receiver = _ledger((sender_root, receiver_extra))

    *_, plan, delta = _sync(sender, receiver)
    assert plan["send_envelope_ids"] == []
    assert plan["receiver_only_envelope_ids"] == [receiver_extra.envelope_id]

    result = apply_delta(receiver, delta, receiver_node_id="NODE-B")
    assert result["status"] == "ALREADY_APPLIED"
    assert receiver.get_envelope(receiver_extra.envelope_id) == receiver_extra
