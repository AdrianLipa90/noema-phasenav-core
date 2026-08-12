"""CLI for target-aware PhaseNav traces."""
from __future__ import annotations

import argparse
import json

from .runtime import trace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cards", nargs="+")
    parser.add_argument("--base-path")
    args = parser.parse_args()
    result = trace(args.cards, args.base_path)
    print(json.dumps(result, default=lambda obj: obj.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
