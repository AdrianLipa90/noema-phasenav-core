from __future__ import annotations
from pathlib import Path
import argparse, json, math, hashlib, datetime, collections

TAU = 2.0 * math.pi

def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",",":")).encode()

def digest(obj):
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z")

def torus_delta(q, r):
    if len(q) != 36 or len(r) != 36:
        raise ValueError("PNV36 requires 36 coordinates")
    return [((b-a+0.5) % 1.0)-0.5 for a,b in zip(q,r)]

def to_turns(phase):
    return [(x/TAU) % 1.0 for x in phase]

def from_turns(q):
    return [(x % 1.0)*TAU for x in q]

def l2(v):
    return math.sqrt(sum(x*x for x in v))

def project(a,b):
    den=sum(x*x for x in b)
    if den == 0.0:
        raise ValueError("cannot project onto zero vector")
    s=sum(x*y for x,y in zip(a,b))/den
    return [s*x for x in b]

def orthogonalize(vectors, eps=1e-12):
    out=[]
    for v in vectors:
        u=list(v)
        for q in out:
            den=sum(x*x for x in q)
            if den > eps:
                s=sum(x*y for x,y in zip(u,q))/den
                u=[x-s*y for x,y in zip(u,q)]
        if l2(u) > eps:
            out.append(u)
    return out

