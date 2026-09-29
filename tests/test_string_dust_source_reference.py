import math

from ciel_geometry.phasenav.einstein_geometric_reference import EinsteinConformalReference
from ciel_geometry.phasenav.string_dust_source_reference import (
    dominant_energy_condition_holds,
    matched_proper_energy_per_coordinate_area,
    mixed_covariant_divergence_reference,
    proper_energy_per_coordinate_area,
    required_density_for_reference,
    source_equation_residual,
    weak_energy_condition_holds,
)


def _norm(v):
    return math.sqrt(sum(x*x for x in v))


def test_required_string_density_matches_reference_exactly():
    ref=EinsteinConformalReference(-0.2)
    kappa=2.3
    for x,y in ((0.0,0.0),(0.3,-0.4),(0.8,0.2)):
        rho=required_density_for_reference(ref,x,y,coupling=kappa)
        assert rho>0.0
        assert source_equation_residual(ref,x,y,rho,coupling=kappa)<1e-13


def test_positive_energy_requires_negative_a_for_positive_coupling():
    kappa=1.7
    assert required_density_for_reference(EinsteinConformalReference(-0.2),0.2,0.1,coupling=kappa)>0.0
    assert required_density_for_reference(EinsteinConformalReference(0.2),0.2,0.1,coupling=kappa)<0.0


def test_string_dust_energy_conditions_for_positive_density():
    assert weak_energy_condition_holds(1.0)
    assert dominant_energy_condition_holds(1.0)
    assert not weak_energy_condition_holds(-1.0)
    assert not dominant_energy_condition_holds(-1.0)


def test_transversely_varying_static_density_is_covariantly_conserved():
    ref=EinsteinConformalReference(-0.2)
    rho=required_density_for_reference(ref,0.3,-0.4,coupling=2.0)
    assert _norm(mixed_covariant_divergence_reference(ref,0.3,-0.4,rho))==0.0


def test_time_or_z_dependence_breaks_source_free_conservation():
    ref=EinsteinConformalReference(-0.2)
    div=mixed_covariant_divergence_reference(ref,0.3,-0.4,1.0,rho_t=0.2,rho_z=-0.1)
    assert math.isclose(div[0],-0.2)
    assert math.isclose(div[3],0.1)


def test_matched_proper_areal_energy_is_constant_and_nonzero():
    ref=EinsteinConformalReference(-0.2)
    kappa=2.0
    target=matched_proper_energy_per_coordinate_area(ref,coupling=kappa)
    assert target>0.0
    for x,y in ((0,0),(0.3,-0.4),(1.0,0.5)):
        rho=required_density_for_reference(ref,x,y,coupling=kappa)
        assert math.isclose(
            proper_energy_per_coordinate_area(ref,x,y,rho),
            target,
            rel_tol=1e-13,
        )


def test_matched_source_is_not_localized_on_infinite_plane():
    ref=EinsteinConformalReference(-0.2)
    kappa=2.0
    density=matched_proper_energy_per_coordinate_area(ref,coupling=kappa)
    # Proper energy inside coordinate square [-L,L]^2 grows as 4 L^2*density.
    e1=4.0*1.0**2*density
    e2=4.0*2.0**2*density
    assert math.isclose(e2/e1,4.0)
