import math
import unittest

from ciel_geometry.phasenav.tetra_null_frame import (
    E_PLUS,
    ETA,
    PARITY,
    canonical_plus_frame4,
    canonical_minus_frame4,
    canonical_bivector_frames,
    canonical_bivector_parity,
    canonical_antipodal_overlay,
    canonical_antipodal_split4,
    exterior_square4,
    frame_columns,
    generic_frame_pair,
    minkowski_inner,
    relative_bivector_operator,
    stella_parity_receipt,
    tetra_null_frame,
)


class TetraNullFrameTypedCarrierTests(unittest.TestCase):
    def test_canonical_frames(self):
        self.assertEqual(canonical_plus_frame4(),E_PLUS)
        self.assertEqual(canonical_minus_frame4()[0],E_PLUS[0])

    def test_relative_operator_is_bivector_parity(self):
        rel=relative_bivector_operator(canonical_plus_frame4(),canonical_minus_frame4())
        par=canonical_bivector_parity()
        for a,b in zip(rel.matrix6,par.matrix6):
            for x,y in zip(a,b):
                self.assertAlmostEqual(x,y,places=12)
        self.assertEqual(
            tuple(round(par.matrix6[i][i]) for i in range(6)),
            (-1,-1,-1,1,1,1),
        )

    def test_bminus_equals_parity_bplus(self):
        plus,minus=canonical_bivector_frames()
        par=canonical_bivector_parity().matrix6
        calc=tuple(
            tuple(
                sum(par[i][k]*plus.matrix6[k][j] for k in range(6))
                for j in range(6)
            )
            for i in range(6)
        )
        for a,b in zip(calc,minus.matrix6):
            for x,y in zip(a,b):
                self.assertAlmostEqual(x,y,places=12)

    def test_overlay_cancels_three_channels_each(self):
        ov=canonical_antipodal_overlay()
        self.assertLess(
            max(abs(x) for row in ov.half_sum.matrix6[:3] for x in row),
            1e-12,
        )
        self.assertLess(
            max(abs(x) for row in ov.half_difference.matrix6[3:] for x in row),
            1e-12,
        )
        self.assertFalse(ov.legacy_phase36_required)
        self.assertFalse(ov.physical_gravity_claim)

    def test_generic_gl4_deformation_stays_exterior_square(self):
        A=((2.0,.2,0,0),(0,1.5,.1,0),(.05,0,1.3,.07),(0,.03,0,1.25))
        E=canonical_plus_frame4()
        E2=tuple(
            tuple(sum(A[i][k]*E[k][j] for k in range(4)) for j in range(4))
            for i in range(4)
        )
        rel=relative_bivector_operator(E,E2)
        from ciel_geometry.phasenav.bivector36 import exterior_square
        target=exterior_square(A)
        for a,b in zip(rel.matrix6,target):
            for x,y in zip(a,b):
                self.assertAlmostEqual(x,y,places=11)

    def test_common_is_rank_one_shape(self):
        s=canonical_antipodal_split4()
        self.assertTrue(
            all(abs(x)<1e-12 for row in s.common_rank1[1:] for x in row)
        )
        self.assertTrue(any(abs(x)>0 for x in s.common_rank1[0]))
        self.assertTrue(
            all(abs(x)<1e-12 for x in s.differential_rank3[0])
        )

    def test_split_reconstructs_plus(self):
        s=canonical_antipodal_split4()
        plus=canonical_plus_frame4()
        rec=tuple(
            tuple(a+b for a,b in zip(ra,rb))
            for ra,rb in zip(s.common_rank1,s.differential_rank3)
        )
        for a,b in zip(rec,plus):
            for x,y in zip(a,b):
                self.assertAlmostEqual(x,y,places=12)


class TetraNullEventParityTests(unittest.TestCase):
    def test_tetra_rays_are_null_and_mutual_inner_products_match(self):
        ell=2.0
        frame=tetra_null_frame(ell)
        cols=frame_columns(frame)
        for i,x in enumerate(cols):
            self.assertAlmostEqual(minkowski_inner(x,x),0.0,places=12)
            for j,y in enumerate(cols):
                if i!=j:
                    self.assertAlmostEqual(
                        minkowski_inner(x,y),
                        ell*ell/3.0,
                        places=12,
                    )

    def test_antipodal_layer_is_scaled_parity(self):
        receipt=stella_parity_receipt(2.0,3.0)
        self.assertLess(receipt.expected_parity_residual,1e-12)
        self.assertLess(receipt.metric_conformal_residual,1e-12)
        self.assertAlmostEqual(receipt.scale_ratio,1.5,places=12)

    def test_bivector_parity_is_exact_three_plus_three(self):
        receipt=stella_parity_receipt(2.0,2.0)
        diag=tuple(receipt.bivector6[i][i] for i in range(6))
        self.assertEqual(diag,(-1.0,-1.0,-1.0,1.0,1.0,1.0))
        off=max(
            abs(receipt.bivector6[i][j])
            for i in range(6)
            for j in range(6)
            if i!=j
        )
        self.assertLess(off,1e-12)

    def test_generic_deformed_pair_recovers_full_relative_frame(self):
        reference=tetra_null_frame(2.0)
        a=(
            (1.10,0.10,0.00,0.00),
            (0.20,0.90,0.05,0.00),
            (0.00,0.10,1.05,0.02),
            (0.03,0.00,0.10,0.95),
        )
        target=tuple(
            tuple(
                sum(a[i][k]*reference[k][j] for k in range(4))
                for j in range(4)
            )
            for i in range(4)
        )
        result=generic_frame_pair(reference,target)
        recovered=result["relative_frame4"]
        self.assertLess(
            max(
                abs(recovered[i][j]-a[i][j])
                for i in range(4)
                for j in range(4)
            ),
            1e-12,
        )

    def test_constant_parity_metadata_is_preserved(self):
        receipt=stella_parity_receipt()
        self.assertFalse(receipt.physical_gravity_claim)
        self.assertTrue(receipt.candidate_only)

    def test_eta_and_parity_are_same_metric_matrix(self):
        self.assertEqual(ETA,PARITY)

    def test_exterior_square4_matches_typed_parity(self):
        raw=exterior_square4(PARITY)
        typed=canonical_bivector_parity().matrix6
        self.assertEqual(raw,typed)


if __name__=="__main__":
    unittest.main()
