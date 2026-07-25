from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any


VECTOR_DIM = 36
TAU = math.tau
ROOT = Path(__file__).resolve().parents[3]
PNV_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class RuntimeLayerRecord:
    layer_id: str
    role: str
    authority_scope: str
    source_module: str
    pnv_path: str
    phase_vector_36d: tuple[float, ...]
    coherence: float
    sha256: str
    bridges: tuple[str, ...]
    schema: str = "noema/runtime-layer-record/v1"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["phase_vector_36d"] = list(self.phase_vector_36d)
        data["bridges"] = list(self.bridges)
        return data


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_angles(seed: str, *, dim: int = VECTOR_DIM) -> tuple[float, ...]:
    data = seed.encode("utf-8")
    angles: list[float] = []
    counter = 0
    while len(angles) < dim:
        digest = sha256(data + counter.to_bytes(2, "big")).digest()
        for idx in range(0, len(digest), 2):
            chunk = digest[idx:idx + 2]
            if len(chunk) < 2:
                continue
            value = int.from_bytes(chunk, "big") / 65535.0
            angles.append(value * TAU)
            if len(angles) == dim:
                break
        counter += 1
    return tuple(angles)


def _order_parameter(vector: tuple[float, ...]) -> float:
    re = sum(math.cos(value) for value in vector) / len(vector)
    im = sum(math.sin(value) for value in vector) / len(vector)
    return math.sqrt(re * re + im * im)


def _file_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _build_record(
    *,
    layer_id: str,
    role: str,
    authority_scope: str,
    source_module: str,
    pnv_path: str,
    bridges: tuple[str, ...],
) -> RuntimeLayerRecord:
    payload = {
        "layer_id": layer_id,
        "role": role,
        "authority_scope": authority_scope,
        "source_module": source_module,
        "pnv_path": pnv_path,
        "bridges": list(bridges),
    }
    vector = _hash_angles(_canonical_json(payload))
    path = ROOT / source_module
    return RuntimeLayerRecord(
        layer_id=layer_id,
        role=role,
        authority_scope=authority_scope,
        source_module=source_module,
        pnv_path=pnv_path,
        phase_vector_36d=vector,
        coherence=_order_parameter(vector),
        sha256=_file_sha(path),
        bridges=bridges,
    )


def build_system_runtime_manifest() -> dict[str, Any]:
    records = [
        _build_record(
            layer_id="aux_runtime",
            role="identity_carrier",
            authority_scope="stateful_runtime",
            source_module="src/ciel_geometry/aux_self.py",
            pnv_path="src/ciel_geometry/phasenav/system_runtime.pnv",
            bridges=("phasenav_runtime", "cielingo_runtime", "memory_runtime"),
        ),
        _build_record(
            layer_id="cielingo_runtime",
            role="semantic_interpreter",
            authority_scope="interactive_runtime",
            source_module="src/ciel_geometry/cielingo_inference.py",
            pnv_path="src/ciel_geometry/phasenav/system_runtime.pnv",
            bridges=("aux_runtime", "phasenav_runtime", "subconscious_runtime"),
        ),
        _build_record(
            layer_id="phasenav_runtime",
            role="phase_interpreter",
            authority_scope="canonical_36d_runtime",
            source_module="src/ciel_geometry/phasenav/pnv_runtime.py",
            pnv_path="src/ciel_geometry/phasenav/pnv_runtime.pnv",
            bridges=("aux_runtime", "cielingo_runtime", "governance_runtime"),
        ),
        _build_record(
            layer_id="subconscious_runtime",
            role="affective_background_stream",
            authority_scope="advisory_runtime",
            source_module="src/ciel_sot_agent/subconsciousness.py",
            pnv_path="src/ciel_geometry/phasenav/system_runtime.pnv",
            bridges=("aux_runtime", "cielingo_runtime", "memory_runtime"),
        ),
        _build_record(
            layer_id="memory_runtime",
            role="domain_router_and_trace_store",
            authority_scope="gated_persistence",
            source_module="src/CIEL_OMEGA_COMPLETE_SYSTEM/ciel_omega/memory/domain_router.py",
            pnv_path="src/ciel_geometry/phasenav/system_runtime.pnv",
            bridges=("aux_runtime", "subconscious_runtime", "governance_runtime"),
        ),
        _build_record(
            layer_id="governance_runtime",
            role="doctor_actuator_oracle_gate",
            authority_scope="gated_execution",
            source_module="src/cielingo_core/autonomy/executable_entities.py",
            pnv_path="src/ciel_geometry/phasenav/executable_entities.pnv",
            bridges=("phasenav_runtime", "memory_runtime", "portal_runtime"),
        ),
        _build_record(
            layer_id="portal_runtime",
            role="surface_transport_and_observability",
            authority_scope="read_write_surface",
            source_module="scripts/noema_portal_daemon.py",
            pnv_path="src/ciel_geometry/phasenav/surface_bridge.pnv",
            bridges=("governance_runtime", "headless_runtime", "cielingo_runtime"),
        ),
        _build_record(
            layer_id="headless_runtime",
            role="autonomous_response_loop",
            authority_scope="runtime_execution",
            source_module="scripts/ciel_headless_daemon.py",
            pnv_path="src/ciel_geometry/phasenav/decision_bridge.pnv",
            bridges=("portal_runtime", "cielingo_runtime", "aux_runtime"),
        ),
    ]
    return {
        "schema": "noema/system-runtime-manifest/v1",
        "phase_contract": "36d",
        "canonical_pnv": "src/ciel_geometry/phasenav/system_runtime.pnv",
        "layers": [record.to_dict() for record in records],
    }


