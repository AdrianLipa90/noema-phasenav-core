import math
import random
import unittest

from ciel_geometry.phasenav.moire_hyperlayers import PhaseMatrix6
from ciel_geometry.phasenav.moire_bivector_decoder import (
    _add,
    _frob,
    _sub,
    decode_moire_to_coframe_generator,
    decompose_co33,
    inverse_lie_exterior_square,
    lie_exterior_square,
    relative_phase_generator,
)


class MoireBivectorDecoderTests(unittest.TestCase):
    def test_decomposition_identities(self):
        rng = random.Random(7)
        x = tuple(
            tuple(rng.uniform(-1.0, 1.0) for _ in range(6))
            for _ in range(6)
        )
        from ciel_geometry.phasenav.bivector36 import BivectorField36
        d = decompose_co33(BivectorField36(x))
        self.assertLess(d.co33_residual, 1e-12)
        self.assertLess(d.defect_symmetry_residual, 1e-12)
        self.assertLess(abs(d.defect_trace), 1e-12)
        self.assertLess(
            _frob(
                _sub(
                    _add(d.geometric.matrix6, d.defect.matrix6),
                    d.raw.matrix6,
                )
            ),
            1e-12,
        )

    def test_lie_inverse_roundtrip(self):
        rng = random.Random(11)
        for _ in range(20):
            h = tuple(
                tuple(rng.uniform(-0.3, 0.3) for _ in range(4))
                for _ in range(4)
            )
            a = lie_exterior_square(h)
            recovered = inverse_lie_exterior_square(a)
            self.assertLess(_frob(_sub(h, recovered)), 1e-11)
            self.assertLess(decompose_co33(a).defect_ratio, 1e-12)

    def test_common_phase_shift_is_gauge_invariant(self):
        rng = random.Random(3)
        a = [rng.random() * 2.0 * math.pi for _ in range(36)]
        b = [rng.random() * 2.0 * math.pi for _ in range(36)]
        shift = 0.731
        left = PhaseMatrix6.from_phase36(a)
        right = PhaseMatrix6.from_phase36(b)
        shifted_left = PhaseMatrix6.from_phase36(
            tuple((v + shift) % (2.0 * math.pi) for v in a)
        )
        shifted_right = PhaseMatrix6.from_phase36(
            tuple((v + shift) % (2.0 * math.pi) for v in b)
        )
        x = relative_phase_generator(left, right)
        y = relative_phase_generator(shifted_left, shifted_right)
        self.assertLess(_frob(_sub(x.matrix6, y.matrix6)), 1e-12)

    def test_layer_swap_is_odd_away_from_pi_cut(self):
        a = tuple(0.2 + 0.001 * i for i in range(36))
        b = tuple(0.6 + 0.002 * i for i in range(36))
        x = relative_phase_generator(
            PhaseMatrix6.from_phase36(a),
            PhaseMatrix6.from_phase36(b),
        )
        y = relative_phase_generator(
            PhaseMatrix6.from_phase36(b),
            PhaseMatrix6.from_phase36(a),
        )
        self.assertLess(_frob(_add(x.matrix6, y.matrix6)), 1e-12)

    def test_known_gl4_generator_has_zero_defect(self):
        h = (
            (0.05, 0.02, 0.0, 0.0),
            (0.0, 0.03, 0.01, 0.0),
            (0.0, 0.0, -0.04, 0.02),
            (0.01, 0.0, 0.0, -0.02),
        )
        a = lie_exterior_square(h).to_flat36()
        left = PhaseMatrix6.from_phase36(
            tuple(x % (2.0 * math.pi) for x in a)
        )
        right = PhaseMatrix6.from_phase36((0.0,) * 36)
        receipt = decode_moire_to_coframe_generator(left, right)
        self.assertLess(receipt.defect_ratio, 1e-12)
        self.assertLess(receipt.co33_residual, 1e-12)
        self.assertLess(receipt.lie_roundtrip_residual, 1e-12)

    def test_generic_relative_phase_has_nonzero_defect(self):
        rng = random.Random(19)
        a = tuple(rng.random() * 2.0 * math.pi for _ in range(36))
        b = tuple(rng.random() * 2.0 * math.pi for _ in range(36))
        receipt = decode_moire_to_coframe_generator(
            PhaseMatrix6.from_phase36(a),
            PhaseMatrix6.from_phase36(b),
        )
        self.assertGreater(receipt.defect_ratio, 0.1)
        self.assertLess(receipt.co33_residual, 1e-12)
        self.assertLess(receipt.lie_roundtrip_residual, 1e-12)




class GL4MetricSplitTests(unittest.TestCase):
    def test_lorentz_boost_is_metric_invisible(self):
        from ciel_geometry.phasenav.moire_bivector_decoder import split_gl4_lorentz_metric, _frob
        b=0.2
        h=((0.0,b,0.0,0.0),(3.0*b,0.0,0.0,0.0),(0.0,0.0,0.0,0.0),(0.0,0.0,0.0,0.0))
        s=split_gl4_lorentz_metric(h)
        self.assertLess(_frob(s.metric_deformation4),1e-12)
        self.assertLess(_frob(s.first_metric_variation4),1e-12)

    def test_strain_lives_in_metric_sector(self):
        from ciel_geometry.phasenav.moire_bivector_decoder import split_gl4_lorentz_metric, _frob
        h=((0.2,0.0,0.0,0.0),(0.0,0.1,0.0,0.0),(0.0,0.0,-0.05,0.0),(0.0,0.0,0.0,0.08))
        s=split_gl4_lorentz_metric(h)
        self.assertLess(_frob(s.lorentz_gauge4),1e-12)
        self.assertGreater(_frob(s.first_metric_variation4),1e-6)

    def test_generic_reconstructs(self):
        from ciel_geometry.phasenav.moire_bivector_decoder import split_gl4_lorentz_metric, _frob, _add, _sub
        h=((.2,.1,0,0),(.25,.3,.12,0),(0,-.08,-.1,.06),(.03,0,.04,.11))
        s=split_gl4_lorentz_metric(h)
        self.assertLess(_frob(_sub(_add(s.lorentz_gauge4,s.metric_deformation4),h)),1e-11)

if __name__ == "__main__":
    unittest.main()
