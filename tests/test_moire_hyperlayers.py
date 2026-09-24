import math
import unittest

from ciel_geometry.phasenav.moire_hyperlayers import (
    PhaseMatrix6,
    direct_pair,
    pair_hyperlayers,
    reconstruct_pair,
    structured_rotation_counts,
    u1_holonomy_memory,
)


class MoireHyperlayerTests(unittest.TestCase):
    def test_36_roundtrip(self):
        p=tuple((0.13*i)%(2*math.pi) for i in range(36))
        self.assertEqual(PhaseMatrix6.from_phase36(p).to_phase36(),p)

    def test_factorized_identity(self):
        a=tuple((0.17*i)%(2*math.pi) for i in range(36))
        b=tuple((0.31*i+0.2)%(2*math.pi) for i in range(36))
        pair=pair_hyperlayers(PhaseMatrix6.from_phase36(a),PhaseMatrix6.from_phase36(b))
        for i in range(36):
            self.assertLess(abs(direct_pair(a[i],b[i])-reconstruct_pair(pair.mean_phase36[i],pair.half_delta36[i])),1e-11)

    def test_antiphase_cancels(self):
        a=tuple((0.07*i)%(2*math.pi) for i in range(36))
        b=tuple((x+math.pi)%(2*math.pi) for x in a)
        pair=pair_hyperlayers(PhaseMatrix6.from_phase36(a),PhaseMatrix6.from_phase36(b))
        self.assertEqual(pair.cancellation_fraction,1.0)

    def test_common_phase_shift_preserves_interference(self):
        a=tuple((0.11*i)%(2*math.pi) for i in range(36))
        b=tuple((0.19*i+0.4)%(2*math.pi) for i in range(36))
        shift=0.73
        p1=pair_hyperlayers(PhaseMatrix6.from_phase36(a),PhaseMatrix6.from_phase36(b))
        p2=pair_hyperlayers(PhaseMatrix6.from_phase36(tuple((x+shift)%(2*math.pi) for x in a)),PhaseMatrix6.from_phase36(tuple((x+shift)%(2*math.pi) for x in b)))
        for x,y in zip(p1.half_delta36,p2.half_delta36): self.assertAlmostEqual(x,y,places=12)
        for x,y in zip(p1.envelope36,p2.envelope36): self.assertAlmostEqual(x,y,places=12)

    def test_rotation_counts(self):
        self.assertEqual(structured_rotation_counts(),{"so6_left":15,"so6_right":15,"so6xso6":30,"so36_full":630})

    def test_holonomy_memory_is_unit_modulus(self):
        self.assertAlmostEqual(abs(u1_holonomy_memory([0.2,-0.4,1.1])),1.0,places=12)


if __name__ == '__main__':
    unittest.main()
