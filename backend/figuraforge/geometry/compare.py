"""Sampled shape and albedo comparison; not exhaustive certification."""
from pathlib import Path
import time
import numpy as np
from .io import load_surface
from .types import Surface
from .validation import to_vtk,validate_mesh
from .colors import delta_e_2000,srgb_to_lab,choose_palette,classify

def colors_at(surface,ids,bary):
    uv=np.einsum('nvc,nv->nc',surface.corner_uv[ids],bary)
    rgb=np.einsum('nvc,nv->nc',surface.corner_rgb[ids],bary)
    proxy=Surface(surface.mesh,np.repeat(uv[:,None,:],3,axis=1),np.repeat(rgb[:,None,:],3,axis=1),
                  surface.material_ids[ids],surface.textures,surface.factors)
    return proxy.sample()


def sampled(surface,count,rng):
    area=surface.mesh.area_faces;ids=rng.choice(len(area),count,p=area/area.sum())
    uv=rng.random((count,2));uv[uv.sum(axis=1)>1]=1-uv[uv.sum(axis=1)>1]
    bary=np.column_stack([1-uv.sum(axis=1),uv])
    return np.einsum('nvc,nv->nc',surface.mesh.triangles[ids],bary),ids,bary


def nearest(surface,points):
    import vtk
    locator=vtk.vtkStaticCellLocator();locator.SetDataSet(to_vtk(surface.mesh));locator.BuildLocator()
    cell=vtk.reference(0);sub=vtk.reference(0);dist=vtk.reference(0.);closest=[0.,0.,0.]
    ids=[];coords=[];distances=[]
    for point in points:
        locator.FindClosestPoint(point,closest,cell,sub,dist)
        ids.append(int(cell));coords.append(tuple(closest));distances.append(float(dist)**.5)
    ids=np.asarray(ids);coords=np.asarray(coords)
    import trimesh
    bary=trimesh.triangles.points_to_barycentric(surface.mesh.triangles[ids],coords)
    return np.asarray(distances),ids,bary


def compare(original,working,height=1000,count=6000,up_axis='Y'):
    started=time.monotonic();a=load_surface(Path(original),height,up_axis,max_faces=4_000_000);b=load_surface(Path(working),height,up_axis)
    rng=np.random.default_rng(405)
    points,ids,bary=sampled(a,count,rng);dist,other_ids,other_bary=nearest(b,points)
    ca=colors_at(a,ids,bary);cb=colors_at(b,other_ids,other_bary)
    de=delta_e_2000(srgb_to_lab(ca),srgb_to_lab(cb))
    reverse_points,_,_=sampled(b,count,rng);reverse,_,_=nearest(a,reverse_points)
    distance=np.r_[dist,reverse];palette=choose_palette(a.sample(),6,weights=a.mesh.area_faces)
    report={'original':validate_mesh(a.mesh),'working':validate_mesh(b.mesh),'height_mm':height,
            'samples_each_direction':count,'geometry_distance_mm':{'median':float(np.median(distance)),
            'p99':float(np.quantile(distance,.99)),'max_sampled':float(distance.max())},
            'albedo_delta_e_2000':{'median':float(np.median(de)),'p95':float(np.quantile(de,.95)),
            'p99':float(np.quantile(de,.99))},
            'six_color_label_disagreement_fraction':float(np.mean(classify(ca,palette)!=classify(cb,palette))),
            'palette':palette,'seconds':round(time.monotonic()-started,3),
            'limitation':'Finite area-weighted samples, not exhaustive Hausdorff, texture or self-intersection certification.'}
    return report


def unchanged_source_faces(surface,mesh,face_ids,*,tolerance_mm=1e-6):
    """Identify unchanged source triangles, independent of corner permutation.

    ``face_ids`` are candidate source-face IDs from ``nearest``. Every corner
    must match a distinct source corner within the tolerance; centroid proximity
    alone cannot classify a newly generated near-surface pocket/cap as exterior.
    Returns one boolean per part triangle. Use only where construction preserves
    the source exterior triangles; refined, tiled or eroded faces need their own
    provenance/distance mapping. This helper does not certify global coverage.
    """
    from itertools import permutations
    from .types import GeometryError
    ids=np.asarray(face_ids)
    if (ids.shape!=(len(mesh.faces),) or not np.issubdtype(ids.dtype,np.integer)
            or (ids<0).any() or (ids>=len(surface.mesh.faces)).any()):
        raise GeometryError('Original-face identity requires one valid source triangle candidate per part face')
    try:tolerance=float(tolerance_mm)
    except (TypeError,ValueError):raise GeometryError('Original-face corner tolerance must be finite and positive') from None
    if not np.isfinite(tolerance) or tolerance<=0:
        raise GeometryError('Original-face corner tolerance must be finite and positive')
    result=np.zeros(len(ids),bool);squared=tolerance*tolerance
    for start in range(0,len(ids),8192):
        stop=min(start+8192,len(ids));actual=mesh.vertices[mesh.faces[start:stop]]
        expected=surface.mesh.vertices[surface.mesh.faces[ids[start:stop]]]
        matched=np.zeros(stop-start,bool)
        for order in permutations(range(3)):
            delta=actual-expected[:,order,:]
            matched|=(np.einsum('fvc,fvc->fv',delta,delta)<=squared).all(axis=1)
        result[start:stop]=matched
    return result
