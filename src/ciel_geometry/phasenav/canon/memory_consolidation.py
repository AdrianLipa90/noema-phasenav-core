"""Append-only episodic-to-semantic memory consolidation and retention.

Consolidation creates a derived SEMANTIC envelope with multiple immutable
EPISODIC parents. Source envelopes are never deleted or overwritten.
"""
from __future__ import annotations

from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence

from .memory_exchange import (
    MEMORY_EXCHANGE_AUTHORITY,
    MEMORY_EXCHANGE_EPISTEMIC,
    MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
    ExchangeOutcome,
    InformationEnvelope,
    MemoryExchangeLedger,
    MemoryLayer,
)

CONSOLIDATION_VERSION = "0.1.0"
CONSOLIDATION_PLAN_SCHEMA = "PHASENAV_MEMORY_CONSOLIDATION_PLAN_V0_1"
CONSOLIDATION_RECEIPT_SCHEMA = "PHASENAV_MEMORY_CONSOLIDATION_RECEIPT_V0_1"
RETENTION_MANIFEST_SCHEMA = "PHASENAV_MEMORY_RETENTION_MANIFEST_V0_1"
DERIVED_SEMANTIC_KIND = "PHASENAV_MEMORY_CONSOLIDATED_SEMANTIC_V0_1"


class RetentionTier(str, Enum):
    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"
    PINNED = "PINNED"


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
        raise ValueError("consolidation values must be finite JSON data") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    out = value.strip()
    if not out:
        raise ValueError(f"{field} must be non-empty")
    return out


