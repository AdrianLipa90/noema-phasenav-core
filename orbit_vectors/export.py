"""CLI exporter for full 36D PhaseNav orbit vectors."""
from __future__ import annotations

import argparse
from pathlib import Path

from .catalog import export_jsonl, records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output",
        nargs="?",
        default="orbit_vectors/PHASENAV_ORBIT_VECTORS_36D.jsonl",
    )
    args = parser.parse_args()
    path = export_jsonl(Path(args.output))
    print(f"wrote {len(records())} full 36D orbit records to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
