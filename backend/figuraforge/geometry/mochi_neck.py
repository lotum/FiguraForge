"""Geometric neck cut with a shared curved seam, flat inner seat and loose key.

Explicit source-bound construction, not general anatomical recognition. Source
exterior triangles and their native Bambu paint strings are retained. A complex
painted triangle crossing the seam is rejected instead of silently repainted.
"""
from __future__ import annotations
import numpy as np
import trimesh
from shapely.geometry import Polygon,Point
from shapely.affinity import scale as scale_polygon,translate
from .topology import boundary_loops,triangulate_polygon,orient_local
from .types import GeometryError


def labelled_mesh(triangles,paint):
    t=np.asarray(triangles,float).reshape(-1,3,3);p=np.asarray(paint,dtype=object)
    if len(t)!=len(p):raise GeometryError('Paint/triangle count mismatch')
    mesh=trimesh.Trimesh(t.reshape(-1,3),np.arange(len(t)*3).reshape(-1,3),process=False)
    mesh.merge_vertices(digits_vertex=7);keep=mesh.nondegenerate_faces(height=1e-8);mesh.update_faces(keep);mesh.remove_unreferenced_vertices()
    return mesh,p[keep].tolist()


def clipped_shell(mesh,paint,values,positive):
    signed=values[mesh.faces]*(1 if positive else -1);inside=signed>=0
    whole=np.flatnonzero(inside.all(axis=1));tris=[mesh.triangles[whole]];colors=[np.asarray(paint,dtype=object)[whole]]
    clipped=[]
    for i in np.flatnonzero(inside.any(axis=1)&~inside.all(axis=1)):
        if paint[i] not in ('4','8'):raise GeometryError('Complex painted triangle crosses the neck seam; explicit subtriangle clipping required')
        tri=mesh.triangles[i];dist=signed[i];flags=inside[i];ring=[]
        for j in range(3):
            a,b=tri[j-1],tri[j];ia,ib=flags[j-1],flags[j]
            if ia!=ib:ring.append(a+(b-a)*dist[j-1]/(dist[j-1]-dist[j]))
            if ib:ring.append(b)
        fan=np.array([[ring[0],ring[j],ring[j+1]] for j in range(1,len(ring)-1)])
        tris.append(fan);colors.append(np.repeat(paint[i],len(fan)));clipped.append(int(i))
    shell,p=labelled_mesh(np.concatenate(tris),np.concatenate(colors))
    return shell,p,clipped


def field(xy,coefficients,center=(0.,-27.),landing_z=108.):
    x,y=np.asarray(xy).T;a,b,c,d,e,f=coefficients
    curved=a+b*x+c*y+d*x*x+e*x*y+f*y*y
    r=np.sqrt(((x-center[0])/27)**2+((y-center[1])/18)**2)
    t=np.clip((r-.55)/.33,0,1);t=t*t*(3-2*t)
    return landing_z+(curved-landing_z)*t


def profile(center,scale_factor,*,clearance=0.):
    # One large clipped corner makes the key asymmetric, including 180 degrees.
    w,d=10.,14.;c=2.;large=6.
    p=Polygon([[-w+c,-d],[w-c,-d],[w,-d+c],[w,d-large],[w-large,d],[-w+c,d],[-w,d-c],[-w,-d+c]])
    if clearance:p=p.buffer(clearance,join_style=2)
    return translate(scale_polygon(p,xfact=1/scale_factor,yfact=1/scale_factor,origin=(0,0)),*center)


