import math
import unittest

from ciel_geometry.phasenav.tetra_null_frame import (
    ETA,
    PARITY,
    exterior_square4,
    frame_columns,
    generic_frame_pair,
    minkowski_inner,
    stella_parity_receipt,
    tetra_null_frame,
)


class TetraNullFrameTests(unittest.TestCase):
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
            max(abs(recovered[i][j]-a[i][j]) for i in range(4) for j in range(4)),
            1e-12,
        )

    def test_constant_parity_is_not_declared_gravity(self):
        receipt=stella_parity_receipt()
        self.assertFalse(receipt.physical_gravity_claim)
        self.assertTrue(receipt.candidate_only)


if __name__=="__main__":
    unittest.main()
