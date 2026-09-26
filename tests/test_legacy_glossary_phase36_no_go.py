import math

from ciel_geometry.phasenav.legacy_glossary_phase36_no_go import (
    common_shift_spread,
    forced_row_major_so2_projection,
    recovered_legacy_glossary_phase36,
    relative_phase36,
)


Q = (3,5,7,11,13,17)


def test_legacy_q_dependence_is_uniform_phase_shift():
    for i,q1 in enumerate(Q):
        for q2 in Q[i+1:]:
            assert common_shift_spread(q1,q2) < 1e-12


def test_same_q_mod_5_collapses_to_same_vector():
    assert recovered_legacy_glossary_phase36(3) == recovered_legacy_glossary_phase36(13)
    assert recovered_legacy_glossary_phase36(7) == recovered_legacy_glossary_phase36(17)


def test_nontrivial_legacy_shift_is_not_xy_so2_generator():
    theta_hat,residual = forced_row_major_so2_projection(3,5)
    assert abs(theta_hat) < 1e-14
    assert residual > 1.0


def test_all_nonzero_legacy_shifts_project_zero_on_j36():
    for i,q1 in enumerate(Q):
        for q2 in Q[i+1:]:
            delta=relative_phase36(q1,q2)
            if max(abs(x) for x in delta) < 1e-14:
                continue
            theta_hat,residual=forced_row_major_so2_projection(q1,q2)
            assert abs(theta_hat) < 1e-13
            assert residual > 1e-6
