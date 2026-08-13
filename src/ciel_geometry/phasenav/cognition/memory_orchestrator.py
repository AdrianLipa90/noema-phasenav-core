from __future__ import annotations
from copy import deepcopy
from collections import defaultdict, deque
from typing import Any
import hashlib, json, math, re

PROFILE="phasenav.representation/t36-text-legacy-v0"
SPACE="T^36"

class MemoryOrchestratorError(ValueError):
    pass

def _canon(x: Any) -> bytes:
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def _sha(x: Any) -> str:
    return hashlib.sha256(_canon(x)).hexdigest()

def _tokens(x: Any) -> set[str]:
    s=json.dumps(x,ensure_ascii=False,sort_keys=True) if not isinstance(x,str) else x
    return set(re.findall(r"[a-zA-Z0-9_]+(?:[/:.-][a-zA-Z0-9_]+)*",s.lower()))

def _finite36(v: Any) -> bool:
    return isinstance(v,(list,tuple)) and len(v)==36 and all(
        isinstance(x,(int,float)) and math.isfinite(float(x)) for x in v
    )

def _wrap_pi(x: float)->float:
    return (float(x)+math.pi)%(2*math.pi)-math.pi

def phase_distance(a: list[float]|None,b: list[float]|None)->float|None:
    if not (_finite36(a) and _finite36(b)):
        return None
    return math.sqrt(sum(_wrap_pi(y-x)**2 for x,y in zip(a,b)))

def seal_trace(trace: dict[str,Any])->dict[str,Any]:
    out=deepcopy(trace); out.pop("trace_sha256",None)
    out["trace_sha256"]=_sha(out)
    return out

def verify_trace(trace: dict[str,Any])->bool:
    body=deepcopy(trace); got=body.pop("trace_sha256",None)
    if got!=_sha(body):
        raise MemoryOrchestratorError("trace hash mismatch")
    pb=trace.get("phase_binding",{})
    if pb.get("status")=="BOUND_VALIDATED":
        if pb.get("space")!="T^36" or not _finite36(pb.get("vector")):
            raise MemoryOrchestratorError("invalid bound phase")
    return True

def bind_trace(trace: dict[str,Any],adapter: Any)->dict[str,Any]:
    text="NOEMA_MEMORY_TRACE_V1\n"+json.dumps({
        "layer":trace["layer"],
        "content":trace["content"],
        "semantic_tags":trace.get("semantic_tags",[]),
        "epistemic_state":trace.get("epistemic_state"),
        "relations":trace.get("relations",[])
    },ensure_ascii=False,sort_keys=True,separators=(",",":"))
    ps=adapter.encode_text(text,profile=PROFILE)
    v=list(ps.coordinates)
    if not _finite36(v):
        raise MemoryOrchestratorError("adapter returned invalid phase")
    out=deepcopy(trace)
    out["phase_binding"]={
        "status":"BOUND_VALIDATED","space":"T^36","vector":v,
        "representation_profile":PROFILE,
        "adapter_manifest_digest_sha256":adapter.manifest.digest_sha256
    }
    return seal_trace(out)

def provenance_rank(trace: dict[str,Any])->int:
    s=str(trace.get("provenance",{}).get("status","UNKNOWN")).upper()
    return {"VERIFIED":4,"RECEIPTED":3,"PARTIAL":2,"UNVERIFIED":1,"UNKNOWN":0}.get(s,0)

def semantic_key(trace: dict[str,Any])->str:
    return _sha({"content":trace.get("content"),"semantic_tags":sorted(trace.get("semantic_tags",[]))})

def mandatory_reasons(cue: dict[str,Any],trace: dict[str,Any])->list[str]:
    reasons=[]
    text_tokens=_tokens(trace.get("content",{})) | _tokens(trace.get("semantic_tags",[]))
    for p in cue.get("active_no_go_patterns",[]):
        pt=_tokens(p)
        if pt and pt.issubset(text_tokens):
            reasons.append("ACTIVE_NO_GO_MATCH")
            break
    for need in cue.get("evidence_needs",[]):
        nt=_tokens(need)
        if nt and nt.issubset(text_tokens):
            reasons.append("EVIDENCE_NEED_MATCH")
            break
    refs=set(cue.get("direct_parent_refs",[]))
    if trace.get("trace_id") in refs or refs.intersection(set(trace.get("provenance",{}).get("refs",[]))):
        reasons.append("DIRECT_CAUSAL_PARENT")
    if trace.get("layer")=="M8" and cue.get("identity_required"):
        reasons.append("IDENTITY_CONTEXT_EXPLICIT")
    return sorted(set(reasons))

