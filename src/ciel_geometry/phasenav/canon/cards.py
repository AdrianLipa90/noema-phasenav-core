"""Canonical PhaseNav card registry generated from a compact seed ledger."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
import struct

from .ciel_executable_map import bindings_for_concept
from .model import CanonicalConceptState
from .native_executable_map import native_bindings_for_concept
from .reciprocal_regularization import concept_algorithm_registry
from .seed_data import SEED_ROWS


_CONCEPT_ALGORITHM_CARD_BINDINGS = {
    "Reciprocal_Inversion": "RECIPROCAL_INVERSION",
    "Riemann_Zeta_Zero": "RIEMANN_ZETA_ZERO",
    "Heisenberg_Uncertainty": "HEISENBERG_UNCERTAINTY",
}


def _load_seeds() -> list[dict]:
    seeds: list[dict] = []
    for raw in SEED_ROWS.splitlines():
        line = raw.strip()
        if not line:
            continue
        glossary_id, canonical_name, operator, card_type, status = line.split("|", 4)
        canonical = status == "C"
        seeds.append(
            {
                "glossary_id": glossary_id,
                "canonical_name": canonical_name,
                "operator": operator,
                "type": card_type,
                "epistemic": {
                    "operator": "canonical" if canonical else "chyba",
                    "canon_allowed": canonical,
                    "reason": (
                        "declared glossary and recovered card agree"
                        if canonical
                        else "recovered card and glossary require authorial resolution"
                    ),
                },
            }
        )
    return seeds


def _state_digest(state: CanonicalConceptState) -> str:
    digest = hashlib.sha256()
    for amplitude in state.hilbert.amplitudes:
        digest.update(struct.pack("!dd", float(amplitude.real), float(amplitude.imag)))
    return digest.hexdigest()


def _orbital_distance(a: CanonicalConceptState, b: CanonicalConceptState) -> float:
    d36 = a.angular_distance(b)
    dm = abs(math.log(a.semantic_mass / b.semantic_mass))
    dq = (
        abs(math.log(a.q_ratio / b.q_ratio))
        if a.q_ratio > 0.0 and b.q_ratio > 0.0
        else math.inf
    )
    return math.sqrt(d36 * d36 + dm * dm + dq * dq)


def _local_algorithm_bindings(canonical_name: str) -> list[dict[str, object]]:
    algorithm_id = _CONCEPT_ALGORITHM_CARD_BINDINGS.get(canonical_name)
    if algorithm_id is None:
        return []
    registry = concept_algorithm_registry()
    return [
        {
            "concept_algorithm_id": algorithm_id,
            **dict(registry[algorithm_id]),
            "binding_status": "CANDIDATE_DIRECT_CONCEPT_BINDING",
            "execution_activation": "EXPLICIT_RUNTIME_DISPATCH",
            "scientific_promotion": "NOT_PERFORMED",
        }
    ]


def _native_algorithm_bindings(glossary_id: str) -> list[dict[str, object]]:
    return [
        {
            "concept_algorithm_id": binding.binding_id,
            **binding.to_dict(),
            "binding_status": "PHASENAV_NATIVE_CURRENT_MAPPED",
        }
        for binding in native_bindings_for_concept(glossary_id)
    ]


def _ciel_source_algorithm_bindings(glossary_id: str) -> list[dict[str, object]]:
    """Attach provenance-exact executable external CIEL source references."""
    return [
        {
            "concept_algorithm_id": binding.binding_id,
            **binding.to_dict(),
            "binding_status": "CIEL_EXECUTABLE_SOURCE_MAPPED",
        }
        for binding in bindings_for_concept(glossary_id)
    ]


def _algorithm_bindings(canonical_name: str, glossary_id: str) -> list[dict[str, object]]:
    return [
        *_local_algorithm_bindings(canonical_name),
        *_native_algorithm_bindings(glossary_id),
        *_ciel_source_algorithm_bindings(glossary_id),
    ]


@lru_cache(maxsize=1)
def _registry_tuple() -> tuple[dict, ...]:
    seeds = _load_seeds()
    states = {
        seed["glossary_id"]: CanonicalConceptState.from_id(seed["glossary_id"])
        for seed in seeds
    }
    cards: list[dict] = []
    for seed in seeds:
        gid = seed["glossary_id"]
        state = states[gid]
        neighbours = sorted(
            (
                (_orbital_distance(state, other), other_id, other)
                for other_id, other in states.items()
                if other_id != gid
            ),
            key=lambda item: (item[0], item[1]),
        )[:5]
        paths = []
        for rank, (distance, other_id, other) in enumerate(neighbours, start=1):
            berry = state.berry_connection(other)
            paths.append(
                {
                    "from": gid,
                    "to": other_id,
                    "rank": rank,
                    "marker": "⟦H2048→T36⟧",
                    "path_type": "canonical_orbital_relation_v1",
                    "angular_distance_36d": round(state.angular_distance(other), 12),
                    "semantic_mass_log_distance": round(
                        abs(math.log(state.semantic_mass / other.semantic_mass)), 12
                    ),
                    "binary_log_radius_distance": round(
                        abs(state.log_radius - other.log_radius), 12
                    ),
                    "berry_connection": round(berry, 12),
                    "edge_weight": round(distance * (1.0 + abs(berry)), 12),
                    "epistemic_operator": "chyba",
                }
            )
        card = {
            "$schema": "phasenav.card.h2048_t36.v1",
            "card_id": f"PNV-H2048-{gid}",
            **seed,
            "canon": {
                "version": "1.0.0",
                "status": "CANON",
                "quality_operator": "TO_JEST_MOJE",
                "issuer": "Adrian Lipa",
            },
            "hilbert_state": {
                "space": "C^2048",
                "basis_bits": 11,
                "generator": state.hilbert.generator,
                "state_digest_sha256": _state_digest(state),
                "normalised": True,
            },
            "binary_complement": {
                "involution": "Jψ[j]=conj(ψ[j xor 2047])",
                "p_plus": round(state.p_plus, 15),
                "p_minus": round(state.p_minus, 15),
                "q_ratio": round(state.q_ratio, 15),
                "log_radius": round(state.log_radius, 15),
                "half_deficit": round(state.half_deficit, 15),
                "fixed_point_residual": round(state.fixed_point_residual, 15),
            },
            "phase_marker_36d": {
                "marker": "⟦H2048→T36⟧",
                "space": "T^36",
                "coordinate_semantics": "phase_angles_radians",
                "vector": list(state.phase36),
                "mean_phase": round(state.mean_phase, 12),
                "order_parameter_R": round(state.order_parameter, 12),
            },
            "semantic_mass_canon": round(state.semantic_mass, 15),
            "algorithm_bindings": _algorithm_bindings(seed["canonical_name"], gid),
            "emergent_paths_canon": paths,
        }
        canonical_payload = json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        card["content_digest_sha256"] = hashlib.sha256(
            canonical_payload.encode("utf-8")
        ).hexdigest()
        cards.append(card)
    return tuple(cards)


def load_canonical_cards() -> list[dict]:
    """Return fresh dictionaries so callers cannot mutate the cached canon."""
    return json.loads(json.dumps(_registry_tuple(), ensure_ascii=False))


def card_by_id(glossary_id: str) -> dict:
    key = str(glossary_id).zfill(3)
    for card in load_canonical_cards():
        if card["glossary_id"] == key:
            return card
    raise KeyError(key)


def emergent_path(start: str, target: str, *, max_steps: int = 12) -> dict | None:
    cards = {card["glossary_id"]: card for card in load_canonical_cards()}
    start = str(start).zfill(3)
    target = str(target).zfill(3)
    if start not in cards or target not in cards:
        raise KeyError(start if start not in cards else target)
    frontier: list[tuple[float, tuple[str, ...]]] = [(0.0, (start,))]
    best: dict[str, float] = {start: 0.0}
    while frontier:
        frontier.sort(key=lambda item: (item[0], item[1]))
        cost, path = frontier.pop(0)
        node = path[-1]
        if node == target:
            return {"path": list(path), "cost": cost, "marker": "⟦H2048→T36-path⟧"}
        if len(path) > max_steps:
            continue
        for edge in cards[node]["emergent_paths_canon"]:
            nxt = edge["to"]
            if nxt in path:
                continue
            new_cost = cost + float(edge["edge_weight"])
            if new_cost < best.get(nxt, math.inf):
                best[nxt] = new_cost
                frontier.append((new_cost, path + (nxt,)))
    return None
