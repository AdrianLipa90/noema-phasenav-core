from __future__ import annotations
from copy import deepcopy
from typing import Any
import hashlib, json

FORBIDDEN_KEYS = {"chain_of_thought", "cot", "hidden_reasoning", "private_reasoning", "scratchpad"}

class TelemetryError(ValueError):
    pass

def _canon(x: Any) -> bytes:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha(x: Any) -> str:
    return hashlib.sha256(_canon(x)).hexdigest()

def _selected_map(braid: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {x["trace_id"]: x for x in braid.get("selected", [])}

def build_selection_telemetry(*, cue: dict[str, Any], baseline_braid: dict[str, Any], modulated_braid: dict[str, Any], affect_state: dict[str, Any] | None) -> dict[str, Any]:
    base = _selected_map(baseline_braid)
    mod = _selected_map(modulated_braid)
    bset, mset = set(base), set(mod)
    added = sorted(mset - bset)
    removed = sorted(bset - mset)
    unchanged = sorted(bset & mset)
    per_trace = []
    for tid in sorted(mset):
        item = mod[tid]
        features = item.get("features", {})
        per_trace.append({
            "trace_id": tid,
            "layer": item.get("layer"),
            "recall_class": item.get("recall_class"),
            "selection_reasons": list(item.get("reasons", [])),
            "mandatory_reasons": [r for r in item.get("reasons", []) if not r.startswith("PARETO_FRONT_") and r != "EXPLICIT_AFFECTIVE_SALIENCE"],
            "semantic_signal": {"goal_overlap": features.get("goal_overlap"), "tag_overlap": features.get("tag_overlap"), "relation_proximity": features.get("relation_proximity")},
            "affective_signal": {"relevant": bool(features.get("affect_relevance", False)), "axes": deepcopy(features.get("affect_axes", {})), "peak": features.get("affect_peak", 0.0), "match_count": features.get("affect_match_count", 0)},
            "provenance_rank": features.get("provenance_rank"),
            "phase_distance": features.get("phase_distance"),
            "changed_by_affect": tid in added,
        })
    policy = modulated_braid.get("affective_salience", {}).get("policy", {})
    body = {
        "schema": "NOEMA_COGNITIVE_TELEMETRY_V1",
        "cue_id": cue.get("cue_id"),
        "session_id": cue.get("session_id"),
        "observable_only": True,
        "hidden_chain_of_thought_persisted": False,
        "affect_state_sha256": None if affect_state is None else affect_state.get("state_sha256"),
        "attention_policy": deepcopy(policy),
        "selection_delta": {"added_by_modulation": added, "removed_by_modulation": removed, "unchanged": unchanged},
        "selected_trace_telemetry": per_trace,
        "epistemic_invariants": {"affect_is_truth": False, "affect_grants_authority": False, "recall_authorizes_execution": False, "phase_is_truth": False},
    }
    forbidden_present = []
    def walk(x: Any, path: str = "$"):
        if isinstance(x, dict):
            for k, v in x.items():
                if k.lower() in FORBIDDEN_KEYS:
                    forbidden_present.append(path + "." + k)
                walk(v, path + "." + k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
    walk(body)
    if forbidden_present:
        raise TelemetryError(f"forbidden hidden-reasoning fields: {forbidden_present}")
    body["telemetry_sha256"] = _sha(body)
    return body
