"""Material-only leather cleanup, with the real source regression when local."""
import hashlib
from pathlib import Path
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.buddy_materials import clean_enclosed_leather_highlights,propose_materials,REVIEWED_LEATHER_FACE_SHA256,REVIEWED_EMBLEM_FACE_SHA256
from figuraforge.geometry.types import GeometryError


def sphere_with_gold_face():
    mesh=trimesh.creation.icosphere(subdivisions=1)
    tags=np.ones(len(mesh.faces),dtype=int);tags[0]=0
    return mesh,tags


def test_small_enclosed_gold_becomes_brown_without_mutating_inputs():
    mesh,tags=sphere_with_gold_face();before=tags.copy();vertices=mesh.vertices.copy();faces=mesh.faces.copy()
    output,report=clean_enclosed_leather_highlights(mesh,tags)
    assert np.array_equal(tags,before)
    assert np.array_equal(mesh.vertices,vertices) and np.array_equal(mesh.faces,faces)
    assert np.flatnonzero(output!=tags).tolist()==[0]
    assert output[0]==1 and report['component_count']==1
    assert report['changed_source_faces']==1
    assert report['changed_source_face_ids_sha256']==hashlib.sha256(np.array([0],dtype='<i8').tobytes()).hexdigest()
    assert not report['geometry_modified'] and not report['anatomical_masks_modified']


def test_large_enclosed_real_fur_stays_gold():
    mesh,tags=sphere_with_gold_face();mesh.apply_scale(1000)
    assert mesh.area_faces[0]>5000
    output,report=clean_enclosed_leather_highlights(mesh,tags)
    assert np.array_equal(output,tags) and report['changed_source_faces']==0


@pytest.mark.parametrize('special',[2,3,4,5,6,7])
def test_enclosure_touching_any_special_material_is_preserved(special):
    mesh,tags=sphere_with_gold_face();edge=mesh.face_adjacency[(mesh.face_adjacency==0).any(axis=1)][0]
    tags[edge[edge!=0][0]]=special
    output,report=clean_enclosed_leather_highlights(mesh,tags)
    assert np.array_equal(output,tags) and report['changed_source_faces']==0


def test_open_mesh_edge_is_not_an_enclosing_leather_boundary():
    mesh=trimesh.Trimesh([[0,0,0],[1,0,0],[0,1,0],[1,1,0]],[[0,1,2],[1,3,2]],process=False)
    tags=np.array([0,1]);output,report=clean_enclosed_leather_highlights(mesh,tags)
    assert np.array_equal(output,tags) and report['changed_source_faces']==0


def test_invalid_tags_are_rejected():
    mesh,tags=sphere_with_gold_face()
    with pytest.raises(GeometryError):clean_enclosed_leather_highlights(mesh,tags[:-1])
    with pytest.raises(GeometryError):clean_enclosed_leather_highlights(mesh,tags.astype(float))


def test_reviewed_source_changes_only_1053_leather_and_five_gold_emblem_faces():
    from figuraforge.geometry.io import load_surface
    from figuraforge.services.buddy_pipeline import _source,anatomical_masks,MESH_HASH
    path=Path(__file__).resolve().parents[1]/'data/projects/2c9a7959d13a438fbeb5b8340d8eefd4/runs/db7728785a564c3d8715c7388992129d/prepared-source.glb'
    if not path.is_file():pytest.skip('Reviewed local Buddy source unavailable')
    surface=load_surface(path,1000,'Y');settings,labels,reference=_source(surface,{'height_mm':1000,'up_axis':'Y'},MESH_HASH,None)
    masks,_=anatomical_masks(surface,labels);before={key:ids.copy() for key,ids in masks.items()};vertices=surface.mesh.vertices.copy()
    document,report,_=propose_materials(surface,reference,masks,[])
    cleanup=report['leather_highlight_cleanup']
    assert cleanup['component_count']==61 and cleanup['changed_source_faces']==1053
    assert cleanup['changed_source_area_mm2']==pytest.approx(7556.588882490762)
    assert cleanup['changed_source_face_ids_sha256']==REVIEWED_LEATHER_FACE_SHA256
    assert report['gold_emblem']['source_faces']==5
    assert report['gold_emblem']['source_area_mm2']==pytest.approx(1996.807740431892)
    assert report['gold_emblem']['source_face_ids_sha256']==REVIEWED_EMBLEM_FACE_SHA256
    assert not report['gold_emblem']['geometry_modified']
    assert not report['gold_emblem']['physical_color_verified']
    assert np.array_equal(surface.mesh.vertices,vertices)
    assert all(np.array_equal(masks[key],before[key]) for key in masks)
    assert set(np.unique(document['face_regions']))==set(range(8))
    # Existing immutable plan provides independent before-cleanup labels.
    import json
    old_path=path.parents[2]/'plans/d2f0f4a355df4999bcb4551bd9c39282/color-plan.json'
    if old_path.is_file():
        old=np.asarray(json.loads(old_path.read_text())['face_regions']);new=np.asarray(document['face_regions']);changed=np.flatnonzero(old!=new)
        assert len(changed)==1058
        leather=np.flatnonzero((old==0)&(new==1));emblem=np.flatnonzero((old==1)&(new==0))
        assert len(leather)==1053 and len(emblem)==5
        assert len(changed)==len(leather)+len(emblem)
        assert hashlib.sha256(leather.astype('<i8').tobytes()).hexdigest()==REVIEWED_LEATHER_FACE_SHA256
        assert hashlib.sha256(emblem.astype('<i8').tobytes()).hexdigest()==REVIEWED_EMBLEM_FACE_SHA256