def objective_features(cue: dict[str,Any],trace: dict[str,Any],relation_distance:int|None)->dict[str,Any]:
    cue_tokens=_tokens(cue.get("goal",""))|_tokens(cue.get("focus",{}))|_tokens(cue.get("hypotheses",[]))|_tokens(cue.get("evidence_needs",[]))
    tt=_tokens(trace.get("content",{}))|_tokens(trace.get("semantic_tags",[]))
    overlap=len(cue_tokens & tt)
    tag_overlap=len(_tokens(cue.get("focus",{})) & _tokens(trace.get("semantic_tags",[])))
    pd=phase_distance(cue.get("phase36"),trace.get("phase_binding",{}).get("vector"))
    return {
        "goal_overlap":overlap,
        "tag_overlap":tag_overlap,
        "provenance_rank":provenance_rank(trace),
        "temporal_order":int(trace.get("temporal_order",0)),
        "relation_proximity":None if relation_distance is None else -relation_distance,
        "phase_affinity":None if pd is None else -pd,
        "phase_distance":pd
    }

_MAX_KEYS=("goal_overlap","tag_overlap","provenance_rank","temporal_order","relation_proximity","phase_affinity")

def dominates(a:dict[str,Any],b:dict[str,Any])->bool:
    common=[k for k in _MAX_KEYS if a.get(k) is not None and b.get(k) is not None]
    if not common:
        return False
    ge=all(a[k]>=b[k] for k in common)
    gt=any(a[k]>b[k] for k in common)
    return ge and gt

def pareto_fronts(items:list[dict[str,Any]])->list[list[dict[str,Any]]]:
    remaining=list(items); fronts=[]
    while remaining:
        front=[]
        for x in remaining:
            if not any(y is not x and dominates(y["features"],x["features"]) for y in remaining):
                front.append(x)
        front=sorted(front,key=lambda z:(z["trace"]["layer"],z["trace"]["trace_id"],z["trace"]["trace_sha256"]))
        fronts.append(front)
        ids={id(x) for x in front}
        remaining=[x for x in remaining if id(x) not in ids]
    return fronts

def _layer_round_robin(front:list[dict[str,Any]])->list[dict[str,Any]]:
    by=defaultdict(list)
    for x in front:
        by[x["trace"]["layer"]].append(x)
    for layer in by:
        by[layer].sort(key=lambda z:(-z["features"]["provenance_rank"],-z["features"]["temporal_order"],z["trace"]["trace_sha256"]))
    layers=sorted(by)
    out=[]
    while any(by.values()):
        for layer in layers:
            if by[layer]:
                out.append(by[layer].pop(0))
    return out

def relation_distances(traces:list[dict[str,Any]],seed_ids:set[str],max_hops:int)->tuple[dict[str,int],list[dict[str,Any]]]:
    index={t["trace_id"]:t for t in traces}
    adj=defaultdict(list)
    for t in traces:
        for r in t.get("relations",[]):
            target=r.get("target")
            if target in index:
                adj[t["trace_id"]].append((target,r.get("type","RELATED")))
                if r.get("symmetric",False):
                    adj[target].append((t["trace_id"],r.get("type","RELATED")))
    d={s:0 for s in sorted(seed_ids) if s in index}; paths=[]
    q=deque(d)
    while q:
        u=q.popleft()
        if d[u]>=max_hops: continue
        for v,typ in sorted(adj[u]):
            if v not in d:
                d[v]=d[u]+1
                paths.append({"from":u,"to":v,"type":typ,"hops":d[v]})
                q.append(v)
    return d,paths

