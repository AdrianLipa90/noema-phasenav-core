from __future__ import annotations

import numpy as np
import pytest

from ciel_geometry.phasenav.canon.context_dynamics import PhaseVector36, TangentVector36
from ciel_geometry.phasenav.canon.operator_calculus import (
    HolonomyCache,
    LinearPhaseOperator,
    SemanticScheduler,
    compress_phase,
    decompress_phase,
    gauge_transform,
    project_forbidden_directions,
    semantic_crc,
    semantic_diff,
    semantic_merge,
    trajectory_curvature,
)
from ciel_geometry.phasenav.pnv_runtime import M_sentence_phase, TAU


def phase(text: str) -> PhaseVector36:
    return PhaseVector36(tuple(M_sentence_phase(text)))


def test_semantic_crc_and_diff_are_deterministic() -> None:
    left = phase("same")
    right = phase("different")
    assert semantic_crc(left) == semantic_crc(left)
    delta = semantic_diff(left, right)
    assert delta.angular_distance > 0.0
    assert delta.crc_left == semantic_crc(left)
    assert not delta.unchanged
    assert semantic_diff(left, left).unchanged


def test_interference_merge_preserves_identical_state() -> None:
    original = phase("merge state")
    result = semantic_merge((original, original), weights=(1.0, 3.0))
    assert result.vector.angular_distance(original) == pytest.approx(0.0)
    assert result.cancellation == pytest.approx(0.0)
    assert all(value == pytest.approx(1.0) for value in result.resultant_amplitude)


def test_phase_compression_round_trip_respects_error_bound() -> None:
    original = phase("compressed semantic state")
    compressed = compress_phase(original, bits=16)
    restored = decompress_phase(compressed)
    delta = semantic_diff(original, restored)
    assert delta.max_component <= compressed.maximum_error + 1.0e-12


def test_common_gauge_shift_preserves_angular_distance() -> None:
    left = phase("left")
    right = phase("right")
    before = left.angular_distance(right)
    after = gauge_transform(left, 0.75).angular_distance(
        gauge_transform(right, 0.75)
    )
    assert after == pytest.approx(before)


def test_trajectory_curvature_detects_turning() -> None:
    base = np.zeros(36)
    p0 = PhaseVector36(tuple(base))
    p1 = PhaseVector36(tuple((base + 0.1) % TAU))
    p2 = PhaseVector36(tuple((base + 0.2) % TAU))
    straight = trajectory_curvature((p0, p1, p2))

    turn = np.full(36, 0.2)
    turn[:18] = 0.0
    p2_turn = PhaseVector36(tuple(turn))
    curved = trajectory_curvature((p0, p1, p2_turn))

    assert straight == pytest.approx(0.0)
    assert curved > straight


def test_linear_operator_algebra_and_projection() -> None:
    identity = LinearPhaseOperator.identity()
    mask = np.eye(36)
    mask[0, 0] = 0.0
    projection = LinearPhaseOperator("P", mask)
    tangent = TangentVector36(tuple([1.0] + [0.5] * 35))

    assert identity.is_orthogonal()
    assert projection.is_projection()
    assert projection.apply(tangent).components[0] == pytest.approx(0.0)
    assert np.allclose(
        identity.commutator(projection).matrix,
        np.zeros((36, 36)),
    )


def test_forbidden_direction_projection_removes_component() -> None:
    tangent = TangentVector36(tuple([1.0, 2.0] + [0.0] * 34))
    normal = TangentVector36(tuple([1.0] + [0.0] * 35))
    result = project_forbidden_directions(tangent, (normal,))

    assert result.rank == 1
    assert result.allowed.components[0] == pytest.approx(0.0)
    assert result.allowed.components[1] == pytest.approx(2.0)
    assert result.removed_norm > 0.0


def test_holonomy_cache_is_path_specific() -> None:
    cache = HolonomyCache()
    start = phase("start")
    end = phase("end")
    result = phase("result")

    cache.put("transport", start, end, 0.25, result)
    hit = cache.get("transport", start, end, 0.25)
    miss = cache.get("transport", start, end, 0.50)

    assert hit is not None
    assert hit.result == result
    assert miss is None
    assert len(cache) == 1


def test_semantic_scheduler_minimizes_cost() -> None:
    scheduler = SemanticScheduler()
    scheduler.push(
        "later", phase("later"), potential=2.0, entropy=0.5, urgency=0.0
    )
    scheduler.push(
        "now", phase("now"), potential=1.0, entropy=0.2, urgency=0.5
    )

    assert scheduler.pop().state_id == "now"
    assert scheduler.pop().state_id == "later"