class PNVPlatform:
    def __init__(self, canon_path, overlay_path=None, receipt_path=None):
        self.canon_path=Path(canon_path)
        self.canon=json.loads(self.canon_path.read_text(encoding="utf-8"))
        self.overlay_path=Path(overlay_path) if overlay_path else None
        self.receipt_path=Path(receipt_path) if receipt_path else None
        self._rebuild()

    def _overlay_events(self):
        if not self.overlay_path or not self.overlay_path.exists():
            return []
        out=[]
        for line in self.overlay_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out

    def _rebuild(self):
        self.concepts={x["id"]:dict(x) for x in self.canon["concepts"]}
        self.words=collections.defaultdict(list)
        for w in self.canon["words"]:
            self.words[w["word"].casefold()].append(w["concept_id"])
        self.vectors={k:dict(v) for k,v in self.canon["vectors"].items()}
        self.relations=[dict(x) for x in self.canon["relations"]]
        self.paths={x["path_id"]:dict(x) for x in self.canon["paths"]}
        self.gates={x["id"]:dict(x) for x in self.canon["gates"]}
        self.operators={x["id"]:dict(x) for x in self.canon["operators"]}
        for ev in self._overlay_events():
            if ev.get("result") != "COMMITTED":
                continue
            p=ev["payload"]; kind=ev["mutation_kind"]
            if kind=="ADD_CONCEPT":
                self.concepts[p["id"]]=dict(p)
            elif kind=="ADD_ALIAS":
                self.words[p["word"].casefold()].append(p["concept_id"])
            elif kind=="ADD_RELATION":
                self.relations.append(dict(p))
            elif kind=="ADD_VECTOR":
                self.vectors[p["id"]]=dict(p)
            elif kind=="ADD_PATH":
                self.paths[p["path_id"]]=dict(p)

    def status(self):
        return {
            "schema":"PNV_PLATFORM_STATUS_V1",
            "canon_status":self.canon.get("status"),
            "dimension":self.canon.get("dimension"),
            "overlay_events":len(self._overlay_events()),
            "counts":{
                "concepts":len(self.concepts),"words":sum(len(v) for v in self.words.values()),
                "vectors":len(self.vectors),"relations":len(self.relations),
                "paths":len(self.paths),"gates":len(self.gates),"operators":len(self.operators)
            }
        }

    def resolve(self, term):
        ids=[]
        if term in self.concepts:
            ids.append(term)
        ids.extend(self.words.get(term.casefold(),[]))
        seen=set(); out=[]
        for i in ids:
            if i not in seen and i in self.concepts:
                out.append(self.concepts[i]); seen.add(i)
        return out

    def vector(self, ident):
        return self.vectors[ident]

    def nearest(self, ident, k=5):
        if ident not in self.vectors:
            raise KeyError(ident)
        q=to_turns(self.vectors[ident]["phase36"])
        rows=[]
        for other,v in self.vectors.items():
            if other==ident: continue
            d=torus_delta(q,to_turns(v["phase36"]))
            rows.append({"id":other,"distance":l2(d),"delta36_turns":d})
        rows.sort(key=lambda x:(x["distance"],x["id"]))
        return rows[:k]

    def relation(self, src=None, dst=None):
        return [r for r in self.relations
                if (src is None or r.get("from")==src) and (dst is None or r.get("to")==dst)]

    def route(self, src, dst):
        graph=collections.defaultdict(list)
        for r in self.relations:
            graph[r["from"]].append((r["to"],r))
        q=collections.deque([(src,[])])
        seen={src}
        while q:
            node,path=q.popleft()
            if node==dst:
                return {"status":"FOUND","nodes":[src]+[e["to"] for e in path],"edges":path}
            for nxt,edge in graph.get(node,[]):
                if nxt not in seen:
                    seen.add(nxt); q.append((nxt,path+[edge]))
        return {"status":"NOT_FOUND","nodes":[],"edges":[]}

    def path(self, src, dst):
        pid=f"PATH_{src}_TO_{dst}"
        if pid in self.paths:
            return self.paths[pid]
        if src not in self.vectors or dst not in self.vectors:
            raise KeyError((src,dst))
        d=torus_delta(to_turns(self.vectors[src]["phase36"]),to_turns(self.vectors[dst]["phase36"]))
        typed=bool(self.relation(src,dst))
        return {
            "path_id":f"DYNAMIC_{src}_TO_{dst}","from":src,"to":dst,
            "tangent36_turns":d,"length_turns_l2":l2(d),
            "typed_relation_exists":typed,
            "status":"DERIVED_TYPED" if typed else "DERIVED_UNTYPED_NOT_CANONICAL"
        }

    def gate_check(self, gate_id, context):
        if gate_id not in self.gates:
            raise KeyError(gate_id)
        allow=True; reason="PASS"
        if gate_id=="PNV.GATE.VECTOR36_SHAPE":
            v=context.get("vector",[])
            allow=len(v)==36 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in v)
            reason="PASS" if allow else "VECTOR_SHAPE_OR_FINITE_FAIL"
        elif gate_id=="PNV.GATE.HALF_STATUS":
            allow=context.get("status") in {"EXACT","MODEL","NUMERICAL","OPEN"}
            reason="PASS" if allow else "INVALID_HALF_STATUS"
        elif gate_id=="PNV.GATE.RH_FIREWALL":
            claim=context.get("claim","")
            target=context.get("target_status","OPEN")
            protected={"SOH-C004","SOH-C005","full Riemann Hypothesis","RH"}
            allow=not (claim in protected and target not in {"OPEN","HYPOTHESIS","MODEL"})
            reason="PASS" if allow else "OPEN_BRIDGE_PROMOTION_DENIED"
        elif gate_id=="PNV.GATE.M8_ROOT_AUTHORITY":
            allow=context.get("target")!="M8" or context.get("authority") in {"USER007","ROOT","USER007/ROOT"}
            reason="PASS" if allow else "M8_REQUIRES_ROOT_AUTHORITY"
        elif gate_id=="PNV.GATE.M10_RECEIPT_ONLY":
            allow=context.get("target")!="M10" or context.get("kind") in {"receipt","provenance"}
            reason="PASS" if allow else "M10_RECEIPT_ONLY"
        elif gate_id=="PNV.GATE.NO_COORDINATE_TO_M":
            allow=not context.get("coordinate_to_memory_mapping",False)
            reason="PASS" if allow else "COORDINATE_TO_M_MAPPING_FORBIDDEN"
        elif gate_id=="PNV.GATE.NOEMA_ONLY":
            allow=context.get("promotion_source","NOEMA_LIBRARY")=="NOEMA_LIBRARY"
            reason="PASS" if allow else "NON_NOEMA_PROMOTION_DENIED"
        elif gate_id=="PNV.GATE.AUX_FRESHNESS":
            allow=bool(context.get("fresh_aux_receipt",False))
            reason="PASS" if allow else "FRESH_AUX_RECEIPT_REQUIRED"
        return {"gate_id":gate_id,"allow":allow,"reason":reason,"context_sha256":digest(context)}

    def execute(self, operator_id, args):
        if operator_id not in self.operators:
            raise KeyError(operator_id)
        if operator_id=="pnv.torus.normalize":
            v=args["vector"];
            if len(v)!=36: raise ValueError("requires 36 coordinates")
            return [((x/TAU)%1.0) for x in v]
        if operator_id=="pnv.torus.delta":
            return torus_delta(args["q"],args["r"])
        if operator_id=="pnv.torus.geodesic":
            q=args["q"]; r=args["r"]; t=float(args["t"]); d=torus_delta(q,r)
            return [((x+t*dx)%1.0) for x,dx in zip(q,d)]
        if operator_id=="pnv.path.length_l2":
            return l2(args["vector"])
        if operator_id=="pnv.vector.project":
            return project(args["a"],args["b"])
        if operator_id=="pnv.vector.orthogonalize":
            return orthogonalize(args["vectors"])
        if operator_id=="pnv.path.compose":
            ids=args["path_ids"]
            seq=[self.paths[i] for i in ids]
            for a,b in zip(seq[:-1],seq[1:]):
                if a["to"]!=b["from"]:
                    raise ValueError("path endpoints do not compose")
            return {"from":seq[0]["from"],"to":seq[-1]["to"],"path_ids":ids,"status":"COMPOSABLE"}
        if operator_id=="pnv.path.closure_residual":
            ids=args["path_ids"]; acc=[0.0]*36
            for i in ids:
                for k,x in enumerate(self.paths[i]["tangent36_turns"]): acc[k]+=x
            wrapped=[((x+0.5)%1.0)-0.5 for x in acc]
            return {"residual36":wrapped,"l2":l2(wrapped),"semantics":"DIAGNOSTIC_NOT_BERRY_HOLONOMY"}
        if operator_id=="pnv.holonomy.eligibility":
            req=["H1_connection","H2_closed_or_composable","H3_gauge_condition","H4_embedding_independence"]
            missing=[x for x in req if not args.get(x,False)]
            return {"status":"ELIGIBLE" if not missing else "OPEN","missing":missing}
        raise NotImplementedError(operator_id)

    def doctor(self, deep=False):
        issues=[]
        if self.canon.get("dimension")!=36: issues.append("DIMENSION_NOT_36")
        for k,v in self.vectors.items():
            p=v.get("phase36")
            if not isinstance(p,list) or len(p)!=36 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in p):
                issues.append(f"BAD_VECTOR:{k}")
        if "PNV.GATE.RH_FIREWALL" not in self.gates: issues.append("RH_FIREWALL_MISSING")
        if "PNV.GATE.M8_ROOT_AUTHORITY" not in self.gates: issues.append("M8_GATE_MISSING")
        if "PNV.GATE.M10_RECEIPT_ONLY" not in self.gates: issues.append("M10_GATE_MISSING")
        if deep:
            for p in self.paths.values():
                if len(p.get("tangent36_turns",[]))!=36: issues.append(f"BAD_PATH:{p.get('path_id')}")
            chain=self.verify_journal()
            if chain["status"]!="PASS": issues.extend(chain["issues"])
        return {"status":"PASS" if not issues else "FAIL","issues":issues,"deep":deep,"counts":self.status()["counts"]}

    def _last_receipt_hash(self):
        if not self.receipt_path or not self.receipt_path.exists():
            return "0"*64
        last=None
        for line in self.receipt_path.read_text(encoding="utf-8").splitlines():
            if line.strip(): last=json.loads(line)
        return last.get("receipt_sha256","0"*64) if last else "0"*64

    def _last_event_hash(self):
        events=self._overlay_events()
        return events[-1].get("event_sha256","0"*64) if events else "0"*64

    def _policy_check_mutation(self, kind, payload, authority):
        ctx={"target":payload.get("id") or payload.get("concept_id") or payload.get("from"),
             "authority":authority,"kind":payload.get("kind"),"promotion_source":"NOEMA_LIBRARY",
             "coordinate_to_memory_mapping":payload.get("coordinate_position_mapping",False)}
        checks=[
            self.gate_check("PNV.GATE.M8_ROOT_AUTHORITY",ctx),
            self.gate_check("PNV.GATE.M10_RECEIPT_ONLY",ctx),
            self.gate_check("PNV.GATE.NO_COORDINATE_TO_M",ctx),
            self.gate_check("PNV.GATE.NOEMA_ONLY",ctx),
        ]
        if kind=="ADD_VECTOR":
            checks.append(self.gate_check("PNV.GATE.VECTOR36_SHAPE",{"vector":payload.get("phase36",[])}))
        return checks

    def mutate(self, kind, payload, authority="USER007", actor="PNV_CLI", commit=False):
        checks=self._policy_check_mutation(kind,payload,authority)
        allow=all(x["allow"] for x in checks)
        input_obj={"mutation_kind":kind,"payload":payload,"authority":authority,"actor":actor}
        if not commit:
            return {"mode":"DRY_RUN","allow":allow,"checks":checks,"input_sha256":digest(input_obj)}
        if not allow:
            return {"mode":"COMMIT_OVERLAY","result":"DENIED","checks":checks,"input_sha256":digest(input_obj)}
        if not self.overlay_path or not self.receipt_path:
            raise RuntimeError("overlay and receipt paths required for commit")
        self.overlay_path.parent.mkdir(parents=True,exist_ok=True)
        self.receipt_path.parent.mkdir(parents=True,exist_ok=True)
        seq=sum(1 for x in self._overlay_events())+1
        event={
            "schema":"PNV_OVERLAY_EVENT_V1","seq":seq,"timestamp_utc":utc_now(),
            "mutation_kind":kind,"payload":payload,"authority":authority,"actor":actor,
            "prev_event_sha256":self._last_event_hash(),"result":"COMMITTED"
        }
        event["event_sha256"]=digest(event)
        with self.overlay_path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(event,sort_keys=True,ensure_ascii=False)+"\n")
        receipt={
            "schema":"PNV_RECEIPT_V1","receipt_id":f"PNV-R-{seq:08d}",
            "timestamp_utc":event["timestamp_utc"],"action":kind,"actor":actor,
            "input_sha256":digest(input_obj),"result":"PASS",
            "event_sha256":event["event_sha256"],
            "prev_receipt_sha256":self._last_receipt_hash()
        }
        receipt["receipt_sha256"]=digest(receipt)
        with self.receipt_path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(receipt,sort_keys=True,ensure_ascii=False)+"\n")
        self._rebuild()
        return {"mode":"COMMIT_OVERLAY","result":"COMMITTED","event":event,"receipt":receipt,"checks":checks}

    def verify_journal(self):
        issues=[]; prev="0"*64
        for n,ev in enumerate(self._overlay_events(),1):
            got=ev.get("event_sha256"); tmp=dict(ev); tmp.pop("event_sha256",None)
            if ev.get("prev_event_sha256")!=prev: issues.append(f"EVENT_PREV_HASH:{n}")
            if digest(tmp)!=got: issues.append(f"EVENT_HASH:{n}")
            prev=got or prev
        prev="0"*64
        if self.receipt_path and self.receipt_path.exists():
            for n,line in enumerate(self.receipt_path.read_text(encoding="utf-8").splitlines(),1):
                if not line.strip(): continue
                r=json.loads(line); got=r.get("receipt_sha256"); tmp=dict(r); tmp.pop("receipt_sha256",None)
                if r.get("prev_receipt_sha256")!=prev: issues.append(f"RECEIPT_PREV_HASH:{n}")
                if digest(tmp)!=got: issues.append(f"RECEIPT_HASH:{n}")
                prev=got or prev
        return {"status":"PASS" if not issues else "FAIL","issues":issues}

