from __future__ import annotations

from ciel_geometry.phasenav.canon.cards import card_by_id, load_canonical_cards
from ciel_geometry.phasenav.canon.ciel_executable_map import (
    CANON_V15_COMMIT,
    CANON_V15_REPO,
    CIEL_EXECUTABLE_MAP_STATUS,
    CIEL_EXECUTABLE_MAP_VERSION,
    LEGACY_CIEL_COMMIT,
    LEGACY_CIEL_REPO,
    binding_by_id,
    bindings_for_concept,
    bindings_for_family,
    ciel_executable_bindings,
    ciel_executable_map_receipt,
    concept_execution_plan,
)
from ciel_geometry.phasenav.canon.ciel_legacy_extended_map import (
    extended_legacy_bindings,
    extended_legacy_bindings_for_concept,
    extended_legacy_bindings_for_family,
)
from ciel_geometry.phasenav.canon.concept_execution import (
    concept_execution_summary,
    execution_plan_for_concept,
)
from ciel_geometry.phasenav.canon.native_executable_map import (
    PHASENAV_NATIVE_COMMIT,
    PHASENAV_NATIVE_REPO,
    native_binding_by_id,
    native_executable_bindings,
    native_executable_map_receipt,
)


def _binding_ids(card: dict) -> set[str]:
    return {str(row["concept_algorithm_id"]) for row in card["algorithm_bindings"]}


def test_new_semantic_nodes_exist_as_candidates() -> None:
    paradox = card_by_id("119")
    causality = card_by_id("120")
    assert paradox["canonical_name"] == "Paradox"
    assert causality["canonical_name"] == "Causality"
    assert paradox["epistemic"]["canon_allowed"] is False
    assert causality["epistemic"]["canon_allowed"] is False


def test_memory_card_carries_native_and_v15_execution_sources() -> None:
    ids = _binding_ids(card_by_id("090"))
    for expected in {
        "PNV.MEMORY.HOLONOMIC_RECALL.NATIVE",
        "PNV.MEMORY.HOLONOMIC_INGEST.NATIVE",
        "PNV.MEMORY.DECAY.NATIVE",
        "PNV.MEMORY.HOLONOMY_CACHE_GET.NATIVE",
        "PNV.MEMORY.HOLONOMY_CACHE_PUT.NATIVE",
        "CIEL.MEMORY.RECONSTRUCT.V15",
        "CIEL.MEMORY.READ_PACKET.V15",
        "CIEL.MEMORY.COMMIT.V15",
        "CIEL.MEMORY.ADMISSION.V15",
        "CIEL.MEMORY.RECEIPT_CHAIN.V15",
    }:
        assert expected in ids


def test_time_card_carries_native_and_legacy_temporal_sources() -> None:
    ids = _binding_ids(card_by_id("018"))
    for expected in {
        "PNV.TIME.GENERATION_DYNAMICS.NATIVE",
        "PNV.TIME.TRAJECTORY_CURVATURE.NATIVE",
        "PNV.MEMORY.DECAY.NATIVE",
        "CIEL.TIME.FIELD_INIT.LEGACY",
        "CIEL.TIME.FIELD_EVOLVE.LEGACY",
        "CIEL.TIME.EVOLUTION_STEP.LEGACY",
        "CIEL.TIME.ZENO.LEGACY",
        "CIEL.TIME.CAUSAL_LOOP.LEGACY",
        "CIEL.TIME.ENTROPY_DECAY.LEGACY",
    }:
        assert expected in ids


def test_context_card_has_native_context_algorithms() -> None:
    ids = _binding_ids(card_by_id("073"))
    for expected in {
        "PNV.CONTEXT.FROM_CONCEPTS.NATIVE",
        "PNV.CONTEXT.VECTOR.NATIVE",
        "PNV.CONTEXT.SAMPLE.NATIVE",
        "PNV.CONTEXT.FIND_ATTRACTORS.NATIVE",
        "PNV.CONTEXT.TRACE_ORBIT.NATIVE",
    }:
        assert expected in ids


def test_kairos_card_has_native_scheduler_and_temporal_algorithms() -> None:
    ids = _binding_ids(card_by_id("115"))
    for expected in {
        "PNV.SCHEDULER.COST.NATIVE",
        "PNV.SCHEDULER.PUSH.NATIVE",
        "PNV.SCHEDULER.POP.NATIVE",
        "PNV.TIME.GENERATION_DYNAMICS.NATIVE",
    }:
        assert expected in ids


