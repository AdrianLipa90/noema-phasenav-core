from __future__ import annotations

import copy

import pytest

from ciel_geometry.phasenav.canon.memory_consolidation import (
    DERIVED_SEMANTIC_KIND,
    RetentionTier,
    apply_consolidation,
    build_consolidation_plan,
    validate_consolidation_plan,
)
from ciel_geometry.phasenav.canon.memory_exchange import (
    ExchangeAck,
    InformationEnvelope,
    MemoryExchangeLedger,
    MemoryLayer,
)


def _episodic(
    *,
    sequence: int,
    value: int,
    subject_id: str = "spectroscopy:ring-6",
    generation_id: str = "gen-001",
    hop_count: int = 0,
    hop_limit: int = 8,
) -> InformationEnvelope:
    return InformationEnvelope.build(
        subject_id=subject_id,
        producer_id="SENSOR",
        generation_id=generation_id,
        sequence=sequence,
        source_layer=MemoryLayer.WORKING,
        target_layer=MemoryLayer.EPISODIC,
        payload={"kind": "OBSERVATION", "value": value},
        provenance=(f"run:{sequence}",),
        dependencies=("instrument:spec-1",),
        route_edge_potentials=(0.1 * (sequence + 1),),
        hop_count=hop_count,
        hop_limit=hop_limit,
    )


def _ledger_with_sources(
    *,
    subject_id: str = "spectroscopy:ring-6",
) -> tuple[MemoryExchangeLedger, InformationEnvelope, InformationEnvelope]:
    first = _episodic(sequence=0, value=3, subject_id=subject_id)
    second = _episodic(sequence=1, value=5, subject_id=subject_id)
    ledger = MemoryExchangeLedger()
    ledger.append(first)
    ledger.append(second)
    ledger.record_ack(
        ExchangeAck.build(
            first,
            consumer_id="EPISODIC-STORE",
            outcome="ACCEPTED",
            reason_code="EPISODIC_INGESTED",
        )
    )
    ledger.record_ack(
        ExchangeAck.build(
            second,
            consumer_id="EPISODIC-STORE",
            outcome="ACCEPTED",
            reason_code="EPISODIC_INGESTED",
        )
    )
    return ledger, first, second


def _plan(ledger: MemoryExchangeLedger, first: InformationEnvelope, second: InformationEnvelope):
    return build_consolidation_plan(
        ledger,
        source_envelope_ids=[second.envelope_id, first.envelope_id],
        producer_id="PHASENAV-CONSOLIDATOR",
        reducer_id="semantic-reducer-v1",
        semantic_payload={
            "pattern": "stable_pair",
            "observations": 2,
            "mean_value": 4.0,
        },
        route_edge_potentials=(0.2, -0.05),
        source_retention=RetentionTier.COLD,
        derived_retention=RetentionTier.HOT,
    )


def test_plan_builds_multi_parent_episodic_to_semantic_derivation() -> None:
    ledger, first, second = _ledger_with_sources()
    plan = _plan(ledger, first, second)
    validated = validate_consolidation_plan(plan)
    derived = validated["_derived"]

    assert derived.source_layer == MemoryLayer.EPISODIC
    assert derived.target_layer == MemoryLayer.SEMANTIC
    assert set(derived.parent_envelope_ids) == {first.envelope_id, second.envelope_id}
    assert derived.sequence == 2
    assert derived.payload["kind"] == DERIVED_SEMANTIC_KIND
    assert derived.payload["semantic_equivalence_proven"] is False
    assert plan["claims"]["source_immutability_required"] is True
    assert plan["claims"]["semantic_equivalence_proven"] is False


def test_apply_is_additive_and_preserves_every_source() -> None:
    ledger, first, second = _ledger_with_sources()
    before_packets = {
        first.envelope_id: first.to_packet(),
        second.envelope_id: second.to_packet(),
    }
    receipt = apply_consolidation(ledger, _plan(ledger, first, second))

    assert receipt["status"] == "APPLIED"
    assert receipt["created"] is True
    assert receipt["claims"]["sources_preserved"] is True
    assert receipt["claims"]["deletion_performed"] is False
    assert receipt["claims"]["overwrite_performed"] is False
    assert ledger.get_envelope(first.envelope_id).to_packet() == before_packets[first.envelope_id]
    assert ledger.get_envelope(second.envelope_id).to_packet() == before_packets[second.envelope_id]

    derived = ledger.get_envelope(receipt["derived_envelope_id"])
    assert set(derived.parent_envelope_ids) == {first.envelope_id, second.envelope_id}
    assert ledger.envelope_count == 3


def test_exact_plan_replay_is_idempotent() -> None:
    ledger, first, second = _ledger_with_sources()
    plan = _plan(ledger, first, second)

    first_receipt = apply_consolidation(ledger, plan)
    second_receipt = apply_consolidation(ledger, plan)

    assert first_receipt["status"] == "APPLIED"
    assert second_receipt["status"] == "ALREADY_APPLIED"
    assert second_receipt["created"] is False
    assert first_receipt["derived_envelope_id"] == second_receipt["derived_envelope_id"]
    assert ledger.envelope_count == 3


