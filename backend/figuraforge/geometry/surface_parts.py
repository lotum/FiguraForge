"""Exact sampled color-boundary surface partitions.

Unlike inlays, this closes each selected color surface with shared interior caps.
Boundary vertices retain all three coordinates: a non-planar color contour is
not flattened into an infinite cut plane. This route is useful for full limbs
and circumferential color bands. It is deliberately an explicit expert mode:
multi-cap assemblies and thin decorative patches need additional review.
"""
from __future__ import annotations
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,Point,LineString
from .types import GeometryError,Part
from .construct import face_components,patch_from_faces,clean_small_islands
from .topology import boundary_loops,frame,triangulate_polygon,orient_local,mesh_from_triangles,projected_outline
from .connectors import pick_connectors,root_with_connectors
from .validation import require_solid,DistanceQuery,sample_surface,check_insert_path


def interior_cap(points):
    points=np.asarray(points,float)
    if len(points)<3: raise GeometryError('Color boundary has fewer than three vertices')
    center=points.mean(axis=0)
    _,_,axes=np.linalg.svd(points-center,full_matrices=False)
    basis=frame(axes[-1]); local=points@basis
    poly=Polygon(local[:,:2])
    if not poly.is_valid or poly.area<1e-7:
        raise GeometryError('Color boundary is not a simple projected loop; split it into smaller regions')
    # A star-shaped cap with an interior anchor avoids reusing exterior mesh
    # diagonals as interior cap edges (which would create zero-thickness ears).
    xy=local[:,:2].mean(axis=0)
    expanded=poly.buffer(1e-8)
    if expanded.covers(Point(xy)) and all(expanded.covers(LineString([xy,p])) for p in local[:,:2]):
        triangles=np.stack([points,np.repeat(center[None,:],len(points),axis=0),np.roll(points,-1,axis=0)],axis=1)
        return mesh_from_triangles(triangles,check=False)
    triangles2=triangulate_polygon(poly)
    distance,index=cKDTree(local[:,:2]).query(triangles2.reshape(-1,2))
    if distance.max()>1e-5: raise GeometryError('Cap triangulation introduced an unanchored boundary vertex')
    # Never reuse an exterior diagonal as an interior cap edge. Split every
    # internal diagonal with a genuinely inward midpoint and give each cell an
    # inward anchor. Boundary edges/vertices stay exact. Unlike a vertical
    # collar, this remains a single-valued height surface for connector clipping.
    signed=np.sum(local[:,0]*np.roll(local[:,1],-1)-np.roll(local[:,0],-1)*local[:,1])
    inward=-np.sign(signed)*basis[:,2]
    cap_indices=index.reshape(-1,3)
    edges=np.sort(np.concatenate([cap_indices[:,[0,1]],cap_indices[:,[1,2]],cap_indices[:,[2,0]]]),axis=1)
    unique,counts=np.unique(edges,axis=0,return_counts=True)
    internal={tuple(edge) for edge in unique[counts==2]}
    def pushed(point):
        distance=poly.boundary.distance(Point((point@basis)[:2]))
        depth=min(.35,float(np.sqrt(poly.area))*.025,distance*.25)
        return point+inward*depth
    midpoint={edge:pushed((points[edge[0]]+points[edge[1]])/2) for edge in internal}
    triangles=[]
    for triangle in cap_indices:
        ring=[]
        for k in range(3):
            ia=int(triangle[k]);ib=int(triangle[(k+1)%3]);ring.append(points[ia])
            edge=tuple(sorted((ia,ib)))
            if edge in midpoint:ring.append(midpoint[edge])
        anchor=pushed(points[triangle].mean(axis=0));ring=np.asarray(ring)
        triangles.extend(np.stack([ring,np.repeat(anchor[None,:],len(ring),axis=0),np.roll(ring,-1,axis=0)],axis=1))
    cap=np.asarray(triangles)@basis
    cap=orient_local(cap,positive=signed<0)
    return mesh_from_triangles(cap@basis.T,check=False)



