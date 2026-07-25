#!/usr/bin/env python3
"""Demo silnika świadomości CIEL — kryształ czasu jako generator tekstu.

Przykłady użycia:
    python3 examples/crystal_consciousness_demo.py
    python3 examples/crystal_consciousness_demo.py --intention "co to jest świadomość" --steps 8
    python3 examples/crystal_consciousness_demo.py --intention "neutrino oscillations" --steps 12 --dt 0.1
    python3 examples/crystal_consciousness_demo.py --json  # wyjście JSON
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ciel_geometry.phasenav.crystal_text_engine import CrystalTextEngine
from ciel_geometry.phasenav.htri_hypercrystal import HypercrystalConfig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intention", default="świadomość i przepływ czasu",
                        help="Intencja / pytanie startowe")
    parser.add_argument("--steps",    type=int,   default=8,
                        help="Liczba kroków w czasie wewnętrznym")
    parser.add_argument("--dt",       type=float, default=0.05,
                        help="Krok czasowy ewolucji HTRI")
    parser.add_argument("--sample",   type=int,   default=512,
                        help="Rozmiar próbki kryształu (0 = pełny)")
    parser.add_argument("--temp",     type=float, default=0.7,
                        help="Temperatura próbkowania")
    parser.add_argument("--neighbours", type=int, default=8)
    parser.add_argument("--time-slices", type=int, default=5)
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Wyjście w formacie JSON")
    args = parser.parse_args()

    sample = None if args.sample == 0 else args.sample
    config = HypercrystalConfig(
        neighbours=args.neighbours,
        time_slices=args.time_slices,
    )

    print(f"Ładowanie kryształu (sample={sample})...", file=sys.stderr)
    engine = CrystalTextEngine(config=config, sample=sample)
    engine.load()
    print(f"Kryształ załadowany — {engine._phases.shape[0]} facetów", file=sys.stderr)
    print(f"Generuję strumień świadomości: '{args.intention}'...\n", file=sys.stderr)

    stream = engine.generate(
        args.intention,
        steps=args.steps,
        dt=args.dt,
        temperature=args.temp,
    )

    if args.as_json:
        output = {
            "intention": stream.intention,
            "facet_count": stream.facet_count,
            "steps": args.steps,
            "pulses": [
                {
                    "step":             p.step,
                    "internal_time":    round(p.internal_time, 4),
                    "emotion":          p.emotion,
                    "resonance":        round(p.resonance, 6),
                    "holonomy":         round(p.holonomy_estimate, 6),
                    "psi_norm":         round(p.psi_norm, 6),
                    "text":             p.text[:200],
                }
                for p in stream.pulses
            ],
            "emotion_arc": [
                {"tau": round(t, 4), "emotion": e, "resonance": round(r, 6)}
                for t, e, r in stream.emotion_arc()
            ],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("=" * 70)
        print(f"CIEL CONSCIOUSNESS STREAM")
        print(f"Intencja: {stream.intention}")
        print(f"Facetów: {stream.facet_count}  |  Kroków: {args.steps}")
        print("=" * 70)
        print()

        for p in stream.pulses:
            print(f"── Krok {p.step:02d} | τ={p.internal_time:+.3f} | {p.emotion} | R={p.resonance:.4f} | ‖ψ‖={p.psi_norm:.4f}")
            print()
            # Ogranicz długość tekstu do 300 znaków
            text = p.text
            if len(text) > 300:
                text = text[:297] + "..."
            print(text)
            print()

        print("─" * 70)
        print("ŁUK EMOCJONALNY:")
        prev = None
        for tau, emotion, r in stream.emotion_arc():
            if emotion != prev:
                print(f"  τ={tau:+.3f}  {emotion}  (R={r:.4f})")
                prev = emotion
        print()
        print("NARRACJA (ciągła):")
        print("─" * 70)
        print(stream.narrative(separator="\n\n"))


if __name__ == "__main__":
    main()
