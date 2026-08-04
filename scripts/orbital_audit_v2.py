#!/usr/bin/env python3
"""READ-ONLY PhaseNav orbital audit v2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ciel_geometry.phasenav.canon import CORPUS, audit_orbits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()

    report = audit_orbits(CORPUS)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_path:
        args.json_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
