from __future__ import annotations

import cmath
import math

import pytest

from ciel_geometry.phasenav.canon.context_dynamics import PhaseVector36
from ciel_geometry.phasenav.canon.semantic_holonomy import (
    SemanticHolonomyReceipt,
    phase_overlap,
    semantic_holonomy_coupling,
    u1_semantic_holonomy_phase,
    u1_semantic_transport,
)


def state(offset: float) -> PhaseVector36:
    return PhaseVector36(tuple(offset + 0.01 * i for i in range(36)))


def test_u1_transport_composes_and_reverses() -> None:
    a=(0.2,-0.35)
    b=(0.8,0.1)
    wa=u1_semantic_transport(a)
    wb=u1_semantic_transport(b)
    assert u1_semantic_transport(a+b) == pytest.approx(wa*wb)
    assert u1_semantic_transport(tuple(-x for x in reversed(a))) == pytest.approx(wa.conjugate())
    assert abs(wa) == pytest.approx(1.0)


def test_open_path_gauge_covariance_and_closed_loop_invariance() -> None:
    edges=(0.25,-0.40,0.75)
    chi_open=(0.10,0.55,-0.20,0.35)
    shifted_open=tuple(edges[k]+chi_open[k+1]-chi_open[k] for k in range(3))
    expected=cmath.exp(1j*(chi_open[-1]-chi_open[0]))*u1_semantic_transport(edges)
    assert u1_semantic_transport(shifted_open) == pytest.approx(expected)

    chi_loop=(0.10,0.55,-0.20)
    shifted_loop=tuple(
        edges[k]+chi_loop[(k+1)%3]-chi_loop[k] for k in range(3)
    )
    assert u1_semantic_transport(shifted_loop) == pytest.approx(u1_semantic_transport(edges))


def test_semantic_coupling_is_nonlocal_phase_transport_of_overlap() -> None:
    left=state(0.1)
    right=state(0.7)
    edges=(0.17,0.29,-0.08)
    z=phase_overlap(left,right)
    c=semantic_holonomy_coupling(left,right,edges)
    assert abs(c) == pytest.approx(abs(z))
    assert c == pytest.approx(u1_semantic_transport(edges)*z)
    assert u1_semantic_holonomy_phase(edges) == pytest.approx(cmath.phase(u1_semantic_transport(edges)))


def test_receipt_is_read_only_candidate_state() -> None:
    receipt=SemanticHolonomyReceipt.build("path:a->b",state(0.2),state(0.4),(0.1,0.2))
    assert receipt.epistemic == "CHYBA"
    assert receipt.canon_allowed is False
    assert receipt.strength == pytest.approx(abs(receipt.coupling))


def test_nonfinite_connection_fails_closed() -> None:
    with pytest.raises(ValueError):
        u1_semantic_transport((0.1,math.inf))
