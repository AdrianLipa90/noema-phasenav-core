from __future__ import annotations

from copy import deepcopy
from collections import defaultdict
from typing import Any
import hashlib
import json
import math

from . import memory_orchestrator as mo

SCHEMA = "NOEMA_AFFECTIVE_SALIENCE_MODULATOR_V1"
FUNCTIONAL_AXES = (
    "urgency",
    "threat",
    "attachment",
    "care",
    "curiosity",
    "reward",
    "aversion",
)
VAD_AXES = ("valence", "arousal", "dominance")
ALLOWED_SOURCES = {
    "EXPLICIT_USER_REPORT",
    "EXPLICIT_OPERATOR_STATE",
    "VALIDATED_SENSOR",
    "EXPLICIT_SYSTEM_DECLARATION",
}
ALLOWED_AFFORDANCE_SOURCES = {
    "EXPLICIT",
    "VALIDATED_ANNOTATION",
    "RECEIPTED_EVENT",
}

class AffectiveSalienceError(ValueError):
    pass

def _canon(x: Any) -> bytes:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha(x: Any) -> str:
    return hashlib.sha256(_canon(x)).hexdigest()

def _finite01(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x)) and 0.0 <= float(x) <= 1.0

def _finite_signed(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x)) and -1.0 <= float(x) <= 1.0

def validate_affect_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    if state is None:
        return None
    if not isinstance(state, dict):
        raise AffectiveSalienceError("affect state must be an object")
    if state.get("schema") != "NOEMA_AFFECT_STATE_V1":
        raise AffectiveSalienceError("unsupported affect schema")
    if state.get("inferred") is not False:
        raise AffectiveSalienceError("automatic/inferred affect is forbidden")
    if state.get("source_type") not in ALLOWED_SOURCES:
        raise AffectiveSalienceError("affect source is not explicitly admissible")
    axes = state.get("axes", {})
    if not isinstance(axes, dict):
        raise AffectiveSalienceError("affect axes must be an object")
    for axis in FUNCTIONAL_AXES:
        if axis in axes and not _finite01(axes[axis]):
            raise AffectiveSalienceError(f"invalid affect axis {axis}")
    if "valence" in axes and not _finite_signed(axes["valence"]):
        raise AffectiveSalienceError("invalid valence")
    for axis in ("arousal", "dominance"):
        if axis in axes and not _finite01(axes[axis]):
            raise AffectiveSalienceError(f"invalid {axis}")
    body = deepcopy(state)
    got = body.pop("state_sha256", None)
    digest = _sha(body)
    if got is not None and got != digest:
        raise AffectiveSalienceError("affect state hash mismatch")
    body["state_sha256"] = digest
    return body

def seal_affect_state(state: dict[str, Any]) -> dict[str, Any]:
    body = deepcopy(state)
    body.pop("state_sha256", None)
    body["state_sha256"] = _sha(body)
    return validate_affect_state(body)

def validate_affordance(trace: dict[str, Any]) -> dict[str, Any] | None:
    aff = trace.get("affective_affordance")
    if aff is None:
        return None
    if not isinstance(aff, dict):
        raise AffectiveSalienceError("trace affective_affordance must be an object")
    if aff.get("schema") != "NOEMA_AFFECTIVE_AFFORDANCE_V1":
        raise AffectiveSalienceError("unsupported affective affordance schema")
    if aff.get("source_type") not in ALLOWED_AFFORDANCE_SOURCES:
        raise AffectiveSalienceError("unadmitted affective affordance source")
    axes = aff.get("axes", {})
    if not isinstance(axes, dict):
        raise AffectiveSalienceError("affordance axes must be an object")
    for axis in FUNCTIONAL_AXES:
        if axis in axes and not _finite01(axes[axis]):
            raise AffectiveSalienceError(f"invalid affordance axis {axis}")
    if not aff.get("provenance_refs"):
        raise AffectiveSalienceError("affective affordance requires provenance refs")
    return aff

