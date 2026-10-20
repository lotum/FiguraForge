"""Conservative face-mask repair; never change the source geometry or relax QA.

A connected patch can have holes touching at one vertex. Filling an entire small
base island can introduce unrelated normals/undercuts. This helper adds only
individual allowed source faces that agree with the explicit assembly direction
and strictly reduce branched boundary vertices. It is not remeshing or anatomy.
"""
from __future__ import annotations
import numpy as np
from itertools import combinations
from .types import GeometryError


def _branches(mesh,selected):
    faces=np.asarray(mesh.faces)[selected]
    edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    edges,count=np.unique(edges,axis=0,return_counts=True)
    vertices,degree=np.unique(edges[count==1],return_counts=True)
    return set(map(int,vertices[degree>2]))


def repair_patch_boundary(mesh,selected,normal,*,allowed_faces=None,min_alignment=.06,max_added=100):
    """Return a superset of face IDs with no branched boundary, or fail explicitly.

    Original selected faces remain present. Added faces retain their original
    source material identity in downstream native mapping. ``allowed_faces``
    can protect an adjacent anatomical part. No destructive fallback is used.
    """
    ids=np.asarray(selected)
    if ids.ndim!=1 or not np.issubdtype(ids.dtype,np.integer) or not len(ids) or ids.min()<0 or ids.max()>=len(mesh.faces):
        raise GeometryError('Patch face IDs must be a nonempty valid integer array')
    normal=np.asarray(normal,float)
    if normal.shape!=(3,) or not np.isfinite(normal).all() or np.linalg.norm(normal)<1e-8:
        raise GeometryError('Explicit finite patch assembly direction required')
    if not .06<=min_alignment<=1 or type(max_added) is not int or max_added<0:
        raise GeometryError('Patch repair limits cannot relax the assembly normal margin')
    normal=normal/np.linalg.norm(normal);selected_mask=np.zeros(len(mesh.faces),bool);selected_mask[ids]=True
    allowed=np.ones(len(mesh.faces),bool)
    if allowed_faces is not None:
        allowed=np.asarray(allowed_faces)
        if allowed.shape!=(len(mesh.faces),) or allowed.dtype!=bool:raise GeometryError('Allowed faces must be a source-sized boolean mask')
    compatible=(mesh.face_normals@normal)>=min_alignment
    if not compatible[selected_mask].all():raise GeometryError('Original patch already violates assembly normal margin')
    added=[];initial=len(_branches(mesh,selected_mask))
    while bad:=_branches(mesh,selected_mask):
        if len(added)>=max_added:raise GeometryError('Patch boundary repair exceeded bounded additions; split the region')
        # A triangular fan may require two adjacent faces before a touching
        # hole opens. Bounded 1–3-face lookahead avoids changing an entire base
        # island while allowing this genuine local topological repair.
        winner=None
        for vertex in sorted(bad):
            candidates=np.unique(mesh.vertex_faces[vertex]);candidates=candidates[candidates>=0]
            candidates=[int(i) for i in candidates if not selected_mask[i] and allowed[i] and compatible[i]]
            for count in range(1,min(3,max_added-len(added),len(candidates))+1):
                for group in combinations(candidates,count):
                    trial=selected_mask.copy();trial[list(group)]=True;remaining=len(_branches(mesh,trial))
                    if remaining>=len(bad):continue
                    score=(remaining,float(mesh.area_faces[list(group)].sum()),count,group)
                    if winner is None or score<winner[0]:winner=(score,group)
            if winner:break
        if winner is None:raise GeometryError('No compatible source face repairs the branched boundary; split the patch')
        group=list(winner[1]);selected_mask[group]=True;added.extend(group)
    return np.flatnonzero(selected_mask),{'method':'bounded compatible source-face additions at branched boundary vertices',
        'initial_branched_vertices':initial,'final_branched_vertices':0,'added_source_face_ids':added,
        'added_source_area_mm2':float(mesh.area_faces[added].sum()),'source_geometry_modified':False,
        'original_selected_faces_preserved':True,'assembly_direction':normal.tolist(),
        'limitation':'Topological mask proposal only. Projection, source thickness, solids and insertion paths still require validation.'}