def validate_system_runtime_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    doctor_findings: list[str] = []
    oracle_findings: list[str] = []
    layers = list(payload.get("layers", []))
    canonical_pnv = ROOT / str(payload.get("canonical_pnv", ""))
    if payload.get("schema") != "noema/system-runtime-manifest/v1":
        doctor_findings.append("schema_mismatch")
    if payload.get("phase_contract") != "36d":
        doctor_findings.append("phase_contract_mismatch")
    if not canonical_pnv.is_file():
        doctor_findings.append("canonical_pnv_missing")
    if len(layers) != 8:
        doctor_findings.append("unexpected_layer_count")

    seen_ids: set[str] = set()
    seen_vectors: set[tuple[float, ...]] = set()
    for layer in layers:
        layer_id = str(layer.get("layer_id", ""))
        source_module = ROOT / str(layer.get("source_module", ""))
        vector = tuple(float(x) for x in layer.get("phase_vector_36d", []))
        bridges = list(layer.get("bridges", []))
        if not layer_id:
            doctor_findings.append("missing_layer_id")
        if layer_id in seen_ids:
            doctor_findings.append(f"duplicate_layer_id:{layer_id}")
        seen_ids.add(layer_id)
        if len(vector) != 36:
            doctor_findings.append(f"bad_vector_dim:{layer_id}")
        if not source_module.is_file():
            doctor_findings.append(f"missing_source:{layer_id}")
        if not bridges:
            doctor_findings.append(f"missing_bridges:{layer_id}")
        if vector in seen_vectors:
            oracle_findings.append(f"phase_vector_collision:{layer_id}")
        seen_vectors.add(vector)
        coherence = float(layer.get("coherence", 0.0))
        if not (0.0 <= coherence <= 1.0):
            oracle_findings.append(f"coherence_out_of_range:{layer_id}")
        if not str(layer.get("sha256", "")):
            oracle_findings.append(f"missing_sha256:{layer_id}")

    return {
        "doctor": {
            "status": "PASS" if not doctor_findings else "FAIL",
            "findings": doctor_findings,
        },
        "oracle": {
            "status": "PASS" if not oracle_findings else "FAIL",
            "findings": oracle_findings,
        },
        "ok": not doctor_findings and not oracle_findings,
    }


__all__ = ["RuntimeLayerRecord", "build_system_runtime_manifest", "validate_system_runtime_manifest"]