def test_paradox_and_causality_cards_collect_their_families() -> None:
    paradox_ids = _binding_ids(card_by_id("119"))
    causality_ids = _binding_ids(card_by_id("120"))
    for expected in {
        "CIEL.PARADOX.NETWORK.LEGACY",
        "CIEL.PARADOX.LIAR_GODEL_RUSSELL.LEGACY",
        "CIEL.PARADOX.THESEUS.LEGACY",
        "CIEL.PARADOX.BANACH_TARSKI.LEGACY",
        "CIEL.PARADOX.HILBERT_HOTEL.LEGACY",
        "CIEL.PARADOX.FERMI.LEGACY",
        "CIEL.PARADOX.EPR.LEGACY",
        "CIEL.PARADOX.WIGNER_FRIEND.LEGACY",
        "CIEL.PARADOX.OLBERS.LEGACY",
        "CIEL.PARADOX.MORAVEC.LEGACY",
        "CIEL.PARADOX.FIELD_INIT.LEGACY",
        "CIEL.PARADOX.FIELD_EVOLVE.LEGACY",
    }:
        assert expected in paradox_ids
    for expected in {
        "CIEL.TIME.CAUSAL_LOOP.LEGACY",
        "CIEL.TIME.BOOTSTRAP_LOOP.LEGACY",
        "CIEL.TIME.GRANDFATHER_GUARD.LEGACY",
        "CIEL.TIME.PREDESTINATION.LEGACY",
    }:
        assert expected in causality_ids


def test_current_and_legacy_heisenberg_are_distinct_bindings() -> None:
    ids = _binding_ids(card_by_id("118"))
    assert "HEISENBERG_UNCERTAINTY" in ids
    assert "CIEL.UNCERTAINTY.HEISENBERG.LEGACY" in ids
    safe = {row.algorithm_id for row in execution_plan_for_concept("118")}
    assert "HEISENBERG_UNCERTAINTY" in safe
    assert "CIEL.UNCERTAINTY.HEISENBERG.LEGACY" not in safe


def test_current_and_legacy_zeta_are_distinct_bindings() -> None:
    ids = _binding_ids(card_by_id("117"))
    assert "RIEMANN_ZETA_ZERO" in ids
    assert "CIEL.ZETA.PROTECTION.LEGACY" in ids
    safe = {row.algorithm_id for row in execution_plan_for_concept("117")}
    assert "RIEMANN_ZETA_ZERO" in safe
    assert "CIEL.ZETA.PROTECTION.LEGACY" not in safe


def test_extended_observer_coherence_and_cosmos_bindings() -> None:
    assert "CIEL.COHERENCE.WATANABE.LEGACY" in _binding_ids(card_by_id("003"))
    assert "CIEL.PARADOX.EPR.LEGACY" in _binding_ids(card_by_id("003"))
    assert "CIEL.OBSERVER.QUANTUM_CREATION.LEGACY" in _binding_ids(card_by_id("031"))
    assert "CIEL.COSMOS.SELF_UNIVERSE.LEGACY" in _binding_ids(card_by_id("094"))
    assert "CIEL.PARADOX.OLBERS.LEGACY" in _binding_ids(card_by_id("094"))


def test_existing_reciprocal_concept_algorithms_survive_v013() -> None:
    assert "RECIPROCAL_INVERSION" in _binding_ids(card_by_id("116"))
    assert "RIEMANN_ZETA_ZERO" in _binding_ids(card_by_id("117"))
    assert "HEISENBERG_UNCERTAINTY" in _binding_ids(card_by_id("118"))


def test_every_binding_points_to_an_existing_concept_card() -> None:
    card_ids = {card["glossary_id"] for card in load_canonical_cards()}
    for binding in (
        *ciel_executable_bindings(),
        *native_executable_bindings(),
        *extended_legacy_bindings(),
    ):
        assert set(binding.concept_ids) <= card_ids


def test_external_binding_provenance_is_exact_and_typed() -> None:
    memory = binding_by_id("CIEL.MEMORY.COMMIT.V15")
    assert memory.source_repo == CANON_V15_REPO
    assert memory.source_commit == CANON_V15_COMMIT
    assert memory.source_blob_sha == "2930a7335f71f52d3cafdd9ded734c4aea4a2227"
    assert memory.provenance_class == "CANONICAL_V15"
    assert memory.side_effect == "WRITE"

    paradox = binding_by_id("CIEL.PARADOX.COHERENCE.LEGACY")
    assert paradox.source_repo == LEGACY_CIEL_REPO
    assert paradox.source_commit == LEGACY_CIEL_COMMIT
    assert paradox.source_blob_sha == "ba3d8d48a40306a50dc67835419c43e130adf705"
    assert paradox.provenance_class == "LEGACY_EXECUTABLE_SOURCE"


