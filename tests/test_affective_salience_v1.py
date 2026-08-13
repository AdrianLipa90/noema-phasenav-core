from copy import deepcopy
import pytest

from ciel_geometry.phasenav.cognition import memory_orchestrator as mo
from ciel_geometry.phasenav.cognition import affective_salience as af
from ciel_geometry.phasenav.cognition import introspective_telemetry as telemetry
from ciel_geometry.phasenav.cognition import m11_calibration as cal


def trace(tid, layer="M3", *, text="memory", tags=None, affordance=None, prov="VERIFIED", relations=None, phase=None):
    t={
        "schema":"NOEMA_MEMORY_TRACE_V1", "trace_id":tid, "layer":layer,
        "content":{"text":text}, "semantic_tags":tags or [],
        "epistemic_state":"OBSERVED", "temporal_order":1, "status":"ACTIVE",
        "provenance":{"status":prov,"refs":[f"receipt:{tid}"]}, "relations":relations or [],
    }
    if affordance is not None:
        t["affective_affordance"]={"schema":"NOEMA_AFFECTIVE_AFFORDANCE_V1","source_type":"VALIDATED_ANNOTATION","axes":affordance,"provenance_refs":[f"aff:{tid}"]}
    if phase is not None:
        t["phase_binding"]={"status":"BOUND_VALIDATED","space":"T^36","vector":phase}
    return mo.seal_trace(t)


def cue(**kw):
    c={"schema":"NOEMA_RECALL_CUE_V1","cue_id":"RC:T","session_id":"S:T","goal":"memory repair","focus":{"topic":"memory"},"hypotheses":[],"evidence_needs":[],"contradictions":[],"active_no_go_patterns":[],"direct_parent_refs":[],"identity_required":False,"phase36":None,"budget":{"max_items":3,"relation_hops":2}}
    c.update(kw); return c


def state(**axes):
    return af.seal_affect_state({"schema":"NOEMA_AFFECT_STATE_V1","source_type":"EXPLICIT_OPERATOR_STATE","inferred":False,"axes":axes,"source_refs":["explicit:test"]})


def test_no_affect_preserves_baseline_selection():
    ts=[trace("A", text="memory repair"), trace("B", text="unrelated")]
    base=mo.orchestrate(cue(), ts)
    mod=af.orchestrate_with_affect(cue(), ts, None)
    assert base["m1_injection"]["selected_trace_refs"] == mod["m1_injection"]["selected_trace_refs"]


def test_inferred_affect_rejected():
    bad={"schema":"NOEMA_AFFECT_STATE_V1","source_type":"EXPLICIT_OPERATOR_STATE","inferred":True,"axes":{"threat":1.0}}
    with pytest.raises(af.AffectiveSalienceError):
        af.validate_affect_state(bad)


def test_threat_focuses_without_authority():
    s=state(threat=0.9, urgency=0.9)
    p=af.attention_policy(cue(), s)
    assert p["mode"] == "FOCUSED_PROTECTIVE"
    assert p["relation_hops"] == 1
    assert p["authority_effect"] is False and p["truth_effect"] is False


def test_curiosity_expands_bounded_exploration():
    p=af.attention_policy(cue(), state(curiosity=0.9))
    assert p["mode"] == "EXPLORATORY"
    assert p["max_items"] == 5 and p["relation_hops"] == 3


def test_affect_can_add_non_truth_salience_channel():
    t=trace("A", text="other", affordance={"care":0.9})
    out=af.orchestrate_with_affect(cue(goal="totally unrelated", focus={}), [t], state(care=0.9))
    assert out["m1_injection"]["selected_trace_refs"] == ["A"]
    assert out["m1_injection"]["authority_granted"] is False
    assert out["m1_injection"]["execution_authorized"] is False
    assert out["m1_injection"]["semantic_claim_promotion"] is False


def test_phase_only_default_admission_remains_blocked():
    phase=[0.0]*36
    t=trace("P", text="unrelated", phase=phase)
    out=af.orchestrate_with_affect(cue(goal="different", focus={}, phase36=phase), [t], state(curiosity=0.2))
    assert "P" not in out["m1_injection"]["selected_trace_refs"]
    assert any(x["trace_id"]=="P" and x["reason"]=="NO_NONPHASE_RELEVANCE_SIGNAL" for x in out["inhibited"])


def test_m8_guard_and_unknown_provenance_survive_affect():
    ts=[trace("ID", layer="M8", text="memory", affordance={"care":1.0}), trace("U", text="memory", prov="UNKNOWN", affordance={"care":1.0})]
    out=af.orchestrate_with_affect(cue(), ts, state(care=1.0))
    reasons={(x["trace_id"],x["reason"]) for x in out["inhibited"]}
    assert ("ID","M8_NOT_EXPLICITLY_REQUIRED") in reasons
    assert ("U","PROVENANCE_UNKNOWN") in reasons


def test_no_go_mandatory_recall_not_suppressed_by_affect():
    ng=trace("NG", text="do not erase history", tags=["no-go"])
    other=trace("O", text="other", affordance={"reward":1.0})
    c=cue(active_no_go_patterns=["erase history"], goal="other")
    out=af.orchestrate_with_affect(c,[ng,other],state(reward=1.0))
    assert "NG" in out["m1_injection"]["must_recall_refs"]


def test_telemetry_is_observable_delta_not_hidden_reasoning():
    ts=[trace("A", text="other", affordance={"care":1.0})]
    c=cue(goal="different",focus={})
    base=af.orchestrate_with_affect(c,ts,None)
    s=state(care=1.0)
    mod=af.orchestrate_with_affect(c,ts,s)
    tel=telemetry.build_selection_telemetry(cue=c,baseline_braid=base,modulated_braid=mod,affect_state=s)
    assert tel["observable_only"] is True
    assert tel["hidden_chain_of_thought_persisted"] is False
    assert tel["selection_delta"]["added_by_modulation"] == ["A"]


def test_m11_learns_only_from_validated_outcomes_and_detects_tamper():
    s=cal.new_state()
    with pytest.raises(cal.CalibrationError):
        cal.update(s, confidence=0.8, correct=True, validated_outcome=False, outcome_ref="x")
    s=cal.update(s, confidence=0.8, correct=True, validated_outcome=True, outcome_ref="receipt:1")
    assert s["observations"] == 1
    bad=deepcopy(s); bad["observations"] += 1
    with pytest.raises(cal.CalibrationError):
        cal.update(bad, confidence=0.5, correct=False, validated_outcome=True, outcome_ref="receipt:2")
