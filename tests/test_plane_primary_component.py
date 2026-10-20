import numpy as np
import pytest
import trimesh
from shapely.geometry import Polygon
from figuraforge.geometry.plane_cut import clip_primary_component
from figuraforge.geometry.topology import triangulate_polygon
from figuraforge.geometry.validation import require_solid
from figuraforge.geometry.types import GeometryError


def comb_solid():
    polygon=Polygon([[-6,-2],[6,-2],[6,3],[2,3],[2,0],[0,0],[0,2],[-1,2],[-1,0],[-3,0],[-3,1.5],[-5,1.5],[-5,0],[-6,0]])
    triangles=triangulate_polygon(polygon)
    vertices,inverse=np.unique(triangles.reshape(-1,2),axis=0,return_inverse=True)
    return trimesh.creation.extrude_triangulation(vertices,inverse.reshape(-1,3),height=2)


def test_minor_positive_lobes_return_to_connected_core_without_surface_loss():
    source=comb_solid();original_vertices=source.vertices.copy();original_faces=source.faces.copy()
    primary,core,report=clip_primary_component(source,1,.75)
    require_solid(primary);require_solid(core)
    assert len(primary.split())==len(core.split())==1
    assert report['selected_components_before']==3 and report['returned_fragments']==2
    assert report['exterior_components_deleted']==0
    assert primary.volume+core.volume==pytest.approx(source.volume,abs=1e-8)
    assert report['parts_exterior_area_mm2']==pytest.approx(source.area,abs=1e-8)
    # Tall/narrow and shorter/wider minor teeth remain on the original core.
    assert core.bounds[1,1]==pytest.approx(2)
    assert primary.bounds[0,0]==pytest.approx(2)
    np.testing.assert_array_equal(source.vertices,original_vertices)
    np.testing.assert_array_equal(source.faces,original_faces)


def test_negative_side_and_single_component_use_same_conservation_contract():
    source=trimesh.creation.box(extents=[4,6,8])
    primary,core,report=clip_primary_component(source,1,.75,positive=False)
    assert report['returned_fragments']==0
    assert primary.is_volume and core.is_volume
    assert primary.volume+core.volume==pytest.approx(source.volume)


def test_disconnected_opposite_core_is_not_claimed_as_one_part():
    with pytest.raises(GeometryError,match='single connected'):
        clip_primary_component(comb_solid(),1,.75,positive=False)


def test_actual_coplanar_source_face_is_never_silently_removed():
    source=trimesh.creation.box(extents=[4,6,8])
    with pytest.raises(GeometryError,match='coplanar'):
        clip_primary_component(source,1,3)