def orchestrate(cue:dict[str,Any],traces:list[dict[str,Any]])->dict[str,Any]:
    for t in traces: verify_trace(t)
    budget=int(cue.get("budget",{}).get("max_items",12))
    hops=int(cue.get("budget",{}).get("relation_hops",2))

    inhibited=[]
    eligible=[]
    for t in traces:
        if t.get("status")!="ACTIVE":
            inhibited.append({"trace_id":t["trace_id"],"reason":f"STATUS_{t.get('status')}"})
            continue
        if t.get("layer")=="M8" and not cue.get("identity_required",False):
            inhibited.append({"trace_id":t["trace_id"],"reason":"M8_NOT_EXPLICITLY_REQUIRED"})
            continue
        if provenance_rank(t)==0:
            inhibited.append({"trace_id":t["trace_id"],"reason":"PROVENANCE_UNKNOWN"})
            continue
        eligible.append(t)

    groups=defaultdict(list)
    for t in eligible: groups[semantic_key(t)].append(t)
    dedup=[]
    for _,group in groups.items():
        group.sort(key=lambda t:(-provenance_rank(t),-int(t.get("temporal_order",0)),t["trace_sha256"]))
        keep=group[0]; dedup.append(keep)
        for t in group[1:]:
            inhibited.append({"trace_id":t["trace_id"],"reason":"SEMANTIC_DUPLICATE","kept":keep["trace_id"]})
    eligible=sorted(dedup,key=lambda t:t["trace_id"])

    mandatory={}
    for t in eligible:
        rs=mandatory_reasons(cue,t)
        if rs: mandatory[t["trace_id"]]=rs

    cue_tokens=_tokens(cue.get("goal",""))|_tokens(cue.get("focus",{}))|_tokens(cue.get("evidence_needs",[]))
    seeds=set(mandatory)
    for t in eligible:
        if cue_tokens & (_tokens(t.get("content",{}))|_tokens(t.get("semantic_tags",[]))):
            seeds.add(t["trace_id"])
    distances,paths=relation_distances(eligible,seeds,hops)

    idx={t["trace_id"]:t for t in eligible}
    changed=True
    while changed:
        changed=False
        anchors=set(mandatory)|seeds
        for aid in list(anchors):
            t=idx.get(aid)
            if not t: continue
            for r in t.get("relations",[]):
                if r.get("type")=="CONFLICTS_WITH" and r.get("status","OPEN")=="OPEN":
                    target=r.get("target")
                    if target in idx and target not in mandatory:
                        mandatory[target]=["OPEN_CONFLICT_COUNTERPART"]
                        changed=True

    candidates=[]
    for t in eligible:
        features=objective_features(cue,t,distances.get(t["trace_id"]))
        reasons=mandatory.get(t["trace_id"],[])
        nonphase_relevant=(
            bool(reasons)
            or features["goal_overlap"]>0
            or features["tag_overlap"]>0
            or features["relation_proximity"] is not None
        )
        if not nonphase_relevant:
            inhibited.append({"trace_id":t["trace_id"],"reason":"NO_NONPHASE_RELEVANCE_SIGNAL"})
            continue
        candidates.append({
            "trace":t,
            "mandatory_reasons":reasons,
            "features":features
        })

    must=[x for x in candidates if x["mandatory_reasons"]]
    must.sort(key=lambda x:(x["trace"]["layer"],x["trace"]["trace_id"]))
    selected=list(must)
    selected_ids={x["trace"]["trace_id"] for x in selected}

    remaining=[x for x in candidates if x["trace"]["trace_id"] not in selected_ids]
    for front_no,front in enumerate(pareto_fronts(remaining),start=1):
        for x in _layer_round_robin(front):
            if len(selected)>=budget and len(selected)>=len(must):
                break
            x["pareto_front"]=front_no
            selected.append(x); selected_ids.add(x["trace"]["trace_id"])
        if len(selected)>=budget and len(selected)>=len(must):
            break

    for x in remaining:
        if x["trace"]["trace_id"] not in selected_ids:
            inhibited.append({"trace_id":x["trace"]["trace_id"],"reason":"OUTSIDE_RECALL_BUDGET"})

    out_selected=[]
    for x in selected:
        out_selected.append({
            "trace_id":x["trace"]["trace_id"],
            "layer":x["trace"]["layer"],
            "recall_class":"MUST_RECALL" if x["mandatory_reasons"] else "SHOULD_RECALL",
            "reasons":x["mandatory_reasons"] or [f"PARETO_FRONT_{x.get('pareto_front',1)}"],
            "features":x["features"],
            "content":x["trace"]["content"],
            "provenance":x["trace"]["provenance"],
            "trace_sha256":x["trace"]["trace_sha256"]
        })

    unresolved=[]
    for x in selected:
        for r in x["trace"].get("relations",[]):
            if r.get("type")=="CONFLICTS_WITH" and r.get("status","OPEN")=="OPEN":
                unresolved.append({"a":x["trace"]["trace_id"],"b":r.get("target"),"relation_id":r.get("relation_id")})
    uniq={}
    for c in unresolved:
        key=tuple(sorted((c["a"],c["b"])))+(c.get("relation_id"),)
        uniq[key]=c
    unresolved=list(uniq.values())

    layers=sorted({x["layer"] for x in out_selected})
    m1={
        "schema":"NOEMA_M1_RECALL_CONTEXT_V1",
        "cue_id":cue["cue_id"],
        "session_id":cue["session_id"],
        "selected_trace_refs":[x["trace_id"] for x in out_selected],
        "must_recall_refs":[x["trace_id"] for x in out_selected if x["recall_class"]=="MUST_RECALL"],
        "unresolved_conflicts":unresolved,
        "execution_authorized":False
    }
    body={
        "schema":"NOEMA_RECALL_BRAID_V1",
        "cue_id":cue["cue_id"],
        "selected":out_selected,
        "inhibited":sorted(inhibited,key=lambda x:(x["reason"],x["trace_id"])),
        "relation_paths":paths,
        "coverage":{"layers":layers,"selected_count":len(out_selected),"budget":budget,
                    "mandatory_count":len(must),"budget_overflow":max(0,len(must)-budget)},
        "unresolved_conflicts":unresolved,
        "m1_injection":m1
    }
    body["braid_sha256"]=_sha(body)
    return body

