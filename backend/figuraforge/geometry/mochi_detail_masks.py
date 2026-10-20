"""Reproducible engineering preset for the inspected 180 mm Mochi reference.

This model-bound proposal must be reviewed; it is not generic semantic anatomy.
No project state, approval, source vertices or source colors are changed.
"""
import hashlib
import numpy as np
from .anatomical import anatomical_seed_cut,seed_geodesic_faces
from .construct import face_components
from .types import GeometryError

REFERENCE_SIGNATURE='1d03ad837398f2c0a9cee65884f2091064ca210ff8981a85e9006e6e9f590675'
REFERENCE_PART_MASKS_SHA256='c5cce0376d6c66fa26d750580f8d5b60d39970b0c31c9000b813fc6fe884b979'
REFERENCE_CLASSES_SHA256='30300ff10765421f0c39c08f03045d4c37c42864b23913d530f7c39efa478d22'


def geometry_signature(mesh):
    return hashlib.sha256(np.asarray(mesh.vertices,dtype='<f8').round(6).tobytes()+np.asarray(mesh.faces,dtype='<i8').tobytes()).hexdigest()


def mochi_detail_masks(surface,plan):
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
    if hashlib.sha256(labels.astype('<u4').tobytes()).hexdigest()!=REFERENCE_CLASSES_SHA256:
        raise GeometryError('Mochi detail-v2 needs the exact reviewed new source-class mask hash; edited masks require a new analysis')
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
    for sign,name,iterations,sigma in [(1,'right-ear',40,.03),(-1,'left-ear',30,.06)]:
        candidates=[ids for ids in cream if centroid(ids)[0]*sign>20 and centroid(ids)[2]>145 and centroid(ids)[1]>-40]
        if not candidates:raise GeometryError('No inner-ear reference component found')
        inner=max(candidates,key=lambda ids:areas[ids].sum())
        seed=seed_geodesic_faces(mesh,inner,2)
        core=np.flatnonzero((centers[:,2]<120)|((np.abs(centers[:,0])<12)&(centers[:,2]<165)))
        seed=np.setdiff1d(seed,core)
        masks[name],reports[name]=anatomical_seed_cut(mesh,seed,core,smoothing_iterations=iterations,concavity_scale=sigma)
    nose_seed=np.flatnonzero((labels==3)&(centers[:,1]<-62)&(centers[:,2]>124)&(centers[:,2]<135)&(np.abs(centers[:,0])<7))
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
    semantic=np.zeros(len(mesh.faces),dtype='<u4')
    for region_id,key in enumerate(['nose','right-ear','left-ear','tail','eye-1','eye-2','eye-3','eye-4'],1):semantic[masks[key]]=region_id
    masks_sha=hashlib.sha256(semantic.tobytes()).hexdigest()
    if masks_sha!=REFERENCE_PART_MASKS_SHA256:raise GeometryError('Mochi detail-v2 derived anatomy masks differ from the independently reviewed mask hash')
    if geometry_signature(mesh)!=REFERENCE_SIGNATURE:raise GeometryError('Anatomical analysis changed source geometry; proposal rejected')
    return masks,{'source_signature':REFERENCE_SIGNATURE,'source_class_mask_sha256':REFERENCE_CLASSES_SHA256,'anatomical_mask_sha256':masks_sha,'whole_part_keys':['tail','right-ear','left-ear','nose'],
        'eye_part_keys':[f'eye-{i}' for i in range(1,len(eyes)+1)],'seed_parameters_mm':{'tail_distal_y':25,'ear_geodesic_growth':2,'nose_geodesic_domain':2,'nose_seed_min_z':124,'nose_excludes_separate_mouth_line':True},
        'cuts':reports,'original_geometry_modified':False,'automatic_approval':False,
        'limitation':'Model-bound local proposal. Anatomical boundary, texture/material assignment and print/assembly checks remain required; smoothing only affects analysis.'}
