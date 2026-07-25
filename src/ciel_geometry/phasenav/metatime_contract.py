"""PhaseNav metatime contract — immutable, receipt-verified axiom set.

PhaseNav is the canonical public name.  This module IS the implementation,
not a wrapper.  The contract is deliberately dependency-free (no numpy,
no PhaseNav runtime) so it can be verified and audited independently.

The information quantum ``kappa = ln(2) / (24*pi)`` is the central constant,
derived from the S4 symmetry group order (|S4| = 4! = 24).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
import re
from typing import Any, Iterable, Mapping


CONTRACT_SCHEMA = "ciel.phasenav.metatime.contract/v1"
CONTRACT_VERSION = "1.0.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

# ── Information quantum ────────────────────────────────────────────────
# kappa = ln(2) / (24*pi)  — derived from |S4| = 4!
INFORMATION_KAPPA = math.log(2.0) / (math.factorial(4) * math.pi)


class EpistemicClass(str, Enum):
    """What kind of support a value has.

    ``FOUNDATIONAL_ANSATZ`` is a first-class, exportable system axiom.
    Exact algebra performed after adopting such an axiom is marked
    ``DERIVED_FROM_FOUNDATIONAL_ANSATZ``.
    """

    EXACT_IDENTITY = "exact_identity"
    FOUNDATIONAL_ANSATZ = "foundational_ansatz"
    DERIVED_FROM_FOUNDATIONAL_ANSATZ = "derived_from_foundational_ansatz"
    EMPIRICAL_FIT = "empirical_fit"
    EXTERNAL_MEASUREMENT = "external_measurement"
    CONFIGURATION = "configuration"
    HYPOTHESIS = "hypothesis"


class ReceiptScope(str, Enum):
    """The claim actually covered by a hash receipt."""

    CONTRACT_PAYLOAD_IDENTITY = "contract_payload_identity_only"
    CALCULATION_PAYLOAD_IDENTITY = "calculation_payload_identity_only"


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class SourceReceipt:
    """SHA-256 receipt with an explicit, deliberately narrow assertion scope."""

    source_id: str
    sha256: str
    scope: ReceiptScope

    def __post_init__(self):
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not _SHA256_RE.fullmatch(self.sha256):
            raise ValueError("sha256 must be a lowercase 64-character digest")

    @classmethod
    def from_payload(cls, source_id: str, payload: Mapping[str, Any], *, scope: ReceiptScope) -> SourceReceipt:
        digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
        return cls(source_id=source_id, sha256=digest, scope=scope)

    def verifies(self, payload: Mapping[str, Any]) -> bool:
        return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest() == self.sha256


@dataclass(frozen=True, slots=True)
class ProvenanceNode:
    """One node in the contract's inspectable dependency graph."""

    node_id: str
    epistemic_class: EpistemicClass
    statement: str
    formula: str | None = None
    depends_on: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.node_id.strip():
            raise ValueError("node_id must not be empty")
        if not self.statement.strip():
            raise ValueError("statement must not be empty")
        if self.node_id in self.depends_on:
            raise ValueError("a provenance node cannot depend on itself")
        if self.epistemic_class is EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ:
            if not self.depends_on:
                raise ValueError("derived ansatz values require an explicit dependency")

    def to_payload(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "epistemic_class": self.epistemic_class.value,
            "statement": self.statement,
            "formula": self.formula,
            "depends_on": list(self.depends_on),
        }


def _finite_positive(name: str, value: float) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return numeric


def _reject_exact_tau(classification: EpistemicClass) -> None:
    if classification is EpistemicClass.EXACT_IDENTITY:
        raise ValueError("a selected tau value cannot be promoted to EXACT_IDENTITY")


