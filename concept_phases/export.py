"""CLI exporter for the canonical 36D concept-phase catalogue."""
from __future__ import annotations

import argparse
from pathlib import Path

from .catalog import export_jsonl, records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output",
        nargs="?",
        default="concept_phases/PHASENAV_CONCEPT_PHASES_36D.jsonl",
    )
    args = parser.parse_args()
    path = export_jsonl(Path(args.output))
    print(f"wrote {len(records())} concept phase records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
