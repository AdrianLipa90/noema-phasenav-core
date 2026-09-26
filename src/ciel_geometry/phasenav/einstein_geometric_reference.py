"""Einstein-tensor geometry reference on the validated conformal Cartan coframe.

This module constructs only geometric tensors from the declared metric. It does
not impose a source equation G_{mu nu}=kappa T_{mu nu}.
"""
from __future__ import annotations

import math

from .cartan_conformal_reference import QuadraticConformalCoframe
from .gl4_coframe_bivector36 import frobenius_norm, sub


class EinsteinReferenceError(ValueError):
    pass


def _diag4(a,b,c,d):
    return (
        (float(a),0.0,0.0,0.0),
        (0.0,float(b),0.0,0.0),
        (0.0,0.0,float(c),0.0),
        (0.0,0.0,0.0,float(d)),
    )


class EinsteinConformalReference(QuadraticConformalCoframe):
    """Einstein geometry for g=diag(-1,e^(2sigma),e^(2sigma),1)."""

    def ricci_cov4(self,x:float,y:float):
        lap=self.laplacian_sigma(x,y)
        return _diag4(0.0,-lap,-lap,0.0)

    def inverse_metric4(self,x:float,y:float):
        e=math.exp(-2.0*self.sigma(x,y))
        return _diag4(-1.0,e,e,1.0)

    def einstein_cov4(self,x:float,y:float):
        g=self.metric4(x,y)
        ric=self.ricci_cov4(x,y)
        r=self.scalar_curvature4(x,y)
        return tuple(tuple(
            ric[i][j]-0.5*g[i][j]*r
            for j in range(4)
        ) for i in range(4))

    def einstein_mixed4(self,x:float,y:float):
        gi=self.inverse_metric4(x,y)
        gc=self.einstein_cov4(x,y)
        return tuple(tuple(
            sum(gi[i][k]*gc[k][j] for k in range(4))
            for j in range(4)
        ) for i in range(4))

    def christoffel4(self,x:float,y:float):
        sx=self.sigma_x(x,y)
        sy=self.sigma_y(x,y)
        # Gamma^rho_{mu nu}
        G=[[[0.0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
        G[1][1][1]=sx
        G[1][1][2]=sy
        G[1][2][1]=sy
        G[1][2][2]=-sx
        G[2][1][1]=-sy
        G[2][1][2]=sx
        G[2][2][1]=sx
        G[2][2][2]=sy
        return tuple(tuple(tuple(G[r][m][n] for n in range(4)) for m in range(4)) for r in range(4))

    def _q(self,x:float,y:float)->float:
        return math.exp(-2.0*self.sigma(x,y))*self.laplacian_sigma(x,y)

    def _partial_einstein_mixed(self,coord:int,rho:int,nu:int,x:float,y:float)->float:
        # G^mu_nu = diag(q,0,0,q) for this reference.
        if rho!=nu or rho not in (0,3):
            return 0.0
        q=self._q(x,y)
        if coord==1:
            return -2.0*self.sigma_x(x,y)*q
        if coord==2:
            return -2.0*self.sigma_y(x,y)*q
        return 0.0

    def contracted_bianchi_mixed(self,x:float,y:float):
        """Return nabla_mu G^mu_nu for nu=0..3."""
        G=self.einstein_mixed4(x,y)
        Gamma=self.christoffel4(x,y)
        out=[]
        for nu in range(4):
            val=0.0
            for mu in range(4):
                val+=self._partial_einstein_mixed(mu,mu,nu,x,y)
                for lam in range(4):
                    val+=Gamma[mu][mu][lam]*G[lam][nu]
                    val-=Gamma[lam][mu][nu]*G[mu][lam]
            out.append(val)
        return tuple(out)

    def einstein_trace_mixed(self,x:float,y:float)->float:
        G=self.einstein_mixed4(x,y)
        return sum(G[i][i] for i in range(4))

    def symmetry_residual(self,x:float,y:float)->float:
        G=self.einstein_cov4(x,y)
        GT=tuple(tuple(G[j][i] for j in range(4)) for i in range(4))
        return frobenius_norm(sub(G,GT))