@dataclass(frozen=True, slots=True)
class RelationalTauSpectrum:
    """Dimensionless relational eigenvalues; not a neutrino mass ratio."""

    tau_1: float
    tau_2: float
    tau_3: float
    epistemic_class: EpistemicClass
    provenance_id: str

    def __post_init__(self):
        values = tuple(
            _finite_positive(name, value)
            for name, value in (
                ("tau_1", self.tau_1),
                ("tau_2", self.tau_2),
                ("tau_3", self.tau_3),
            )
        )
        if values != tuple(sorted(values)) or len(set(values)) != 3:
            raise ValueError("relational tau values must be strictly increasing")
        _reject_exact_tau(self.epistemic_class)
        if not self.provenance_id.strip():
            raise ValueError("provenance_id must not be empty")

    @property
    def values(self) -> tuple[float, float, float]:
        return (self.tau_1, self.tau_2, self.tau_3)


@dataclass(frozen=True, slots=True)
class PhaseTauBaseline:
    """A dimensionless phase-normalization baseline."""

    value: float
    epistemic_class: EpistemicClass
    provenance_id: str

    def __post_init__(self):
        _finite_positive("phase tau baseline", self.value)
        _reject_exact_tau(self.epistemic_class)
        if not self.provenance_id.strip():
            raise ValueError("provenance_id must not be empty")


@dataclass(frozen=True, slots=True)
class NeutrinoMassAnsatzRatios:
    """Dimensionless neutrino mass ratios, never interchangeable with relational tau."""

    ratios: tuple[float, float, float]
    epistemic_class: EpistemicClass
    provenance_id: str

    def __post_init__(self):
        if len(self.ratios) != 3:
            raise ValueError("exactly three neutrino mass ratios are required")
        for index, value in enumerate(self.ratios, start=1):
            _finite_positive(f"neutrino mass ratio {index}", value)
        _reject_exact_tau(self.epistemic_class)
        if self.epistemic_class not in {
            EpistemicClass.FOUNDATIONAL_ANSATZ,
            EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ,
        }:
            raise ValueError("neutrino ansatz ratios require an ansatz epistemic class")
        if not self.provenance_id.strip():
            raise ValueError("provenance_id must not be empty")


@dataclass(frozen=True, slots=True)
class DerivedScalar:
    name: str
    value: float
    unit: str
    epistemic_class: EpistemicClass
    formula: str
    dependency_chain: tuple[str, ...]
    receipt: SourceReceipt


@dataclass(frozen=True, slots=True)
class ExactPhaseMetrics:
    """Threshold-free circular statistics defined by exact formulas.

    The formulas are exact identities for the supplied floating-point inputs.
    Their numerical representation is still subject to normal floating-point
    rounding and makes no semantic or physical interpretation claim.
    """

    normalized_phases: tuple[float, ...]
    signed_reference_deltas: tuple[float, ...]
    pairwise_signed_deltas: tuple[tuple[float, ...], ...]
    resultant_x: float
    resultant_y: float
    resultant_length: float
    circular_variance: float
    reference_phase: float
    epistemic_class: EpistemicClass
    formulae: tuple[str, ...]
    receipt: SourceReceipt


def _finite_phase(name: str, value: float) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def normalize_phase(phase_radians: float) -> float:
    """Return ``phase mod 2*pi`` in ``[0, 2*pi)``."""
    return _finite_phase("phase_radians", phase_radians) % math.tau


def signed_phase_delta(source_radians: float, target_radians: float) -> float:
    """Return the principal signed delta in ``[-pi, pi]``."""
    source = _finite_phase("source_radians", source_radians)
    target = _finite_phase("target_radians", target_radians)
    delta = target - source
    return math.atan2(math.sin(delta), math.cos(delta))


