import math

from ciel_geometry.phasenav.saint_venant_linearized_einstein import (
    alpha_derivatives_from_second_plastic_distortion,
    conformal_quadratic_strain_second_derivatives,
    frobenius_norm3,
    incompatibility_from_second_strain_derivatives,
    kroner_incompatibility_from_second_plastic_distortion,
    linearized_einstein_from_second_strain_derivatives,
    subtract3,
    symmetric_second_derivatives_of_distortion,
    sym_curl_alpha_transpose_from_alpha_derivatives,
)


def _d2eps_control():
    # symmetric strain indices and symmetric second-derivative indices
    d=[[[[0.0]*3 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(i,3):
            for k in range(3):
                for l in range(k,3):
                    v=0.17*(i+1)*(j+2)+0.11*(k+1)*(l+1)+0.03*(i+j+k+l)
                    d[i][j][k][l]=v
                    d[j][i][k][l]=v
                    d[i][j][l][k]=v
                    d[j][i][l][k]=v
    return tuple(tuple(tuple(tuple(v for v in ls) for ls in ks) for ks in js) for js in d)


def _compatible_d2strain_from_cubic_displacement():
    # U[c][i][k][l] = d_i d_k d_l u_c; derivative indices symmetric.
    U=[[[[0.0]*3 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    for c in range(3):
        for i in range(3):
            for k in range(3):
                for l in range(3):
                    U[c][i][k][l]=(c+1)*0.13 + 0.07*(i+k+l) + 0.02*(i*k+i*l+k*l)
    d=[[[[0.0]*3 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    d[i][j][k][l]=0.5*(U[j][i][k][l]+U[i][j][k][l])
    return tuple(tuple(tuple(tuple(v for v in ls) for ls in ks) for ks in js) for js in d)


def _d2beta_control():
    d=[[[[0.0]*3 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(k,3):
                    v=0.19*(i+1)-0.07*(j+2)+0.05*(k+l)+0.03*k*l
                    d[i][j][k][l]=v
                    d[i][j][l][k]=v
    return tuple(tuple(tuple(tuple(v for v in ls) for ls in ks) for ks in js) for js in d)


def test_saint_venant_equals_linearized_einstein_exactly():
    d=_d2eps_control()
    inc=incompatibility_from_second_strain_derivatives(d)
    G=linearized_einstein_from_second_strain_derivatives(d)
    assert frobenius_norm3(subtract3(inc,G))<1e-13


def test_compatible_strain_has_zero_incompatibility():
    d=_compatible_d2strain_from_cubic_displacement()
    assert frobenius_norm3(incompatibility_from_second_strain_derivatives(d))<1e-13
    assert frobenius_norm3(linearized_einstein_from_second_strain_derivatives(d))<1e-13


def test_kroner_identity_for_arbitrary_plastic_distortion():
    d2beta=_d2beta_control()
    lhs=incompatibility_from_second_strain_derivatives(
        symmetric_second_derivatives_of_distortion(d2beta)
    )
    rhs=kroner_incompatibility_from_second_plastic_distortion(d2beta)
    assert frobenius_norm3(subtract3(lhs,rhs))<1e-13


def test_elastic_incompatibility_from_compatible_total_split():
    # total distortion is compatible; set its second derivatives to the
    # compatible cubic-displacement control encoded as strain plus arbitrary
    # skew-free choice. For incompatibility, inc(total strain)=0, so
    # eps_e = eps_total - sym beta_p gives inc(eps_e)=-inc(sym beta_p).
    d2total_strain=_compatible_d2strain_from_cubic_displacement()
    d2beta_p=_d2beta_control()
    d2sym_p=symmetric_second_derivatives_of_distortion(d2beta_p)
    d2eps_e=tuple(tuple(tuple(tuple(
        d2total_strain[i][j][k][l]-d2sym_p[i][j][k][l]
        for l in range(3))
        for k in range(3))
        for j in range(3))
        for i in range(3))
    lhs=incompatibility_from_second_strain_derivatives(d2eps_e)
    rhs=kroner_incompatibility_from_second_plastic_distortion(d2beta_p)
    neg_rhs=tuple(tuple(-rhs[i][j] for j in range(3)) for i in range(3))
    assert frobenius_norm3(subtract3(lhs,neg_rhs))<1e-13


def test_conformal_quadratic_reference_linearized_tensor():
    a=0.2
    d=conformal_quadratic_strain_second_derivatives(a)
    G=linearized_einstein_from_second_strain_derivatives(d)
    assert abs(G[0][0])<1e-14
    assert abs(G[1][1])<1e-14
    assert math.isclose(G[2][2],4*a,rel_tol=1e-14,abs_tol=1e-14)


def test_conformal_reference_matches_exact_spatial_einstein_at_origin():
    # Exact 3D spatial Einstein for h=diag(e^(2sigma),e^(2sigma),1)
    # has G_zz=4a e^(-2sigma), so at sigma(0)=0 it is exactly 4a.
    a=-0.3
    d=conformal_quadratic_strain_second_derivatives(a)
    G=linearized_einstein_from_second_strain_derivatives(d)
    assert math.isclose(G[2][2],4*a,rel_tol=1e-14,abs_tol=1e-14)