def cap_and_socket(outline,boundary,*,center,coefficients,scale_factor,head,landing_z=108.,clearance_mm=.10,engagement_mm=18.,tip_gap_mm=.6):
    land=translate(scale_polygon(Point(0,0).buffer(1,quad_segs=16),xfact=12.,yfact=8.,origin=(0,0)),*center)
    socket=profile(center,scale_factor,clearance=clearance_mm)
    if not outline.buffer(-1.).covers(land) or not land.buffer(-.5).covers(socket):raise GeometryError('Safe internal neck landing/key footprint does not fit')
    lookup={tuple(np.round(p[:2],8)):p[2] for p in boundary}
    lookup.update({tuple(np.round(p,8)):landing_z for p in np.asarray(land.exterior.coords)[:-1]})
    pieces=[]
    for poly in [outline.difference(land),land.difference(socket)]:
        for poly in ([poly] if poly.geom_type=='Polygon' else poly.geoms):
            xy=triangulate_polygon(poly);z=[]
            for p in xy.reshape(-1,2):
                key=tuple(np.round(p,8))
                if key in lookup:z.append(lookup[key])
                elif socket.boundary.distance(Point(p))<1e-7:z.append(landing_z)
                else:raise GeometryError('Unexpected cap triangulation vertex')
            t=np.concatenate([xy,np.asarray(z).reshape(-1,3,1)],axis=2);pieces.append(orient_local(t,positive=not head))
    xy=np.asarray(socket.exterior.coords)[:-1]
    # Shapely buffers can reverse winding; cavity rings must be CCW.
    if not socket.exterior.is_ccw:xy=xy[::-1]
    end=landing_z+(1 if head else -1)*(engagement_mm+tip_gap_mm)/scale_factor
    lower,upper=sorted([landing_z,end]);low=np.column_stack([xy,np.repeat(lower,len(xy))]);high=np.column_stack([xy,np.repeat(upper,len(xy))])
    walls=[]
    for i in range(len(xy)):
        j=(i+1)%len(xy);walls.extend([[low[i],high[i],high[j]],[low[i],high[j],low[j]]])
    pieces.append(np.asarray(walls))
    if head:
        # Roof rises at least 45 degrees above the build plane: no wide flat ceiling.
        edges=np.roll(xy,-1,axis=0)-xy;vectors=np.asarray(center)-xy
        distances=np.abs(edges[:,0]*vectors[:,1]-edges[:,1]*vectors[:,0])/np.linalg.norm(edges,axis=1)
        roof_height=float(distances.max())+.5/scale_factor;apex=np.array([*center,end+roof_height]);roof=[]
        for i in range(len(xy)):roof.append([high[i],apex,high[(i+1)%len(xy)]])
        pieces.append(np.asarray(roof))
    else:
        xytri=triangulate_polygon(socket);pieces.append(orient_local(np.concatenate([xytri,np.full((*xytri.shape[:2],1),end)],axis=2),True))
    return np.concatenate(pieces),{'radial_clearance_mm':clearance_mm,'engagement_mm':engagement_mm,'tip_gap_mm':tip_gap_mm,'head_self_supporting_roof_mm':roof_height*scale_factor if head else None,'socket_outline_source_xy':xy.tolist(),'socket_end_source_z':end}


def loose_key(center,scale_factor,*,landing_z=108.,engagement_mm=18.):
    poly=profile(center,scale_factor);xy=np.asarray(poly.exterior.coords)[:-1]
    if not poly.exterior.is_ccw:xy=xy[::-1]
    middle=np.asarray(center);tipxy=middle+(xy-middle)*(1-.8/10.)
    rings=[]
    for z,ring in [(-engagement_mm,tipxy),(-engagement_mm+1.5,xy),(engagement_mm-1.5,xy),(engagement_mm,tipxy)]:rings.append(np.column_stack([ring,np.repeat(landing_z+z/scale_factor,len(xy))]))
    triangles=[]
    for low,high in zip(rings,rings[1:]):
        for i in range(len(xy)):
            j=(i+1)%len(xy);triangles.extend([[low[i],low[j],high[j]],[low[i],high[j],high[i]]])
    for ring,positive in [(rings[0],False),(rings[-1],True)]:
        tr=triangulate_polygon(Polygon(ring[:,:2]));triangles.extend(orient_local(np.concatenate([tr,np.full((*tr.shape[:2],1),ring[0,2])],axis=2),positive))
    mesh,paint=labelled_mesh(triangles,['0C']*len(triangles));return mesh,paint


def split_neck(mesh,paint,coefficients,scale_factor):
    values=mesh.vertices[:,2]-field(mesh.vertices[:,:2],coefficients);low,lp,cut=clipped_shell(mesh,paint,values,False);high,hp,_=clipped_shell(mesh,paint,values,True)
    loops=boundary_loops(low)
    if len(loops)!=1:raise GeometryError('Geometric neck cut must have exactly one closed boundary')
    boundary=low.vertices[loops[0]];outline=Polygon(boundary[:,:2])
    if not outline.is_valid:raise GeometryError('Neck contour is not single-valued in insertion direction')
    rows=[]
    for shell,p,head in [(low,lp,False),(high,hp,True)]:
        cap,report=cap_and_socket(outline,boundary,center=(0.,-27.),coefficients=coefficients,scale_factor=scale_factor,head=head)
        part,colors=labelled_mesh(np.concatenate([shell.triangles,cap]),p+['4']*len(cap))
        if not part.is_volume or len(part.split(only_watertight=False))!=1:raise GeometryError('Constructed neck part is not one closed solid')
        rows.append((part,colors,report))
    key,kp=loose_key((0.,-27.),scale_factor)
    if not key.is_volume:raise GeometryError('Loose key is not a closed solid')
    return rows[0],rows[1],(key,kp),{'source_scale_factor':float(scale_factor),'cut_source_faces':cut,'boundary_source':boundary.tolist(),'source_valley_quadratic':coefficients,'landing_z_source':108.,'asymmetric_key_mm':[20,28,36],'assembly_direction':[0,0,1],'cap_outline_area_source_mm2':outline.area}
