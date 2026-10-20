import numpy as np
import pytest
from figuraforge.geometry.detail_regions import DetailRegion,vertex_importance,allocate_face_budget


def test_brush_is_local_smooth_and_overlap_does_not_multiply():
    points=np.array([[0,0,0],[1,0,0],[2,0,0],[3,0,0]])
    region=DetailRegion((0,0,0),2,5)
    assert vertex_importance(points,[region,region]).tolist()==[5,3,1,1]


def test_protected_eyes_receive_higher_retained_fraction_without_overshoot():
    allocation=allocate_face_budget([90000,10000],[1,5],20000)
    assert allocation.sum()==20000
    assert allocation[1]/10000>allocation[0]/90000
    assert (allocation<=np.array([90000,10000])).all()


def test_tiny_protected_region_caps_at_original_and_redistributes():
    assert allocate_face_budget([1000,2],[1,100],500).tolist()==[498,2]
    assert allocate_face_budget([10,0,4],[1,5,2],100).tolist()==[10,0,4]
    assert allocate_face_budget([],[],0).tolist()==[]


def test_budget_invariant_for_many_different_region_sizes():
    rng=np.random.default_rng(17)
    for _ in range(100):
        counts=rng.integers(0,1000,20);weights=rng.uniform(1,15,20)
        budget=int(rng.integers(20,20000))
        result=allocate_face_budget(counts,weights,budget)
        assert result.sum()==min(budget,counts.sum())
        assert (result<=counts).all()
        assert (result[counts>0]>0).all()


@pytest.mark.parametrize('args', [((0,0,float('nan')),1,2),((0,0,0),0,2),((0,0,0),1,101)])
def test_invalid_brush_rejected(args):
    with pytest.raises(ValueError):DetailRegion(*args)


@pytest.mark.parametrize('counts,weights,budget', [([2,3],[1,1],1),([2.5],[1],2),([2],[float('nan')],2),([2],[1],True)])
def test_invalid_budget_rejected(counts,weights,budget):
    with pytest.raises(ValueError):allocate_face_budget(counts,weights,budget)
