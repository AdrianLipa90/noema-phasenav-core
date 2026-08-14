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
        elif gate_id=="PNV.GATE.NOEMA_ONLY"
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
            return [((v/TAU)%1.0) for x in v]
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
            return {"mode":"COMMIT_OVERLAY","result":"DENIED","checks":checks,"input_sha256":dÚYÙ\İ
[œ]ÛØšŠ_BˆYˆ›İÙ[‹›İ™\›^WÜ]Üˆ›İÙ[‹œ™XÙZ\Ü]‚ˆ˜Z\ÙH[[YQ\œ›ÜŠ›İ™\›^H[™™XÙZ\]È™\]Z\™Y›ÜˆÛÛ[Z]ŠBˆÙ[‹›İ™\›^WÜ]œ\™[›ZÙ\Š\™[ÏUYK^\İÛÚÏUYJBˆÙ[‹œ™XÙZ\Ü]œ\™[›ZÙ\Š\™[ÏUYK^\İÛÚÏUYJBˆÙ\O\İ[JH›Üˆ[ˆÙ[‹—Ûİ™\›^WÙ]™[Ê
JJÌBˆ]™[^ÂˆœØÚ[XHˆ”•—ÓÕ‘T“VWÑU‘S•ÕŒH‹œÙ\HœÙ\K[Y\İ[\İ]È]×Û›İÊ
Kˆ›]]][Û—ÚÚ[™šÚ[™œ^[ØYœ^[ØY˜]]Üš]H˜]]Üš]K˜XİÜˆ˜XİÜ‹ˆœ™]—Ù]™[ÜÚLMˆœÙ[‹—Û\İÙ]™[Ú\Ú

Kœ™\İ[ˆÓÓSRUQ‚ˆBˆ]™[È™]™[ÜÚLMˆ—OYYÙ\İ
]™[
BˆÚ]Ù[‹›İ™\›^WÜ]›Ü[Š˜H‹[˜ÛÙ[™ÏH]‹NŠH\È‚ˆ‹Üš]JœÛÛ‹™[\Ê]™[ÛÜÚÙ^\ÏUYK[œİ\™WØ\ØÚZOQ˜[ÙJJÈ—ˆŠBˆ™XÙZ\^ÂˆœØÚ[XHˆ”•—Ô‘PÑRTÕŒH‹œ™XÙZ\ÚY™ˆ”•‹T‹^ÜÙ\NŒH‹ˆ[Y\İ[\İ]È™]™[È[Y\İ[\İ]È—K˜Xİ[ÛˆšÚ[™˜XİÜˆ˜XİÜ‹ˆš[œ]ÜÚLMˆ™YÙ\İ
[œ]ÛØšŠKœ™\İ[ˆ”TÔÈ‹ˆ™]™[ÜÚLMˆ™]™[È™]™[ÜÚLMˆ—Kˆœ™]—Ü™XÙZ\ÜÚLMˆœÙ[‹—Û\İÜ™XÙZ\Ú\Ú

BˆBˆ™XÙZ\Èœ™XÙZ\ÜÚLMˆ—OYYÙ\İ
™XÙZ\
BˆÚ]Ù[‹œ™XÙZ\Ü]›Ü[Š˜H‹[˜ÛÙ[™ÏH]‹NŠH\È‚ˆ‹Üš]JœÛÛ‹™[\Ê™XÙZ\ÛÜÚÙ^\ÏUYK[œİ\™WØ\ØÚZOQ˜[ÙJJÈ—ˆŠBˆÙ[‹—Ü™XZ[

Bˆ™]\›ˆÈ›[ÙHˆÓÓSRUÓÕ‘T“VH‹œ™\İ[ˆÓÓSRUQ‹™]™[™]™[œ™XÙZ\œ™XÙZ\˜ÚXÚÜÈ˜ÚXÚÜßB‚ˆYˆ™\šYWÚ›İ\›˜[
Ù[ŠN‚ˆ\ÜİY\ÏV×NÈ™]HŒŠˆ›Üˆ‹]ˆ[ˆ[[Y\˜]JÙ[‹—Ûİ™\›^WÙ]™[Ê
KJN‚ˆÛİY]‹™Ù]
™]™[ÜÚLMˆŠNÈ\YXİ
]ŠNÈ\œÜ
™]™[ÜÚLMˆ‹›Û™JBˆYˆ]‹™Ù]
œ™]—Ù]™[ÜÚLMˆŠHO\™]ˆ\ÜİY\Ë˜\[™
ˆ‘U‘S•Ô‘U—ÒTÒÛŸHŠBˆYˆYÙ\İ
\
HOYÛİˆ\ÜİY\Ë˜\[™
ˆ‘U‘S•ÒTÒÛŸHŠBˆ™]YÛİÜˆ™]‚ˆ™]HŒŠˆYˆÙ[‹œ™XÙZ\Ü][™Ù[‹œ™XÙZ\Ü]™^\İÊ
N‚ˆ›Üˆ‹[™H[ˆ[[Y\˜]JÙ[‹œ™XÙZ\Ü]œ™XYİ^
[˜ÛÙ[™ÏH]‹NŠKœÜ][™\Ê
KJN‚ˆYˆ›İ[™Kœİš\

NˆÛÛ[YBˆZœÛÛ‹›ØYÊ[™JNÈÛİ\‹™Ù]
œ™XÙZ\ÜÚLMˆŠNÈ\YXİ
ŠNÈ\œÜ
œ™XÙZ\ÜÚLMˆ‹›Û™JBˆYˆ‹™Ù]
œ™]—Ü™XÙZ\ÜÚLMˆŠHO\™]ˆ\ÜİY\Ë˜\[™
ˆ”‘PÑRTÔ‘U—ÒTÒÛŸHŠBˆYˆYÙ\İ
\
HOYÛİˆ\ÜİY\Ë˜\[™
ˆ”‘PÑRTÒTÒÛŸHŠBˆ™]YÛİÜˆ™]‚ˆ™]\›ˆÈœİ]\Èˆ”TÔÈˆYˆ›İ\ÜİY\È[ÙH‘RS‹š\ÜİY\Èš\ÜİY\ßB‚™Yˆ\œÙWÚœÛÛ—Ø\™Ê˜[YJN‚ˆT]
˜[YJBˆYˆ™^\İÊ
N‚ˆ™]\›ˆœÛÛ‹›ØYÊœ™XYİ^
[˜ÛÙ[™ÏH]‹NŠJBˆ™]\›ˆœÛÛ‹›ØYÊ˜[YJB‚™YˆXZ[Š
N‚ˆ\X\™Ü\œÙK\™İ[Y[\œÙ\Š›ÙÏHœˆ‹\ØÜš\[ÛH”\ÙS˜]ˆ˜]]™H\›Z[˜[]›Ü›HŠBˆ\˜YØ\™İ[Y[
‹KXØ[›Ûˆ‹™\]Z\™YUYJBˆ\˜YØ\™İ[Y[
‹K[İ™\›^HŠBˆ\˜YØ\™İ[Y[
‹K\™XÙZ\ÈŠBˆİXX\˜YÜİXœ\œÙ\œÊ\İH˜ÛY‹™\]Z\™YUYJB‚ˆİX‹˜YÜ\œÙ\Šœİ]\ÈŠBˆ\İX‹˜YÜ\œÙ\Šœ™\ÛÛ™HŠNÈ‹˜YØ\™İ[Y[
\›HŠBˆ\İX‹˜YÜ\œÙ\Š™XİÜˆŠNÈ‹˜YØ\™İ[Y[
šYŠBˆ\İX‹˜YÜ\œÙ\Š›™X\™\İŠNÈ‹˜YØ\™İ[Y[
šYŠNÈ‹˜YØ\™İ[Y[
‹ZÈ‹\OZ[Y˜][MJBˆ™[\İX‹˜YÜ\œÙ\Šœ™[][ÛˆŠNÈ™[˜YØ\™İ[Y[
‹KYœ›ÛKZYŠNÈ™[˜YØ\™İ[Y[
‹K]ËZYŠBˆ\İX‹˜YÜ\œÙ\Šœ›İ]HŠNÈ˜YØ\™İ[Y[
œÜ˜ÈŠNÈ˜YØ\™İ[Y[
™İŠBˆ\İX‹˜YÜ\œÙ\Šœ]ŠNÈ˜YØ\™İ[Y[
œÜ˜ÈŠNÈ˜YØ\™İ[Y[
™İŠBˆØÏ\İX‹˜YÜ\œÙ\Š™Ø]KXÚXÚÈŠNÈØË˜YØ\™İ[Y[
™Ø]WÚYŠNÈØË˜YØ\™İ[Y[
˜ÛÛ^ÚœÛÛˆŠBˆ^\İX‹˜YÜ\œÙ\Š™^Xİ]HŠNÈ^˜YØ\™İ[Y[
›Ü\˜]Ü—ÚYŠNÈ^˜YØ\™İ[Y[
˜\™Ü×ÚœÛÛˆŠBˆ]O\İX‹˜YÜ\œÙ\Š›]]]HŠNÈ]K˜YØ\™İ[Y[
›]]][Û—ÚÚ[™ŠNÈ]K˜YØ\™İ[Y[
œ^[ØYÚœÛÛˆŠBˆ]K˜YØ\™İ[Y[
‹KX]]Üš]H‹Y˜][H•TÑTŒÈŠNÈ]K˜YØ\™İ[Y[
‹KXXİÜˆ‹Y˜][H”•—ĞÓHŠBˆ]K˜YØ\™İ[Y[
‹KXÛÛ[Z]‹Xİ[ÛHœİÜ™WİYHŠBˆØÏ\İX‹˜YÜ\œÙ\Š™ØİÜˆŠNÈØË˜YØ\™İ[Y[
‹KYY\‹Xİ[ÛHœİÜ™WİYHŠBˆİX‹˜YÜ\œÙ\Š™\šYKZ›İ\›˜[ŠB‚ˆOX\œ\œÙWØ\™ÜÊ
BˆT•”]›Ü›JK˜Ø[›Û‹K›İ™\›^KKœ™XÙZ\ÊBˆYˆK˜ÛYOHœİ]\Èˆİ]Y‹œİ]\Ê
Bˆ[YˆK˜ÛYOHœ™\ÛÛ™Hˆİ]Y‹œ™\ÛÛ™JK\›JBˆ[YˆK˜ÛYOH™XİÜˆˆİ]Y‹™XİÜŠKšY
Bˆ[YˆK˜ÛYOH›™X\™\İˆİ]Y‹›™X\™\İ
KšYKšÊBˆ[YˆK˜ÛYOHœ™[][Ûˆˆİ]Y‹œ™[][ÛŠK™œ›ÛWÚYK×ÚY
Bˆ[YˆK˜ÛYOHœ›İ]Hˆİ]Y‹œ›İ]JKœÜ˜ËK™İ
Bˆ[YˆK˜ÛYOHœ]ˆİ]Y‹œ]
KœÜ˜ËK™İ
Bˆ[YˆK˜ÛYOH™Ø]KXÚXÚÈˆİ]Y‹™Ø]WØÚXÚÊK™Ø]WÚY\œÙWÚœÛÛ—Ø\™ÊK˜ÛÛ^ÚœÛÛŠJBˆ[YˆK˜ÛYOH™^Xİ]Hˆİ]Y‹™^Xİ]JK›Ü\˜]Ü—ÚY\œÙWÚœÛÛ—Ø\™ÊK˜\™Ü×ÚœÛÛŠJBˆ[YˆK˜ÛYOH›]]]Hˆİ]Y‹›]]]JK›]]][Û—ÚÚ[™\œÙWÚœÛÛ—Ø\™ÊKœ^[ØYÚœÛÛŠKK˜]]Üš]KK˜XİÜ‹K˜ÛÛ[Z]
Bˆ[YˆK˜ÛYOH™ØİÜˆˆİ]Y‹™ØİÜŠK™Y\
Bˆ[ÙNˆİ]Y‹™\šYWÚ›İ\›˜[

Bˆš[
œÛÛ‹™[\Êİ][™[L‹[œİ\™WØ\ØÚZOQ˜[ÙJJB‚šYˆ×Û˜[YW×ÏOH—×ÛXZ[—×È‚ˆXZ[Š
B