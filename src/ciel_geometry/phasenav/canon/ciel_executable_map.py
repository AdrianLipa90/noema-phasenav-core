"""Typed CIEL executable-source -> PhaseNav concept bindings.

This layer maps executable algorithms that already exist in CIEL source trees
onto PhaseNav concept cards.  It does not copy legacy implementations, import
external repositories implicitly, or promote scientific claims.

Two provenance classes are intentionally kept distinct:

* ``CANONICAL_V15``: promoted NOEMA/CIELingo integration boundary currently in
  ``CIEL-NOEMA-HTRI-CIELingo-Phasenav``;
* ``LEGACY_EXECUTABLE_SOURCE`` / ``LEGACY_TEST_EXECUTABLE``: executable source
  recovered from the older full CIEL/Ω kernel.  These bindings are semantic
  routing references, not canon promotion of the legacy implementation.

A concept match therefore yields an execution *plan*.  Actual external callable
resolution remains an explicit runtime step and write-capable bindings are never
auto-executed by this module.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable, Literal


CIEL_EXECUTABLE_MAP_VERSION = "0.13.0"
CIEL_EXECUTABLE_MAP_STATUS = "CANDIDATE_TYPED_SOURCE_BINDING_NO_AUTO_EXECUTION"

CANON_V15_REPO = "AdrianLipa90/CIEL-NOEMA-HTRI-CIELingo-Phasenav"
CANON_V15_COMMIT = "f24b125039833d47316e5be1bcb4e18ce030a893"
LEGACY_CIEL_REPO = "AdrianLipa90/CIEL-Omega-General-Quantum-Consciousness"
LEGACY_CIEL_COMMIT = "5812b547a6308d79ef6b42606b9bda28f1879274"

SideEffect = Literal["PURE", "READ", "WRITE", "STATEFUL", "VERIFY", "ORCHESTRATE"]
ProvenanceClass = Literal[
    "CANONICAL_V15",
    "LEGACY_EXECUTABLE_SOURCE",
    "LEGACY_TEST_EXECUTABLE",
]


@dataclass(frozen=True)
class CielExecutableBinding:
    binding_id: str
    family: str
    source_repo: str
    source_commit: str
    source_blob_sha: str
    source_path: str
    symbol: str
    provenance_class: ProvenanceClass
    side_effect: SideEffect
    concept_ids: tuple[str, ...]
    priority: int
    semantic_role: str
    execution_activation: str = "EXPLICIT_RUNTIME_DISPATCH"
    scientific_promotion: str = "NOT_PERFORMED"

    def __post_init__(self) -> None:
        if not self.binding_id or not self.family or not self.symbol:
            raise ValueError("binding identity, family, and symbol must be non-empty")
        if not self.concept_ids:
            raise ValueError(f"{self.binding_id}: at least one concept target is required")
        if any(len(str(cid)) != 3 or not str(cid).isdigit() for cid in self.concept_ids):
            raise ValueError(f"{self.binding_id}: concept ids must be zero-padded 3-digit strings")
        if self.execution_activation != "EXPLICIT_RUNTIME_DISPATCH":
            raise ValueError("CIEL bindings may not auto-execute from concept recognition")
        if self.priority < 0:
            raise ValueError("priority must be non-negative")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# Exact source-file identities observed on the referenced commits.
_BLOB = {
    "v15_memory_commit": "2930a7335f71f52d3cafdd9ded734c4aea4a2227",
    "v15_pipeline": "ee482a6a51dcbe54f1f51a2e38639881877aa9ab",
    "v15_runtime": "f25c7f8c7901db295b976cff99546316377e5d02",
    "v15_doctor": "9f47b0a6e240c01dfefa021cfaacf8cea73e437c",
    "legacy_memory": "d858c9543420a2f7b26d96455155c3d38c662cdb",
    "legacy_paradox": "ba3d8d48a40306a50dc67835419c43e130adf705",
}


def _b(
    binding_id: str,
    family: str,
    *,
    repo: str,
    commit: str,
    blob: str,
    path: str,
    symbol: str,
    provenance: ProvenanceClass,
    side_effect: SideEffect,
    concepts: Iterable[str],
    priority: int,
    role: str,
) -> CielExecutableBinding:
    return CielExecutableBinding(
        binding_id=binding_id,
        family=family,
        source_repo=repo,
        source_commit=commit,
        source_blob_sha=blob,
        source_path=path,
        symbol=symbol,
        provenance_class=provenance,
        side_effect=side_effect,
        concept_ids=tuple(str(x).zfill(3) for x in concepts),
        priority=priority,
        semantic_role=role,
    )


_BINDINGS: tuple[CielExecutableBinding, ...] = (
    # ---------------------------------------------------------------- memory
    _b(
        "CIEL.MEMORY.RECONSTRUCT.V15", "memory",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_runtime"],
        path="integration/canonical_v15/runtime_adapters.py",
        symbol="SafeTieredMemoryReadAdapter.reconstruct",
        provenance="CANONICAL_V15", side_effect="READ",
        concepts=("090", "089", "073"), priority=10,
        role="durable memory reconstruction with Tier-1/CIELingo PhaseMemory bypass",
    ),
    _b(
        "CIEL.MEMORY.READ_PACKET.V15", "memory",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_pipeline"],
        path="integration/canonical_v15/integration_pipeline.py",
        symbol="MemoryHomeReadAdapter.read",
        provenance="CANONICAL_V15", side_effect="READ",
        concepts=("090", "089", "073"), priority=20,
        role="reconstructed Memory Home -> provenance-bearing CIELingo packet",
    ),
    _b(
        "CIEL.MEMORY.COMMIT.V15", "memory",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_memory_commit"],
        path="integration/canonical_v15/canonical_memory_commit.py",
        symbol="SafeTieredMemoryCommitAdapter.commit",
        provenance="CANONICAL_V15", side_effect="WRITE",
        concepts=("090", "105"), priority=90,
        role="fail-closed durable/deep memory commit with canonical admission metadata",
    ),
    _b(
        "CIEL.MEMORY.ADMISSION.V15", "memory",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_pipeline"],
        path="integration/canonical_v15/integration_pipeline.py",
        symbol="AdmissionPolicy.admit_surface",
        provenance="CANONICAL_V15", side_effect="WRITE",
        concepts=("079", "100", "090"), priority=80,
        role="classification and validation gate before canonical memory write",
    ),
    _b(
        "CIEL.MEMORY.RECEIPT_CHAIN.V15", "memory",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_pipeline"],
        path="integration/canonical_v15/integration_pipeline.py",
        symbol="verify_receipt_chain",
        provenance="CANONICAL_V15", side_effect="VERIFY",
        concepts=("039", "079", "090"), priority=70,
        role="verify predecessor-linked PASS receipt chain",
    ),
    _b(
        "CIEL.MEMORY.CAPTURE.LEGACY", "memory",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_memory"],
        path="ciel_memory/orchestrator.py",
        symbol="UnifiedMemoryOrchestrator.capture",
        provenance="LEGACY_TEST_EXECUTABLE", side_effect="PURE",
        concepts=("090", "077"), priority=30,
        role="capture context/sense/associations/timestamp/meta as a DataVector",
    ),
    _b(
        "CIEL.MEMORY.TMP_EVALUATE.LEGACY", "memory",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_memory"],
        path="ciel_memory/orchestrator.py",
        symbol="UnifiedMemoryOrchestrator.run_tmp",
        provenance="LEGACY_TEST_EXECUTABLE", side_effect="STATEFUL",
        concepts=("090", "067"), priority=40,
        role="legacy test-friendly TMP evaluation and verification-queue staging",
    ),
    _b(
        "CIEL.MEMORY.BIFURCATION_PROMOTE.LEGACY", "memory",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_memory"],
        path="ciel_memory/orchestrator.py",
        symbol="UnifiedMemoryOrchestrator.promote_if_bifurcated",
        provenance="LEGACY_TEST_EXECUTABLE", side_effect="WRITE",
        concepts=("090", "080"), priority=85,
        role="legacy bifurcation-triggered memory persistence",
    ),
    _b(
        "CIEL.MEMORY.MAINTENANCE.LEGACY", "memory",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_memory"],
        path="ciel_memory/orchestrator.py",
        symbol="UnifiedMemoryOrchestrator.daily_maintenance",
        provenance="LEGACY_TEST_EXECUTABLE", side_effect="STATEFUL",
        concepts=("090", "080"), priority=95,
        role="purge completed TMP reports and preserve pending verification state",
    ),

    # -------------------------------------------------------------- language
    _b(
        "CIEL.SEMANTIC.LINGOPHYSICS.V15", "semantic",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_pipeline"],
        path="integration/canonical_v15/integration_pipeline.py",
        symbol="LingophysicsAdapter.analyze",
        provenance="CANONICAL_V15", side_effect="PURE",
        concepts=("096", "104", "073"), priority=20,
        role="formal meaning proposal from reconstructed memory packet",
    ),
    _b(
        "CIEL.SEMANTIC.SURFACE.V15", "semantic",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_pipeline"],
        path="integration/canonical_v15/integration_pipeline.py",
        symbol="CIELingoSurfaceAdapter.generate",
        provenance="CANONICAL_V15", side_effect="PURE",
        concepts=("109", "106", "096"), priority=30,
        role="proposal-only surface realization",
    ),
    _b(
        "CIEL.SEMANTIC.LANGUAGE_LOOP.V15", "semantic",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_pipeline"],
        path="integration/canonical_v15/integration_pipeline.py",
        symbol="CanonicalLanguageLoop.run",
        provenance="CANONICAL_V15", side_effect="ORCHESTRATE",
        concepts=("105", "096", "090"), priority=50,
        role="memory -> lingophysics -> surface -> optional admission orchestration",
    ),
    _b(
        "CIEL.VERIFY.DOCTOR.V15", "verification",
        repo=CANON_V15_REPO, commit=CANON_V15_COMMIT, blob=_BLOB["v15_doctor"],
        path="integration/canonical_v15/doctor.py",
        symbol="doctor",
        provenance="CANONICAL_V15", side_effect="VERIFY",
        concepts=("067", "039", "079"), priority=10,
        role="source, reconstruction, admission and receipt-chain audit",
    ),

    # -------------------------------------------------------------- paradoxes
    _b(
        "CIEL.PARADOX.NETWORK.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.initialize_paradox_networks",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("119", "073"), priority=10,
        role="directed network of interacting paradox operators",
    ),
    _b(
        "CIEL.PARADOX.COHERENCE.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.compute_paradox_coherence",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("119", "003"), priority=20,
        role="network-connectivity paradox coherence metric",
    ),
    _b(
        "CIEL.PARADOX.LIAR_GODEL_RUSSELL.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.russell_godel_liar_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("119", "039", "096"), priority=30,
        role="self-referential truth oscillation",
    ),
    _b(
        "CIEL.PARADOX.SORITES.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.sorites_paradox_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("119", "072"), priority=30,
        role="gradual category-boundary dissolution",
    ),
    _b(
        "CIEL.PARADOX.THESEUS.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.ship_of_theseus_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("119", "032"), priority=30,
        role="identity continuity under component replacement",
    ),
    _b(
        "CIEL.PARADOX.UNEXPECTED_HANGING.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.unexpected_hanging_paradox",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("119", "034", "050"), priority=30,
        role="self-negating prediction/expectation interaction",
    ),
    _b(
        "CIEL.PARADOX.NEWCOMB.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.newcombs_paradox_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("119", "033", "034"), priority=30,
        role="agency versus prediction decision operator",
    ),
    _b(
        "CIEL.PARADOX.SIMPSON.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.simpsons_paradox_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("119", "067"), priority=30,
        role="aggregation-reversal evaluation operator",
    ),
    _b(
        "CIEL.PARADOX.MEREOLOGY.LEGACY", "paradox",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.mereology_paradox",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("119", "070"), priority=30,
        role="whole-versus-parts emergent relation",
    ),

    # --------------------------------------------------------------- temporal
    _b(
        "CIEL.TIME.FIELD_INIT.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.initialize_temporal_field",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("018", "114"), priority=10,
        role="initialize temporal-superfluid phase field",
    ),
    _b(
        "CIEL.TIME.FIELD_EVOLVE.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.evolve_temporal_field",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("018", "114", "080"), priority=20,
        role="temporal evolution from viscosity, causal gradient, and paradox-loop phase",
    ),
    _b(
        "CIEL.TIME.EVOLUTION_STEP.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.ultimate_evolution_step",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="ORCHESTRATE",
        concepts=("018", "080", "115"), priority=40,
        role="advance the coupled field state by one explicit dt step",
    ),
    _b(
        "CIEL.TIME.ZENO.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.zeno_quantum_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("018", "077", "119"), priority=30,
        role="observation-rate temporal freezing operator",
    ),
    _b(
        "CIEL.TIME.CAUSAL_LOOP.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.tachyonic_causality_loop",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("120", "018", "119"), priority=30,
        role="phase-valued causal-loop relation from event separation",
    ),
    _b(
        "CIEL.TIME.BOOTSTRAP_LOOP.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.bootstrap_paradox_4d",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("120", "119", "114"), priority=30,
        role="future/past phase-loop consistency operator",
    ),
    _b(
        "CIEL.TIME.GRANDFATHER_GUARD.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.grandfather_paradox_prevention",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("120", "119"), priority=30,
        role="timeline-coherence intervention branching rule",
    ),
    _b(
        "CIEL.TIME.PREDESTINATION.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.predestination_paradox_field",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("120", "119", "034", "114"), priority=30,
        role="closed-loop self-consistent timeline field",
    ),
    _b(
        "CIEL.TIME.ENTROPY_DECAY.LEGACY", "temporal",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.heat_death_entropy_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("018", "026"), priority=30,
        role="time-parameterized entropy-field attenuation",
    ),

    # --------------------------------------------------------- intention/ethic
    _b(
        "CIEL.INTENTION.FIELD_INIT.LEGACY", "intention",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.initialize_intention_field",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("002", "040"), priority=10,
        role="initialize intention phase field",
    ),
    _b(
        "CIEL.INTENTION.FIELD_EVOLVE.LEGACY", "intention",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.evolve_intention_field",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("002", "080"), priority=20,
        role="evolve intention phase field",
    ),
    _b(
        "CIEL.ETHICS.PROTECT.LEGACY", "ethics",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.ciel_protective_operator",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("100",), priority=10,
        role="ethical-potential attenuation/protection operator",
    ),
    _b(
        "CIEL.ETHICS.FIELD_EVOLVE.LEGACY", "ethics",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.evolve_ethical_field",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("100", "056", "039"), priority=20,
        role="ethical field evolution using compassion gradient and truth-preservation term",
    ),

    # ------------------------------------------------------------ resonance etc
    _b(
        "CIEL.RESONANCE.ULTIMATE.LEGACY", "resonance",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.compute_ultimate_resonance",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("001", "003"), priority=10,
        role="pairwise field-correlation resonance aggregation",
    ),
    _b(
        "CIEL.CHAOS.COLLATZ.LEGACY", "dynamics",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateParadoxOperators.collatz_chaos_order",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="PURE",
        concepts=("093", "080"), priority=10,
        role="bounded Collatz trajectory generator",
    ),
    _b(
        "CIEL.CONSCIOUSNESS.FIELD_EVOLVE.LEGACY", "consciousness",
        repo=LEGACY_CIEL_REPO, commit=LEGACY_CIEL_COMMIT, blob=_BLOB["legacy_paradox"],
        path="paradoxes/ultimate_operators.py",
        symbol="UltimateUniversalLawEngine4D.evolve_consciousness_field",
        provenance="LEGACY_EXECUTABLE_SOURCE", side_effect="STATEFUL",
        concepts=("031", "032", "080"), priority=10,
        role="self-referential consciousness-field phase evolution",
    ),
)


def ciel_executable_bindings() -> tuple[CielExecutableBinding, ...]:
    """Return the immutable v0.13 source-binding set."""
    return _BINDINGS


def binding_by_id(binding_id: str) -> CielExecutableBinding:
    for binding in _BINDINGS:
        if binding.binding_id == binding_id:
            return binding
    raise KeyError(binding_id)


def bindings_for_concept(concept_id: str | int) -> tuple[CielExecutableBinding, ...]:
    key = str(concept_id).zfill(3)
    return tuple(
        sorted(
            (binding for binding in _BINDINGS if key in binding.concept_ids),
            key=lambda item: (item.priority, item.binding_id),
        )
    )


def bindings_for_family(family: str) -> tuple[CielExecutableBinding, ...]:
    key = str(family).strip().lower()
    return tuple(
        sorted(
            (binding for binding in _BINDINGS if binding.family == key),
            key=lambda item: (item.priority, item.binding_id),
        )
    )


def concept_execution_plan(
    concept_id: str | int,
    *,
    include_legacy: bool = False,
    include_writes: bool = False,
) -> tuple[CielExecutableBinding, ...]:
    """Return an explicit, side-effect-aware execution plan for one concept.

    Default policy is conservative: canonical V15 references only, and no WRITE
    bindings.  Legacy source and writes require separate opt-ins.  Returning a
    plan never imports or executes the external source.
    """
    rows = bindings_for_concept(concept_id)
    out: list[CielExecutableBinding] = []
    for binding in rows:
        if not include_legacy and binding.provenance_class != "CANONICAL_V15":
            continue
        if not include_writes and binding.side_effect == "WRITE":
            continue
        out.append(binding)
    return tuple(out)


def ciel_executable_map_receipt() -> dict[str, object]:
    rows = [binding.to_dict() for binding in _BINDINGS]
    payload: dict[str, object] = {
        "schema": "phasenav.ciel-executable-concept-map/v0.13",
        "version": CIEL_EXECUTABLE_MAP_VERSION,
        "status": CIEL_EXECUTABLE_MAP_STATUS,
        "source_anchors": {
            "canonical_v15": {"repo": CANON_V15_REPO, "commit": CANON_V15_COMMIT},
            "legacy_full_kernel": {"repo": LEGACY_CIEL_REPO, "commit": LEGACY_CIEL_COMMIT},
        },
        "bindings": rows,
        "binding_count": len(rows),
        "families": sorted({binding.family for binding in _BINDINGS}),
        "policy": {
            "auto_execute_from_concept_match": False,
            "external_import_performed": False,
            "write_binding_requires_explicit_opt_in": True,
            "legacy_binding_requires_explicit_opt_in": True,
            "scientific_promotion": "NOT_PERFORMED",
        },
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    payload["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
