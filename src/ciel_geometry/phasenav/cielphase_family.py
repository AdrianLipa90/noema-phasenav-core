from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError as _e:
        raise ImportError("tomli is required for Python < 3.11: pip install tomli") from _e

try:
    import yaml
except ImportError as _e:
    raise ImportError("pyyaml is required: pip install pyyaml") from _e


VECTOR_DIM = 36
TAU = math.tau
ROOT = Path(__file__).resolve().parents[3]

STRUCTURED_SUFFIXES = {".json", ".jsonl", ".toml"}
DECLARATIVE_SUFFIXES = {".yaml", ".yml"}
DESCRIPTIVE_SUFFIXES = {".md", ".txt"}
SUPPORTED_SUFFIXES = STRUCTURED_SUFFIXES | DECLARATIVE_SUFFIXES | DESCRIPTIVE_SUFFIXES


class CielPhaseFamily(str, Enum):
    PNV = "pnv"
    PNS = "pns"
    PNY = "pny"
    PND = "pnd"
    PNGV = "pngv"
    PNA = "pna"
    PNB = "pnb"


class TwinEquivalenceStatus(str, Enum):
    EQUIVALENT = "equivalent"
    DRIFTED = "drifted"
    INVALID = "invalid"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class CanonicalPhaseArtifact:
    artifact_id: str
    family: str
    source_path: str
    twin_path: str
    source_sha256: str
    semantic_sha256: str
    phase_vector_36d: tuple[float, ...]
    coherence: float
    payload_format: str
    line_count: int
    provenance: dict[str, Any]
    schema: str = "noema/cielphase-artifact/v1"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["phase_vector_36d"] = list(self.phase_vector_36d)
        return data


@dataclass(frozen=True)
class PhaseTwinReceipt:
    receipt_id: str
    source_path: str
    twin_path: str
    family: str
    equivalence_status: str
    doctor_status: str
    oracle_status: str
    source_sha256: str
    twin_sha256: str
    semantic_sha256: str
    artifact_id: str
    schema: str = "noema/phase-twin-receipt/v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorOracleGateResult:
    ok: bool
    doctor_status: str
    oracle_status: str
    doctor_findings: tuple[str, ...]
    oracle_findings: tuple[str, ...]
    equivalence_status: str
    schema: str = "noema/doctor-oracle-gate-result/v1"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["doctor_findings"] = list(self.doctor_findings)
        data["oracle_findings"] = list(self.oracle_findings)
        return data


def _canonical_json(payload: Any) -> str:
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


