"""Canonical PhaseNav card model with explicit 36D phase markers.

The module provides an additive, sidecar-oriented normalization layer for the
heterogeneous card systems used by PhaseNav, CIELingo and NOEMA.  It never
modifies source records.  Inferred or reconstructed information is marked with
``epistemic_status='chyba'`` and cannot become canon automatically.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

TAU = 2.0 * math.pi
VECTOR_DIM = 36
MARKER_SCHEMA = "PHASENAV-36D/1"
CARD_SCHEMA = "PHASENAV-CARD/1"
EPISTEMIC_STATES = frozenset({"canon", "chyba", "candidate", "quarantine"})

SECTORS: dict[str, slice] = {
    "lorentz": slice(0, 6),
    "intention": slice(6, 12),
    "soul": slice(12, 13),
    "semantic": slice(13, 36),
}


def _json_digest(value: Any, *, length: int = 24) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:length]


def normalize_label(value: str) -> str:
    """Return a stable human-readable slug without erasing Unicode identity."""
    text = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    text = re.sub(r"[^\w\-.:]+", "-", text, flags=re.UNICODE)
    return text.strip("-") or "unnamed"


def coerce_phase36(value: Sequence[float] | np.ndarray) -> tuple[float, ...]:
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.shape != (VECTOR_DIM,):
        raise ValueError(f"expected a {VECTOR_DIM}D phase vector, got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("phase vector contains non-finite values")
    return tuple(float(x % TAU) for x in arr)


def circular_summary(values: Sequence[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return 0.0, 0.0
    z = np.mean(np.exp(1j * arr))
    return float(abs(z)), float(np.angle(z) % TAU)


@dataclass(frozen=True)
class Phase36Marker:
    """Stable marker describing one 36D phase state.

    The fingerprint is a technical integrity identifier.  It is not a claim of
    semantic identity and must not be used as an authorization or SOURCE seal.
    """

    vector: tuple[float, ...]
    encoding: str = "unknown"
    schema: str = MARKER_SCHEMA
    dimension: int = VECTOR_DIM
    fingerprint: str = ""
    order_parameter: float = 0.0
    mean_phase_rad: float = 0.0
    sector_order: dict[str, float] = field(default_factory=dict)
    sector_phase_rad: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_vector(
        cls,
        vector: Sequence[float] | np.ndarray,
        *,
        encoding: str = "unknown",
    ) -> "Phase36Marker":
        vec = coerce_phase36(vector)
        rounded = [round(x, 12) for x in vec]
        order_parameter, mean_phase = circular_summary(vec)
        sector_order: dict[str, float] = {}
        sector_phase: dict[str, float] = {}
        arr = np.asarray(vec, dtype=np.float64)
        for name, sector in SECTORS.items():
            r, phase = circular_summary(arr[sector])
            sector_order[name] = round(r, 12)
            sector_phase[name] = round(phase, 12)
        fingerprint = "p36:" + _json_digest(
            {"schema": MARKER_SCHEMA, "encoding": encoding, "vector": rounded},
            length=32,
        )
        return cls(
            vector=vec,
            encoding=encoding,
            fingerprint=fingerprint,
            order_parameter=round(order_parameter, 12),
            mean_phase_rad=round(mean_phase, 12),
            sector_order=sector_order,
            sector_phase_rad=sector_phase,
        )

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema != MARKER_SCHEMA:
            issues.append(f"unsupported marker schema: {self.schema}")
        if self.dimension != VECTOR_DIM:
            issues.append(f"dimension must equal {VECTOR_DIM}")
        if len(self.vector) != VECTOR_DIM:
            issues.append(f"vector must contain {VECTOR_DIM} phases")
        if any(not math.isfinite(x) or not 0.0 <= x < TAU for x in self.vector):
            issues.append("all vector components must be finite and in [0, 2π)")
        if not 0.0 <= self.order_parameter <= 1.0 + 1e-12:
            issues.append("order_parameter must be in [0, 1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalCard:
    """Canonical view of one source card or crystal facet.

    Canonicalization means stable identity and schema normalization.  It does
    not automatically mean epistemic canonization.
    """

    card_id: str
    card_type: str
    label: str
    marker_36d: Phase36Marker
    aliases: list[str] = field(default_factory=list)
    language: str = "und"
    text: str = ""
    operator_bindings: list[str] = field(default_factory=list)
    semantic_mass: float | None = None
    epistemic_status: str = "chyba"
    confidence: float = 0.5
    canon_allowed: bool = False
    provenance: list[dict[str, Any]] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    schema: str = CARD_SCHEMA

    def validate(self) -> list[str]:
        issues = self.marker_36d.validate()
        if not self.card_id:
            issues.append("card_id is required")
        if not self.card_type:
            issues.append("card_type is required")
        if not self.label:
            issues.append("label is required")
        if self.epistemic_status not in EPISTEMIC_STATES:
            issues.append(f"invalid epistemic_status: {self.epistemic_status}")
        if not 0.0 <= self.confidence <= 1.0:
            issues.append("confidence must be in [0, 1]")
        if self.epistemic_status != "canon" and self.canon_allowed:
            issues.append("canon_allowed cannot be true outside canon status")
        return issues

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["phase_36d"] = result.pop("marker_36d")["vector"]
        result["phase36_marker"] = self.marker_36d.to_dict()
        return result


def _first(record: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and value != "":
            return value
    return default


def _infer_card_type(record: Mapping[str, Any], source_kind: str | None) -> str:
    explicit = _first(record, "card_type", "type", "ontology_class")
    if explicit:
        return normalize_label(str(explicit))
    if source_kind:
        return normalize_label(source_kind)
    if _first(record, "operator_card_id", "operator_hook", "operator"):
        return "operator"
    if _first(record, "emotion", "soul", "phase_R") is not None:
        return "facet"
    return "concept"


def _infer_epistemic(record: Mapping[str, Any]) -> tuple[str, bool, float]:
    explicit = str(_first(record, "epistemic_status", "canon_state", default="")).casefold()
    canon_allowed = bool(record.get("canon_allowed", False))
    source_binding = str(record.get("source_binding", "")).casefold()
    validation = str(_first(record, "validation_status", "status", default="")).casefold()

    if explicit in EPISTEMIC_STATES:
        status = explicit
    elif explicit in {"canonical", "canonized", "canonised"}:
        status = "canon"
    elif explicit in {"quarantined", "rejected", "invalid"}:
        status = "quarantine"
    elif explicit in {"candidate", "review", "pending", "draft"}:
        status = "candidate"
    elif canon_allowed and source_binding == "source" and validation in {"validated", "pass", "approved"}:
        status = "canon"
    else:
        status = "chyba"

    if status != "canon":
        canon_allowed = False

    confidence_raw = _first(record, "confidence", "confidence_score", default=None)
    if confidence_raw is None:
        confidence = {
            "canon": 1.0,
            "candidate": 0.65,
            "chyba": 0.5,
            "quarantine": 0.0,
        }[status]
    else:
        try:
            confidence = min(1.0, max(0.0, float(confidence_raw)))
        except (TypeError, ValueError):
            confidence = 0.5
    return status, canon_allowed, confidence


def _canonical_id(
    record: Mapping[str, Any],
    *,
    card_type: str,
    label: str,
    source_namespace: str,
    source_index: int | None,
) -> tuple[str, list[str]]:
    explicit_values: list[str] = []
    for key in ("concept_card_id", "card_id", "operator_card_id", "marker_id", "id"):
        value = record.get(key)
        if value is not None and str(value).strip():
            explicit_values.append(str(value).strip())

    if explicit_values:
        primary = explicit_values[0]
        if ":" in primary:
            return primary, explicit_values
        return f"{card_type}:{primary}", explicit_values

    seed = {
        "namespace": source_namespace,
        "type": card_type,
        "label": normalize_label(label),
        "index": source_index,
        "text": str(record.get("text", ""))[:512],
    }
    digest = _json_digest(seed, length=20)
    return f"{card_type}:{normalize_label(label)}:{digest}", []


def _extract_vector(record: Mapping[str, Any], vector: Sequence[float] | np.ndarray | None) -> Sequence[float]:
    if vector is not None:
        return vector
    candidate = _first(
        record,
        "phase_36d",
        "v36",
        "vector_36d",
        "phase_vector",
        "vector",
    )
    if candidate is None:
        raise ValueError("record has no 36D phase vector")
    return candidate


def canonicalize_record(
    record: Mapping[str, Any],
    *,
    vector: Sequence[float] | np.ndarray | None = None,
    source_kind: str | None = None,
    source_namespace: str = "unknown",
    source_path: str | None = None,
    source_index: int | None = None,
    encoding: str | None = None,
) -> CanonicalCard:
    """Build a canonical card view without mutating the source record."""
    card_type = _infer_card_type(record, source_kind)
    label = str(_first(record, "name", "normalized", "lemma", "label", "text", default="unnamed"))
    card_id, source_ids = _canonical_id(
        record,
        card_type=card_type,
        label=label,
        source_namespace=source_namespace,
        source_index=source_index,
    )
    phase = _extract_vector(record, vector)
    effective_encoding = str(
        encoding
        or _first(record, "encoding", "phase_encoding", default="unknown")
    )
    marker = Phase36Marker.from_vector(phase, encoding=effective_encoding)
    status, canon_allowed, confidence = _infer_epistemic(record)

    aliases_raw = _first(record, "aliases", "surface_forms", default=[])
    if isinstance(aliases_raw, str):
        aliases = [aliases_raw]
    else:
        aliases = [str(x) for x in aliases_raw or []]
    for candidate in (_first(record, "normalized"), _first(record, "lemma")):
        if candidate and str(candidate) != label:
            aliases.append(str(candidate))
    aliases = sorted(set(a for a in aliases if a and a != label))

    ops_raw = _first(record, "operator_bindings", default=None)
    if ops_raw is None:
        op = _first(record, "operator", "operator_hook", "operator_card_id")
        ops = [str(op)] if op else []
    elif isinstance(ops_raw, str):
        ops = [ops_raw]
    else:
        ops = [str(x) for x in ops_raw]

    semantic_mass_raw = record.get("semantic_mass")
    try:
        semantic_mass = float(semantic_mass_raw) if semantic_mass_raw is not None else None
    except (TypeError, ValueError):
        semantic_mass = None

    provenance = {
        "source_namespace": source_namespace,
        "source_kind": source_kind or "unknown",
        "source_path": source_path,
        "source_index": source_index,
        "source_record_digest": _json_digest(dict(record), length=32),
        "source_binding": record.get("source_binding", "ARTIFACT_GROUNDED"),
    }
    attributes = dict(record)
    for key in (
        "phase_36d",
        "v36",
        "vector_36d",
        "phase_vector",
        "vector",
    ):
        attributes.pop(key, None)

    card = CanonicalCard(
        card_id=card_id,
        card_type=card_type,
        label=label,
        marker_36d=marker,
        aliases=aliases,
        language=str(_first(record, "language_id", "language", default="und")),
        text=str(record.get("text", "")),
        operator_bindings=sorted(set(ops)),
        semantic_mass=semantic_mass,
        epistemic_status=status,
        confidence=confidence,
        canon_allowed=canon_allowed,
        provenance=[provenance],
        source_ids=source_ids,
        attributes=attributes,
    )
    issues = card.validate()
    if issues:
        raise ValueError("invalid canonical card: " + "; ".join(issues))
    return card


def canonicalize_crystal_facet(
    metadata: Mapping[str, Any],
    vector: Sequence[float] | np.ndarray,
    index: int,
    *,
    source_path: str | None = None,
) -> CanonicalCard:
    record = dict(metadata)
    record.setdefault("card_type", "facet")
    record.setdefault("encoding", metadata.get("encoding", "v1_precise"))
    return canonicalize_record(
        record,
        vector=vector,
        source_kind="facet",
        source_namespace="phase-crystal",
        source_path=source_path,
        source_index=index,
    )


def canonicalize_runtime_card(
    record: Mapping[str, Any],
    *,
    source_path: str | None = None,
    source_index: int | None = None,
) -> CanonicalCard:
    return canonicalize_record(
        record,
        source_kind="concept",
        source_namespace="phasenav-runtime",
        source_path=source_path,
        source_index=source_index,
    )


def canonicalize_operator_card(
    record: Mapping[str, Any],
    *,
    source_path: str | None = None,
    source_index: int | None = None,
) -> CanonicalCard:
    return canonicalize_record(
        record,
        source_kind="operator",
        source_namespace="phasenav-operator",
        source_path=source_path,
        source_index=source_index,
    )


def merge_card_views(cards: Iterable[CanonicalCard]) -> list[CanonicalCard]:
    """Merge compatible views additively and preserve every conflict.

    A phase conflict never gets averaged silently.  The first marker is retained,
    all variants are recorded, and the merged card is demoted to ``chyba``.
    """
    merged: dict[str, CanonicalCard] = {}
    for incoming in cards:
        current = merged.get(incoming.card_id)
        if current is None:
            merged[incoming.card_id] = incoming
            continue

        current.aliases = sorted(set(current.aliases + incoming.aliases))
        current.operator_bindings = sorted(
            set(current.operator_bindings + incoming.operator_bindings)
        )
        current.provenance.extend(incoming.provenance)
        current.source_ids = sorted(set(current.source_ids + incoming.source_ids))

        phase_delta = np.abs(
            ((
                np.asarray(incoming.marker_36d.vector)
                - np.asarray(current.marker_36d.vector)
                + math.pi
            ) % TAU)
            - math.pi
        )
        phase_equivalent = bool(np.max(phase_delta) <= 1.0e-5)
        if not phase_equivalent:
            current.conflicts.append(
                {
                    "kind": "phase36_conflict",
                    "retained": current.marker_36d.fingerprint,
                    "variant": incoming.marker_36d.to_dict(),
                    "max_wrapped_delta": float(np.max(phase_delta)),
                    "variant_provenance": incoming.provenance,
                }
            )
            current.epistemic_status = "chyba"
            current.canon_allowed = False
            current.confidence = min(current.confidence, incoming.confidence, 0.5)
        elif current.marker_36d.fingerprint != incoming.marker_36d.fingerprint:
            current.attributes.setdefault("phase36_equivalent_views", []).append(
                {
                    "fingerprint": incoming.marker_36d.fingerprint,
                    "max_wrapped_delta": float(np.max(phase_delta)),
                    "provenance": incoming.provenance,
                }
            )

        if current.card_type != incoming.card_type:
            if current.card_type == "concept":
                current.attributes.setdefault("card_type_views", []).append(current.card_type)
                current.card_type = incoming.card_type
            elif incoming.card_type != "concept":
                current.conflicts.append(
                    {
                        "kind": "card_type_conflict",
                        "retained": current.card_type,
                        "variant": incoming.card_type,
                        "variant_provenance": incoming.provenance,
                    }
                )
                current.epistemic_status = "chyba"
                current.canon_allowed = False

        if current.label != incoming.label:
            current.aliases = sorted(set(current.aliases + [incoming.label]))
        if not current.text and incoming.text:
            current.text = incoming.text
        if current.semantic_mass is None:
            current.semantic_mass = incoming.semantic_mass
        elif incoming.semantic_mass is not None and not math.isclose(
            current.semantic_mass, incoming.semantic_mass, rel_tol=1e-9, abs_tol=1e-12
        ):
            current.conflicts.append(
                {
                    "kind": "semantic_mass_conflict",
                    "retained": current.semantic_mass,
                    "variant": incoming.semantic_mass,
                    "variant_provenance": incoming.provenance,
                }
            )
            current.epistemic_status = "chyba"
            current.canon_allowed = False

    return sorted(merged.values(), key=lambda card: card.card_id)


def cards_to_jsonl(cards: Iterable[CanonicalCard]) -> str:
    return "\n".join(
        json.dumps(card.to_dict(), ensure_ascii=False, sort_keys=True)
        for card in cards
    ) + "\n"


__all__ = [
    "CARD_SCHEMA",
    "MARKER_SCHEMA",
    "VECTOR_DIM",
    "SECTORS",
    "Phase36Marker",
    "CanonicalCard",
    "normalize_label",
    "coerce_phase36",
    "circular_summary",
    "canonicalize_record",
    "canonicalize_crystal_facet",
    "canonicalize_runtime_card",
    "canonicalize_operator_card",
    "merge_card_views",
    "cards_to_jsonl",
]