def cut_region(mesh,labels,indexes,base_color=0,radius=2,length=5,clearance=.2,shape='keyed'):
    patch=patch_from_faces(mesh,indexes); loops=boundary_loops(patch)
    if not loops: raise GeometryError('This color region encloses an entire component; separate that component first')
    caps=[interior_cap(np.asarray(patch.vertices)[loop]) for loop in loops]
    query=DistanceQuery(mesh)
    for cap in caps:
        if query.values(sample_surface(cap,1500)).max()>.035:
            raise GeometryError('Interior color-boundary cap exits the source solid. Use inlay mode or subdivide the region.')
    # Nested coplanar caps indicate an annular inlay, not a separable whole body part.
    for i,a in enumerate(caps):
        na=np.average(a.face_normals,axis=0,weights=a.area_faces);na/=np.linalg.norm(na)
        for b in caps[i+1:]:
            if np.abs((b.vertices-a.centroid)@na).max()<.05:
                basis=frame(na)
                pa=projected_outline(a,basis);pb=projected_outline(b,basis)
                if pa.intersection(pb).area>.05:
                    raise GeometryError('Nested color boundaries require a shared inlay pocket, not independent body-part caps')
    keep=np.ones(len(mesh.faces),bool);keep[indexes]=False
    target0=mesh_from_triangles(np.concatenate([patch.triangles,*[c.triangles for c in caps]]))
    rest0=mesh_from_triangles(np.concatenate([mesh.triangles[keep],*[c.triangles[:,::-1] for c in caps]]))
    require_solid(target0);require_solid(rest0)
    rest_query=DistanceQuery(rest0)
    target_tri=[patch.triangles];rest_tri=[mesh.triangles[keep]];connections=[];directions=[];interfaces=[]
    for cap_index,cap in enumerate(caps):
        root=cap.copy();root.invert()
        n=np.average(root.face_normals,axis=0,weights=root.area_faces);n/=np.linalg.norm(n)
        basis=frame(n);outline=projected_outline(root,basis)
        connectors=pick_connectors(outline,root,basis,0,radius=radius,length=length,clearance=clearance,count=2,shape=shape)
        safe=[]
        for connector in connectors:
            tip=np.array([[connector.x,connector.y,connector.tip_z-.35]])@basis.T
            if rest_query.values(tip)[0]<-(radius+.5):safe.append(connector)
        target_tri.append(root_with_connectors(root,basis,safe,socket=False))
        rest_tri.append(root_with_connectors(root,basis,safe,socket=True))
        for connector in safe:
            item=connector.summary(basis);item['interface']=cap_index;connections.append(item)
        directions.append(n.tolist());interfaces.append({'index':cap_index,'direction':n.tolist(),'area_mm2':float(cap.area),'connectors':len(safe)})
    target=mesh_from_triangles(np.concatenate(target_tri));remainder=mesh_from_triangles(np.concatenate(rest_tri))
    require_solid(target);require_solid(remainder)
    if abs((target0.volume+rest0.volume)-mesh.volume)>max(.01,mesh.volume*1e-7):
        raise GeometryError('Color partition failed volume conservation')
    if target.volume+remainder.volume>mesh.volume+max(.01,mesh.volume*1e-6):
        raise GeometryError('Connected parts exceed original volume; possible cap overlap')
    # Preserve original exterior color IDs, label new hidden interfaces as core.
    before=np.concatenate(rest_tri)
    before_labels=np.r_[labels[keep],np.full(sum(len(t) for t in rest_tri[1:]),base_color,int)]
    dist,mapping=cKDTree(before.mean(axis=1)).query(remainder.triangles_center)
    if dist.max()>1e-5:raise GeometryError('Failed to transfer exterior labels after partition')
    return target,remainder,before_labels[mapping],connections,interfaces


def make_surface_parts(mesh,labels,palette,base_color=0,pin_radius_mm=2,pin_length_mm=5,
                       pin_clearance_mm=.2,connector_shape='keyed',min_region_area_mm2=3,
                       validate_paths=True,progress=None,**ignored):
    require_solid(mesh);source=mesh.copy();remaining=mesh.copy()
    labels,merged=clean_small_islands(mesh,np.asarray(labels),min_region_area_mm2)
    parts=[];reports=[];iteration=0
    while np.any(labels!=base_color):
        iteration+=1
        if iteration>100:raise GeometryError('More than 100 color regions; simplify the palette or increase the island filter')
        colors=np.unique(labels[labels!=base_color])
        color=max(colors,key=lambda c:remaining.area_faces[labels==c].sum())
        components=face_components(remaining,labels==color)
        indexes=max(components,key=lambda i:remaining.area_faces[i].sum())
        if progress:progress(f'Ganzteil entlang der organischen Farbgrenze: {iteration}')
        target,remaining,labels,connectors,interfaces=cut_region(remaining,labels,indexes,base_color,
                    pin_radius_mm,pin_length_mm,pin_clearance_mm,connector_shape)
        warnings=['Shared color-boundary caps have no surface gap. Confirm physical fit and assembly sequence.']
        direction=interfaces[0]['direction'] if len(interfaces)==1 else None
        if len(interfaces)>1:warnings.append('Multiple connection directions: assemble neighboring parts sequentially. No single straight extraction path is certified.')
        if not connectors:warnings.append('No safe structural connector fits. Retention requires manual construction or a different partition.')
        mean_depth=abs(target.volume)/max(target.area/2,1e-8)
        if mean_depth<1.:warnings.append('Thin color part: volume/area thickness proxy is below 1 mm. Use the inlay strategy for decorative surface patches.')
        checks=None
        if validate_paths and direction:
            # This validates extraction from the current remainder, not all final assembly sequences.
            travel=max(pin_length_mm+3,min(30,float(target.extents.max())))
            checks=check_insert_path(target,remaining,direction,travel_mm=travel)
            if not checks['passed']:raise GeometryError('Whole color part cannot be extracted along the proposed interface direction')
        part=Part(f'color-{iteration:03d}',f'Farbkoerper {iteration:02d}',target,palette[int(color)],int(color),'color-body',direction,connectors,warnings)
        parts.append(part);reports.append({'part_id':part.id,'interfaces':interfaces,'path_check':checks,'thickness_proxy_mm':mean_depth})
    for i,component in enumerate(remaining.split(only_watertight=False)):
        require_solid(component)
        parts.insert(0,Part('body' if i==0 else f'body-{i:03d}','Grundkoerper' if i==0 else f'Grundkoerper {i+1}',component,palette[base_color],base_color,'body',warnings=['Check access and assembly order for color-boundary connections.']))
    return parts,{'strategy':'shared non-planar boundary caps','source_volume_mm3':float(source.volume),
                  'parts_volume_mm3':float(sum(p.mesh.volume for p in parts)),'merged_islands':merged,
                  'interfaces':reports,'pockets':[], 'insertion_checks':[r['path_check'] for r in reports if r['path_check']],
                  'limitation':'Expert strategy. Color labels are not semantic anatomy; non-projectable loops, crossing caps and assembly sequencing may require manual intervention.'}
