import numpy as np
import pytest
from shapely.geometry import Polygon
from figuraforge.geometry.surface_parts import interior_cap
from figuraforge.geometry.topology import triangulate_polygon,orient_local,mesh_from_triangles,boundary_loops,projected_outline,frame


@pytest.mark.parametrize('reverse',[False,True])
def test_concave_cap_has_true_interior_volume_without_reused_exterior_diagonals(reverse):
    # Mean is inside the U's notch, so the single-anchor star fan is invalid.
    points=np.array([[0,0],[4,0],[4,4],[3,4],[3,1],[1,1],[1,4],[0,4]],float)
    triangles=triangulate_polygon(Polygon(points))
    exterior=orient_local(np.dstack([triangles,np.zeros(triangles.shape[:2])]),positive=not reverse)
    patch=mesh_from_triangles(exterior,check=False)
    loop=boundary_loops(patch)[0];boundary=patch.vertices[loop]
    cap=interior_cap(boundary)
    solid=mesh_from_triangles(np.concatenate([patch.triangles,cap.triangles]))
    assert solid.is_watertight and solid.is_winding_consistent
    assert abs(solid.volume)>.1
    assert np.ptp(cap.vertices[:,2])>=.05
    assert np.max(np.bincount(solid.edges_unique_inverse))==2
    normal=np.array([0,0,1 if reverse else -1])
    assert (cap.face_normals@normal).min()>0
    assert projected_outline(cap,frame(normal)).area==pytest.approx(Polygon(points).area)
    # Original boundary remains exact; only internal cap vertices move.
    assert all(np.min(np.linalg.norm(cap.vertices-point,axis=1))<1e-9 for point in boundary)
