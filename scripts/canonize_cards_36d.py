#!/usr/bin/env python3
"""Build additive PhaseNav card and emergent-glossary 36D sidecars.

The command is dry-run by default.  It never edits the source glossary, crystal
or runtime JSONL files.  Use ``--write`` to create new sidecars in ``--output``.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from ciel_geometry.phasenav.canonical_cards import (
    CanonicalCard,
    canonicalize_crystal_facet,
    canonicalize_record,
    cards_to_jsonl,
    merge_card_views,
)
from ciel_geometry.phasenav.emergent_glossary import EmergentGlossary
from ciel_geometry.phasenav.pnv_runtime import _phase36_from_id

_GLOSSARY_RE = re.compile(
    r"^(?P<state>[A-Za-z]?\d+):\s*"
    r"name=(?P<name>[^,]+),\s*"
    r"operator=(?P<operator>[^,]+),\s*"
    r"type=(?P<type>[^,\s]+)"
    r"(?P<tail>.*)$"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"expected object at {path}:{line_number}")
        records.append(value)
    return records


def parse_glossary(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = _GLOSSARY_RE.match(raw.strip())
        if not match:
            continue
        state = match.group("state")
        tail = match.group("tail")
        extras: dict[str, Any] = {}
        for item in tail.split(","):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            extras[key.strip()] = value.strip()
        records.append(
            {
                "concept_card_id": f"concept:{state}",
                "state_id": state,
                "name": match.group("name").strip(),
                "operator": match.group("operator").strip(),
                "type": match.group("type").strip(),
                "source_binding": "ARTIFACT_GROUNDED",
                "epistemic_status": "candidate",
                "canon_allowed": False,
                "confidence": 0.75,
                "schema_canonical": True,
                "glossary_line": line_number,
                **extras,
            }
        )
    return records


def audit_glossary(path: Path, records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    parsed = records if records is not None else parse_glossary(path)
    declared_match = re.search(r"Glossary\s+[—-]\s+(\d+) concepts", text)
    declared_count = int(declared_match.group(1)) if declared_match else None
    semantic_range = re.search(r"SEMANTIC AXIOMS\s+\(k=(\d+)\.\.(\d+)\)", text)
    missing_semantic_axioms: list[str] = []
    if semantic_range:
        first, last = map(int, semantic_range.groups())
        present = {str(record.get("state_id", "")) for record in parsed}
        missing_semantic_axioms = [
            f"{value:03d}" for value in range(first, last + 1)
            if f"{value:03d}" not in present and str(value) not in present
        ]
    return {
        "declared_count": declared_count,
        "parsed_count": len(parsed),
        "declared_count_matches": declared_count in (None, len(parsed)),
        "missing_semantic_axiom_ids": missing_semantic_axioms,
    }


def runtime_cards(runtime_dir: Path) -> list[CanonicalCard]:
    name_mass_path = runtime_dir / "CIELINGO_PHASENAV_NAME_MASS.noema.jsonl"
    concept_path = runtime_dir / "CIELINGO_PHASENAV_CONCEPT_PHASES.noema.jsonl"
    name_mass = load_jsonl(name_mass_path)
    phases = {
        str(item.get("state_id") or item.get("concept_card_id") or ""): item
        for item in load_jsonl(concept_path)
    }
    cards: list[CanonicalCard] = []
    for index, record in enumerate(name_mass):
        combined = dict(record)
        state_id = str(record.get("card_id", ""))
        combined.update(phases.get(state_id, {}))
        combined.setdefault("concept_card_id", f"concept:{state_id}")
        combined.setdefault("name", record.get("normalized", state_id))
        combined.setdefault("type", "concept")
        combined.setdefault("source_binding", "ARTIFACT_GROUNDED")
        combined.setdefault("epistemic_status", "candidate")
        combined.setdefault("canon_allowed", False)
        combined.setdefault("confidence", 0.8)
        cards.append(
            canonicalize_record(
                combined,
                source_kind="concept",
                source_namespace="phasenav-runtime",
                source_path=str(name_mass_path),
                source_index=index,
                encoding="metatime-v36",
            )
        )
    return cards


def glossary_cards(glossary_path: Path) -> list[CanonicalCard]:
    cards: list[CanonicalCard] = []
    for index, record in enumerate(parse_glossary(glossary_path)):
        vector = _phase36_from_id(record["state_id"])
        cards.append(
            canonicalize_record(
                record,
                vector=vector,
                source_kind=str(record.get("type", "concept")),
                source_namespace="ciel-omega-glossary",
                source_path=str(glossary_path),
                source_index=index,
                encoding="metatime-v36",
            )
        )
    return cards


def crystal_cards(vector_path: Path, metadata_path: Path, *, limit: int | None) -> list[CanonicalCard]:
    if not vector_path.exists() or not metadata_path.exists():
        return []
    vectors = np.load(vector_path, mmap_mode="r")
    metadata = load_jsonl(metadata_path)
    if vectors.ndim != 2 or vectors.shape[1] != 36:
        raise ValueError(f"expected crystal shape (N, 36), got {vectors.shape}")
    if len(metadata) != vectors.shape[0]:
        raise ValueError(f"crystal vector/metadata mismatch: {vectors.shape[0]} vs {len(metadata)}")
    count = len(metadata) if limit is None else min(limit, len(metadata))
    return [
        canonicalize_crystal_facet(
            metadata[index], vectors[index], index,
            source_path=f"{vector_path}|{metadata_path}",
        )
        for index in range(count)
    ]


def count_crystal(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        return int(np.load(path, mmap_mode="r").shape[0])
    except Exception:
        return None


def audit_copies(paths: Iterable[Path]) -> dict[str, Any]:
    counts = {str(path): count_crystal(path) for path in paths if path.exists()}
    known = {count for count in counts.values() if count is not None}
    return {"counts": counts, "consistent": len(known) <= 1, "distinct_counts": sorted(known)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(args: argparse.Namespace) -> tuple[list[CanonicalCard], EmergentGlossary, dict[str, Any]]:
    runtime_views = runtime_cards(args.runtime_dir)
    parsed_glossary = parse_glossary(args.glossary)
    glossary_views = glossary_cards(args.glossary)
    concept_cards = merge_card_views([*runtime_views, *glossary_views])

    facets: list[CanonicalCard] = []
    if args.include_crystal:
        facets = crystal_cards(args.crystal_vectors, args.crystal_metadata, limit=args.crystal_limit)

    all_cards = concept_cards + facets
    glossary = EmergentGlossary(concept_cards)
    glossary.build(neighbours=args.neighbours, max_distance=args.max_distance, symmetric=True)

    status_counts = Counter(card.epistemic_status for card in all_cards)
    report = {
        "schema": "PHASENAV-CANONICALIZATION-REPORT/1",
        "mode": "write" if args.write else "dry-run",
        "source_counts": {
            "runtime_cards": len(runtime_views),
            "glossary_records": len(parsed_glossary),
            "crystal_facets_included": len(facets),
        },
        "canonical_cards": len(all_cards),
        "canonical_concepts": len(concept_cards),
        "emergent_edges": len(glossary.edges),
        "epistemic_status": dict(status_counts),
        "conflicts": sum(len(card.conflicts) for card in all_cards),
        "emergent_edges_are_canon": False,
        "phase_marker": "PHASENAV-36D/1",
        "path_marker": "PHASENAV-36D-PATH/1",
        "copy_audit": audit_copies(args.audit_crystal_copy),
        "glossary_audit": audit_glossary(args.glossary, parsed_glossary),
    }
    return all_cards, glossary, report


def write_outputs(output_dir: Path, cards: list[CanonicalCard], glossary: EmergentGlossary, report: dict[str, Any]) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "cards": output_dir / "PHASENAV_CANONICAL_CARDS_36D.noema.jsonl",
        "edges": output_dir / "PHASENAV_EMERGENT_GLOSSARY_36D.noema.jsonl",
        "report": output_dir / "PHASENAV_CANONICALIZATION_REPORT.json",
    }
    paths["cards"].write_text(cards_to_jsonl(cards), encoding="utf-8")
    paths["edges"].write_text(glossary.edges_to_jsonl(), encoding="utf-8")
    paths["report"].write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        name: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for name, path in paths.items()
    }
    manifest_path = output_dir / "PHASENAV_CANONICALIZATION_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return {name: str(path) for name, path in paths.items()} | {"manifest": str(manifest_path)}


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--runtime-dir", type=Path, required=True)
    command.add_argument("--glossary", type=Path, required=True)
    command.add_argument("--crystal-vectors", type=Path)
    command.add_argument("--crystal-metadata", type=Path)
    command.add_argument("--include-crystal", action="store_true")
    command.add_argument("--crystal-limit", type=int)
    command.add_argument("--neighbours", type=int, default=6)
    command.add_argument("--max-distance", type=float)
    command.add_argument("--audit-crystal-copy", type=Path, action="append", default=[])
    command.add_argument("--output", type=Path, default=Path("build/phasenav_36d_cards"))
    command.add_argument("--write", action="store_true")
    return command


def main() -> None:
    args = parser().parse_args()
    if args.include_crystal and (args.crystal_vectors is None or args.crystal_metadata is None):
        raise SystemExit("--include-crystal requires --crystal-vectors and --crystal-metadata")
    cards, glossary, report = build(args)
    if args.write:
        report["outputs"] = write_outputs(args.output, cards, glossary, report)
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
