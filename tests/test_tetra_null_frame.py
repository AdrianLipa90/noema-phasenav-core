import unittest
from ciel_geometry.phasenav.tetra_null_frame import (
    E_PLUS, PARITY, canonical_plus_frame4, canonical_minus_frame4,
    canonical_bivector_frames, canonical_bivector_parity,
    canonical_antipodal_overlay, relative_bivector_operator,
)

class TetraNullFrameTests(unittest.TestCase):
    def test_canonical_frames(self):
        self.assertEqual(canonical_plus_frame4(),E_PLUS)
        self.assertEqual(canonical_minus_frame4()[0],E_PLUS[0])

    def test_relative_operator_is_bivector_parity(self):
        rel=relative_bivector_operator(canonical_plus_frame4(),canonical_minus_frame4())
        par=canonical_bivector_parity()
        for a,b in zip(rel.matrix6,par.matrix6):
            for x,y in zip(a,b): self.assertAlmostEqual(x,y,places=12)
        self.assertEqual(tuple(round(par.matrix6[i][i]) for i in range(6)),(-1,-1,-1,1,1,1))

    def test_bminus_equals_parity_bplus(self):
        plus,minus=canonical_bivector_frames()
        par=canonical_bivector_parity().matrix6
        calc=tuple(tuple(sum(par[i][k]*plus.matrix6[k][j] for k in range(6)) for j in range(6)) for i in range(6))
        for a,b in zip(calc,minus.matrix6):
            for x,y in zip(a,b): self.assertAlmostEqual(x,y,places=12)

    def test_overlay_cancels_three_channels_each(self):
        ov=canonical_antipodal_overlay()
        # parity basis: half-sum has zero first three rows, half-difference zero last three rows
        self.assertLess(max(abs(x) for row in ov.half_sum.matrix6[:3] for x in row),1e-12)
        self.assertLess(max(abs(x) for row in ov.half_difference.matrix6[3:] for x in row),1e-12)
        self.assertFalse(ov.legacy_phase36_required)
        self.assertFalse(ov.physical_gravity_claim)

    def test_generic_gl4_deformation_stays_exterior_square(self):
        A=((2.0,.2,0,0),(0,1.5,.1,0),(.05,0,1.3,.07),(0,.03,0,1.25))
        E=canonical_plus_frame4()
        E2=tuple(tuple(sum(A[i][k]*E[k][j] for k in range(4)) for j in range(4)) for i in range(4))
        rel=relative_bivector_operator(E,E2)
        from ciel_geometry.phasenav.bivector36 import exterior_square
        target=exterior_square(A)
        for a,b in zip(rel.matrix6,target):
            for x,y in zip(a,b): self.assertAlmostEqual(x,y,places=11)

if __name__=="__main__": unittest.main()
