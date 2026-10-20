"""Shared nonplanar neck interfaces, paint conservation and printable loose key."""
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.mochi_neck import split_neck,clipped_shell,field
from figuraforge.geometry.types import GeometryError
from figuraforge.geometry.validation import check_insert_path


def specimen():
    profile=np.array([[0,60],[40,60],[36,90],[28,110],[40,125],[44,145],[32,170],[0,180]])
    mesh=trimesh.creation.revolve(profile,sections=48);mesh.apply_translation([0,-27,0]);assert mesh.is_volume
    return mesh


def test_curved_neck_closes_and_retains_unmodified_painted_triangles():
    mesh=specimen();paint=np.full(len(mesh.faces),'4',dtype=object);complex_mask=mesh.triangles_center[:,2]>140;paint[complex_mask]='8848'
    coeff=[110,0,0,.004,0,0];factor=470/180
    low,high,key,report=split_neck(mesh,paint.tolist(),coeff,factor)
    for part,*_ in (low,high,key):assert part.is_volume and len(part.split(only_watertight=False))==1
    assert np.ptp(np.array(report['boundary_source'])[:,2])>1
    assert high[1].count('8848')==int(complex_mask.sum())
    actual=high[0].triangles[np.asarray(high[1])=='8848'];expected=mesh.triangles[complex_mask]
    assert np.allclose(actual,expected)
    assert np.allclose(key[0].extents*factor,[20,28,36])
    assert check_insert_path(high[0],low[0],[0,0,1],travel_mm=20,samples=10)['passed']
    assert check_insert_path(key[0],low[0],[0,0,1],travel_mm=20,samples=10)['passed']
    assert check_insert_path(key[0],high[0],[0,0,-1],travel_mm=20,samples=10)['passed']
    assert report['source_scale_factor']==factor
    # Underside cavity roof must rise at least 45 degrees from horizontal.
    head=high[0];end=high[2]['socket_end_source_z'];roof=(head.triangles_center[:,2]>end)&(head.face_normals[:,2]<-.1)&(np.linalg.norm(head.triangles_center[:,:2]-[0,-27],axis=1)<8)
    assert roof.any();assert np.max(abs(head.face_normals[roof,2]))<2**-.5+1e-6


def test_never_silently_repaints_complex_subtriangles_at_cut():
    mesh=specimen();values=mesh.vertices[:,2]-110.123;paint=['8848']*len(mesh.faces)
    with pytest.raises(GeometryError,match='Complex painted triangle crosses'):
        clipped_shell(mesh,paint,values,True)