def affective_features(state: dict[str, Any] | None, trace: dict[str, Any]) -> dict[str, Any]:
    if state is None:
        return {"affect_relevance": False, "affect_peak": 0.0, "affect_match_count": 0, "affect_axes": {}}
    aff = validate_affordance(trace)
    if aff is None:
        return {"affect_relevance": False, "affect_peak": 0.0, "affect_match_count": 0, "affect_axes": {}}
    sx = state.get("axes", {})
    tx = aff.get("axes", {})
    matches: dict[str, float] = {}
    for axis in FUNCTIONAL_AXES:
        value = float(sx.get(axis, 0.0)) * float(tx.get(axis, 0.0))
        if value > 0.0:
            matches[axis] = value
    return {
        "affect_relevance": bool(matches),
        "affect_peak": max(matches.values(), default=0.0),
        "affect_match_count": len(matches),
        "affect_axes": dict(sorted(matches.items())),
    }

def attention_policy(cue: dict[str, Any], state: dict[str, Any] | None) -> dict[str, Any]:
    base_budget = int(cue.get("budget", {}).get("max_items", 12))
    base_hops = int(cue.get("budget", {}).get("relation_hops", 2))
    if state is None:
        return {"mode": "BASELINE", "max_items": base_budget, "relation_hops": base_hops, "preferred_layers": [], "reason_axes": [], "authority_effect": False, "truth_effect": False}
    a = state.get("axes", {})
    urgency = float(a.get("urgency", 0.0))
    threat = float(a.get("threat", 0.0))
    curiosity = float(a.get("curiosity", 0.0))
    attachment = float(a.get("attachment", 0.0))
    care = float(a.get("care", 0.0))
    if max(urgency, threat) >= 0.75:
        return {"mode": "FOCUSED_PROTECTIVE", "max_items": max(6, min(base_budget, 12)), "relation_hops": max(0, base_hops - 1), "preferred_layers": ["M4", "M10", "M11", "M6", "M2", "M9", "M3", "M7", "M5", "M0", "M1"], "reason_axes": [k for k in ("urgency", "threat") if float(a.get(k, 0.0)) >= 0.75], "authority_effect": False, "truth_effect": False}
    if curiosity >= 0.65 and threat < 0.50:
        return {"mode": "EXPLORATORY", "max_items": min(16, base_budget + 2), "relation_hops": min(3, base_hops + 1), "preferred_layers": ["M3", "M6", "M7", "M9", "M2", "M4", "M10", "M11", "M5", "M0", "M1"], "reason_axes": ["curiosity"], "authority_effect": False, "truth_effect": False}
    if max(attachment, care) >= 0.65:
        return {"mode": "RELATIONAL", "max_items": base_budget, "relation_hops": base_hops, "preferred_layers": ["M6", "M7", "M2", "M9", "M3", "M4", "M10", "M11", "M5", "M0", "M1"], "reason_axes": [k for k in ("attachment", "care") if float(a.get(k, 0.0)) >= 0.65], "authority_effect": False, "truth_effect": False}
    return {"mode": "MODULATED_STABLE", "max_items": base_budget, "relation_hops": base_hops, "preferred_layers": [], "reason_axes": [], "authority_effect": False, "truth_effect": False}

_MAX_KEYS_V2 = ("goal_overlap", "tag_overlap", "provenance_rank", "temporal_order", "relation_proximity", "phase_affinity", "affect_peak", "affect_match_count")

def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    common = [k for k in _MAX_KEYS_V2 if a.get(k) is not None and b.get(k) is not None]
    if not common:
        return False
    return all(a[k] >= b[k] for k in common) and any(a[k] > b[k] for k in common)

