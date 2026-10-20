"""Reproducible engineering preset for the inspected 180 mm Mochi reference.

This model-bound proposal must be reviewed; it is not generic semantic anatomy.
No project state, approval, source vertices or source colors are changed.
"""
import hashlib
import numpy as np
from .anatomical import anatomical_seed_cut,seed_geodesic_faces
from .construct import face_components
from .types import GeometryError

REFERENCE_SIGNATURE='2449e3b7215d04bbb5c2143139245e1b92eac858de42b8fa9227d3b2353396af'


def geometry_signature(mesh):
    return hashlib.sha256(np.asarray(mesh.vertices,dtype='<f8').round(6).tobytes()+np.asarray(mesh.faces,dtype='<i8').tobytes()).hexdigest()


def mochi_masks(surface,plan):
    """Return (mask_dict, report) using only current source geometry/color plan.

    Dictionary values are original face-index arrays. Whole-part keys: tail,
    right-ear, left-ear, nose. Additional eye-N keys are decorative inlay masks.
    Geometry and subsequent cap/connector/path checks remain separate.
    """
    mesh=surface.mesh
    if geometry_signature(mesh)!=REFERENCE_SIGNATURE:
        raise GeometryError('Mochi preset requires the verified 180 mm reference working copy; another source/scale must be analyzed separately')
    if hasattr(plan,'model_dump'):plan=plan.model_dump()
    labels=np.asarray(plan.get('face_regions',[]))
    if labels.shape!=(len(mesh.faces),) or not np.issubdtype(labels.dtype,np.integer):
        raise GeometryError('Mochi reference color plan does not match the working copy')
    if int(np.sum(labels==2))!=26833 or int(np.sum(labels==3))!=202:
        raise GeometryError('Mochi reference preset needs the original cream/dark analysis regions; edited regions require a new reviewed analysis')
    centers=mesh.triangles_center;areas=mesh.area_faces
    def centroid(ids):return np.average(centers[ids],axis=0,weights=areas[ids])
    cream=face_components(mesh,labels==2)
    tail_components=[ids for ids in cream if areas[ids].sum()>100 and centroid(ids)[1]>10 and centroid(ids)[2]<60]
    if not tail_components:raise GeometryError('No proximal tail reference component found')
    proximal=min(tail_components,key=lambda ids:centroid(ids)[1])
    tail_seed=np.unique(np.r_[np.flatnonzero(centers[:,1]>25),proximal])
    tail_core=np.flatnonzero((centers[:,2]>85)|((centers[:,1]<-15)&(centers[:,2]>3)))
    masks={};reports={}
    masks['tail'],reports['tail']=anatomical_seed_cut(mesh,tail_seed,tail_core,smoothing_iterations=30,concavity_scale=.06)
    for sign,name,iterations,sigma in [(1,'right-ear',40,.03),(-1,'left-ear',10,.08)]:
        candidates=[ids for ids in cream if centroid(ids)[0]*sign>20 and centroid(ids)[2]>145 and centroid(ids)[1]>-40]
        if not candidates:raise GeometryError('No inner-ear reference component found')
        inner=max(candidates,key=lambda ids:areas[ids].sum())
        seed=seed_geodesic_faces(mesh,inner,2)
        core=np.flatnonzero((centers[:,2]<120)|((np.abs(centers[:,0])<12)&(centers[:,2]<165)))
        seed=np.setdiff1d(seed,core)
        masks[name],reports[name]=anatomical_seed_cut(mesh,seed,core,smoothing_iterations=iterations,concavity_scale=sigma)
    nose_seed=np.flatnonzero((labels==3)&(centers[:,1]<-62)&(centers[:,2]>120)&(centers[:,2]<135)&(np.abs(centers[:,0])<7))
    domain=seed_geodesic_faces(mesh,nose_seed,2)
    core=np.setdiff1d(np.arange(len(mesh.faces)),domain)
    masks['nose'],reports['nose']=anatomical_seed_cut(mesh,nose_seed,core,smoothing_iterations=30,concavity_scale=.06)
    eyes=[]
    for ids in face_components(mesh,labels==3):
        center=centroid(ids)
        if areas[ids].sum()>=3 and center[1]<-45 and 134<center[2]<145:eyes.append(ids)
    eyes.sort(key=lambda ids:(centroid(ids)[0],centroid(ids)[2]))
    for index,ids in enumerate(eyes,1):masks[f'eye-{index}']=ids
    occupied=np.zeros(len(mesh.faces),dtype=np.uint8)
    for name,ids in masks.items():
        if occupied[ids].any():raise GeometryError(f'Anatomical proposals overlap at {name}; review required')
        occupied[ids]=1
    if geometry_signature(mesh)!=REFERENCE_SIGNATURE:raise GeometryError('Anatomical analysis changed source geometry; proposal rejected')
    return masks,{'source_signature':REFERENCE_SIGNATURE,'whole_part_keys':['tail','right-ear','left-ear','nose'],
        'eye_part_keys':[f'eye-{i}' for i in range(1,len(eyes)+1)],'seed_parameters_mm':{'tail_distal_y':25,'ear_geodesic_growth':2,'nose_geodesic_domain':2},
        'cuts':reports,'original_geometry_modified':False,'automatic_approval':False,
        'limitation':'Model-bound local proposal. Anatomical boundary, texture/material assignment and print/assembly checks remain required; smoothing only affects analysis.'}
