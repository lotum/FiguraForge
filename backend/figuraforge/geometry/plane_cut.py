"""Surface-preserving half-space clipping with a constrained planar cap.

Used for additional build-volume cuts only. Color-region construction remains
organic. A failed cap is rejected instead of automatically filling arbitrary
holes in the source mesh.
"""
from __future__ import annotations
import numpy as np
import trimesh
from shapely.geometry import Polygon
from .types import GeometryError
from .topology import boundary_loops, frame, mesh_from_triangles, triangulate_polygon, polygons, orient_local


def clip_closed(mesh,axis,position,positive):
    sign=1 if positive else -1
    triangles=np.asarray(mesh.triangles)
    distance=(triangles[:,:,axis]-position)*sign
    inside=distance>=0
    groups=[triangles[inside.all(axis=1)]]
    for tri,flags in zip(triangles[inside.any(axis=1)&~inside.all(axis=1)],inside[inside.any(axis=1)&~inside.all(axis=1)]):
        ring=[]
        for index in range(3):
            a=tri[index-1];b=tri[index];ia=flags[index-1];ib=flags[index]
            if ia!=ib:
                fraction=(position-a[axis])/(b[axis]-a[axis])
                point=a+(b-a)*fraction;point[axis]=position;ring.append(point)
            if ib:ring.append(b)
        if len(ring)>=3:
            groups.append(np.array([[ring[0],ring[index],ring[index+1]] for index in range(1,len(ring)-1)]))
    if not any(len(x) for x in groups): raise GeometryError('Half-space clipping produced an empty mesh')
    shell=mesh_from_triangles(np.concatenate(groups),check=False)
    loops=boundary_loops(shell)
    if not loops:
        if not shell.is_volume: raise GeometryError('Clipping produced an invalid solid')
        return shell
    normal=-sign*np.eye(3)[axis];basis=frame(normal)
    outline=Polygon()
    for loop in loops:
        points=np.asarray(shell.vertices)[loop]
        if np.max(np.abs(points[:,axis]-position))>2e-6:
            raise GeometryError('Half-space cut exposed a non-planar hole; source/cut must be repaired explicitly')
        poly=Polygon((points@basis)[:,:2])
        if not poly.is_valid: raise GeometryError('Half-space boundary branches or crosses itself')
        outline=outline.symmetric_difference(poly)
    if not outline.is_valid or outline.is_empty: raise GeometryError('Invalid half-space cap region')
    cap=[]
    z=float((np.eye(3)[axis]*position)@basis[:,2])
    for poly in polygons(outline):
        xy=triangulate_polygon(poly)
        cap.append(orient_local(np.dstack([xy,np.full(xy.shape[:2],z)]),True)@basis.T)
    if not cap: raise GeometryError('Empty constrained half-space cap')
    return mesh_from_triangles(np.concatenate([shell.triangles,*cap]))


def clip_primary_component(mesh,axis,position,positive=True):
    """Detach one main lobe and retain cut-off minor exterior fragments on core.

    Both half-spaces are constructed first. Only their artificial planar caps
    are removed when rejoining minor positive pieces to the opposite half.
    No exterior triangle or component is deleted. Source faces coplanar with
    the cut are ambiguous and explicitly rejected. This adds no connectors and
    certifies neither a physical assembly nor an exhaustive absence of collision.
    """
    from .validation import require_solid
    if type(axis) is not int or axis not in (0,1,2) or not np.isfinite(position):
        raise GeometryError('A finite cut position and axis 0, 1 or 2 are required')
    if type(positive) is not bool:raise GeometryError('Cut side must be boolean')
    require_solid(mesh)
    if len(mesh.split(only_watertight=False))!=1:
        raise GeometryError('Primary-component cut requires a single connected source body')
    tolerance=max(1.,abs(float(position)))*1e-10
    def cap_mask(part):return np.all(np.abs(part.triangles[:,:,axis]-position)<=tolerance,axis=1)
    if cap_mask(mesh).any():
        raise GeometryError('Source has faces coplanar with the requested cut; choose an offset plane to preserve exterior faces')
    selected=clip_closed(mesh,axis,position,positive)
    opposite=clip_closed(mesh,axis,position,not positive)
    components=sorted(selected.split(only_watertight=False),key=lambda part:-abs(part.volume))
    for part in components:require_solid(part)
    primary=components[0];minor=components[1:]
    primary_caps=cap_mask(primary)
    if not primary_caps.any():raise GeometryError('Selected main component has no cut interface')
    if minor:
        exterior=[opposite.triangles[~cap_mask(opposite)]]
        exterior.extend(part.triangles[~cap_mask(part)] for part in minor)
        # The core gets precisely the complement of the retained main cap.
        remainder=mesh_from_triangles(np.concatenate([*exterior,primary.triangles[primary_caps][:,::-1]]))
    else:remainder=opposite
    require_solid(primary);require_solid(remainder)
    if len(primary.split(only_watertight=False))!=1 or len(remainder.split(only_watertight=False))!=1:
        raise GeometryError('Reassigned exterior fragments do not form single connected main/core solids')
    source_volume=float(mesh.volume);parts_volume=float(primary.volume+remainder.volume)
    if abs(parts_volume-source_volume)>max(.01,abs(source_volume)*1e-7):
        raise GeometryError('Primary-component cut failed volume conservation')
    exterior_area=float(primary.area_faces[~cap_mask(primary)].sum()+remainder.area_faces[~cap_mask(remainder)].sum())
    if abs(exterior_area-mesh.area)>max(.01,mesh.area*1e-7):
        raise GeometryError('Primary-component cut failed exterior surface conservation')
    return primary,remainder,{'strategy':'main component retained; minor cut fragments returned to core',
        'axis':axis,'position_mm':float(position),'positive':positive,
        'selected_components_before':len(components),'returned_fragments':len(minor),
        'returned_fragment_volumes_mm3':[float(p.volume) for p in minor],
        'source_volume_mm3':source_volume,'parts_volume_mm3':parts_volume,
        'volume_difference_mm3':parts_volume-source_volume,
        'source_exterior_area_mm2':float(mesh.area),'parts_exterior_area_mm2':exterior_area,
        'exterior_components_deleted':0,'connectors_created':False,
        'limitation':'Geometric conservation only; connectors, extraction path, physical fit and printability require separate checks.'}