def derive_exact_phase_metrics(
    phases_radians: Iterable[float],
    *,
    reference_phase: float,
) -> ExactPhaseMetrics:
    """Compute circular metrics without fitted weights, thresholds, or hidden defaults."""
    phases = tuple(
        _finite_phase(f"phases_radians[{index}]", value)
        for index, value in enumerate(phases_radians)
    )
    if not phases:
        raise ValueError("at least one phase is required")
    reference = _finite_phase("reference_phase", reference_phase)
    normalized = tuple(normalize_phase(value) for value in phases)
    signed_deltas = tuple(signed_phase_delta(reference, value) for value in phases)
    pairwise = tuple(
        tuple(signed_phase_delta(source, target) for target in phases)
        for source in phases
    )
    count = len(phases)
    resultant_x = math.fsum(math.cos(value) for value in phases) / count
    resultant_y = math.fsum(math.sin(value) for value in phases) / count
    resultant_length = math.hypot(resultant_x, resultant_y)
    resultant_length = min(1.0, resultant_length)
    circular_variance = 1.0 - resultant_length
    formulae = (
        "normalized_phase = phase mod (2*pi)",
        "signed_delta(a,b) = atan2(sin(b-a), cos(b-a))",
        "R_x = mean(cos(phase_i))",
        "R_y = mean(sin(phase_i))",
        "resultant_length = sqrt(R_x^2 + R_y^2)",
        "circular_variance = 1 - resultant_length",
    )
    payload = {
        "schema": "phasenav.metatime.exact-phase-metrics/v1",
        "phases_radians": list(phases),
        "reference_phase": reference,
        "normalized_phases": list(normalized),
        "signed_reference_deltas": list(signed_deltas),
        "pairwise_signed_deltas": [list(row) for row in pairwise],
        "resultant_x": resultant_x,
        "resultant_y": resultant_y,
        "resultant_length": resultant_length,
        "circular_variance": circular_variance,
        "formulae": list(formulae),
    }
    receipt = SourceReceipt.from_payload(
        "phasenav:exact-phase-metrics/v1",
        payload,
        scope=ReceiptScope.CALCULATION_PAYLOAD_IDENTITY,
    )
    return ExactPhaseMetrics(
        normalized_phases=normalized,
        signed_reference_deltas=signed_deltas,
        pairwise_signed_deltas=pairwise,
        resultant_x=resultant_x,
        resultant_y=resultant_y,
        resultant_length=resultant_length,
        circular_variance=circular_variance,
        reference_phase=reference,
        epistemic_class=EpistemicClass.EXACT_IDENTITY,
        formulae=formulae,
        receipt=receipt,
    )