def _hex64(value: Any, field: str) -> str:
    text = _text(value, field).lower()
    if len(text) != 64:
        raise ValueError(f"{field} must be a 64-hex commitment")
    try:
        int(text, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
    return text


def _envelope_id(value: Any) -> str:
    text = _text(value, "envelope_id")
    if not text.startswith("px:"):
        raise ValueError("envelope_id must start with px:")
    _hex64(text[3:], "envelope_id commitment")
    return text


def _ack_id(value: Any) -> str:
    text = _text(value, "ack_id")
    if not text.startswith("pxa:"):
        raise ValueError("ack_id must start with pxa:")
    _hex64(text[4:], "ack_id commitment")
    return text


def _retention_tier(value: RetentionTier | str) -> RetentionTier:
    if isinstance(value, RetentionTier):
        return value
    try:
        return RetentionTier(_text(value, "retention_tier").upper())
    except ValueError as exc:
        raise ValueError("unsupported retention tier") from exc


def _source_descriptor(envelope: InformationEnvelope) -> dict[str, Any]:
    return {
        "envelope_id": envelope.envelope_id,
        "subject_id": envelope.subject_id,
        "generation_id": envelope.generation_id,
        "sequence": envelope.sequence,
        "payload_sha256": envelope.payload_sha256,
        "target_layer": envelope.target_layer.value,
    }


def _accepted_ack_map(ledger: MemoryExchangeLedger) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for ack in ledger.acknowledgements():
        if ack.outcome == ExchangeOutcome.ACCEPTED:
            out.setdefault(ack.envelope_id, []).append(ack.ack_id)
    return {key: sorted(values) for key, values in out.items()}


def _retention_manifest(
    *,
    source_ids: Sequence[str],
    derived_id: str,
    source_tier: RetentionTier,
    derived_tier: RetentionTier,
) -> dict[str, Any]:
    entries = [
        {
            "envelope_id": envelope_id,
            "role": "SOURCE",
            "retention_tier": source_tier.value,
            "deletion_allowed": False,
            "overwrite_allowed": False,
            "retrievable": True,
        }
        for envelope_id in sorted(source_ids)
    ]
    entries.append(
        {
            "envelope_id": derived_id,
            "role": "DERIVED",
            "retention_tier": derived_tier.value,
            "deletion_allowed": False,
            "overwrite_allowed": False,
            "retrievable": True,
        }
    )
    entries.sort(key=lambda row: (row["role"], row["envelope_id"]))
    core = {
        "schema": RETENTION_MANIFEST_SCHEMA,
        "version": CONSOLIDATION_VERSION,
        "entries": entries,
        "policy": "RETENTION_HINT_ONLY_NO_DELETION_AUTHORITY",
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    return {
        **core,
        "manifest_sha256": _sha256(core),
        "claims": {
            "source_preservation_required": True,
            "retention_tier_is_storage_hint": True,
            "deletion_authority": False,
            "overwrite_authority": False,
            "canon_promoted": False,
        },
    }


def build_consolidation_plan(
    ledger: MemoryExchangeLedger,
    *,
    source_envelope_ids: Sequence[str],
    producer_id: str,
    reducer_id: str,
    semantic_payload: Mapping[str, Any],
    route_edge_potentials: Sequence[float] = (),
    source_retention: RetentionTier | str = RetentionTier.COLD,
    derived_retention: RetentionTier | str = RetentionTier.HOT,
) -> dict[str, Any]:
    """Build one explicit EPISODIC -> SEMANTIC multi-parent derivation plan."""
    if isinstance(source_envelope_ids, (str, bytes)):
        raise ValueError("source_envelope_ids must be a sequence")
    source_ids = sorted({_envelope_id(value) for value in source_envelope_ids})
    if len(source_ids) < 2:
        raise ValueError("consolidation requires at least two unique EPISODIC sources")
    producer = _text(producer_id, "producer_id")
    reducer = _text(reducer_id, "reducer_id")
    if not isinstance(semantic_payload, Mapping):
        raise ValueError("semantic_payload must be a mapping")
    semantic = dict(semantic_payload)

    sources = [ledger.get_envelope(envelope_id) for envelope_id in source_ids]
    if any(source.target_layer != MemoryLayer.EPISODIC for source in sources):
        raise ValueError("all consolidation sources must target EPISODIC")
    subjects = {source.subject_id for source in sources}
    generations = {source.generation_id for source in sources}
    if len(subjects) != 1:
        raise ValueError("v0.1 consolidation sources must share one subject_id")
    if len(generations) != 1:
        raise ValueError("v0.1 consolidation sources must share one generation_id")

    accepted = _accepted_ack_map(ledger)
    required_ack_ids: dict[str, str] = {}
    for source in sources:
        candidates = accepted.get(source.envelope_id, ())
        if not candidates:
            raise RuntimeError(
                "every EPISODIC consolidation source requires at least one ACCEPTED ACK"
            )
        required_ack_ids[source.envelope_id] = candidates[0]

    hop_limit = min(source.hop_limit for source in sources)
    hop_count = max(source.hop_count for source in sources) + 1
    if hop_count > hop_limit:
        raise RuntimeError("consolidation would exceed source hop limit")

    sequence = max(source.sequence for source in sources) + 1
    provenance = sorted(
        {
            *(
                item
                for source in sources
                for item in source.provenance
            ),
            f"consolidation-reducer:{reducer}",
        }
    )
    dependencies = sorted(
        {
            *(
                item
                for source in sources
                for item in source.dependencies
            ),
            *(f"source:{source.envelope_id}" for source in sources),
            *(f"ack:{required_ack_ids[source.envelope_id]}" for source in sources),
        }
    )
    derived_payload = {
        "kind": DERIVED_SEMANTIC_KIND,
        "derivation_mode": "CALLER_SUPPLIED_SEMANTIC_REDUCTION",
        "reducer_id": reducer,
        "source_envelope_ids": source_ids,
        "source_payload_sha256": {
            source.envelope_id: source.payload_sha256 for source in sources
        },
        "semantic_payload": semantic,
        "semantic_equivalence_proven": False,
    }
    derived = InformationEnvelope.build(
        subject_id=next(iter(subjects)),
        producer_id=producer,
        generation_id=next(iter(generations)),
        sequence=sequence,
        source_layer=MemoryLayer.EPISODIC,
        target_layer=MemoryLayer.SEMANTIC,
        payload=derived_payload,
        parent_envelope_ids=source_ids,
        provenance=provenance,
        dependencies=dependencies,
        route_edge_potentials=route_edge_potentials,
        hop_count=hop_count,
        hop_limit=hop_limit,
    )
    retention = _retention_manifest(
        source_ids=source_ids,
        derived_id=derived.envelope_id,
        source_tier=_retention_tier(source_retention),
        derived_tier=_retention_tier(derived_retention),
    )
    source_descriptors = [_source_descriptor(source) for source in sources]
    source_descriptors.sort(key=lambda row: (row["sequence"], row["envelope_id"]))
    core = {
        "schema": CONSOLIDATION_PLAN_SCHEMA,
        "version": CONSOLIDATION_VERSION,
        "subject_id": derived.subject_id,
        "generation_id": derived.generation_id,
        "producer_id": producer,
        "reducer_id": reducer,
        "source_descriptors": source_descriptors,
        "required_accepted_ack_ids": required_ack_ids,
        "derived_envelope": derived.to_packet(),
        "retention_manifest": retention,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    return {
        **core,
        "plan_sha256": _sha256(core),
        "claims": {
            "multi_parent_derivation": True,
            "source_immutability_required": True,
            "source_deletion_authority": False,
            "source_overwrite_authority": False,
            "semantic_equivalence_proven": False,
            "reducer_identity_authenticated": False,
            "canon_promoted": False,
        },
    }


def _validate_retention_manifest(
    packet: Mapping[str, Any],
    *,
    expected_source_ids: Sequence[str],
    expected_derived_id: str,
) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        raise ValueError("retention_manifest must be a mapping")
    row = dict(packet)
    if row.get("schema") != RETENTION_MANIFEST_SCHEMA or row.get("version") != CONSOLIDATION_VERSION:
        raise ValueError("unsupported retention manifest")
    raw_entries = row.get("entries")
    if not isinstance(raw_entries, Sequence) or isinstance(raw_entries, (str, bytes)):
        raise ValueError("retention entries must be a sequence")
    entries = []
    seen: set[str] = set()
    source_ids: set[str] = set()
    derived_ids: set[str] = set()
    for raw in raw_entries:
        if not isinstance(raw, Mapping):
            raise ValueError("retention entry must be a mapping")
        item = dict(raw)
        envelope_id = _envelope_id(item.get("envelope_id"))
        if envelope_id in seen:
            raise ValueError("duplicate retention envelope_id")
        seen.add(envelope_id)
        role = _text(item.get("role"), "role").upper()
        if role not in {"SOURCE", "DERIVED"}:
            raise ValueError("unsupported retention role")
        tier = _retention_tier(item.get("retention_tier")).value
        if item.get("deletion_allowed") is not False:
            raise ValueError("retention manifest cannot grant deletion authority")
        if item.get("overwrite_allowed") is not False:
            raise ValueError("retention manifest cannot grant overwrite authority")
        if item.get("retrievable") is not True:
            raise ValueError("all retained envelopes must remain retrievable")
        if role == "SOURCE":
            source_ids.add(envelope_id)
        else:
            derived_ids.add(envelope_id)
        entries.append({
            "envelope_id": envelope_id,
            "role": role,
            "retention_tier": tier,
            "deletion_allowed": False,
            "overwrite_allowed": False,
            "retrievable": True,
        })
    if source_ids != set(expected_source_ids):
        raise ValueError("retention manifest source set mismatch")
    if derived_ids != {expected_derived_id}:
        raise ValueError("retention manifest derived set mismatch")
    entries.sort(key=lambda item: (item["role"], item["envelope_id"]))
    core = {
        "schema": RETENTION_MANIFEST_SCHEMA,
        "version": CONSOLIDATION_VERSION,
        "entries": entries,
        "policy": "RETENTION_HINT_ONLY_NO_DELETION_AUTHORITY",
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    manifest_sha = _sha256(core)
    if row.get("manifest_sha256") != manifest_sha:
        raise ValueError("retention manifest commitment mismatch")
    claims = row.get("claims")
    if not isinstance(claims, Mapping):
        raise ValueError("retention claims must be a mapping")
    if claims.get("source_preservation_required") is not True:
        raise ValueError("source preservation must remain required")
    if claims.get("retention_tier_is_storage_hint") is not True:
        raise ValueError("retention tier must remain a storage hint")
    for key in ("deletion_authority", "overwrite_authority", "canon_promoted"):
        if claims.get(key) is not False:
            raise ValueError(f"retention claim must remain false: {key}")
    return {**core, "manifest_sha256": manifest_sha, "claims": dict(claims)}


def validate_consolidation_plan(packet: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        raise ValueError("consolidation plan must be a mapping")
    row = dict(packet)
    if row.get("schema") != CONSOLIDATION_PLAN_SCHEMA or row.get("version") != CONSOLIDATION_VERSION:
        raise ValueError("unsupported consolidation plan")
    subject = _text(row.get("subject_id"), "subject_id")
    generation = _text(row.get("generation_id"), "generation_id")
    producer = _text(row.get("producer_id"), "producer_id")
    reducer = _text(row.get("reducer_id"), "reducer_id")
    raw_sources = row.get("source_descriptors")
    if not isinstance(raw_sources, Sequence) or isinstance(raw_sources, (str, bytes)):
        raise ValueError("source_descriptors must be a sequence")
    if len(raw_sources) < 2:
        raise ValueError("consolidation requires at least two source descriptors")
    descriptors = []
    source_ids: list[str] = []
    source_sequences: list[int] = []
    for raw in raw_sources:
        if not isinstance(raw, Mapping):
            raise ValueError("source descriptor must be a mapping")
        desc = dict(raw)
        envelope_id = _envelope_id(desc.get("envelope_id"))
        if envelope_id in source_ids:
            raise ValueError("duplicate consolidation source")
        if _text(desc.get("subject_id"), "source.subject_id") != subject:
            raise ValueError("source subject_id mismatch")
        if _text(desc.get("generation_id"), "source.generation_id") != generation:
            raise ValueError("source generation_id mismatch")
        sequence = desc.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ValueError("source sequence must be non-negative")
        payload_sha = _hex64(desc.get("payload_sha256"), "source.payload_sha256")
        if _text(desc.get("target_layer"), "source.target_layer").upper() != "EPISODIC":
            raise ValueError("consolidation source must target EPISODIC")
        descriptors.append({
            "envelope_id": envelope_id,
            "subject_id": subject,
            "generation_id": generation,
            "sequence": sequence,
            "payload_sha256": payload_sha,
            "target_layer": "EPISODIC",
        })
        source_ids.append(envelope_id)
        source_sequences.append(sequence)
    descriptors.sort(key=lambda item: (item["sequence"], item["envelope_id"]))
    if list(raw_sources) != descriptors:
        raise ValueError("source_descriptors must be canonical and sorted")

    raw_acks = row.get("required_accepted_ack_ids")
    if not isinstance(raw_acks, Mapping) or set(raw_acks) != set(source_ids):
        raise ValueError("required_accepted_ack_ids must cover every source")
    required_acks = {
        envelope_id: _ack_id(raw_acks[envelope_id])
        for envelope_id in sorted(source_ids)
    }

    derived_raw = row.get("derived_envelope")
    if not isinstance(derived_raw, Mapping):
        raise ValueError("derived_envelope must be a mapping")
    derived = InformationEnvelope.from_packet(derived_raw)
    if derived.subject_id != subject or derived.generation_id != generation:
        raise ValueError("derived envelope subject/generation mismatch")
    if derived.source_layer != MemoryLayer.EPISODIC or derived.target_layer != MemoryLayer.SEMANTIC:
        raise ValueError("derived envelope must be EPISODIC -> SEMANTIC")
    if set(derived.parent_envelope_ids) != set(source_ids):
        raise ValueError("derived envelope parent set mismatch")
    if derived.sequence <= max(source_sequences):
        raise ValueError("derived sequence must exceed all source sequences")
    if derived.producer_id != producer:
        raise ValueError("derived producer_id mismatch")
    payload = dict(derived.payload)
    if payload.get("kind") != DERIVED_SEMANTIC_KIND:
        raise ValueError("derived payload kind mismatch")
    if payload.get("derivation_mode") != "CALLER_SUPPLIED_SEMANTIC_REDUCTION":
        raise ValueError("unsupported derivation mode")
    if payload.get("reducer_id") != reducer:
        raise ValueError("derived reducer_id mismatch")
    if payload.get("source_envelope_ids") != sorted(source_ids):
        raise ValueError("derived source_envelope_ids mismatch")
    if payload.get("semantic_equivalence_proven") is not False:
        raise ValueError("semantic equivalence must remain unproven")
    source_payloads = payload.get("source_payload_sha256")
    if not isinstance(source_payloads, Mapping):
        raise ValueError("source_payload_sha256 must be a mapping")
    expected_payloads = {
        desc["envelope_id"]: desc["payload_sha256"] for desc in descriptors
    }
    if dict(source_payloads) != expected_payloads:
        raise ValueError("derived source payload commitments mismatch")
    if not isinstance(payload.get("semantic_payload"), Mapping):
        raise ValueError("semantic_payload must be a mapping")

    retention = _validate_retention_manifest(
        row.get("retention_manifest"),
        expected_source_ids=source_ids,
        expected_derived_id=derived.envelope_id,
    )
    if row.get("authentication") != MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION:
        raise ValueError("consolidation authentication boundary mismatch")
    if row.get("epistemic") != MEMORY_EXCHANGE_EPISTEMIC or row.get("authority") != MEMORY_EXCHANGE_AUTHORITY:
        raise ValueError("consolidation epistemic/authority mismatch")
    if row.get("canon_allowed") is not False:
        raise ValueError("consolidation must remain canon_allowed=false")
    core = {
        "schema": CONSOLIDATION_PLAN_SCHEMA,
        "version": CONSOLIDATION_VERSION,
        "subject_id": subject,
        "generation_id": generation,
        "producer_id": producer,
        "reducer_id": reducer,
        "source_descriptors": descriptors,
        "required_accepted_ack_ids": required_acks,
        "derived_envelope": derived.to_packet(),
        "retention_manifest": retention,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    plan_sha = _sha256(core)
    if row.get("plan_sha256") != plan_sha:
        raise ValueError("consolidation plan commitment mismatch")
    claims = row.get("claims")
    if not isinstance(claims, Mapping):
        raise ValueError("consolidation claims must be a mapping")
    if claims.get("multi_parent_derivation") is not True:
        raise ValueError("multi_parent_derivation must be true")
    if claims.get("source_immutability_required") is not True:
        raise ValueError("source immutability must remain required")
    if claims.get("semantic_equivalence_proven") is not False:
        raise ValueError("semantic equivalence must remain unproven")
    for key in (
        "source_deletion_authority",
        "source_overwrite_authority",
        "reducer_identity_authenticated",
        "canon_promoted",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"consolidation claim must remain false: {key}")
    return {
        **core,
        "plan_sha256": plan_sha,
        "claims": dict(claims),
        "_derived": derived,
    }


def apply_consolidation(
    ledger: MemoryExchangeLedger,
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Append the derived SEMANTIC envelope after full source/ACK preflight."""
    validated = validate_consolidation_plan(plan)
    source_ids = [row["envelope_id"] for row in validated["source_descriptors"]]
    ledger_acks = {ack.ack_id: ack for ack in ledger.acknowledgements()}

    for descriptor in validated["source_descriptors"]:
        source = ledger.get_envelope(descriptor["envelope_id"])
        if _source_descriptor(source) != descriptor:
            raise RuntimeError("consolidation source changed or descriptor mismatch")
        required_ack_id = validated["required_accepted_ack_ids"][source.envelope_id]
        ack = ledger_acks.get(required_ack_id)
        if ack is None:
            raise RuntimeError("required source ACK is absent from ledger")
        if ack.envelope_id != source.envelope_id or ack.outcome != ExchangeOutcome.ACCEPTED:
            raise RuntimeError("required source ACK is not an ACCEPTED ACK for its source")

    before = ledger.snapshot()
    derived: InformationEnvelope = validated["_derived"]
    created = ledger.append(derived)
    after = ledger.snapshot()
    core = {
        "schema": CONSOLIDATION_RECEIPT_SCHEMA,
        "version": CONSOLIDATION_VERSION,
        "status": "APPLIED" if created else "ALREADY_APPLIED",
        "created": created,
        "plan_sha256": validated["plan_sha256"],
        "derived_envelope_id": derived.envelope_id,
        "derived_payload_sha256": derived.payload_sha256,
        "source_envelope_ids": sorted(source_ids),
        "source_count": len(source_ids),
        "retention_manifest_sha256": validated["retention_manifest"]["manifest_sha256"],
        "before_ledger_sha256": before["ledger_sha256"],
        "after_ledger_sha256": after["ledger_sha256"],
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    return {
        **core,
        "receipt_sha256": _sha256(core),
        "derived_envelope": derived.to_packet(),
        "retention_manifest": validated["retention_manifest"],
        "claims": {
            "sources_preserved": all(
                ledger.get_envelope(envelope_id).envelope_id == envelope_id
                for envelope_id in source_ids
            ),
            "derived_semantic_is_additive": True,
            "semantic_equivalence_proven": False,
            "deletion_performed": False,
            "overwrite_performed": False,
            "canon_promoted": False,
        },
    }


__all__ = [
    "CONSOLIDATION_PLAN_SCHEMA",
    "CONSOLIDATION_RECEIPT_SCHEMA",
    "CONSOLIDATION_VERSION",
    "DERIVED_SEMANTIC_KIND",
    "RETENTION_MANIFEST_SCHEMA",
    "RetentionTier",
    "apply_consolidation",
    "build_consolidation_plan",
    "validate_consolidation_plan",
]
