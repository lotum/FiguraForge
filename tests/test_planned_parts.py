import numpy as np
import pytest
import trimesh
from figuraforge.geometry.planned_parts import make_planned_parts
from figuraforge.geometry.types import GeometryError,Part


@pytest.fixture
def planned_sphere():
    mesh=trimesh.creation.icosphere(subdivisions=3,radius=35)
    mesh.apply_translation([0,0,35]);c=mesh.triangles_center
    labels=np.zeros(len(mesh.faces),int)
    labels[c[:,2]>52]=1
    labels[(c[:,1]<-29)&(np.abs(c[:,0])<12)&(c[:,2]>25)&(c[:,2]<41)]=2
    return mesh,labels,['#888888','#FFCC00','#CC4422']


def test_mixed_whole_cap_and_side_inlay_are_closed_bounded_and_unique(planned_sphere):
    mesh,labels,palette=planned_sphere;original=mesh.faces.copy();original_labels=labels.copy()
    parts,report=make_planned_parts(mesh,labels,palette,{1},depth_mm=2,pin_radius_mm=1,pin_length_mm=2,
                                   min_region_area_mm2=0,validate_paths=True)
    assert {p.role for p in parts}=={'body','color-body','inlay'}
    assert len({p.id for p in parts})==len(parts)
    assert all(p.mesh.is_volume for p in parts)
    assert sum(p.mesh.volume for p in parts)<=mesh.volume
    assert sum(len(p.connectors) for p in parts)>=2
    assert {p.color_index for p in parts}=={0,1,2}
    assert report['combined_paths_checked'] and report['combined_collision_checks']
    assert all(c['passed'] for c in report['insertion_checks'])
    assert report['label_transfer'][0]['hidden_or_new_faces']>0
    assert 'not an exhaustive' in report['limitation']
    np.testing.assert_array_equal(mesh.faces,original);np.testing.assert_array_equal(labels,original_labels)


def test_no_whole_labels_keeps_existing_inlay_route(planned_sphere):
    mesh,labels,palette=planned_sphere
    labels[labels==1]=0
    parts,report=make_planned_parts(mesh,labels,palette,set(),depth_mm=2,pin_radius_mm=1,pin_length_mm=2)
    assert {p.role for p in parts}=={'body','inlay'}
    assert 'whole_part_report' not in report


def test_no_inlays_keeps_existing_surface_route(planned_sphere):
    mesh,labels,palette=planned_sphere;labels[labels==2]=0
    parts,report=make_planned_parts(mesh,labels,palette,{1},pin_radius_mm=1,pin_length_mm=2)
    assert {p.role for p in parts}=={'body','color-body'}
    assert report['strategy']=='shared non-planar boundary caps'


def test_failed_final_collision_check_blocks_combination(planned_sphere,monkeypatch):
    from figuraforge.geometry import planned_parts
    monkeypatch.setattr(planned_parts,'check_insert_path',lambda *a,**kw:{'passed':False,'max_penetration_mm':1.2})
    mesh,labels,palette=planned_sphere
    with pytest.raises(GeometryError,match='extraction collides'):
        make_planned_parts(mesh,labels,palette,{1},depth_mm=2,pin_radius_mm=1,pin_length_mm=2)


@pytest.mark.parametrize('whole',[{0},{-1},{99},{True}])
def test_invalid_whole_labels_rejected(planned_sphere,whole):
    mesh,labels,palette=planned_sphere
    with pytest.raises(GeometryError):make_planned_parts(mesh,labels,palette,whole)


def test_real_overlapping_parts_are_rejected_by_combined_checks():
    from figuraforge.geometry.planned_parts import _combined_checks
    a=trimesh.creation.box(extents=[10,10,10])
    b=a.copy();b.apply_translation([2,2,2])
    parts=[Part('a','A',a,'#FFFFFF'),Part('b','B',b,'#FFFFFF')]
    with pytest.raises(GeometryError,match='overlap'):_combined_checks(parts,10)
