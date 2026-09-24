import unittest
from ciel_geometry.phasenav.bivector36 import (
    BivectorField36, exterior_square, euclidean_half_projectors, _matmul
)

class Bivector36Tests(unittest.TestCase):
    def test_roundtrip(self):
        x=tuple(float(i) for i in range(36))
        self.assertEqual(BivectorField36.from_flat36(x).to_flat36(),x)

    def test_exact_compound_passes_gate(self):
        e=((1,2,0,1),(0,1,1,0),(1,0,2,1),(0,1,0,1))
        b=BivectorField36(exterior_square(e))
        lam,res=b.wedge_conformal_residual()
        self.assertGreater(abs(lam),0)
        self.assertLess(res,1e-12)
        self.assertTrue(b.passes_necessary_lift_gate())

    def test_perturbation_fails_gate(self):
        e=((1,2,0,1),(0,1,1,0),(1,0,2,1),(0,1,0,1))
        m=[list(r) for r in exterior_square(e)]
        m[0][0]+=0.125
        self.assertFalse(BivectorField36(tuple(tuple(r) for r in m)).passes_necessary_lift_gate())

    def test_half_projectors(self):
        pp,pm=euclidean_half_projectors()
        p2=_matmul(pp,pp)
        m2=_matmul(pm,pm)
        cross=_matmul(pp,pm)
        self.assertLess(max(abs(p2[i][j]-pp[i][j]) for i in range(6) for j in range(6)),1e-12)
        self.assertLess(max(abs(m2[i][j]-pm[i][j]) for i in range(6) for j in range(6)),1e-12)
        self.assertLess(max(abs(cross[i][j]) for i in range(6) for j in range(6)),1e-12)
        self.assertAlmostEqual(sum(pp[i][i] for i in range(6)),3.0,places=12)
        self.assertAlmostEqual(sum(pm[i][i] for i in range(6)),3.0,places=12)

if __name__=='__main__':
    unittest.main()
