from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union, polylabel
import trimesh
from .topology import boundary_loops, triangulate_polygon, orient_local, clip_surface, mesh_from_triangles, polygons
from .types import GeometryError


@dataclass
class Connector:
    x: float
    y: float
    radius: float
    length: float
    tip_z: float
    shape: str='round'
    clearance: float=.20
    tip_clearance: float=.35

    def profile(self, socket=False):
        r=self.radius+(self.clearance if socket else 0)
        if self.shape=='keyed':
            # Chamfered square, not an aggressive undercut snap-fit.
            pts=np.array([[-.7,-1],[.7,-1],[1,-.7],[1,.7],[.7,1],[-.7,1],[-1,.7],[-1,-.7]])*r
            return Polygon(pts+[self.x,self.y])
        return Point(self.x,self.y).buffer(r,quad_segs=8)

    def summary(self,basis):
        return {'shape':self.shape,'diameter_mm':round(self.radius*2,3),
                'nominal_length_mm':self.length,'radial_clearance_mm':self.clearance,
                'position_mm':np.round(np.array([self.x,self.y,self.tip_z])@basis.T,3).tolist(),
                'requires_calibration':True}


def pick_connectors(outline, top_patch, basis, depth:float, radius=1.6,length=5.0,
                    clearance=.2,count=2,shape='round',wall=1.0) -> list[Connector]:
    inner=outline.buffer(-(radius+clearance+wall))
    if inner.is_empty: return []
    components=sorted(polygons(inner),key=lambda p:-p.area)
    candidates=[]
    for poly in components:
        p=polylabel(poly,tolerance=.3); candidates.append([p.x,p.y])
        x0,y0,x1,y1=poly.bounds
        for x in np.linspace(x0,x1,9):
            for y in np.linspace(y0,y1,9):
                if poly.contains(Point(x,y)): candidates.append([x,y])
    if not candidates: return []
    # A keyed pin is a chamfered square: its corners extend beyond the nominal
    # half-width. A circular center margin alone does not preserve wall stock.
    # Check the real socket footprint, including the requested wall allowance.
    safe_outline=outline.buffer(-wall)
    candidates=[p for p in candidates if safe_outline.covers(
        Connector(float(p[0]),float(p[1]),radius,length,0,shape,clearance).profile(socket=True))]
    if not candidates:return []
    points=np.array(candidates)
    edge=np.array([outline.boundary.distance(Point(p)) for p in points])
    chosen=[int(np.argmax(edge))]
    for _ in range(1,count):
        dist=np.min(np.linalg.norm(points[:,None]-points[chosen][None],axis=2),axis=1)
        i=int(np.argmax(dist + .1*edge))
        if dist[i]<radius*4+3: break
        chosen.append(i)
    local=top_patch.triangles@basis
    result=[]
    for i in chosen:
        xy=points[i]; z=None
        for tri in local:
            mat=np.column_stack([tri[1,:2]-tri[0,:2],tri[2,:2]-tri[0,:2]])
            if abs(np.linalg.det(mat))<1e-10: continue
            uv=np.linalg.solve(mat,xy-tri[0,:2])
            if min(uv)>=-1e-7 and uv.sum()<=1+1e-7:
                z=tri[0,2]+uv[0]*(tri[1,2]-tri[0,2])+uv[1]*(tri[2,2]-tri[0,2]); break
        if z is None: continue
        result.append(Connector(float(xy[0]),float(xy[1]),radius,length,float(z-depth-length),shape,clearance))
    return result


def root_with_connectors(root_patch:trimesh.Trimesh, basis:np.ndarray,
                         connectors:list[Connector],socket=False) -> np.ndarray:
    """Replace root disks by pin/socket walls and caps, without mesh booleans.

    root_patch has positive insertion-axis normal. Returned socket roots have
    positive orientation; male roots face negative insertion-axis.
    """
    if not connectors:
        return root_patch.triangles.copy() if socket else root_patch.triangles[:,::-1].copy()
    footprints=unary_union([c.profile(socket) for c in connectors])
    root_tri=clip_surface(root_patch,basis,holes=footprints)
    root=mesh_from_triangles(root_tri,check=False)
    loops=boundary_loops(root)
    surfaces=[root_tri if socket else root_tri[:,::-1]]
    used=set()
    for loop in loops:
        world=np.asarray(root.vertices)[loop]
        p=world@basis
        poly=Polygon(p[:,:2])
        if poly.area<1e-10: continue
        match=None
        for j,c in enumerate(connectors):
            shape=c.profile(socket)
            # A root footprint may be split into extra vertices by surface edges.
            if poly.symmetric_difference(shape).area < max(.02,shape.area*.005):
                match=(j,c); break
        if match is None: continue
        j,c=match; used.add(j)
        tip=p.copy()
        scale=1.0 if socket else .85
        tip[:,:2]=np.array([c.x,c.y])+(tip[:,:2]-[c.x,c.y])*scale
        tip[:,2]=c.tip_z-(c.tip_clearance if socket else 0)
        # The root follows the curved back of the inlay; the tip is planar.
        if tip[0,2]>=p[:,2].min()-.25:
            raise GeometryError('Connector length is too short for the curved root')
        a=p; b=np.roll(p,-1,axis=0); at=tip; bt=np.roll(tip,-1,axis=0)
        walls=np.concatenate([np.stack([a,at,bt],axis=1),np.stack([a,bt,b],axis=1)])
        if not socket: walls=walls[:,::-1]
        caps=triangulate_polygon(Polygon(tip[:,:2]))
        cap3=np.dstack([caps,np.full(caps.shape[:2],tip[0,2])])
        cap3=orient_local(cap3,positive=socket)
        surfaces.extend([walls@basis.T,cap3@basis.T])
    if len(used)!=len(connectors):
        raise GeometryError('A connector footprint touches or crosses the patch boundary')
    return np.concatenate(surfaces)
