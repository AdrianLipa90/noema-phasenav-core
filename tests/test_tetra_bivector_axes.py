import itertools
import unittest

from ciel_geometry.phasenav.tetra_bivector_axes import (
    EDGE_BASIS,
    EDGE_LABELS,
    TetraEdgePairField36,
    induced_edge_matrix,
    legacy_phase36_row_major_view,
    opposite_edge_pairing,
)

def transpose(A):
    return tuple(tuple(A[j][i] for j in range(len(A))) for i in range(len(A[0])))

def matmul(A,B):
    return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))) for i in range(len(A)))

def scale(A,s):
    return tuple(tuple(s*x for x in row) for row in A)

def parity(p):
    inv=sum(1 for i in range(4) for j in range(i+1,4) if p[i]>p[j])
    return -1.0 if inv%2 else 1.0

class TetraBivectorAxisTests(unittest.TestCase):
    def test_six_edges_and_thirty_six_pairs(self):
        self.assertEqual(len(EDGE_BASIS),6)
        self.assertEqual(len(EDGE_LABELS)**2,36)

    def test_all_s4_actions_have_expected_J_sign(self):
        J=opposite_edge_pairing()
        passed=0
        for p in itertools.permutations(range(4)):
            C=induced_edge_matrix(p)
            lhs=matmul(matmul(transpose(C),J),C)
            self.assertEqual(lhs,scale(J,parity(p)))
            passed+=1
        self.assertEqual(passed,24)

    def test_explicit_relation_field_requires_all_36(self):
        relations={(a,b):float(i*6+j) for i,a in enumerate(EDGE_LABELS) for j,b in enumerate(EDGE_LABELS)}
        field=TetraEdgePairField36.from_mapping(relations,source_receipt="receipt:test")
        self.assertEqual(len(field.to_flat36()),36)
        self.assertEqual(field.binding_status,"EXPLICIT_TETRA_EDGE_PAIR_RELATIONS")

    def test_legacy_reshape_fails_physical_binding(self):
        view=legacy_phase36_row_major_view(range(36))
        self.assertFalse(view["physical_binding"])
        self.assertEqual(view["binding_status"],"LEGACY_ROW_MAJOR_RESHAPE_NOT_DERIVED")

if __name__=="__main__":
    unittest.main()
