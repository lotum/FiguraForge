from __future__ import annotations
import numpy as np
import trimesh
import shapely
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.ops import unary_union, polygonize
from .types import GeometryError


def mesh_from_triangles(triangles: np.ndarray, check=True) -> trimesh.Trimesh:
    t=np.asarray(triangles,float).reshape(-1,3,3)
    if not len(t): raise GeometryError('Operation produced an empty mesh')
    m=trimesh.Trimesh(t.reshape(-1,3),np.arange(len(t)*3).reshape(-1,3),process=False)
    m.merge_vertices(digits_vertex=6)
    m.update_faces(m.nondegenerate_faces(height=1e-8))
    m.remove_unreferenced_vertices()
    if check and not m.is_watertight:
        raise GeometryError(f'Constructed mesh is not closed ({len(m.faces)} triangles)')
    if m.is_watertight and m.volume<0: m.invert()
    return m


def frame(normal: np.ndarray) -> np.ndarray:
    n=np.asarray(normal,float); n/=np.linalg.norm(n)
    anchor=np.eye(3)[np.argmin(np.abs(n))]
    u=np.cross(anchor,n); u/=np.linalg.norm(u); v=np.cross(n,u)
    return np.column_stack([u,v,n])


def directed_boundary(mesh: trimesh.Trimesh) -> np.ndarray:
    f=np.asarray(mesh.faces)
    edges=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    sort=np.sort(edges,axis=1)
    _,idx,count=np.unique(sort,axis=0,return_index=True,return_counts=True)
    if (count>2).any(): raise GeometryError('Non-manifold edges in surface patch')
    return edges[idx[count==1]]


def boundary_loops(mesh: trimesh.Trimesh) -> list[np.ndarray]:
    edges=directed_boundary(mesh)
    if not len(edges): return []
    links={}
    for a,b in edges:
        if int(a) in links: raise GeometryError('Boundary has a branching vertex; simplify the color island')
        links[int(a)]=int(b)
    loops=[]
    while links:
        start=next(iter(links)); cur=start; loop=[]
        for _ in range(len(edges)+1):
            loop.append(cur)
            if cur not in links: raise GeometryError('Boundary loop is open')
            cur=links.pop(cur)
            if cur==start: break
        else: raise GeometryError('Boundary loop did not close')
        loops.append(np.array(loop))
    return loops


def projected_outline(patch: trimesh.Trimesh, basis: np.ndarray):
    local=patch.vertices @ basis
    loops=boundary_loops(patch)
    if not loops: raise GeometryError('The selected surface has no boundary')
    # Even/odd fill supports holes and nested contours.
    result=Polygon()
    for loop in loops:
        p=Polygon(local[loop,:2])
        if not p.is_valid:
            raise GeometryError('The region folds over itself in the assembly direction; choose a different direction or split it')
        if p.area>1e-8: result=result.symmetric_difference(p)
    if result.is_empty or not result.is_valid: raise GeometryError('Invalid projected region outline')
    a=local[patch.faces][:,1,:2]-local[patch.faces][:,0,:2]
    b=local[patch.faces][:,2,:2]-local[patch.faces][:,0,:2]
    projected_area=np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]).sum()/2
    if projected_area>result.area*1.005:
        raise GeometryError('The surface is not single-valued along the assembly direction (undercut)')
    return result


def polygons(g):
    if isinstance(g,Polygon): return [g] if not g.is_empty else []
    if hasattr(g,'geoms'): return [p for q in g.geoms for p in polygons(q)]
    return []


def triangulate_polygon(poly: Polygon) -> np.ndarray:
    if poly.area<1e-10: return np.empty((0,3,2))
    tris=shapely.constrained_delaunay_triangles(poly)
    return np.array([np.asarray(t.exterior.coords)[:3,:2] for t in tris.geoms if t.area>1e-10])


def orient_local(t: np.ndarray, positive=True) -> np.ndarray:
    if not len(t): return t
    signed=(t[:,1,0]-t[:,0,0])*(t[:,2,1]-t[:,0,1])-(t[:,1,1]-t[:,0,1])*(t[:,2,0]-t[:,0,0])
    flip=signed<0 if positive else signed>0
    t=t.copy(); t[flip]=t[flip][:,[0,2,1]]
    return t


def clip_surface(patch: trimesh.Trimesh, basis: np.ndarray, keep=None, holes=None) -> np.ndarray:
    """Clip projected triangles; lift each result to its original 3D triangle.

    Visible geometry is not flattened. Exact existing triangle planes are kept.
    """
    local=patch.triangles @ basis
    out=[]
    for tri in local:
        p=Polygon(tri[:,:2])
        if p.area<1e-10: raise GeometryError('Surface contains a face perpendicular to the insertion direction')
        g=p if keep is None else p.intersection(keep)
        if holes is not None and not holes.is_empty: g=g.difference(holes)
        for poly in polygons(g):
            pts=triangulate_polygon(poly)
            if not len(pts): continue
            xy=pts.reshape(-1,2)
            # Barycentric lifting works across non-planar patch boundaries.
            matrix=np.column_stack([tri[1,:2]-tri[0,:2],tri[2,:2]-tri[0,:2]])
            uv=np.linalg.solve(matrix,(xy-tri[0,:2]).T).T
            z=tri[0,2]+uv[:,0]*(tri[1,2]-tri[0,2])+uv[:,1]*(tri[2,2]-tri[0,2])
            lifted=np.c_[xy,z].reshape(-1,3,3)
            out.append(orient_local(lifted,True) @ basis.T)
    if not out: raise GeometryError('Clipping removed the whole patch')
    return np.concatenate(out)


def side_triangles(patch: trimesh.Trimesh, vector: np.ndarray) -> np.ndarray:
    edges=directed_boundary(patch)
    a=patch.vertices[edges[:,0]]; b=patch.vertices[edges[:,1]]
    # Outward walls of a solid extending opposite its top-face normals.
    return np.concatenate([np.stack([a,a+vector,b+vector],axis=1),
                           np.stack([a,b+vector,b],axis=1)])


def signed_volume(triangles):
    t=np.asarray(triangles)
    return np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6
