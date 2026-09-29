import math
import pytest

from ciel_geometry.phasenav.einstein_geometric_reference import EinsteinConformalReference
from ciel_geometry.phasenav.einstein_source_admission import (
    SourceAdmissionError,
    best_fit_vacuum_lambda,
    covariant_divergence_mixed,
    einstein_equation_residual,
    geometric_placeholder_source_cov,
    tensor_symmetry_residual,
    vacuum_lambda_residual,
)


def _norm(v):
    return math.sqrt(sum(x*x for x in v))


def test_flat_reference_admits_vacuum_lambda_zero():
    ref=EinsteinConformalReference(0.0)
    assert vacuum_lambda_residual(ref,0.2,-0.3,0.0)==0.0


def test_nonflat_reference_has_no_constant_lambda_vacuum_at_point():
    ref=EinsteinConformalReference(0.2)
    lam,res=best_fit_vacuum_lambda(ref,0.3,-0.4)
    assert res>1e-3
    assert vacuum_lambda_residual(ref,0.3,-0.4,0.0)>1e-3


def test_algebraic_placeholder_closes_equation_but_is_not_source_evidence():
    ref=EinsteinConformalReference(0.2)
    T=geometric_placeholder_source_cov(ref,0.3,-0.4,coupling=2.0,cosmological_constant=0.1)
    assert einstein_equation_residual(
        ref,0.3,-0.4,T,coupling=2.0,cosmological_constant=0.1
    )<1e-14


def test_nonsymmetric_source_fails_closed():
    ref=EinsteinConformalReference(0.2)
    T=((0,1,0,0),(0,0,0,0),(0,0,0,0),(0,0,0,0))
    assert tensor_symmetry_residual(T)>0.0
    with pytest.raises(SourceAdmissionError,match="symmetric"):
        einstein_equation_residual(ref,0.0,0.0,T,coupling=1.0)


def test_geometric_placeholder_is_covariantly_conserved_for_lambda_zero():
    ref=EinsteinConformalReference(0.2)
    x,y=0.3,-0.4
    # Mixed T=G/kappa with kappa=2.
    G=ref.einstein_mixed4(x,y)
    T=tuple(tuple(0.5*G[i][j] for j in range(4)) for i in range(4))
    partials=[]
    for c in range(4):
        block=[]
        for rho in range(4):
            row=[]
            for nu in range(4):
                row.append(0.5*ref._partial_einstein_mixed(c,rho,nu,x,y))
            block.append(tuple(row))
        partials.append(tuple(block))
    assert _norm(covariant_divergence_mixed(ref,x,y,T,tuple(partials)))<1e-13


def test_bad_source_conservation_is_detected():
    ref=EinsteinConformalReference(0.0)
    x,y=0.3,-0.4
    T=((0.0,0.0,0.0,0.0),(0.0,x,0.0,0.0),(0.0,0.0,0.0,0.0),(0.0,0.0,0.0,0.0))
    partials=[[[0.0]*4 for _ in range(4)] for _ in range(4)]
    partials[1][1][1]=1.0
    div=covariant_divergence_mixed(ref,x,y,T,partials)
    assert abs(div[1]-1.0)<1e-14
