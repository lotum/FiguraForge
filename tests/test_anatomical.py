import numpy as np
import pytest
import trimesh
from figuraforge.geometry.anatomical import analysis_copy,seed_geodesic_faces,anatomical_seed_cut
from figuraforge.geometry.types import GeometryError


def test_analysis_copy_smooths_only_copy_and_preserves_original_topology():
    mesh=trimesh.creation.icosphere(subdivisions=2,radius=10)
    mesh.vertices[0]*=1.3;vertices=mesh.vertices.copy();faces=mesh.faces.copy()
    result=analysis_copy(mesh,10)
    assert not np.allclose(result.vertices,vertices)
    np.testing.assert_array_equal(mesh.vertices,vertices)
    np.testing.assert_array_equal(mesh.faces,faces)
    np.testing.assert_array_equal(result.faces,faces)


def test_seeded_cut_respects_hard_seeds_and_returns_original_face_ids():
    mesh=trimesh.creation.icosphere(subdivisions=2,radius=10);centers=mesh.triangles_center
    north=np.flatnonzero(centers[:,2]>7);south=np.flatnonzero(centers[:,2]<-7)
    before=mesh.vertices.copy()
    selected,report=anatomical_seed_cut(mesh,north,south,smoothing_iterations=10)
    assert set(north)<=set(selected) and not set(south)&set(selected)
    assert len(selected)<len(mesh.faces) and report['cut_edges']>0
    np.testing.assert_array_equal(mesh.vertices,before)
    assert not report['original_geometry_modified']


def test_geodesic_growth_is_local_and_does_not_allocate_dense_seed_matrix():
    mesh=trimesh.creation.icosphere(subdivisions=2,radius=10)
    small=seed_geodesic_faces(mesh,np.array([0]),0)
    grown=seed_geodesic_faces(mesh,np.array([0]),5)
    assert small.tolist()==[0]
    assert 1<len(grown)<len(mesh.faces)


def test_conflicting_or_noninteger_seeds_rejected():
    mesh=trimesh.creation.icosphere(subdivisions=1)
    with pytest.raises(GeometryError):anatomical_seed_cut(mesh,[0],[0])
    with pytest.raises(GeometryError):anatomical_seed_cut(mesh,[.5],[1])
    with pytest.raises(GeometryError):seed_geodesic_faces(mesh,[0],float('nan'))


def test_model_bound_mochi_preset_rejects_unrelated_source_without_mutation():
    from figuraforge.geometry.mochi_masks import mochi_masks,geometry_signature
    from figuraforge.geometry.types import Surface
    mesh=trimesh.creation.icosphere(subdivisions=1);before=geometry_signature(mesh)
    surface=Surface(mesh,np.zeros((len(mesh.faces),3,2)),np.ones((len(mesh.faces),3,3)),np.zeros(len(mesh.faces),int))
    with pytest.raises(GeometryError,match='verified 180 mm'):
        mochi_masks(surface,{'face_regions':[0]*len(mesh.faces)})
    assert geometry_signature(mesh)==before
