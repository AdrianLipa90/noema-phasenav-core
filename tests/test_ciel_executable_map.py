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


def _binding_ids(card: dict) -> set[str]:
    return {str(row["concept_algorithm_id"]) for row in card["algorithm_bindings"]}


def test_new_semantic_nodes_exist_as_candidates() -> None:
    paradox = card_by_id("119")
    causality = card_by_id("120")
    assert paradox["canonical_name"] == "Paradox"
    assert causality["canonical_name"] == "Causality"
    assert paradox["epistemic"]["canon_allowed"] is False
    assert causality["epistemic"]["canon_allowed"] is False


def test_memory_card_carries_canonical_v15_execution_sources() -> None:
    ids = _binding_ids(card_by_id("090"))
    assert "CIEL.MEMORY.RECONSTRUCT.V15" in ids
    assert "CIEL.MEMORY.READ_PACKET.V15" in ids
    assert "CIEL.MEMORY.COMMIT.V15" in ids
    assert "CIEL.MEMORY.ADMISSION.V15" in ids
    assert "CIEL.MEMORY.RECEIPT_CHAIN.V15" in ids


def test_time_card_carries_temporal_execution_sources() -> None:
    ids = _binding_ids(card_by_id("018"))
    assert "CIEL.TIME.FIELD_INIT.LEGACY" in ids
    assert "CIEL.TIME.FIELD_EVOLVE.LEGACY" in ids
    assert "CIEL.TIME.EVOLUTION_STEP.LEGACY" in ids
    assert "CIEL.TIME.ZENO.LEGACY" in ids
    assert "CIEL.TIME.CAUSAL_LOOP.LEGACY" in ids
    assert "CIEL.TIME.ENTROPY_DECAY.LEGACY" in ids


def test_paradox_and_causality_cards_collect_their_families() -> None:
    paradox_ids = _binding_ids(card_by_id("119"))
    causality_ids = _binding_ids(card_by_id("120"))
    assert "CIEL.PARADOX.NETWORK.LEGACY" in paradox_ids
    assert "CIEL.PARADOX.LIAR_GODEL_RUSSELL.LEGACY" in paradox_ids
    assert "CIEL.PARADOX.THESEUS.LEGACY" in paradox_ids
    assert "CIEL.TIME.CAUSAL_LOOP.LEGACY" in causality_ids
    assert "CIEL.TIME.BOOTSTRAP_LOOP.LEGACY" in causality_ids
    assert "CIEL.TIME.GRANDFATHER_GUARD.LEGACY" in causality_ids
    assert "CIEL.TIME.PREDESTINATION.LEGACY" in causality_ids


def test_existing_reciprocal_concept_algorithms_survive_v013() -> None:
    assert "RECIPROCAL_INVERSION" in _binding_ids(card_by_id("116"))
    assert "RIEMANN_ZETA_ZERO" in _binding_ids(card_by_id("117"))
    assert "HEISENBERG_UNCERTAINTY" in _binding_ids(card_by_id("118"))


def test_every_binding_points_to_an_existing_concept_card() -> None:
    card_ids = {card["glossary_id"] for card in load_canonical_cards()}
    for binding in ciel_executable_bindings():
        assert set(binding.concept_ids) <= card_ids


def test_binding_provenance_is_exact_and_typed() -> None:
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


def test_default_execution_plan_is_fail_closed() -> None:
    memory_plan = concept_execution_plan("090")
    assert memory_plan
    assert all(row.provenance_class == "CANONICAL_V15" for row in memory_plan)
    assert all(row.side_effect != "WRITE" for row in memory_plan)
    assert all(row.execution_activation == "EXPLICIT_RUNTIME_DISPATCH" for row in memory_plan)

    # Paradox sources are legacy and therefore require explicit opt-in.
    assert concept_execution_plan("119") == ()
    assert concept_execution_plan("119", include_legacy=True)


def test_writes_require_explicit_plan_opt_in() -> None:
    safe = {row.binding_id for row in concept_execution_plan("090")}
    writes = {
        row.binding_id
        for row in concept_execution_plan("090", include_writes=True)
    }
    assert "CIEL.MEMORY.COMMIT.V15" not in safe
    assert "CIEL.MEMORY.ADMISSION.V15" not in safe
    assert "CIEL.MEMORY.COMMIT.V15" in writes
    assert "CIEL.MEMORY.ADMISSION.V15" in writes


def test_family_queries_are_typed() -> None:
    memory = bindings_for_family("memory")
    temporal = bindings_for_family("temporal")
    paradox = bindings_for_family("paradox")
    assert memory and temporal and paradox
    assert all(row.family == "memory" for row in memory)
    assert all(row.family == "temporal" for row in temporal)
    assert all(row.family == "paradox" for row in paradox)


def test_concept_query_is_priority_sorted() -> None:
    rows = bindings_for_concept("090")
    keys = [(row.priority, row.binding_id) for row in rows]
    assert keys == sorted(keys)


def test_no_binding_auto_executes() -> None:
    assert all(
        row.execution_activation == "EXPLICIT_RUNTIME_DISPATCH"
        for row in ciel_executable_bindings()
    )


def test_receipt_is_deterministic_and_non_promoting() -> None:
    left = ciel_executable_map_receipt()
    right = ciel_executable_map_receipt()
    assert left["version"] == CIEL_EXECUTABLE_MAP_VERSION
    assert left["status"] == CIEL_EXECUTABLE_MAP_STATUS
    assert left["receipt_sha256"] == right["receipt_sha256"]
    assert left["policy"]["auto_execute_from_concept_match"] is False
    assert left["policy"]["scientific_promotion"] == "NOT_PERFORMED"