def _line_count(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def family_for_path(path: str | Path) -> CielPhaseFamily:
    suffix = Path(path).suffix.lower()
    if suffix in STRUCTURED_SUFFIXES:
        return CielPhaseFamily.PNS
    if suffix in DECLARATIVE_SUFFIXES:
        return CielPhaseFamily.PNY
    if suffix in DESCRIPTIVE_SUFFIXES:
        return CielPhaseFamily.PND
    raise ValueError(f"Unsupported source suffix: {suffix}")


def twin_suffix_for_family(family: CielPhaseFamily) -> str:
    return "." + family.value


def twin_path_for_source(source_path: str | Path, family: CielPhaseFamily | None = None) -> Path:
    source = Path(source_path)
    resolved_family = family or family_for_path(source)
    return source.with_suffix(twin_suffix_for_family(resolved_family))


def _relative_to_root(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def _normalize_markdown(text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in text.splitlines()]
    words = sum(len(line.split()) for line in lines)
    headings = [line.lstrip("# ").strip() for line in lines if line.lstrip().startswith("#")]
    return {
        "content": "\n".join(lines).strip(),
        "headings": headings,
        "line_count": len(lines),
        "word_count": words,
    }


def _normalize_text(text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in text.splitlines()]
    return {
        "content": "\n".join(lines).strip(),
        "line_count": len(lines),
        "word_count": sum(len(line.split()) for line in lines),
    }


def _normalize_jsonl(text: str) -> list[Any]:
    rows: list[Any] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
    return rows


def _normalized_payload_for_path(path: str | Path) -> tuple[CielPhaseFamily, Any, str]:
    source = Path(path)
    suffix = source.suffix.lower()
    text = source.read_text(encoding="utf-8")
    if suffix == ".json":
        return CielPhaseFamily.PNS, json.loads(text), "json"
    if suffix == ".jsonl":
        return CielPhaseFamily.PNS, _normalize_jsonl(text), "jsonl"
    if suffix == ".toml":
        return CielPhaseFamily.PNS, tomllib.loads(text), "toml"
    if suffix in DECLARATIVE_SUFFIXES:
        return CielPhaseFamily.PNY, yaml.safe_load(text) or {}, "yaml"
    if suffix == ".md":
        return CielPhaseFamily.PND, _normalize_markdown(text), "markdown"
    if suffix == ".txt":
        return CielPhaseFamily.PND, _normalize_text(text), "text"
    raise ValueError(f"Unsupported source suffix: {suffix}")


def _artifact_seed(*, family: CielPhaseFamily, source_path: Path, semantic_sha: str, payload_format: str) -> str:
    payload = {
        "family": family.value,
        "source_path": _relative_to_root(source_path),
        "semantic_sha256": semantic_sha,
        "payload_format": payload_format,
    }
    return _canonical_json(payload)


def emit_phase_twin(source_path: str | Path, family: CielPhaseFamily | None = None) -> CanonicalPhaseArtifact:
    source = Path(source_path).resolve()
    detected_family, normalized_payload, payload_format = _normalized_payload_for_path(source)
    resolved_family = family or detected_family
    if resolved_family != detected_family:
        raise ValueError(f"Family mismatch for {source}: expected {detected_family.value}, got {resolved_family.value}")
    canonical_payload = _canonical_json(normalized_payload)
    semantic_sha = sha256(canonical_payload.encode("utf-8")).hexdigest()
    twin_path = twin_path_for_source(source, resolved_family)
    artifact_seed = _artifact_seed(
        family=resolved_family,
        source_path=source,
        semantic_sha=semantic_sha,
        payload_format=payload_format,
    )
    vector = _hash_angles(artifact_seed)
    artifact = CanonicalPhaseArtifact(
        artifact_id="cphase_" + sha256(artifact_seed.encode("utf-8")).hexdigest()[:24],
        family=resolved_family.value,
        source_path=_relative_to_root(source),
        twin_path=_relative_to_root(twin_path),
        source_sha256=_file_sha(source),
        semantic_sha256=semantic_sha,
        phase_vector_36d=vector,
        coherence=_order_parameter(vector),
        payload_format=payload_format,
        line_count=_line_count(source.read_text(encoding="utf-8")),
        provenance={
            "phase_contract": "36d",
            "source_suffix": source.suffix.lower(),
            "family": resolved_family.value,
        },
    )
    twin_payload = {
        "schema": "noema/cielphase-twin/v1",
        "family": resolved_family.value,
        "source_path": artifact.source_path,
        "payload_format": payload_format,
        "semantic_sha256": semantic_sha,
        "phase_vector_36d": list(vector),
        "coherence": artifact.coherence,
        "normalized_payload": normalized_payload,
        "provenance": artifact.provenance,
    }
    twin_path.parent.mkdir(parents=True, exist_ok=True)
    twin_path.write_text(json.dumps(twin_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact


def find_phase_twin(source_path: str | Path) -> Path | None:
    source = Path(source_path)
    try:
        twin = twin_path_for_source(source)
    except ValueError:
        return None
    if twin.is_file():
        return twin
    return None


def load_cielphase_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != "noema/cielphase-twin/v1":
        raise ValueError(f"Unsupported CielPhase artifact schema: {payload.get('schema')}")
    return payload


def validate_phase_twin(source_path: str | Path, twin_path: str | Path | None = None) -> DoctorOracleGateResult:
    source = Path(source_path).resolve()
    resolved_twin = Path(twin_path).resolve() if twin_path else find_phase_twin(source)
    doctor_findings: list[str] = []
    oracle_findings: list[str] = []
    if not source.is_file():
        doctor_findings.append("source_missing")
    if resolved_twin is None or not Path(resolved_twin).is_file():
        doctor_findings.append("twin_missing")
        return DoctorOracleGateResult(
            ok=False,
            doctor_status="FAIL",
            oracle_status="FAIL",
            doctor_findings=tuple(doctor_findings),
            oracle_findings=("twin_missing",),
            equivalence_status=TwinEquivalenceStatus.INVALID.value,
        )

    artifact = load_cielphase_artifact(resolved_twin)
    expected_family, normalized_payload, payload_format = _normalized_payload_for_path(source)
    semantic_sha = sha256(_canonical_json(normalized_payload).encode("utf-8")).hexdigest()
    if artifact.get("family") != expected_family.value:
        doctor_findings.append("family_mismatch")
    if artifact.get("payload_format") != payload_format:
        doctor_findings.append("payload_format_mismatch")
    if artifact.get("source_path") != _relative_to_root(source):
        doctor_findings.append("source_path_mismatch")
    vector = tuple(float(x) for x in artifact.get("phase_vector_36d", []))
    if len(vector) != 36:
        doctor_findings.append("bad_vector_dim")
    if artifact.get("semantic_sha256") != semantic_sha:
        oracle_findings.append("semantic_sha_mismatch")
    coherence = float(artifact.get("coherence", 0.0))
    if not (0.0 <= coherence <= 1.0):
        oracle_findings.append("coherence_out_of_range")
    equivalence = (
        TwinEquivalenceStatus.EQUIVALENT
        if not doctor_findings and not oracle_findings
        else TwinEquivalenceStatus.DRIFTED
    )
    return DoctorOracleGateResult(
        ok=not doctor_findings and not oracle_findings,
        doctor_status="PASS" if not doctor_findings else "FAIL",
        oracle_status="PASS" if not oracle_findings else "FAIL",
        doctor_findings=tuple(doctor_findings),
        oracle_findings=tuple(oracle_findings),
        equivalence_status=equivalence.value,
    )


def export_phase_receipt(source_path: str | Path, twin_path: str | Path | None = None) -> PhaseTwinReceipt:
    source = Path(source_path).resolve()
    resolved_twin = Path(twin_path).resolve() if twin_path else find_phase_twin(source)
    if resolved_twin is None or not resolved_twin.is_file():
        raise FileNotFoundError(f"Phase twin missing for {source}")
    artifact = load_cielphase_artifact(resolved_twin)
    validation = validate_phase_twin(source, resolved_twin)
    receipt_seed = _canonical_json(
        {
            "source_path": _relative_to_root(source),
            "twin_path": _relative_to_root(resolved_twin),
            "semantic_sha256": artifact["semantic_sha256"],
        }
    )
    return PhaseTwinReceipt(
        receipt_id="ptwin_" + sha256(receipt_seed.encode("utf-8")).hexdigest()[:24],
        source_path=_relative_to_root(source),
        twin_path=_relative_to_root(resolved_twin),
        family=str(artifact["family"]),
        equivalence_status=validation.equivalence_status,
        doctor_status=validation.doctor_status,
        oracle_status=validation.oracle_status,
        source_sha256=_file_sha(source),
        twin_sha256=_file_sha(resolved_twin),
        semantic_sha256=str(artifact["semantic_sha256"]),
        artifact_id="cphase_" + sha256(_artifact_seed(
            family=CielPhaseFamily(str(artifact["family"])),
            source_path=source,
            semantic_sha=str(artifact["semantic_sha256"]),
            payload_format=str(artifact["payload_format"]),
        ).encode("utf-8")).hexdigest()[:24],
    )


def build_cielphase_registry(root: str | Path) -> dict[str, Any]:
    root_path = Path(root).resolve()
    artifacts: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    doctor_findings: list[str] = []
    oracle_findings: list[str] = []
    seen_vectors: set[tuple[float, ...]] = set()
    for source in sorted(path for path in root_path.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES):
        artifact = emit_phase_twin(source)
        twin = find_phase_twin(source)
        receipt = export_phase_receipt(source, twin)
        artifacts.append(artifact.to_dict())
        receipts.append(receipt.to_dict())
        vector = artifact.phase_vector_36d
        if vector in seen_vectors:
            oracle_findings.append(f"phase_vector_collision:{artifact.source_path}")
        seen_vectors.add(vector)
        if receipt.doctor_status != "PASS":
            doctor_findings.append(f"doctor_fail:{artifact.source_path}")
        if receipt.oracle_status != "PASS":
            oracle_findings.append(f"oracle_fail:{artifact.source_path}")

    validation = DoctorOracleGateResult(
        ok=not doctor_findings and not oracle_findings,
        doctor_status="PASS" if not doctor_findings else "FAIL",
        oracle_status="PASS" if not oracle_findings else "FAIL",
        doctor_findings=tuple(doctor_findings),
        oracle_findings=tuple(oracle_findings),
        equivalence_status=TwinEquivalenceStatus.EQUIVALENT.value if not doctor_findings and not oracle_findings else TwinEquivalenceStatus.DRIFTED.value,
    )
    return {
        "schema": "noema/cielphase-registry/v1",
        "phase_contract": "36d",
        "root": _relative_to_root(root_path),
        "artifacts": artifacts,
        "receipts": receipts,
        "validation": validation.to_dict(),
    }


__all__ = [
    "CanonicalPhaseArtifact",
    "CielPhaseFamily",
    "DoctorOracleGateResult",
    "PhaseTwinReceipt",
    "TwinEquivalenceStatus",
    "build_cielphase_registry",
    "emit_phase_twin",
    "export_phase_receipt",
    "family_for_path",
    "find_phase_twin",
    "load_cielphase_artifact",
    "twin_path_for_source",
    "validate_phase_twin",
]