def test_native_binding_provenance_is_exact_and_current() -> None:
    recall = native_binding_by_id("PNV.MEMORY.HOLONOMIC_RECALL.NATIVE")
    assert recall.source_repo == PHASENAV_NATIVE_REPO
    assert recall.source_commit == PHASENAV_NATIVE_COMMIT
    assert recall.source_blob_sha == "24a2965c42ecedfd27555f055643c3e0c7671fda"
    assert recall.provenance_class == "PHASENAV_NATIVE_CURRENT"
    assert recall.execution_activation == "EXPLICIT_RUNTIME_DISPATCH"


def test_external_plan_remains_fail_closed() -> None:
    memory_plan = concept_execution_plan("090")
    assert memory_plan
    assert all(row.provenance_class == "CANONICAL_V15" for row in memory_plan)
    assert all(row.side_effect != "WRITE" for row in memory_plan)
    assert all(row.execution_activation == "EXPLICIT_RUNTIME_DISPATCH" for row in memory_plan)
    assert concept_execution_plan("119") == ()
    assert concept_execution_plan("119", include_legacy=True)


def test_unified_default_plan_prefers_current_and_v15_without_legacy_or_writes() -> None:
    plan = execution_plan_for_concept("090")
    assert plan
    provenance = {row.provenance_class for row in plan}
    assert "PHASENAV_NATIVE_CURRENT" in provenance
    assert "CANONICAL_V15" in provenance
    assert not any(row.legacy for row in plan)
    assert not any(row.write_capable for row in plan)
    ids = {row.algorithm_id for row in plan}
    assert "PNV.MEMORY.HOLONOMIC_RECALL.NATIVE" in ids
    assert "CIEL.MEMORY.RECONSTRUCT.V15" in ids
    assert "CIEL.MEMORY.COMMIT.V15" not in ids


def test_unified_paradox_plan_requires_legacy_opt_in() -> None:
    assert execution_plan_for_concept("119") == ()
    plan = execution_plan_for_concept("119", include_legacy=True)
    assert plan
    assert all(row.legacy for row in plan)


def test_unified_writes_require_explicit_opt_in() -> None:
    safe = {row.algorithm_id for row in execution_plan_for_concept("090")}
    writes = {row.algorithm_id for row in execution_plan_for_concept("090", include_writes=True)}
    assert "CIEL.MEMORY.COMMIT.V15" not in safe
    assert "CIEL.MEMORY.ADMISSION.V15" not in safe
    assert "CIEL.MEMORY.COMMIT.V15" in writes
    assert "CIEL.MEMORY.ADMISSION.V15" in writes


def test_concept_execution_summary_reports_policy() -> None:
    summary = concept_execution_summary("090")
    assert summary["concept_name"] == "Memory"
    assert summary["mapped_algorithm_count"] >= summary["default_plan_count"] > 0
    assert summary["write_binding_count"] >= 2
    assert summary["legacy_binding_count"] >= 1
    assert summary["default_policy"]["auto_execute"] is False


def test_family_queries_are_typed() -> None:
    memory = bindings_for_family("memory")
    temporal = bindings_for_family("temporal")
    paradox = bindings_for_family("paradox")
    extended_paradox = extended_legacy_bindings_for_family("paradox")
    assert memory and temporal and paradox and extended_paradox
    assert all(row.family == "memory" for row in memory)
    assert all(row.family == "temporal" for row in temporal)
    assert all(row.family == "paradox" for row in paradox)
    assert all(row.family == "paradox" for row in extended_paradox)


def test_extended_concept_query_is_priority_sorted() -> None:
    rows = extended_legacy_bindings_for_concept("119")
    keys = [(row.priority, row.binding_id) for row in rows]
    assert keys == sorted(keys)


def test_no_binding_auto_executes() -> None:
    assert all(
        row.execution_activation == "EXPLICIT_RUNTIME_DISPATCH"
        for row in (
            *ciel_executable_bindings(),
            *native_executable_bindings(),
            *extended_legacy_bindings(),
        )
    )


def test_receipts_are_deterministic_and_non_promoting() -> None:
    external_left = ciel_executable_map_receipt()
    external_right = ciel_executable_map_receipt()
    assert external_left["version"] == CIEL_EXECUTABLE_MAP_VERSION
    assert external_left["status"] == CIEL_EXECUTABLE_MAP_STATUS
    assert external_left["receipt_sha256"] == external_right["receipt_sha256"]
    assert external_left["policy"]["auto_execute_from_concept_match"] is False
    assert external_left["policy"]["scientific_promotion"] == "NOT_PERFORMED"

    native_left = native_executable_map_receipt()
    native_right = native_executable_map_receipt()
    assert native_left["receipt_sha256"] == native_right["receipt_sha256"]
    assert native_left["policy"]["auto_execute_from_concept_match"] is False
    assert native_left["policy"]["scientific_promotion"] == "NOT_PERFORMED"