def _pareto_fronts(items: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    remaining = list(items)
    fronts: list[list[dict[str, Any]]] = []
    while remaining:
        front = [x for x in remaining if not any(y is not x and _dominates(y["features"], x["features"]) for y in remaining)]
        front.sort(key=lambda z: (z["trace"]["layer"], z["trace"]["trace_id"], z["trace"]["trace_sha256"]))
        fronts.append(front)
        ids = {id(x) for x in front}
        remaining = [x for x in remaining if id(x) not in ids]
    return fronts

def _layer_order(policy: dict[str, Any]) -> dict[str, int]:
    return {layer: i for i, layer in enumerate(policy.get("preferred_layers", []))}

def _layer_round_robin(front: list[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in front:
        by[x["trace"]["layer"]].append(x)
    for layer in by:
        by[layer].sort(key=lambda z: (-z["features"]["affect_peak"], -z["features"]["affect_match_count"], -z["features"]["provenance_rank"], -z["features"]["temporal_order"], z["trace"]["trace_sha256"]))
    order = _layer_order(policy)
    layers = sorted(by, key=lambda layer: (order.get(layer, 10_000), layer))
    out: list[dict[str, Any]] = []
    while any(by.values()):
        for layer in layers:
            if by[layer]:
                out.append(by[layer].pop(0))
    return out

def _objective_features(cue: dict[str, Any], trace: dict[str, Any], relation_distance: int | None, state: dict[str, Any] | None) -> dict[str, Any]:
    return {**mo.objective_features(cue, trace, relation_distance), **affective_features(state, trace)}

def orchestrate_with_affect(cue: dict[str, Any], traces: list[dict[str, Any]], affect_state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = validate_affect_state(affect_state)
    if state is None:
        baseline = mo.orchestrate(cue, traces)
        out = deepcopy(baseline)
        out["schema"] = "NOEMA_RECALL_BRAID_V2_AFFECTIVE"
        out["affective_salience"] = {"state_ref": None, "policy": attention_policy(cue, None), "causal_effect": "NONE", "truth_effect": False, "authority_effect": False}
        out["braid_sha256"] = _sha({k: v for k, v in out.items() if k != "braid_sha256"})
        return out
    for trace in traces:
        mo.verify_trace(trace)
        validate_affordance(trace)
    policy = attention_policy(cue, state)
    cue2 = deepcopy(cue)
    cue2["budget"] = {"max_items": policy["max_items"], "relation_hops": policy["relation_hops"]}
    budget = int(policy["max_items"])
    hops = int(policy["relation_hops"])
    inhibited: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    for t in traces:
        if t.get("status") != "ACTIVE":
            inhibited.append({"trace_id": t["trace_id"], "reason": f"STATUS_{t.get('status')}"})
            continue
        if t.get("layer") == "M8" and not cue2.get("identity_required", False):
            inhibited.append({"trace_id": t["trace_id"], "reason": "M8_NOT_EXPLICITLY_REQUIRED"})
            continue
        if mo.provenance_rank(t) == 0:
            inhibited.append({"trace_id": t["trace_id"], "reason": "PROVENANCE_UNKNOWN"})
            continue
        eligible.append(t)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in eligible:
        groups[mo.semantic_key(t)].append(t)
    dedup: list[dict[str, Any]] = []
    for group in groups.values():
        group.sort(key=lambda t: (-mo.provenance_rank(t), -int(t.get("temporal_order", 0)), t["trace_sha256"]))
        keep = group[0]
        dedup.append(keep)
        for t in group[1:]:
            inhibited.append({"trace_id": t["trace_id"], "reason": "SEMANTIC_DUPLICATE", "kept": keep["trace_id"]})
    eligible = sorted(dedup, key=lambda t: t["trace_id"])
    mandatory: dict[str, list[str]] = {}
    for t in eligible:
        rs = mo.mandatory_reasons(cue2, t)
        if rs:
            mandatory[t["trace_id"]] = rs
    cue_tokens = mo._tokens(cue2.get("goal", "")) | mo._tokens(cue2.get("focus", {})) | mo._tokens(cue2.get("evidence_needs", []))
    seeds = set(mandatory)
    for t in eligible:
        lexical = cue_tokens & (mo._tokens(t.get("content", {})) | mo._tokens(t.get("semantic_tags", [])))
        if lexical or affective_features(state, t)["affect_relevance"]:
            seeds.add(t["trace_id"])
    distances, paths = mo.relation_distances(eligible, seeds, hops)
    idx = {t["trace_id"]: t for t in eligible}
    changed = True
    while changed:
        changed = False
        anchors = set(mandatory) | seeds
        for aid in list(anchors):
            t = idx.get(aid)
            if not t:
                continue
            for r in t.get("relations", []):
                if r.get("type") == "CONFLICTS_WITH" and r.get("status", "OPEN") == "OPEN":
                    target = r.get("target")
                    if target in idx and target not in mandatory:
                        mandatory[target] = ["OPEN_CONFLICT_COUNTERPART"]
                        changed = True
    candidates: list[dict[str, Any]] = []
    for t in eligible:
        features = _objective_features(cue2, t, distances.get(t["trace_id"]), state)
        reasons = mandatory.get(t["trace_id"], [])
        nonphase_relevant = bool(reasons) or features["goal_overlap"] > 0 or features["tag_overlap"] > 0 or features["relation_proximity"] is not None or features["affect_relevance"]
        if not nonphase_relevant:
            inhibited.append({"trace_id": t["trace_id"], "reason": "NO_NONPHASE_RELEVANCE_SIGNAL"})
            continue
        candidates.append({"trace": t, "mandatory_reasons": reasons, "features": features})
    must = [x for x in candidates if x["mandatory_reasons"]]
    must.sort(key=lambda x: (x["trace"]["layer"], x["trace"]["trace_id"]))
    selected = list(must)
    selected_ids = {x["trace"]["trace_id"] for x in selected}
    remaining = [x for x in candidates if x["trace"]["trace_id"] not in selected_ids]
    for front_no, front in enumerate(_pareto_fronts(remaining), start=1):
        for x in _layer_round_robin(front, policy):
            if len(selected) >= budget and len(selected) >= len(must):
                break
            x["pareto_front"] = front_no
            selected.append(x)
            selected_ids.add(x["trace"]["trace_id"])
        if len(selected) >= budget and len(selected) >= len(must):
            break
    for x in remaining:
        if x["trace"]["trace_id"] not in selected_ids:
            inhibited.append({"trace_id": x["trace"]["trace_id"], "reason": "OUTSIDE_RECALL_BUDGET"})
    out_selected: list[dict[str, Any]] = []
    for x in selected:
        reasons = x["mandatory_reasons"] or [f"PARETO_FRONT_{x.get('pareto_front', 1)}"]
        if x["features"]["affect_relevance"] and not x["mandatory_reasons"]:
            reasons = reasons + ["EXPLICIT_AFFECTIVE_SALIENCE"]
        out_selected.append({"trace_id": x["trace"]["trace_id"], "layer": x["trace"]["layer"], "recall_class": "MUST_RECALL" if x["mandatory_reasons"] else "SHOULD_RECALL", "reasons": reasons, "features": x["features"], "content": x["trace"]["content"], "provenance": x["trace"]["provenance"], "trace_sha256": x["trace"]["trace_sha256"]})
    unresolved: list[dict[str, Any]] = []
    for x in selected:
        for r in x["trace"].get("relations", []):
            if r.get("type") == "CONFLICTS_WITH" and r.get("status", "OPEN") == "OPEN":
                unresolved.append({"a": x["trace"]["trace_id"], "b": r.get("target"), "relation_id": r.get("relation_id")})
    uniq: dict[tuple[Any, ...], dict[str, Any]] = {}
    for c in unresolved:
        uniq[tuple(sorted((c["a"], c["b"]))) + (c.get("relation_id"),)] = c
    unresolved = list(uniq.values())
    layers = sorted({x["layer"] for x in out_selected})
    m1 = {"schema": "NOEMA_M1_RECALL_CONTEXT_V2_AFFECTIVE", "cue_id": cue2["cue_id"], "session_id": cue2["session_id"], "selected_trace_refs": [x["trace_id"] for x in out_selected], "must_recall_refs": [x["trace_id"] for x in out_selected if x["recall_class"] == "MUST_RECALL"], "unresolved_conflicts": unresolved, "affect_state_sha256": state["state_sha256"], "execution_authorized": False, "authority_granted": False, "semantic_claim_promotion": False}
    body = {"schema": "NOEMA_RECALL_BRAID_V2_AFFECTIVE", "cue_id": cue2["cue_id"], "selected": out_selected, "inhibited": sorted(inhibited, key=lambda x: (x["reason"], x["trace_id"])), "relation_paths": paths, "coverage": {"layers": layers, "selected_count": len(out_selected), "budget": budget, "mandatory_count": len(must), "budget_overflow": max(0, len(must) - budget)}, "unresolved_conflicts": unresolved, "m1_injection": m1, "affective_salience": {"state_ref": state["state_sha256"], "policy": policy, "causal_effect": "RECALL_MODULATION_ONLY", "truth_effect": False, "authority_effect": False, "execution_effect": False}}
    body["braid_sha256"] = _sha(body)
    return body