def test_retention_tiers_are_hints_and_never_delete() -> None:
    ledger, first, second = _ledger_with_sources()
    plan = _plan(ledger, first, second)
    manifest = plan["retention_manifest"]

    entries = {row["envelope_id"]: row for row in manifest["entries"]}
    assert entries[first.envelope_id]["retention_tier"] == "COLD"
    assert entries[second.envelope_id]["retention_tier"] == "COLD"
    derived_id = plan["derived_envelope"]["envelope_id"]
    assert entries[derived_id]["retention_tier"] == "HOT"
    assert all(row["deletion_allowed"] is False for row in manifest["entries"])
    assert all(row["overwrite_allowed"] is False for row in manifest["entries"])
    assert all(row["retrievable"] is True for row in manifest["entries"])
    assert manifest["claims"]["retention_tier_is_storage_hint"] is True


def test_consolidation_requires_accepted_ack_for_every_source() -> None:
    first = _episodic(sequence=0, value=1)
    second = _episodic(sequence=1, value=2)
    ledger = MemoryExchangeLedger()
    ledger.append(first)
    ledger.append(second)
    ledger.record_ack(
        ExchangeAck.build(
            first,
            consumer_id="EPISODIC-STORE",
            outcome="ACCEPTED",
        )
    )

    with pytest.raises(RuntimeError, match="requires at least one ACCEPTED ACK"):
        build_consolidation_plan(
            ledger,
            source_envelope_ids=[first.envelope_id, second.envelope_id],
            producer_id="PHASENAV-CONSOLIDATOR",
            reducer_id="semantic-reducer-v1",
            semantic_payload={"summary": "candidate"},
        )


def test_cross_subject_and_cross_generation_fusion_fail_closed() -> None:
    first = _episodic(sequence=0, value=1, subject_id="a")
    second = _episodic(sequence=1, value=2, subject_id="b")
    ledger = MemoryExchangeLedger()
    for envelope in (first, second):
        ledger.append(envelope)
        ledger.record_ack(
            ExchangeAck.build(envelope, consumer_id="STORE", outcome="ACCEPTED")
        )

    with pytest.raises(ValueError, match="subject_id"):
        build_consolidation_plan(
            ledger,
            source_envelope_ids=[first.envelope_id, second.envelope_id],
            producer_id="C",
            reducer_id="R",
            semantic_payload={"summary": "no"},
        )

    third = _episodic(sequence=2, value=3, subject_id="a", generation_id="gen-002")
    ledger.append(third)
    ledger.record_ack(ExchangeAck.build(third, consumer_id="STORE", outcome="ACCEPTED"))
    with pytest.raises(ValueError, match="generation_id"):
        build_consolidation_plan(
            ledger,
            source_envelope_ids=[first.envelope_id, third.envelope_id],
            producer_id="C",
            reducer_id="R",
            semantic_payload={"summary": "no"},
        )


def test_non_episodic_source_is_rejected() -> None:
    ledger, first, second = _ledger_with_sources()
    semantic = second.promote(producer_id="RAVEN")
    ledger.append(semantic)
    ledger.record_ack(ExchangeAck.build(semantic, consumer_id="STORE", outcome="ACCEPTED"))

    with pytest.raises(ValueError, match="target EPISODIC"):
        build_consolidation_plan(
            ledger,
            source_envelope_ids=[first.envelope_id, semantic.envelope_id],
            producer_id="C",
            reducer_id="R",
            semantic_payload={"summary": "no"},
        )


def test_hop_limit_blocks_consolidation() -> None:
    first = _episodic(sequence=0, value=1, hop_count=1, hop_limit=1)
    second = _episodic(sequence=1, value=2, hop_count=1, hop_limit=1)
    ledger = MemoryExchangeLedger()
    for envelope in (first, second):
        ledger.append(envelope)
        ledger.record_ack(
            ExchangeAck.build(envelope, consumer_id="STORE", outcome="ACCEPTED")
        )

    with pytest.raises(RuntimeError, match="hop limit"):
        build_consolidation_plan(
            ledger,
            source_envelope_ids=[first.envelope_id, second.envelope_id],
            producer_id="C",
            reducer_id="R",
            semantic_payload={"summary": "no"},
        )


def test_retention_tamper_and_semantic_equivalence_promotion_fail_closed() -> None:
    ledger, first, second = _ledger_with_sources()
    plan = _plan(ledger, first, second)

    bad_retention = copy.deepcopy(plan)
    bad_retention["retention_manifest"]["entries"][0]["deletion_allowed"] = True
    with pytest.raises(ValueError, match="deletion"):
        validate_consolidation_plan(bad_retention)

    bad_semantics = copy.deepcopy(plan)
    bad_semantics["derived_envelope"]["payload"]["semantic_equivalence_proven"] = True
    with pytest.raises(ValueError):
        validate_consolidation_plan(bad_semantics)


def test_plan_is_bound_to_exact_source_payload_commitments() -> None:
    ledger, first, second = _ledger_with_sources()
    plan = _plan(ledger, first, second)
    tampered = copy.deepcopy(plan)
    tampered["source_descriptors"][0]["payload_sha256"] = "0" * 64

    with pytest.raises(ValueError):
        validate_consolidation_plan(tampered)


def test_source_ack_requirement_is_bound_during_apply() -> None:
    ledger, first, second = _ledger_with_sources()
    plan = _plan(ledger, first, second)
    tampered = copy.deepcopy(plan)
    tampered["required_accepted_ack_ids"][first.envelope_id] = "pxa:" + ("0" * 64)

    with pytest.raises(ValueError):
        validate_consolidation_plan(tampered)
