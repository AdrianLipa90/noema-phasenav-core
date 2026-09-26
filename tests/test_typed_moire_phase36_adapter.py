import math
import pytest

from ciel_geometry.phasenav.typed_moire_phase36_adapter import (
    GENERIC_T36_BASIS_ID,
    MOIRE_PHASE_MATRIX6_BASIS_ID,
    Phase36AdapterError,
    Phase36Record,
    adapt_typed_phase36_to_bivector36_so2,
    encode_homobilayer_period_phase36,
    encode_so2_log_phase36,
    physical_moire_period,
)


def _generic_zero():
    return Phase36Record(
        angles=(0.0,) * 36,
        basis_id=GENERIC_T36_BASIS_ID,
        derivation_id="legacy",
        source_id="legacy-zero",
    )


def test_generic_legacy_basis_fails_closed():
    generic = _generic_zero()
    typed = encode_so2_log_phase36(0.1, source_id="typed")
    with pytest.raises(Phase36AdapterError, match="unassigned axis semantics"):
        adapt_typed_phase36_to_bivector36_so2(generic, typed)


def test_exact_typed_roundtrip():
    reference = encode_so2_log_phase36(0.0, source_id="ref")
    target = encode_so2_log_phase36(math.radians(3.5), source_id="target")
    binding = adapt_typed_phase36_to_bivector36_so2(reference, target)
    assert binding.admitted
    assert math.isclose(binding.theta_radians, math.radians(3.5), rel_tol=1e-13)
    assert binding.generator_fit_abs < 1e-13


def test_relative_pair_recovers_difference():
    a = math.radians(1.1)
    b = math.radians(4.2)
    left = encode_so2_log_phase36(a, source_id="a")
    right = encode_so2_log_phase36(b, source_id="b")
    binding = adapt_typed_phase36_to_bivector36_so2(left, right)
    assert math.isclose(binding.theta_radians, b-a, rel_tol=1e-13, abs_tol=1e-13)


def test_layer_swap_changes_angle_sign_preserves_residual():
    ref = encode_so2_log_phase36(0.0, source_id="ref")
    target = encode_so2_log_phase36(0.4, source_id="target")
    ab = adapt_typed_phase36_to_bivector36_so2(ref, target)
    ba = adapt_typed_phase36_to_bivector36_so2(target, ref)
    assert math.isclose(ab.theta_radians, -ba.theta_radians, rel_tol=1e-13)
    assert math.isclose(ab.calibrated_residual, ba.calibrated_residual, rel_tol=1e-13)


def test_off_axis_phase_component_fails_closed():
    ref = encode_so2_log_phase36(0.0, source_id="ref")
    target = encode_so2_log_phase36(0.2, source_id="target")
    bad = list(target.angles)
    bad[2] = (bad[2] + 0.01) % (2.0 * math.pi)
    corrupted = Phase36Record(
        angles=tuple(bad),
        basis_id=MOIRE_PHASE_MATRIX6_BASIS_ID,
        derivation_id=target.derivation_id,
        source_id="corrupt",
    )
    with pytest.raises(Phase36AdapterError, match=r"off the calibrated SO\(2\) generator axis"):
        adapt_typed_phase36_to_bivector36_so2(ref, corrupted)


def test_branch_cut_rejected():
    with pytest.raises(Phase36AdapterError, match="branch cut"):
        encode_so2_log_phase36(math.pi, source_id="pi")


def test_graphene_magic_angle_period():
    ref = encode_so2_log_phase36(0.0, source_id="ref")
    target = encode_so2_log_phase36(math.radians(1.12), source_id="target")
    binding = adapt_typed_phase36_to_bivector36_so2(ref, target)
    L = physical_moire_period(binding, 0.246)
    assert abs(L - 12.6) < 0.05


def test_measured_period_forward_binding():
    ref = encode_so2_log_phase36(0.0, source_id="ref")
    target = encode_homobilayer_period_phase36(
        0.246,
        12.6,
        source_id="stm:tilak-2021:12.6nm",
    )
    binding = adapt_typed_phase36_to_bivector36_so2(ref, target)
    assert abs(math.degrees(binding.theta_radians) - 1.12) < 0.01
    assert abs(physical_moire_period(binding, 0.246) - 12.6) < 1e-10


def test_invalid_period_geometry_fails_closed():
    with pytest.raises(Phase36AdapterError, match="too small"):
        encode_homobilayer_period_phase36(1.0, 0.1, source_id="impossible")


def test_record_validation():
    with pytest.raises(Phase36AdapterError):
        Phase36Record(
            angles=(0.0,) * 35,
            basis_id=MOIRE_PHASE_MATRIX6_BASIS_ID,
            derivation_id="x",
            source_id="bad",
        )
