from __future__ import annotations
from copy import deepcopy
from typing import Any
import hashlib, json, math

class CalibrationError(ValueError):
    pass

def _canon(x: Any) -> bytes:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def _sha(x: Any) -> str:
    return hashlib.sha256(_canon(x)).hexdigest()

def _valid_confidence(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x)) and 0.0 <= float(x) <= 1.0

def new_state(bin_count: int = 10) -> dict[str, Any]:
    if not isinstance(bin_count, int) or bin_count < 2 or bin_count > 50:
        raise CalibrationError("bin_count must be 2..50")
    body = {
        "schema": "NOEMA_M11_CALIBRATION_STATE_V1",
        "bin_count": bin_count,
        "observations": 0,
        "bins": [{"bin": i, "low": i / bin_count, "high": (i + 1) / bin_count, "count": 0, "confidence_sum": 0.0, "correct_sum": 0.0, "brier_sum": 0.0} for i in range(bin_count)],
        "metrics": {"ece": None, "brier": None},
        "durable_write_requires_validated_outcome": True,
    }
    body["state_sha256"] = _sha(body)
    return body

def _recompute(state: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(state)
    out.pop("state_sha256", None)
    n = int(out["observations"])
    if n == 0:
        out["metrics"] = {"ece": None, "brier": None}
    else:
        ece = 0.0
        brier = 0.0
        for b in out["bins"]:
            c = int(b["count"])
            brier += float(b["brier_sum"])
            if c:
                mean_conf = float(b["confidence_sum"]) / c
                acc = float(b["correct_sum"]) / c
                ece += (c / n) * abs(mean_conf - acc)
        out["metrics"] = {"ece": ece, "brier": brier / n}
    out["state_sha256"] = _sha(out)
    return out

def update(state: dict[str, Any], *, confidence: float, correct: bool, validated_outcome: bool, outcome_ref: str) -> dict[str, Any]:
    if not validated_outcome:
        raise CalibrationError("M11 calibration only learns from validated outcomes")
    if not outcome_ref:
        raise CalibrationError("validated outcome requires provenance reference")
    if not _valid_confidence(confidence):
        raise CalibrationError("confidence must be in [0,1]")
    if not isinstance(correct, bool):
        raise CalibrationError("correct must be boolean")
    out = deepcopy(state)
    old_hash = out.pop("state_sha256", None)
    if old_hash != _sha(out):
        raise CalibrationError("calibration state hash mismatch")
    nbin = int(out["bin_count"])
    idx = min(nbin - 1, int(float(confidence) * nbin))
    b = out["bins"][idx]
    y = 1.0 if correct else 0.0
    p = float(confidence)
    b["count"] += 1
    b["confidence_sum"] += p
    b["correct_sum"] += y
    b["brier_sum"] += (p - y) ** 2
    out["observations"] += 1
    out["last_validated_outcome"] = {"outcome_ref": outcome_ref, "confidence": p, "correct": correct}
    return _recompute(out)

def calibration_receipt(state: dict[str, Any]) -> dict[str, Any]:
    body = deepcopy(state)
    got = body.pop("state_sha256", None)
    if got != _sha(body):
        raise CalibrationError("calibration state hash mismatch")
    populated = [{"bin": b["bin"], "count": b["count"], "mean_confidence": b["confidence_sum"] / b["count"], "accuracy": b["correct_sum"] / b["count"]} for b in state["bins"] if b["count"]]
    receipt = {"schema": "NOEMA_M11_CALIBRATION_RECEIPT_V1", "state_sha256": state["state_sha256"], "observations": state["observations"], "metrics": deepcopy(state["metrics"]), "populated_bins": populated, "interpretation": "empirical calibration telemetry; not a truth oracle"}
    receipt["receipt_sha256"] = _sha(receipt)
    return receipt