def consolidation_plan(source_result_ref:str,explicit:dict[str,Any])->dict[str,Any]:
    writes=[]; skips=[]
    mapping=[
      ("episode","M2"),("semantic","M3"),("procedure","M4"),("relations","M6"),
      ("braid","M7"),("trajectory","M9"),("provenance","M10"),("metacognition","M11")
    ]
    for key,layer in mapping:
        if key in explicit and explicit[key] not in (None,[],{},""):
            writes.append({"layer":layer,"kind":key,"value":explicit[key],"mode":"CANDIDATE_AFTER_VALIDATION"})
    if explicit.get("affect") not in (None,[],{},""):
        if explicit.get("affect_explicitly_supplied") is True:
            writes.append({"layer":"M5","kind":"affect","value":explicit["affect"],"mode":"EXPLICIT_ONLY"})
        else:
            skips.append({"layer":"M5","reason":"NO_AUTOMATIC_AFFECT_INFERENCE"})
    if explicit.get("identity") not in (None,[],{},""):
        if explicit.get("owner_authorized_identity_write") is True:
            writes.append({"layer":"M8","kind":"identity","value":explicit["identity"],"mode":"ROOT_AUTHORITY_REQUIRED"})
        else:
            skips.append({"layer":"M8","reason":"PROTECTED_ROOT_AUTHORITY_REQUIRED"})
    body={
      "schema":"NOEMA_MEMORY_CONSOLIDATION_PLAN_V1",
      "source_result_ref":source_result_ref,
      "writes":writes,
      "protected_skips":skips,
      "validation_required":True,
      "direct_write":False
    }
    body["plan_sha256"]=_sha(body)
    return body

def replay_priority(trace:dict[str,Any])->tuple:
    """Class precedence only; no learned or weighted scalar salience."""
    open_conflict=any(r.get("type")=="CONFLICTS_WITH" and r.get("status","OPEN")=="OPEN" for r in trace.get("relations",[]))
    has_nogo=bool(trace.get("content",{}).get("no_go_id") or trace.get("semantic_tags") and "no-go" in [x.lower() for x in trace["semantic_tags"]])
    return (
      0 if open_conflict else 1,
      0 if has_nogo else 1,
      -provenance_rank(trace),
      -int(trace.get("temporal_order",0)),
      trace["trace_sha256"]
    )

def replay_queue(traces:list[dict[str,Any]],limit:int=20)->list[str]:
    live=[t for t in traces if t.get("status")=="ACTIVE" and provenance_rank(t)>0 and t.get("layer")!="M8"]
    return [t["trace_id"] for t in sorted(live,key=replay_priority)[:limit]]