@dataclass(frozen=True, slots=True)
class MetatimeContract:
    """Immutable metatime axiom set plus its validated provenance DAG."""

    schema: str
    version: str
    relational_tau: RelationalTauSpectrum
    phase_tau_baseline: PhaseTauBaseline
    symmetry_group: str
    provenance: tuple[ProvenanceNode, ...]
    receipt: SourceReceipt
    neutrino_mass_ratios: NeutrinoMassAnsatzRatios | None = None

    def __post_init__(self):
        if self.schema != CONTRACT_SCHEMA:
            raise ValueError(f"unsupported contract schema: {self.schema!r}")
        if not _SEMVER_RE.fullmatch(self.version):
            raise ValueError("contract version must use MAJOR.MINOR.PATCH")
        if self.symmetry_group != "S4":
            raise ValueError("contract v1 supports the versioned S4 ansatz only")
        nodes = self._node_map()
        self._validate_graph(nodes)
        for typed_value in (self.relational_tau, self.phase_tau_baseline):
            node = nodes.get(typed_value.provenance_id)
            if node is None:
                raise ValueError(f"missing provenance node: {typed_value.provenance_id}")
            if node.epistemic_class is not typed_value.epistemic_class:
                raise ValueError("typed value and provenance epistemic classes disagree")
        if self.neutrino_mass_ratios is not None:
            node = nodes.get(self.neutrino_mass_ratios.provenance_id)
            if node is None:
                raise ValueError("neutrino ratios reference a missing provenance node")
            if node.epistemic_class is not self.neutrino_mass_ratios.epistemic_class:
                raise ValueError("neutrino ratio and provenance classes disagree")
        if self.receipt.scope is not ReceiptScope.CONTRACT_PAYLOAD_IDENTITY:
            raise ValueError("contract receipt has the wrong assertion scope")
        if not self.receipt.verifies(self.identity_payload()):
            raise ValueError("contract payload does not match its SHA-256 receipt")

    def _node_map(self) -> dict[str, ProvenanceNode]:
        nodes = {node.node_id: node for node in self.provenance}
        if len(nodes) != len(self.provenance):
            raise ValueError("provenance node ids must be unique")
        return nodes

    @staticmethod
    def _validate_graph(nodes: Mapping[str, ProvenanceNode]) -> None:
        for node in nodes.values():
            missing = set(node.depends_on).difference(nodes)
            if missing:
                raise ValueError(f"unknown provenance dependencies: {sorted(missing)}")

        visiting: set[str] = set()
        reaches_foundation_cache: dict[str, bool] = {}

        def visit(node_id: str) -> bool:
            if node_id in visiting:
                raise ValueError("provenance dependencies must be acyclic")
            if node_id in reaches_foundation_cache:
                return reaches_foundation_cache[node_id]
            visiting.add(node_id)
            reaches_foundation = (
                nodes[node_id].epistemic_class is EpistemicClass.FOUNDATIONAL_ANSATZ
            )
            for dependency in nodes[node_id].depends_on:
                reaches_foundation = visit(dependency) or reaches_foundation
            visiting.remove(node_id)
            if (
                nodes[node_id].epistemic_class
                is EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ
                and not reaches_foundation
            ):
                raise ValueError("derived ansatz must trace to a foundational ansatz")
            reaches_foundation_cache[node_id] = reaches_foundation
            return reaches_foundation

        for node_id in nodes:
            visit(node_id)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "symmetry_group": self.symmetry_group,
            "relational_tau": {
                "values": list(self.relational_tau.values),
                "epistemic_class": self.relational_tau.epistemic_class.value,
                "provenance_id": self.relational_tau.provenance_id,
                "unit": "dimensionless",
            },
            "phase_tau_baseline": {
                "value": self.phase_tau_baseline.value,
                "epistemic_class": self.phase_tau_baseline.epistemic_class.value,
                "provenance_id": self.phase_tau_baseline.provenance_id,
                "unit": "dimensionless",
            },
            "neutrino_mass_ratios": (
                None
                if self.neutrino_mass_ratios is None
                else {
                    "ratios": list(self.neutrino_mass_ratios.ratios),
                    "epistemic_class": self.neutrino_mass_ratios.epistemic_class.value,
                    "provenance_id": self.neutrino_mass_ratios.provenance_id,
                    "unit": "dimensionless_ratio",
                }
            ),
            "provenance": [node.to_payload() for node in self.provenance],
        }

    def dependency_chain(self, node_id: str) -> tuple[str, ...]:
        nodes = self._node_map()
        if node_id not in nodes:
            raise KeyError(node_id)
        ordered: list[str] = []
        seen: set[str] = set()

        def collect(current: str) -> None:
            for dependency in nodes[current].depends_on:
                collect(dependency)
            if current not in seen:
                ordered.append(current)
                seen.add(current)

        collect(node_id)
        return tuple(ordered)

    @property
    def information_kappa(self) -> DerivedScalar:
        node_id = "metatime.metric.information_kappa.v1"
        return DerivedScalar(
            name="information_kappa",
            value=INFORMATION_KAPPA,
            unit="dimensionless",
            epistemic_class=EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ,
            formula="ln(2) / (|S4| * pi), |S4| = 4!",
            dependency_chain=self.dependency_chain(node_id),
            receipt=self.receipt,
        )


