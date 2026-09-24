"""Bucketed anti-entropy synchronization for PhaseNav memory ledgers.

The protocol discovers set differences by commitments first and transfers only
missing envelopes/ACKs. It is append-only: no remote item can overwrite or
delete a local item.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .memory_exchange import (
    MEMORY_EXCHANGE_AUTHORITY,
    MEMORY_EXCHANGE_EPISTEMIC,
    MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
    ExchangeAck,
    InformationEnvelope,
    MemoryExchangeLedger,
)

SYNC_VERSION = "0.1.0"
SYNC_INVENTORY_SCHEMA = "PHASENAV_MEMORY_ANTI_ENTROPY_INVENTORY_V0_1"
SYNC_MANIFEST_SCHEMA = "PHASENAV_MEMORY_ANTI_ENTROPY_BUCKET_MANIFEST_V0_1"
SYNC_PLAN_SCHEMA = "PHASENAV_MEMORY_ANTI_ENTROPY_DELTA_PLAN_V0_1"
SYNC_DELTA_SCHEMA = "PHASENAV_MEMORY_ANTI_ENTROPY_DELTA_V0_1"
SYNC_BUCKET_HEX_WIDTH = 2


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
        raise ValueError("sync values must be finite JSON data") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    out = value.strip()
    if not out:
        raise ValueError(f"{field} must be non-empty")
    return out


def _hex_commitment(value: Any, field: str) -> str:
    text = _text(value, field)
    if len(text) != 64:
        raise ValueError(f"{field} must be a 64-hex commitment")
    try:
        int(text, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc
    return text.lower()


def _item_digest(item_id: str, prefix: str) -> str:
    text = _text(item_id, "item_id")
    if not text.startswith(prefix):
        raise ValueError(f"item id must start with {prefix}")
    return _hex_commitment(text[len(prefix):], "item_id commitment")


def _bucket_for(item_id: str) -> str:
    if item_id.startswith("pxa:"):
        digest = _item_digest(item_id, "pxa:")
    elif item_id.startswith("px:"):
        digest = _item_digest(item_id, "px:")
    else:
        raise ValueError("unsupported anti-entropy item id")
    return digest[:SYNC_BUCKET_HEX_WIDTH]


def _prefix(value: Any) -> str:
    text = _text(value, "bucket_prefix").lower()
    if len(text) != SYNC_BUCKET_HEX_WIDTH:
        raise ValueError("bucket prefix must be exactly two hex characters")
    try:
        int(text, 16)
    except ValueError as exc:
        raise ValueError("bucket prefix must be hexadecimal") from exc
    return text


def _envelope_descriptor(envelope: InformationEnvelope) -> dict[str, Any]:
    return {
        "envelope_id": envelope.envelope_id,
        "payload_sha256": envelope.payload_sha256,
        "generation_id": envelope.generation_id,
        "sequence": envelope.sequence,
        "parent_envelope_ids": list(envelope.parent_envelope_ids),
        "target_layer": envelope.target_layer.value,
    }


def _ack_descriptor(ack: ExchangeAck) -> dict[str, Any]:
    return {
        "ack_id": ack.ack_id,
        "envelope_id": ack.envelope_id,
        "consumer_id": ack.consumer_id,
        "outcome": ack.outcome.value,
    }


def _bucket_payload(
    prefix: str,
    envelopes: Sequence[dict[str, Any]],
    acks: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "prefix": _prefix(prefix),
        "envelopes": sorted(envelopes, key=lambda row: row["envelope_id"]),
        "acks": sorted(acks, key=lambda row: row["ack_id"]),
    }


def _bucket_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    envelopes = list(payload["envelopes"])
    acks = list(payload["acks"])
    return {
        "envelope_count": len(envelopes),
        "ack_count": len(acks),
        "root_sha256": _sha256(dict(payload)),
    }


def _ledger_bucket_payloads(ledger: MemoryExchangeLedger) -> dict[str, dict[str, Any]]:
    env_by_bucket: dict[str, list[dict[str, Any]]] = {}
    ack_by_bucket: dict[str, list[dict[str, Any]]] = {}
    for envelope in ledger.envelopes():
        env_by_bucket.setdefault(_bucket_for(envelope.envelope_id), []).append(
            _envelope_descriptor(envelope)
        )
    for ack in ledger.acknowledgements():
        ack_by_bucket.setdefault(_bucket_for(ack.ack_id), []).append(_ack_descriptor(ack))
    prefixes = sorted(set(env_by_bucket) | set(ack_by_bucket))
    return {
        prefix: _bucket_payload(
            prefix,
            env_by_bucket.get(prefix, ()),
            ack_by_bucket.get(prefix, ()),
        )
        for prefix in prefixes
    }


def build_inventory(
    ledger: MemoryExchangeLedger,
    *,
    node_id: str,
) -> dict[str, Any]:
    """Build a compact anti-entropy summary over all non-empty commitment buckets."""
    node = _text(node_id, "node_id")
    payloads = _ledger_bucket_payloads(ledger)
    buckets = {
        prefix: _bucket_summary(payload)
        for prefix, payload in payloads.items()
    }
    snapshot = ledger.snapshot()
    content_core = {
        "envelope_count": ledger.envelope_count,
        "ack_count": ledger.ack_count,
        "ledger_sha256": snapshot["ledger_sha256"],
        "buckets": buckets,
    }
    core = {
        "schema": SYNC_INVENTORY_SCHEMA,
        "version": SYNC_VERSION,
        "node_id": node,
        "content_root_sha256": _sha256(content_core),
        **content_core,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    return {
        **core,
        "inventory_sha256": _sha256(core),
        "claims": {
            "set_reconciliation_only": True,
            "node_identity_authenticated": False,
            "deletion_authority": False,
            "overwrite_authority": False,
            "canon_promoted": False,
        },
    }


def validate_inventory(packet: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        raise ValueError("inventory must be a mapping")
    row = dict(packet)
    if row.get("schema") != SYNC_INVENTORY_SCHEMA or row.get("version") != SYNC_VERSION:
        raise ValueError("unsupported anti-entropy inventory")
    node = _text(row.get("node_id"), "node_id")
    if row.get("authentication") != MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION:
        raise ValueError("inventory authentication boundary mismatch")
    if row.get("epistemic") != MEMORY_EXCHANGE_EPISTEMIC:
        raise ValueError("inventory must remain epistemic=CHYBA")
    if row.get("authority") != MEMORY_EXCHANGE_AUTHORITY:
        raise ValueError("inventory must remain SHARED_COGNITION_ONLY")
    if row.get("canon_allowed") is not False:
        raise ValueError("inventory must remain canon_allowed=false")

    envelope_count = row.get("envelope_count")
    ack_count = row.get("ack_count")
    if isinstance(envelope_count, bool) or not isinstance(envelope_count, int) or envelope_count < 0:
        raise ValueError("envelope_count must be a non-negative integer")
    if isinstance(ack_count, bool) or not isinstance(ack_count, int) or ack_count < 0:
        raise ValueError("ack_count must be a non-negative integer")
    ledger_sha = _hex_commitment(row.get("ledger_sha256"), "ledger_sha256")

    raw_buckets = row.get("buckets")
    if not isinstance(raw_buckets, Mapping):
        raise ValueError("buckets must be a mapping")
    buckets: dict[str, dict[str, Any]] = {}
    env_total = 0
    ack_total = 0
    for raw_prefix, raw_summary in raw_buckets.items():
        prefix = _prefix(raw_prefix)
        if not isinstance(raw_summary, Mapping):
            raise ValueError("bucket summary must be a mapping")
        env_n = raw_summary.get("envelope_count")
        ack_n = raw_summary.get("ack_count")
        if isinstance(env_n, bool) or not isinstance(env_n, int) or env_n < 0:
            raise ValueError("bucket envelope_count must be non-negative")
        if isinstance(ack_n, bool) or not isinstance(ack_n, int) or ack_n < 0:
            raise ValueError("bucket ack_count must be non-negative")
        root = _hex_commitment(raw_summary.get("root_sha256"), "bucket root_sha256")
        if env_n == 0 and ack_n == 0:
            raise ValueError("empty buckets must be omitted from inventory")
        buckets[prefix] = {
            "envelope_count": env_n,
            "ack_count": ack_n,
            "root_sha256": root,
        }
        env_total += env_n
        ack_total += ack_n
    if env_total != envelope_count or ack_total != ack_count:
        raise ValueError("inventory item counts do not match bucket totals")

    content_core = {
        "envelope_count": envelope_count,
        "ack_count": ack_count,
        "ledger_sha256": ledger_sha,
        "buckets": buckets,
    }
    content_root = _sha256(content_core)
    if row.get("content_root_sha256") != content_root:
        raise ValueError("content_root_sha256 mismatch")
    core = {
        "schema": SYNC_INVENTORY_SCHEMA,
        "version": SYNC_VERSION,
        "node_id": node,
        "content_root_sha256": content_root,
        **content_core,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    inventory_sha = _sha256(core)
    if row.get("inventory_sha256") != inventory_sha:
        raise ValueError("inventory_sha256 mismatch")
    claims = row.get("claims")
    if not isinstance(claims, Mapping):
        raise ValueError("inventory claims must be a mapping")
    if claims.get("set_reconciliation_only") is not True:
        raise ValueError("set_reconciliation_only must remain true")
    for key in ("node_identity_authenticated", "deletion_authority", "overwrite_authority", "canon_promoted"):
        if claims.get(key) is not False:
            raise ValueError(f"inventory claim must remain false: {key}")
    return {**core, "inventory_sha256": inventory_sha, "claims": dict(claims)}


def divergent_buckets(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> tuple[str, ...]:
    a = validate_inventory(left)
    b = validate_inventory(right)
    prefixes = sorted(set(a["buckets"]) | set(b["buckets"]))
    out = []
    for prefix in prefixes:
        av = a["buckets"].get(prefix)
        bv = b["buckets"].get(prefix)
        if av != bv:
            out.append(prefix)
    return tuple(out)


def build_bucket_manifest(
    ledger: MemoryExchangeLedger,
    *,
    node_id: str,
    prefixes: Sequence[str],
) -> dict[str, Any]:
    inventory = build_inventory(ledger, node_id=node_id)
    normalized_prefixes = tuple(sorted({_prefix(prefix) for prefix in prefixes}))
    payloads = _ledger_bucket_payloads(ledger)
    buckets: dict[str, dict[str, Any]] = {}
    for prefix in normalized_prefixes:
        payload = payloads.get(prefix, _bucket_payload(prefix, (), ()))
        buckets[prefix] = {
            **payload,
            **_bucket_summary(payload),
        }
    core = {
        "schema": SYNC_MANIFEST_SCHEMA,
        "version": SYNC_VERSION,
        "node_id": inventory["node_id"],
        "inventory_sha256": inventory["inventory_sha256"],
        "prefixes": list(normalized_prefixes),
        "buckets": buckets,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    return {
        **core,
        "manifest_sha256": _sha256(core),
        "claims": {
            "metadata_only": True,
            "payload_transferred": False,
            "node_identity_authenticated": False,
            "deletion_authority": False,
            "overwrite_authority": False,
        },
    }


def validate_bucket_manifest(
    packet: Mapping[str, Any],
    inventory: Mapping[str, Any],
) -> dict[str, Any]:
    inv = validate_inventory(inventory)
    if not isinstance(packet, Mapping):
        raise ValueError("manifest must be a mapping")
    row = dict(packet)
    if row.get("schema") != SYNC_MANIFEST_SCHEMA or row.get("version") != SYNC_VERSION:
        raise ValueError("unsupported anti-entropy manifest")
    if _text(row.get("node_id"), "node_id") != inv["node_id"]:
        raise ValueError("manifest node_id does not match inventory")
    if row.get("inventory_sha256") != inv["inventory_sha256"]:
        raise ValueError("manifest is not bound to supplied inventory")
    if row.get("authentication") != MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION:
        raise ValueError("manifest authentication boundary mismatch")
    if row.get("epistemic") != MEMORY_EXCHANGE_EPISTEMIC or row.get("authority") != MEMORY_EXCHANGE_AUTHORITY:
        raise ValueError("manifest epistemic/authority mismatch")
    if row.get("canon_allowed") is not False:
        raise ValueError("manifest must remain canon_allowed=false")

    raw_prefixes = row.get("prefixes")
    if not isinstance(raw_prefixes, Sequence) or isinstance(raw_prefixes, (str, bytes)):
        raise ValueError("manifest prefixes must be a sequence")
    prefixes = tuple(sorted({_prefix(prefix) for prefix in raw_prefixes}))
    if list(prefixes) != list(raw_prefixes):
        raise ValueError("manifest prefixes must be unique and sorted")
    raw_buckets = row.get("buckets")
    if not isinstance(raw_buckets, Mapping) or set(raw_buckets) != set(prefixes):
        raise ValueError("manifest bucket keys must equal prefixes")

    buckets: dict[str, dict[str, Any]] = {}
    for prefix in prefixes:
        raw = raw_buckets[prefix]
        if not isinstance(raw, Mapping):
            raise ValueError("manifest bucket must be a mapping")
        raw_env = raw.get("envelopes")
        raw_acks = raw.get("acks")
        if not isinstance(raw_env, Sequence) or isinstance(raw_env, (str, bytes)):
            raise ValueError("manifest envelopes must be a sequence")
        if not isinstance(raw_acks, Sequence) or isinstance(raw_acks, (str, bytes)):
            raise ValueError("manifest acks must be a sequence")
        envelopes = []
        env_ids: set[str] = set()
        for descriptor in raw_env:
            if not isinstance(descriptor, Mapping):
                raise ValueError("envelope descriptor must be a mapping")
            desc = dict(descriptor)
            envelope_id = _text(desc.get("envelope_id"), "envelope_id")
            if _bucket_for(envelope_id) != prefix or envelope_id in env_ids:
                raise ValueError("invalid or duplicate envelope descriptor")
            _hex_commitment(desc.get("payload_sha256"), "payload_sha256")
            _text(desc.get("generation_id"), "generation_id")
            sequence = desc.get("sequence")
            if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
                raise ValueError("descriptor sequence must be non-negative")
            parents = desc.get("parent_envelope_ids")
            if not isinstance(parents, Sequence) or isinstance(parents, (str, bytes)):
                raise ValueError("parent_envelope_ids must be a sequence")
            for parent_id in parents:
                _item_digest(parent_id, "px:")
            _text(desc.get("target_layer"), "target_layer")
            env_ids.add(envelope_id)
            envelopes.append(desc)
        acks = []
        ack_ids: set[str] = set()
        for descriptor in raw_acks:
            if not isinstance(descriptor, Mapping):
                raise ValueError("ACK descriptor must be a mapping")
            desc = dict(descriptor)
            ack_id = _text(desc.get("ack_id"), "ack_id")
            if _bucket_for(ack_id) != prefix or ack_id in ack_ids:
                raise ValueError("invalid or duplicate ACK descriptor")
            _item_digest(_text(desc.get("envelope_id"), "envelope_id"), "px:")
            _text(desc.get("consumer_id"), "consumer_id")
            _text(desc.get("outcome"), "outcome")
            ack_ids.add(ack_id)
            acks.append(desc)
        payload = _bucket_payload(prefix, envelopes, acks)
        summary = _bucket_summary(payload)
        if raw.get("envelope_count") != summary["envelope_count"]:
            raise ValueError("manifest envelope_count mismatch")
        if raw.get("ack_count") != summary["ack_count"]:
            raise ValueError("manifest ack_count mismatch")
        if raw.get("root_sha256") != summary["root_sha256"]:
            raise ValueError("manifest bucket root mismatch")
        inventory_summary = inv["buckets"].get(prefix)
        if inventory_summary is None:
            if summary["envelope_count"] or summary["ack_count"]:
                raise ValueError("manifest contains items absent from inventory")
        elif inventory_summary != summary:
            raise ValueError("manifest bucket does not match inventory root/counts")
        buckets[prefix] = {**payload, **summary}

    core = {
        "schema": SYNC_MANIFEST_SCHEMA,
        "version": SYNC_VERSION,
        "node_id": inv["node_id"],
        "inventory_sha256": inv["inventory_sha256"],
        "prefixes": list(prefixes),
        "buckets": buckets,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    manifest_sha = _sha256(core)
    if row.get("manifest_sha256") != manifest_sha:
        raise ValueError("manifest_sha256 mismatch")
    claims = row.get("claims")
    if not isinstance(claims, Mapping):
        raise ValueError("manifest claims must be a mapping")
    if claims.get("metadata_only") is not True or claims.get("payload_transferred") is not False:
        raise ValueError("manifest must remain metadata-only")
    for key in ("node_identity_authenticated", "deletion_authority", "overwrite_authority"):
        if claims.get(key) is not False:
            raise ValueError(f"manifest claim must remain false: {key}")
    return {**core, "manifest_sha256": manifest_sha, "claims": dict(claims)}


def plan_delta(
    sender_inventory: Mapping[str, Any],
    receiver_inventory: Mapping[str, Any],
    sender_manifest: Mapping[str, Any],
    receiver_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    sender_inv = validate_inventory(sender_inventory)
    receiver_inv = validate_inventory(receiver_inventory)
    prefixes = divergent_buckets(sender_inv, receiver_inv)
    sender_man = validate_bucket_manifest(sender_manifest, sender_inv)
    receiver_man = validate_bucket_manifest(receiver_manifest, receiver_inv)
    if tuple(sender_man["prefixes"]) != prefixes or tuple(receiver_man["prefixes"]) != prefixes:
        raise ValueError("both manifests must cover exactly all divergent buckets")

    sender_env: dict[str, dict[str, Any]] = {}
    receiver_env: dict[str, dict[str, Any]] = {}
    sender_ack: dict[str, dict[str, Any]] = {}
    receiver_ack: dict[str, dict[str, Any]] = {}
    for prefix in prefixes:
        for desc in sender_man["buckets"][prefix]["envelopes"]:
            sender_env[desc["envelope_id"]] = desc
        for desc in receiver_man["buckets"][prefix]["envelopes"]:
            receiver_env[desc["envelope_id"]] = desc
        for desc in sender_man["buckets"][prefix]["acks"]:
            sender_ack[desc["ack_id"]] = desc
        for desc in receiver_man["buckets"][prefix]["acks"]:
            receiver_ack[desc["ack_id"]] = desc

    for item_id in sorted(set(sender_env) & set(receiver_env)):
        if sender_env[item_id] != receiver_env[item_id]:
            raise RuntimeError("same envelope commitment has different descriptor")
    for item_id in sorted(set(sender_ack) & set(receiver_ack)):
        if sender_ack[item_id] != receiver_ack[item_id]:
            raise RuntimeError("same ACK commitment has different descriptor")

    send_envelopes = sorted(set(sender_env) - set(receiver_env))
    send_acks = sorted(set(sender_ack) - set(receiver_ack))
    receiver_only_envelopes = sorted(set(receiver_env) - set(sender_env))
    receiver_only_acks = sorted(set(receiver_ack) - set(sender_ack))
    core = {
        "schema": SYNC_PLAN_SCHEMA,
        "version": SYNC_VERSION,
        "sender_node_id": sender_inv["node_id"],
        "receiver_node_id": receiver_inv["node_id"],
        "sender_inventory_sha256": sender_inv["inventory_sha256"],
        "receiver_inventory_sha256": receiver_inv["inventory_sha256"],
        "divergent_prefixes": list(prefixes),
        "send_envelope_ids": send_envelopes,
        "send_ack_ids": send_acks,
        "receiver_only_envelope_ids": receiver_only_envelopes,
        "receiver_only_ack_ids": receiver_only_acks,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    return {
        **core,
        "plan_sha256": _sha256(core),
        "claims": {
            "append_only_delta": True,
            "delete_receiver_only_items": False,
            "overwrite_receiver_items": False,
            "node_identity_authenticated": False,
            "canon_promoted": False,
        },
    }


def validate_plan(packet: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        raise ValueError("delta plan must be a mapping")
    row = dict(packet)
    if row.get("schema") != SYNC_PLAN_SCHEMA or row.get("version") != SYNC_VERSION:
        raise ValueError("unsupported anti-entropy delta plan")
    sender = _text(row.get("sender_node_id"), "sender_node_id")
    receiver = _text(row.get("receiver_node_id"), "receiver_node_id")
    sender_inventory = _hex_commitment(row.get("sender_inventory_sha256"), "sender_inventory_sha256")
    receiver_inventory = _hex_commitment(row.get("receiver_inventory_sha256"), "receiver_inventory_sha256")
    raw_prefixes = row.get("divergent_prefixes")
    if not isinstance(raw_prefixes, Sequence) or isinstance(raw_prefixes, (str, bytes)):
        raise ValueError("divergent_prefixes must be a sequence")
    prefixes = tuple(sorted({_prefix(prefix) for prefix in raw_prefixes}))
    if list(prefixes) != list(raw_prefixes):
        raise ValueError("divergent_prefixes must be unique and sorted")

    def ids(field: str, item_prefix: str) -> list[str]:
        raw = row.get(field)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ValueError(f"{field} must be a sequence")
        out = sorted({_text(item, field) for item in raw})
        if out != list(raw):
            raise ValueError(f"{field} must be unique and sorted")
        for item in out:
            _item_digest(item, item_prefix)
        return out

    send_envelopes = ids("send_envelope_ids", "px:")
    send_acks = ids("send_ack_ids", "pxa:")
    receiver_env = ids("receiver_only_envelope_ids", "px:")
    receiver_acks = ids("receiver_only_ack_ids", "pxa:")
    if row.get("authentication") != MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION:
        raise ValueError("plan authentication boundary mismatch")
    if row.get("epistemic") != MEMORY_EXCHANGE_EPISTEMIC or row.get("authority") != MEMORY_EXCHANGE_AUTHORITY:
        raise ValueError("plan epistemic/authority mismatch")
    if row.get("canon_allowed") is not False:
        raise ValueError("plan must remain canon_allowed=false")
    core = {
        "schema": SYNC_PLAN_SCHEMA,
        "version": SYNC_VERSION,
        "sender_node_id": sender,
        "receiver_node_id": receiver,
        "sender_inventory_sha256": sender_inventory,
        "receiver_inventory_sha256": receiver_inventory,
        "divergent_prefixes": list(prefixes),
        "send_envelope_ids": send_envelopes,
        "send_ack_ids": send_acks,
        "receiver_only_envelope_ids": receiver_env,
        "receiver_only_ack_ids": receiver_acks,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    plan_sha = _sha256(core)
    if row.get("plan_sha256") != plan_sha:
        raise ValueError("plan_sha256 mismatch")
    claims = row.get("claims")
    if not isinstance(claims, Mapping) or claims.get("append_only_delta") is not True:
        raise ValueError("plan must remain append-only")
    for key in ("delete_receiver_only_items", "overwrite_receiver_items", "node_identity_authenticated", "canon_promoted"):
        if claims.get(key) is not False:
            raise ValueError(f"plan claim must remain false: {key}")
    return {**core, "plan_sha256": plan_sha, "claims": dict(claims)}


def export_delta(
    ledger: MemoryExchangeLedger,
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    validated = validate_plan(plan)
    envelope_packets = []
    for envelope_id in validated["send_envelope_ids"]:
        envelope_packets.append(ledger.get_envelope(envelope_id).to_packet())
    envelope_packets.sort(key=lambda row: (row["sequence"], row["envelope_id"]))

    ack_map = {ack.ack_id: ack for ack in ledger.acknowledgements()}
    ack_packets = []
    for ack_id in validated["send_ack_ids"]:
        try:
            ack_packets.append(ack_map[ack_id].to_packet())
        except KeyError as exc:
            raise KeyError("delta plan references ACK absent from sender ledger") from exc
    ack_packets.sort(key=lambda row: (row["envelope_id"], row["consumer_id"], row["ack_id"]))
    core = {
        "schema": SYNC_DELTA_SCHEMA,
        "version": SYNC_VERSION,
        "plan_sha256": validated["plan_sha256"],
        "sender_node_id": validated["sender_node_id"],
        "receiver_node_id": validated["receiver_node_id"],
        "sender_inventory_sha256": validated["sender_inventory_sha256"],
        "receiver_inventory_sha256": validated["receiver_inventory_sha256"],
        "envelopes": envelope_packets,
        "acks": ack_packets,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    return {
        **core,
        "delta_sha256": _sha256(core),
        "claims": {
            "append_only_delta": True,
            "deletion_authority": False,
            "overwrite_authority": False,
            "node_identity_authenticated": False,
            "canon_promoted": False,
        },
    }


def validate_delta(packet: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        raise ValueError("delta must be a mapping")
    row = dict(packet)
    if row.get("schema") != SYNC_DELTA_SCHEMA or row.get("version") != SYNC_VERSION:
        raise ValueError("unsupported anti-entropy delta")
    plan_sha = _hex_commitment(row.get("plan_sha256"), "plan_sha256")
    sender = _text(row.get("sender_node_id"), "sender_node_id")
    receiver = _text(row.get("receiver_node_id"), "receiver_node_id")
    sender_inv = _hex_commitment(row.get("sender_inventory_sha256"), "sender_inventory_sha256")
    receiver_inv = _hex_commitment(row.get("receiver_inventory_sha256"), "receiver_inventory_sha256")
    raw_env = row.get("envelopes")
    raw_acks = row.get("acks")
    if not isinstance(raw_env, Sequence) or isinstance(raw_env, (str, bytes)):
        raise ValueError("delta envelopes must be a sequence")
    if not isinstance(raw_acks, Sequence) or isinstance(raw_acks, (str, bytes)):
        raise ValueError("delta acks must be a sequence")
    envelopes = [InformationEnvelope.from_packet(item).to_packet() for item in raw_env]
    if envelopes != sorted(envelopes, key=lambda item: (item["sequence"], item["envelope_id"])):
        raise ValueError("delta envelopes must be parent-friendly sorted by sequence/id")
    if len({item["envelope_id"] for item in envelopes}) != len(envelopes):
        raise ValueError("delta contains duplicate envelope ids")
    # ACK hydration requires its referenced envelope. Validate commitment structure
    # here and perform envelope binding during preflight/apply.
    acks = []
    for item in raw_acks:
        if not isinstance(item, Mapping):
            raise ValueError("delta ACK must be a mapping")
        ack = dict(item)
        _item_digest(_text(ack.get("ack_id"), "ack_id"), "pxa:")
        _item_digest(_text(ack.get("envelope_id"), "envelope_id"), "px:")
        _hex_commitment(ack.get("payload_sha256"), "payload_sha256")
        _text(ack.get("consumer_id"), "consumer_id")
        _text(ack.get("outcome"), "outcome")
        _text(ack.get("reason_code"), "reason_code")
        if ack.get("authentication") != MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION:
            raise ValueError("delta ACK authentication boundary mismatch")
        if ack.get("epistemic") != MEMORY_EXCHANGE_EPISTEMIC or ack.get("authority") != MEMORY_EXCHANGE_AUTHORITY:
            raise ValueError("delta ACK epistemic/authority mismatch")
        if ack.get("canon_allowed") is not False:
            raise ValueError("delta ACK must remain canon_allowed=false")
        acks.append(ack)
    if acks != sorted(acks, key=lambda item: (item["envelope_id"], item["consumer_id"], item["ack_id"])):
        raise ValueError("delta ACKs must be deterministically sorted")
    if len({item["ack_id"] for item in acks}) != len(acks):
        raise ValueError("delta contains duplicate ACK ids")

    if row.get("authentication") != MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION:
        raise ValueError("delta authentication boundary mismatch")
    if row.get("epistemic") != MEMORY_EXCHANGE_EPISTEMIC or row.get("authority") != MEMORY_EXCHANGE_AUTHORITY:
        raise ValueError("delta epistemic/authority mismatch")
    if row.get("canon_allowed") is not False:
        raise ValueError("delta must remain canon_allowed=false")
    core = {
        "schema": SYNC_DELTA_SCHEMA,
        "version": SYNC_VERSION,
        "plan_sha256": plan_sha,
        "sender_node_id": sender,
        "receiver_node_id": receiver,
        "sender_inventory_sha256": sender_inv,
        "receiver_inventory_sha256": receiver_inv,
        "envelopes": envelopes,
        "acks": acks,
        "authentication": MEMORY_EXCHANGE_IDENTITY_AUTHENTICATION,
        "epistemic": MEMORY_EXCHANGE_EPISTEMIC,
        "authority": MEMORY_EXCHANGE_AUTHORITY,
        "canon_allowed": False,
    }
    delta_sha = _sha256(core)
    if row.get("delta_sha256") != delta_sha:
        raise ValueError("delta_sha256 mismatch")
    claims = row.get("claims")
    if not isinstance(claims, Mapping) or claims.get("append_only_delta") is not True:
        raise ValueError("delta must remain append-only")
    for key in ("deletion_authority", "overwrite_authority", "node_identity_authenticated", "canon_promoted"):
        if claims.get(key) is not False:
            raise ValueError(f"delta claim must remain false: {key}")
    return {**core, "delta_sha256": delta_sha, "claims": dict(claims)}


def _delta_already_present(
    ledger: MemoryExchangeLedger,
    delta: Mapping[str, Any],
) -> bool:
    envelope_map = {row.envelope_id: row for row in ledger.envelopes()}
    ack_map = {row.ack_id: row for row in ledger.acknowledgements()}
    for packet in delta["envelopes"]:
        existing = envelope_map.get(packet["envelope_id"])
        if existing is None or existing.to_packet() != packet:
            return False
    for packet in delta["acks"]:
        existing = ack_map.get(packet["ack_id"])
        if existing is None or existing.to_packet() != packet:
            return False
    return True


def _clone_ledger(ledger: MemoryExchangeLedger) -> MemoryExchangeLedger:
    clone = MemoryExchangeLedger()
    for envelope in ledger.envelopes():
        clone.append(envelope)
    for ack in ledger.acknowledgements():
        clone.record_ack(ack)
    return clone


def _stage_delta(
    ledger: MemoryExchangeLedger,
    delta: Mapping[str, Any],
) -> tuple[int, int]:
    envelope_created = 0
    ack_created = 0
    for packet in delta["envelopes"]:
        if ledger.append(InformationEnvelope.from_packet(packet)):
            envelope_created += 1
    for packet in delta["acks"]:
        envelope = ledger.get_envelope(packet["envelope_id"])
        ack = ExchangeAck.from_packet(envelope, packet)
        if ledger.record_ack(ack):
            ack_created += 1
    return envelope_created, ack_created


def apply_delta(
    ledger: MemoryExchangeLedger,
    delta: Mapping[str, Any],
    *,
    receiver_node_id: str,
) -> dict[str, Any]:
    """Preflight then append one delta; never delete or overwrite receiver-only state."""
    validated = validate_delta(delta)
    receiver = _text(receiver_node_id, "receiver_node_id")
    if validated["receiver_node_id"] != receiver:
        raise ValueError("delta receiver_node_id mismatch")

    before = build_inventory(ledger, node_id=receiver)
    if _delta_already_present(ledger, validated):
        return {
            "status": "ALREADY_APPLIED",
            "delta_sha256": validated["delta_sha256"],
            "created_envelopes": 0,
            "created_acks": 0,
            "before_inventory_sha256": before["inventory_sha256"],
            "after_inventory_sha256": before["inventory_sha256"],
            "content_root_sha256": before["content_root_sha256"],
            "append_only": True,
            "canon_allowed": False,
        }
    if before["inventory_sha256"] != validated["receiver_inventory_sha256"]:
        raise RuntimeError("receiver inventory changed since delta planning")

    # Preflight on a complete clone prevents partial mutation on malformed or
    # causally incomplete batches.
    clone = _clone_ledger(ledger)
    _stage_delta(clone, validated)

    created_envelopes, created_acks = _stage_delta(ledger, validated)
    after = build_inventory(ledger, node_id=receiver)
    return {
        "status": "APPLIED",
        "delta_sha256": validated["delta_sha256"],
        "created_envelopes": created_envelopes,
        "created_acks": created_acks,
        "before_inventory_sha256": before["inventory_sha256"],
        "after_inventory_sha256": after["inventory_sha256"],
        "content_root_sha256": after["content_root_sha256"],
        "append_only": True,
        "canon_allowed": False,
    }


__all__ = [
    "SYNC_BUCKET_HEX_WIDTH",
    "SYNC_DELTA_SCHEMA",
    "SYNC_INVENTORY_SCHEMA",
    "SYNC_MANIFEST_SCHEMA",
    "SYNC_PLAN_SCHEMA",
    "SYNC_VERSION",
    "apply_delta",
    "build_bucket_manifest",
    "build_inventory",
    "divergent_buckets",
    "export_delta",
    "plan_delta",
    "validate_bucket_manifest",
    "validate_delta",
    "validate_inventory",
    "validate_plan",
]