def parse_json_arg(value):
    p=Path(value)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(value)

def main():
    ap=argparse.ArgumentParser(prog="pnv",description="PhaseNav native terminal platform")
    ap.add_argument("--canon",required=True)
    ap.add_argument("--overlay")
    ap.add_argument("--receipts")
    sub=ap.add_subparsers(dest="cmd",required=True)

    sub.add_parser("status")
    r=sub.add_parser("resolve"); r.add_argument("term")
    v=sub.add_parser("vector"); v.add_argument("id")
    n=sub.add_parser("nearest"); n.add_argument("id"); n.add_argument("-k",type=int,default=5)
    rel=sub.add_parser("relation"); rel.add_argument("--from-id"); rel.add_argument("--to-id")
    rt=sub.add_parser("route"); rt.add_argument("src"); rt.add_argument("dst")
    p=sub.add_parser("path"); p.add_argument("src"); p.add_argument("dst")
    gc=sub.add_parser("gate-check"); gc.add_argument("gate_id"); gc.add_argument("context_json")
    ex=sub.add_parser("execute"); ex.add_argument("operator_id"); ex.add_argument("args_json")
    mu=sub.add_parser("mutate"); mu.add_argument("mutation_kind"); mu.add_argument("payload_json")
    mu.add_argument("--authority",default="USER007"); mu.add_argument("--actor",default="PNV_CLI")
    mu.add_argument("--commit",action="store_true")
    doc=sub.add_parser("doctor"); doc.add_argument("--deep",action="store_true")
    sub.add_parser("verify-journal")

    a=ap.parse_args()
    db=PNVPlatform(a.canon,a.overlay,a.receipts)
    if a.cmd=="status": out=db.status()
    elif a.cmd=="resolve": out=db.resolve(a.term)
    elif a.cmd=="vector": out=db.vector(a.id)
    elif a.cmd=="nearest": out=db.nearest(a.id,a.k)
    elif a.cmd=="relation": out=db.relation(a.from_id,a.to_id)
    elif a.cmd=="route": out=db.route(a.src,a.dst)
    elif a.cmd=="path": out=db.path(a.src,a.dst)
    elif a.cmd=="gate-check": out=db.gate_check(a.gate_id,parse_json_arg(a.context_json))
    elif a.cmd=="execute": out=db.execute(a.operator_id,parse_json_arg(a.args_json))
    elif a.cmd=="mutate": out=db.mutate(a.mutation_kind,parse_json_arg(a.payload_json),a.authority,a.actor,a.commit)
    elif a.cmd=="doctor": out=db.doctor(a.deep)
    else: out=db.verify_journal()
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
