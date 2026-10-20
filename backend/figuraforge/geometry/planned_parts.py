"""Compose explicit whole-body cuts and decorative inlays without implicit repair."""
from __future__ import annotations
from types import SimpleNamespace
import numpy as np
from .types import GeometryError
from .surface_parts import make_surface_parts
from .construct import make_inlays
from .compare import nearest
from .validation import require_solid,check_insert_path,DistanceQuery,sample_surface


def _rename(parts,report,prefix):
    mapping={p.id:f'{prefix}{p.id}' for p in parts}
    for part in parts:part.id=mapping[part.id]
    def visit(value):
        if isinstance(value,dict):
            return {k:mapping.get(v,v) if k=='part_id' and isinstance(v,str) else visit(v) for k,v in value.items()}
        if isinstance(value,list):return [visit(v) for v in value]
        return value
    return visit(report)


def _combined_checks(parts,travel):
    """Fail on sampled assembled overlap or a blocked final extraction path."""
    checks=[]
    for i,part in enumerate(parts):
        for j,other in enumerate(parts):
            if j<=i:continue
            if np.any(part.mesh.bounds[1]<other.mesh.bounds[0]-.03) or np.any(other.mesh.bounds[1]<part.mesh.bounds[0]-.03):continue
            penetration=max(0.,-float(DistanceQuery(other.mesh).values(sample_surface(part.mesh,1800)).min()),
                            -float(DistanceQuery(part.mesh).values(sample_surface(other.mesh,1800)).min()))
            if penetration>.03:
                raise GeometryError(f'Planned parts {part.id} and {other.id} overlap (sampled penetration {penetration:.4f} mm). Revise boundaries or connectors.')
    for part in parts:
        if part.role=='body' or part.assembly_direction is None:continue
        direction=np.asarray(part.assembly_direction,float)
        d=direction/np.linalg.norm(direction)*travel
        low=np.minimum(part.mesh.bounds[0],part.mesh.bounds[0]+d)
        high=np.maximum(part.mesh.bounds[1],part.mesh.bounds[1]+d)
        for other in parts:
            if other is part:continue
            if np.any(high<other.mesh.bounds[0]-.03) or np.any(other.mesh.bounds[1]<low-.03):continue
            result=check_insert_path(part.mesh,other.mesh,direction,travel_mm=travel)
            result.update({'part_id':part.id,'obstacle_part_id':other.id})
            checks.append(result)
            if not result['passed']:
                raise GeometryError(f'Planned part {part.id} extraction collides with {other.id} (sampled penetration {result["max_penetration_mm"]} mm). Revise direction, boundaries or assembly plan.')
    return checks


def make_planned_parts(mesh,labels,palette,whole_labels:set[int],**kwargs):
    """Cut whole regions first, then carve remaining labeled exterior inlays.

    New caps/socket surfaces inherit ground color. Original label IDs remain
    independent from their display colors. No mesh is overwritten and a failed
    direction, solid, volume or sampled collision check propagates as an error.
    """
    labels=np.asarray(labels)
    if labels.shape!=(len(mesh.faces),) or not np.issubdtype(labels.dtype,np.integer):
        raise GeometryError('One integer construction label is required per source face')
    if (labels<0).any() or (labels>=len(palette)).any():raise GeometryError('Construction labels must refer to the supplied palette')
    base=int(kwargs.get('base_color',0))
    if not 0<=base<len(palette):raise GeometryError('Base color is outside the supplied palette')
    whole=set(whole_labels)
    if any(isinstance(x,bool) or not isinstance(x,(int,np.integer)) or not 0<=x<len(palette) for x in whole):
        raise GeometryError('Whole-part labels must be valid integer palette indices')
    if base in whole:raise GeometryError('Ground color cannot be marked as a whole part')
    whole.intersection_update(np.unique(labels).tolist())
    if not whole:return make_inlays(mesh,labels,palette,**kwargs)
    inlay_mask=(labels!=base)&~np.isin(labels,list(whole))
    if not inlay_mask.any():return make_surface_parts(mesh,labels,palette,**kwargs)
    require_solid(mesh)
    whole_map=np.where(np.isin(labels,list(whole)),labels,base)
    cut_parts,cut_report=make_surface_parts(mesh,whole_map,palette,**kwargs)
    cut_report=_rename(cut_parts,cut_report,'whole-')
    bodies=[p for p in cut_parts if p.role=='body']
    parts=[p for p in cut_parts if p.role!='body'];reports=[];transfers=[]
    original=SimpleNamespace(mesh=mesh)
    for index,body in enumerate(bodies):
        distance,face_ids,_=nearest(original,body.mesh.triangles_center)
        transferred=labels[face_ids].copy()
        transferred[(distance>.03)|np.isin(transferred,list(whole))]=base
        built,report=make_inlays(body.mesh,transferred,palette,**kwargs)
        report=_rename(built,report,f'rest-{index:03d}-')
        parts.extend(built);reports.append(report)
        transfers.append({'body_id':body.id,'source_surface_faces':int(np.sum(distance<=.03)),
                          'hidden_or_new_faces':int(np.sum(distance>.03)),
                          'inlay_faces':int(np.sum(transferred!=base)),
                          'max_transfer_distance_mm':.03})
    if not bodies:raise GeometryError('Whole-part construction produced no remaining ground body')
    if len({p.id for p in parts})!=len(parts):raise GeometryError('Planned part IDs are not unique')
    for part in parts:require_solid(part.mesh)
    total=float(sum(p.mesh.volume for p in parts));source=float(mesh.volume)
    if total>source+max(1.,source*1e-5):raise GeometryError('Planned parts exceed original volume; possible overlapping cuts or connectors')
    validate=kwargs.get('validate_paths',True)
    checks=_combined_checks(parts,float(kwargs.get('depth_mm',3.2))+float(kwargs.get('pin_length_mm',4.))+3) if validate else []
    return parts,{'strategy':'planned whole parts followed by surface-preserving inlays',
                  'source_volume_mm3':source,'parts_volume_mm3':total,'clearance_void_mm3':max(0.,source-total),
                  'whole_labels':sorted(int(x) for x in whole),'whole_part_report':cut_report,
                  'inlay_reports':reports,'label_transfer':transfers,
                  'interfaces':cut_report.get('interfaces',[]),
                  'pockets':[p for r in reports for p in (r.get('pockets') or [])],
                  'merged_islands':cut_report.get('merged_islands',[])+[m for r in reports for m in r.get('merged_islands',[])],
                  'insertion_checks':cut_report.get('insertion_checks',[])+[c for r in reports for c in r.get('insertion_checks',[])]+checks,
                  'combined_collision_checks':checks,'combined_paths_checked':bool(validate),
                  'limitation':'Discrete sampled collision checks are not an exhaustive intersection or assembly-sequence certificate. Physical fit requires calibration and review.'}
