from adaptive_separator import (
    canonical_edges,schedule_occurrences,dynamic_edge_weights,minimum_fixed_size_cut,
    pareto_fixed_size_cuts,build_balanced_separator_tree,summarize_separator_tree
)


def cycle4():return ((0,1),(1,2),(2,3),(3,0))

def test_schedule_occurrences():
    assert schedule_occurrences('ABCD',10)=={'A':3,'B':3,'C':2,'D':2}


def test_dynamic_edge_weights():
    m={'A':((0,1),),'B':((1,2),),'C':((2,3),),'D':((3,0),)}
    w=dynamic_edge_weights(m,'ABCD',8,operator_schmidt_rank=2)
    assert all(v==2.0 for v in w.values())


def test_fixed_size_cycle_cut_optimal():
    r=minimum_fixed_size_cut(range(4),cycle4(),2,time_limit_s=5)
    assert r.solver_optimal
    assert r.edge_cut_count==2
    assert len(r.left)==2 and len(r.right)==2


def test_weighted_cut_prefers_cheap_edges():
    edges=((0,1),(1,2),(2,3),(3,0))
    weights={canonical_edges([(0,1)])[0]:10.0,(1,2):1.0,(2,3):10.0,(0,3):1.0}
    r=minimum_fixed_size_cut(range(4),edges,2,edge_weights=weights,time_limit_s=5)
    assert r.objective_weight==2.0


def test_pareto_removes_dominated():
    # Path of 5: k=2 can cut one edge with imbalance1; k=1 also cuts one with imbalance3, so k=1 is dominated.
    edges=((0,1),(1,2),(2,3),(3,4))
    p=pareto_fixed_size_cuts(range(5),edges,[1,2],time_limit_s=5)
    assert len(p.pareto)==1
    assert p.pareto[0].target_size==2


def test_tree_leaf_bound():
    edges=((0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7))
    t=build_balanced_separator_tree(range(8),edges,leaf_max=2,time_limit_s=5)
    s=summarize_separator_tree(t)
    assert s.max_leaf_size<=2
    assert s.leaf_count==4