def build_metatime_contract_v1() -> MetatimeContract:
    """Build the deterministic v1 contract.

    The relational tau spectrum and S4 normalization are versioned foundational
    ansatzes.  The baseline and information kappa are exact consequences of
    those adopted ansatzes.
    """
    relational_id = "metatime.ansatz.relational_tau.v1"
    baseline_id = "metatime.selection.phase_tau_baseline.v1"
    s4_id = "metatime.ansatz.s4_phase_normalization.v1"
    s4_order_id = "metatime.identity.s4_order.v1"
    kappa_id = "metatime.metric.information_kappa.v1"
    relational_tau = RelationalTauSpectrum(
        0.263, 0.353, 0.489,
        epistemic_class=EpistemicClass.FOUNDATIONAL_ANSATZ,
        provenance_id=relational_id,
    )
    phase_tau_baseline = PhaseTauBaseline(
        0.353,
        epistemic_class=EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ,
        provenance_id=baseline_id,
    )
    provenance = (
        ProvenanceNode(
            node_id=relational_id,
            epistemic_class=EpistemicClass.FOUNDATIONAL_ANSATZ,
            statement="Adopt ordered dimensionless relational tau spectrum (0.263, 0.353, 0.489) for v1.",
        ),
        ProvenanceNode(
            node_id=baseline_id,
            epistemic_class=EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ,
            statement="Select the middle relational eigenvalue as phase baseline.",
            formula="phase_tau_baseline = relational_tau.tau_2",
            depends_on=(relational_id,),
        ),
        ProvenanceNode(
            node_id=s4_id,
            epistemic_class=EpistemicClass.FOUNDATIONAL_ANSATZ,
            statement="Adopt S4 as phase-normalization symmetry group for v1.",
        ),
        ProvenanceNode(
            node_id=s4_order_id,
            epistemic_class=EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ,
            statement="Compute the order of the adopted S4 group.",
            formula="|S4| = 4! = 24",
            depends_on=(s4_id,),
        ),
        ProvenanceNode(
            node_id=kappa_id,
            epistemic_class=EpistemicClass.DERIVED_FROM_FOUNDATIONAL_ANSATZ,
            statement="Compute information-kappa normalization from S4 order.",
            formula="information_kappa = ln(2) / (|S4| * pi)",
            depends_on=(s4_order_id,),
        ),
    )
    payload = {
        "schema": CONTRACT_SCHEMA,
        "version": CONTRACT_VERSION,
        "symmetry_group": "S4",
        "relational_tau": {
            "values": list(relational_tau.values),
            "epistemic_class": relational_tau.epistemic_class.value,
            "provenance_id": relational_tau.provenance_id,
            "unit": "dimensionless",
        },
        "phase_tau_baseline": {
            "value": phase_tau_baseline.value,
            "epistemic_class": phase_tau_baseline.epistemic_class.value,
            "provenance_id": phase_tau_baseline.provenance_id,
            "unit": "dimensionless",
        },
        "neutrino_mass_ratios": None,
        "provenance": [node.to_payload() for node in provenance],
    }
    receipt = SourceReceipt.from_payload(
        f"phasenav-metatime-contract:{CONTRACT_VERSION}",
        payload,
        scope=ReceiptScope.CONTRACT_PAYLOAD_IDENTITY,
    )
    return MetatimeContract(
        schema=CONTRACT_SCHEMA,
        version=CONTRACT_VERSION,
        relational_tau=relational_tau,
        phase_tau_baseline=phase_tau_baseline,
        symmetry_group="S4",
        provenance=provenance,
        receipt=receipt,
    )


# Canonical PhaseNav names.  Keep these as explicit aliases rather than a
# second implementation so old callers cannot silently select another
# metatime model or import tree.
PhaseNavEpistemicClass = EpistemicClass
PhaseNavMetatimeContract = MetatimeContract
PhaseNavNeutrinoMassAnsatzRatios = NeutrinoMassAnsatzRatios


def build_phasenav_metatime_contract() -> PhaseNavMetatimeContract:
    return build_metatime_contract_v1()


def derive_phasenav_phase_metrics(*args: Any, **kwargs: Any) -> ExactPhaseMetrics:
    return derive_exact_phase_metrics(*args, **kwargs)


__all__ = [
    "CONTRACT_SCHEMA", "CONTRACT_VERSION", "INFORMATION_KAPPA",
    "EpistemicClass", "ReceiptScope",
    "SourceReceipt", "ProvenanceNode",
    "RelationalTauSpectrum", "PhaseTauBaseline",
    "NeutrinoMassAnsatzRatios", "DerivedScalar", "ExactPhaseMetrics",
    "MetatimeContract",
    "normalize_phase", "signed_phase_delta",
    "derive_exact_phase_metrics",
    "build_metatime_contract_v1",
    "PhaseNavEpistemicClass", "PhaseNavMetatimeContract",
    "PhaseNavNeutrinoMassAnsatzRatios",
    "build_phasenav_metatime_contract", "derive_phasenav_phase_metrics",
]
