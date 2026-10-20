import numpy as np
import pytest
import trimesh
from figuraforge.geometry.types import Surface,GeometryError
from figuraforge.geometry.compare import unchanged_source_faces


def source():
    mesh=trimesh.creation.box()
    return Surface(mesh,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,int))


def triangle_mesh(triangles):
    triangles=np.asarray(triangles)
    return trimesh.Trimesh(vertices=triangles.reshape(-1,3),faces=np.arange(len(triangles)*3).reshape(-1,3),process=False)


def test_permuted_original_is_exterior_but_nearby_and_coplanar_new_caps_are_not():
    s=source();triangle=s.mesh.triangles[0];center=triangle.mean(axis=0)
    original=triangle[[2,0,1]]
    near=triangle+s.mesh.face_normals[0]*1e-5  # Inside old .0001 threshold.
    coplanar=center+(triangle-center)*.2       # Centroid distance exactly zero.
    mesh=triangle_mesh([original,near,coplanar])
    assert unchanged_source_faces(s,mesh,np.array([0,0,0])).tolist()==[True,False,False]


def test_corner_matching_is_bijective_and_respects_the_explicit_tolerance():
    s=source();triangle=s.mesh.triangles[0]
    duplicate=np.array([triangle[0],triangle[0],triangle[2]])
    within=triangle+np.array([.25e-6,0,0]);outside=triangle+np.array([2e-6,0,0])
    mesh=triangle_mesh([duplicate,within,outside])
    assert unchanged_source_faces(s,mesh,np.array([0,0,0])).tolist()==[False,True,False]


def test_identity_mapping_rejects_invalid_candidates_instead_of_inventing_provenance():
    s=source();mesh=triangle_mesh([s.mesh.triangles[0]])
    for ids in [np.array([-1]),np.array([12]),np.array([0.]),np.array([0,1])]:
        with pytest.raises(GeometryError,match='candidate'):
            unchanged_source_faces(s,mesh,ids)
    with pytest.raises(GeometryError,match='tolerance'):
        unchanged_source_faces(s,mesh,np.array([0]),tolerance_mm=float('nan'))
