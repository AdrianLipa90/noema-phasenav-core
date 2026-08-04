from __future__ import annotations

import json

import pytest

from ciel_geometry.phasenav.canon.context_dynamics import PhaseVector36
from ciel_geometry.phasenav.canon.observer_generation import (
    DynamicsConfig,
    GenerationPlan,
    HolonomicMemory,
    HTRIConfig,
    HTRIOscillatorField,
    Observation,
    ObserverState,
    ObserverToGenerationPipeline,
)
from ciel_geometry.phasenav.pnv_runtime import M_sentence_phase


def phase(text: str) -> PhaseVector36:
    return PhaseVector36(tuple(M_sentence_phase(text)))


def test_observation_is_deterministic_and_provenanced() -> None:
    first = Observation.from_text("observer sees a phase relation", source="test")
    second = Observation.from_text("observer sees a phase relation", source="test")

    assert first.phase == second.phase
    assert first.holonomy == pytest.approx(second.holonomy)
    assert first.provenance.digest_sha256 == second.provenance.digest_sha256
    assert len(first.trajectory) >= 1


def test_minimal_holonomic_memory_merges_nearby_observations() -> None:
    memory = HolonomicMemory()
    observation = Observation.from_text("stable memory basin", source="test")

    created = memory.ingest(observation, semantic_mass=1.0)
    merged = memory.ingest(observation, semantic_mass=2.0)
    recalls = memory.recall(observation.phase, top_k=1)

    assert created.cluster_id == merged.cluster_id
    assert merged.member_count == 2
    assert merged.semantic_mass == pytest.approx(3.0)
    assert len(memory.clusters) == 1
    assert recalls[0].cluster.cluster_id == created.cluster_id
    assert recalls[0].score > 0.0


def test_htri_field_vectorizes_cpu_and_logical_gpu_banks() -> None:
    field = HTRIOscillatorField(
        HTRIConfig(
            oscillators=12,
            cpu_fraction=0.5,
            steps=3,
            backend="cpu",
        )
    )
    state = field.evolve(
        phase("seed"),
        observer=phase("observer"),
        intention=phase("intention"),
        memory=phase("memory"),
        ai_phase=phase("ai"),
        mcp_phases=(phase("mcp one"), phase("mcp two")),
    )

    assert len(state.cpu_phases) == 6
    assert len(state.gpu_phases) == 6
    assert len(state.phase36.components) == 36
    assert 0.0 <= state.cpu_order <= 1.0
    assert 0.0 <= state.gpu_order <= 1.0
    assert 0.0 <= state.global_order <= 1.0
    assert state.backend == "cpu-numpy"
    assert state.gpu_emulated is False


def test_pipeline_stops_at_generation_plan_for_cielingo() -> None:
    pipeline = ObserverToGenerationPipeline(
        htri=HTRIOscillatorField(
            HTRIConfig(oscillators=12, steps=2, backend="cpu")
        ),
        dynamics=DynamicsConfig(steps=3, dt=0.1),
    )
    observer = ObserverState(
        observer_id="observer:test",
        phase=phase("initial observer"),
    )
    result = pipeline.run(
        observer,
        "meaning becomes language",
        intention_text="form a coherent generative state",
        ai_induction="AI proposal",
        mcp_inductions=("memory tool", "compiler tool"),
    )

    assert isinstance(result.plan, GenerationPlan)
    assert result.observer.sequence == 1
    assert len(result.plan.content_phase.components) == 36
    assert len(result.plan.trajectory) == 4
    assert result.dynamics.steps[-1].hamiltonian >= 0.0
    assert result.dynamics.steps[-1].lagrangian == pytest.approx(
        result.dynamics.steps[-1].kinetic_energy
        - result.dynamics.steps[-1].potential
    )
    assert len(result.plan.receipt_sha256) == 64
    assert not hasattr(result.plan, "text")

    payload = result.plan.to_cielingo_payload()
    assert payload["schema"] == "phasenav.generation-plan/v1"
    assert "content_phase" in payload
    assert "receipt_sha256" in payload
    assert "text" not in payload
    json.dumps(payload)


def test_pipeline_receipt_is_deterministic_for_equal_initial_state() -> None:
    observer = ObserverState(
        observer_id="observer:determinism",
        phase=phase("deterministic observer"),
    )

    def run_once() -> str:
        pipeline = ObserverToGenerationPipeline(
            htri=HTRIOscillatorField(
                HTRIConfig(oscillators=10, steps=2, backend="cpu")
            ),
            dynamics=DynamicsConfig(steps=2, dt=0.1),
        )
        return pipeline.run(
            observer,
            "same observation",
            intention_text="same intention",
            ai_induction="same AI state",
            mcp_inductions=("same MCP state",),
        ).plan.receipt_sha256

    assert run_once() == run_once()


def test_ai_and_mcp_induction_change_the_oscillator_projection() -> None:
    field = HTRIOscillatorField(
        HTRIConfig(oscillators=18, steps=4, backend="cpu")
    )
    common = {
        "seed": phase("seed"),
        "observer": phase("observer"),
        "intention": phase("intention"),
    }
    baseline = field.evolve(**common)
    induced = field.evolve(
        **common,
        ai_phase=phase("external AI induction"),
        mcp_phases=(phase("MCP induced state"),),
    )

    assert baseline.phase36.angular_distance(induced.phase36) > 0.0


def test_htri_base_frequency_parameter_changes_evolution() -> None:
    common = {
        "seed": phase("seed"),
        "observer": phase("observer"),
        "intention": phase("intention"),
    }
    low = HTRIOscillatorField(
        HTRIConfig(
            oscillators=12,
            steps=3,
            backend="cpu",
            base_frequency_hz=7.83,
        )
    ).evolve(**common)
    high = HTRIOscillatorField(
        HTRIConfig(
            oscillators=12,
            steps=3,
            backend="cpu",
            base_frequency_hz=15.66,
        )
    ).evolve(**common)

    assert low.phase36.angular_distance(high.phase36) > 0.0
