import numpy as np
import pytest
import trimesh
from figuraforge.geometry.patch_masks import repair_patch_boundary,_branches
from figuraforge.geometry.types import GeometryError


def touching_holes():
    vertices=np.array([[x,y,0] for y in range(6) for x in range(6)],float);faces=[];selected=[]
    for y in range(5):
        for x in range(5):
            a=y*6+x;b=a+1;c=a+6;d=c+1
            faces.extend([[a,b,d],[a,d,c]])
            selected.extend([(x,y) not in [(1,1),(2,2)]]*2)
    return trimesh.Trimesh(vertices,np.array(faces),process=False),np.asarray(selected)


def test_touching_holes_repaired_without_changing_geometry_or_dropping_source_faces():
    mesh,mask=touching_holes();vertices=mesh.vertices.copy();faces=mesh.faces.copy()
    assert len(_branches(mesh,mask))==1
    ids,report=repair_patch_boundary(mesh,np.flatnonzero(mask),[0,0,1])
    repaired=np.zeros(len(mask),bool);repaired[ids]=True
    assert not _branches(mesh,repaired)
    assert np.all(repaired[mask]) and report['added_source_face_ids']
    assert np.array_equal(mesh.vertices,vertices) and np.array_equal(mesh.faces,faces)
    assert report['final_branched_vertices']==0


def test_protected_or_incompatible_faces_never_silently_used():
    mesh,mask=touching_holes()
    with pytest.raises(GeometryError,match='No compatible'):
        repair_patch_boundary(mesh,np.flatnonzero(mask),[0,0,1],allowed_faces=mask)
    with pytest.raises(GeometryError,match='Original patch'):
        repair_patch_boundary(mesh,np.flatnonzero(mask),[0,0,-1])
    with pytest.raises(GeometryError,match='bounded additions'):
        repair_patch_boundary(mesh,np.flatnonzero(mask),[0,0,1],max_added=0)
