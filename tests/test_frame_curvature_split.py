import random
import unittest

from ciel_geometry.phasenav.bivector36 import BivectorField36
from ciel_geometry.phasenav.frame_curvature_split import split_frame_curvature


class FrameCurvatureSplitTests(unittest.TestCase):
    def test_random_matrix_splits_into_16_plus_20_representation(self):
        rng=random.Random(20260924)
        m=tuple(tuple(rng.uniform(-1,1) for _ in range(6)) for _ in range(6))
        out=split_frame_curvature(BivectorField36(m))
        self.assertEqual(out.frame_dimension,16)
        self.assertEqual(out.curvature_dimension,20)
        self.assertLess(out.curvature_symmetry_residual,1e-12)
        self.assertLess(out.bianchi_residual,1e-12)
        self.assertAlmostEqual(out.reconstruction_fraction,1.0,places=12)
        self.assertFalse(out.physical_curvature_claim)

    def test_canonical_tetra_overlap_has_exact_numeric_half_split(self):
        x=(
            (-1/3,2/3,2/3,1/3,2/3,0),
            (2/3,-1/3,2/3,0,1/3,2/3),
            (2/3,2/3,-1/3,2/3,0,1/3),
            (1/3,0,2/3,-1/3,0,0),
            (2/3,1/3,0,0,-1/3,0),
            (0,2/3,1/3,0,0,-1/3),
        )
        out=split_frame_curvature(BivectorField36(x))
        self.assertAlmostEqual(out.frame_fraction_frob2,0.5,places=12)
        self.assertAlmostEqual(out.curvature_fraction_frob2,0.5,places=12)
        self.assertLess(out.curvature_symmetry_residual,1e-12)
        self.assertLess(out.bianchi_residual,1e-12)


if __name__=="__main__":
    unittest.main()
