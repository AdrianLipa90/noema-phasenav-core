import unittest

from ciel_geometry.phasenav.packet_coframe import (
    ElapsedBlochPacket,
    PacketFrame4,
    canonical_tetra_frame,
    spatial_parity4,
)
from ciel_geometry.phasenav.bivector36 import exterior_square

def max_error(a,b):
    return max(
        abs(x-y)
        for ra,rb in zip(a,b)
        for x,y in zip(ra,rb)
    )

class PacketCoframeTests(unittest.TestCase):
    def test_null_tetra_is_invertible(self):
        frame=canonical_tetra_frame(2.0)
        self.assertGreater(abs(frame.determinant),1e-8)
        for packet in frame.packets:
            self.assertAlmostEqual(packet.minkowski_norm2,0.0,places=12)

    def test_antipode_is_spatial_parity(self):
        plus=canonical_tetra_frame(2.0)
        minus=canonical_tetra_frame(2.0,antipodal=True)
        self.assertLess(
            max_error(minus.relative_to(plus),spatial_parity4()),
            1e-12,
        )

    def test_antipode_bivector_split(self):
        c=exterior_square(spatial_parity4())
        diagonal=(-1,-1,-1,1,1,1)
        for i in range(6):
            for j in range(6):
                target=diagonal[i] if i==j else 0.0
                self.assertAlmostEqual(c[i][j],target,places=12)

    def test_uniform_elapsed_scale_ratio(self):
        source=canonical_tetra_frame(2.0)
        target=canonical_tetra_frame(6.0)
        relative=target.relative_to(source)
        expected=tuple(
            tuple(3.0 if i==j else 0.0 for j in range(4))
            for i in range(4)
        )
        self.assertLess(max_error(relative,expected),1e-12)

    def test_mixed_packets_form_full_frame(self):
        frame=PacketFrame4((
            ElapsedBlochPacket(2.0,(0.2,0.1,0.0)),
            ElapsedBlochPacket(3.0,(-0.1,0.3,0.1)),
            ElapsedBlochPacket(4.0,(0.1,-0.2,0.3)),
            ElapsedBlochPacket(5.0,(-0.2,-0.1,-0.2)),
        ))
        self.assertGreater(abs(frame.determinant),1e-8)
        biv=frame.bivector_relative_to(canonical_tetra_frame(2.0))
        self.assertEqual(len(biv.to_flat36()),36)

    def test_invalid_bloch_packet_fails_closed(self):
        with self.assertRaises(ValueError):
            ElapsedBlochPacket(1.0,(2.0,0.0,0.0))

if __name__=="__main__":
    unittest.main()
