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



class TetraEdgePairPhaseObservableTests(unittest.TestCase):
    def test_constant_edge_phases_are_recovered(self):
        from ciel_geometry.phasenav.tetra_bivector_axes import phase_overlap_edge_pair_field
        D=36
        plus={label:(0.0,)*D for label in EDGE_LABELS}
        theta={"01":0.1,"02":0.2,"03":0.3,"23":-0.4,"31":0.5,"12":-0.6}
        minus={label:(value,)*D for label,value in theta.items()}
        rec=phase_overlap_edge_pair_field(plus,minus,source_receipt="receipt:test-phase")
        for row in rec.field.matrix6:
            for j,label in enumerate(EDGE_LABELS):
                self.assertAlmostEqual(row[j],theta[label],places=12)
        for row in rec.overlap_abs6:
            for value in row:
                self.assertAlmostEqual(value,1.0,places=12)

    def test_common_shift_is_invariant(self):
        from ciel_geometry.phasenav.tetra_bivector_axes import phase_overlap_edge_pair_field
        D=36
        plus={label:tuple(0.01*k+0.03*i for k in range(D)) for i,label in enumerate(EDGE_LABELS)}
        minus={label:tuple(0.02*k-0.04*i for k in range(D)) for i,label in enumerate(EDGE_LABELS)}
        a=phase_overlap_edge_pair_field(plus,minus,source_receipt="receipt:a")
        shift=0.77
        p2={k:tuple(x+shift for x in v) for k,v in plus.items()}
        m2={k:tuple(x+shift for x in v) for k,v in minus.items()}
        b=phase_overlap_edge_pair_field(p2,m2,source_receipt="receipt:b")
        for ra,rb in zip(a.field.matrix6,b.field.matrix6):
            for x,y in zip(ra,rb):
                self.assertAlmostEqual(x,y,places=12)

if __name__=="__main__":
    unittest.main()
